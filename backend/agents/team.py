"""Campus Customs desk team.

Five PydanticAI agents share one model. Any agent may ask any other agent.
Shop rows come from the MCP server, not from a second database layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import TextPart, ToolCallPart
from pydantic_ai.usage import UsageLimits

from audit import append_step, tool_returns
from models import ROLES, Delegation, Role, TeamResult
from shop_mcp import call_shop_tool

from .config import MODEL_NAME, build_model, load_prompt

# Boss, then Inventory, Customer Service, and Accounting.
# Ticket 103 needs that fourth seat so Accounting can name the invoice
# without the Boss being asked again. A fifth seat is still refused.
MAX_DEPTH = 4
MAX_HANDOFFS = 4
REQUEST_LIMIT = 4

_PROMPT_FILES: dict[Role, str] = {
    "boss": "boss.md",
    "inventory": "inventory.md",
    "accounting": "accounting.md",
    "facilities": "facilities.md",
    "customer_service": "customer_service.md",
}


@dataclass
class DeskDeps:
    """Shared across the whole handoff chain so a loop can be seen and stopped."""

    run_id: str
    stack: list[Role] = field(default_factory=list)
    delegations: list[Delegation] = field(default_factory=list)


def _agents() -> dict[Role, Agent[DeskDeps, str]]:
    model = build_model()
    agents: dict[Role, Agent[DeskDeps, str]] = {}
    for role in ROLES:
        agents[role] = Agent(
            model,
            deps_type=DeskDeps,
            output_type=str,
            instructions=load_prompt(_PROMPT_FILES[role]),
            retries=1,
        )
    for role, agent in agents.items():
        _add_shop_tools(agent, role)
        for other in ROLES:
            if other != role:
                agent.tool(_ask_tool(other))
    return agents


def _add_shop_tools(agent: Agent[DeskDeps, str], role: Role) -> None:
    @agent.tool_plain
    async def check_size_on_hand(sku: str, size: str) -> dict:
        """Read one inventory row from the MCP server for this SKU and size.

        Returns found, sku, name, size, qty, and location. found is false when
        that SKU and size are not in the working database.
        """

        return await call_shop_tool("check_size_on_hand", {"sku": sku, "size": size})

    @agent.tool_plain
    async def read_vendor_invoice(invoice_id: int) -> dict:
        """Read one invoice and its vendor from the MCP server.

        Returns the bill amount, due date, status, description, vendor name,
        specialty, and lead_days. found is false when the id is not in invoices.
        """

        return await call_shop_tool("read_vendor_invoice", {"invoice_id": invoice_id})

    @agent.tool_plain
    async def read_lease(lease_id: int) -> dict:
        """Read one lease from the MCP server.

        Returns the space, landlord, monthly rent, and next due date.
        found is false when the id is not in leases.
        """

        return await call_shop_tool("read_lease", {"lease_id": lease_id})

    extras = _EXTRA_TOOLS[role]
    if "list_open_tickets" in extras:
        agent.tool_plain(list_open_tickets)
    if "read_ticket" in extras:
        agent.tool_plain(read_ticket)
    if "read_shop_date" in extras:
        agent.tool_plain(read_shop_date)
    if "read_cash_accounts" in extras:
        agent.tool_plain(read_cash_accounts)
    if "read_sku_price" in extras:
        agent.tool_plain(read_sku_price)
    if "list_sizes_on_hand" in extras:
        agent.tool_plain(list_sizes_on_hand)


_EXTRA_TOOLS: dict[Role, tuple[str, ...]] = {
    "boss": ("list_open_tickets", "read_ticket", "read_shop_date"),
    "inventory": ("read_ticket", "list_sizes_on_hand", "read_sku_price"),
    "accounting": ("read_ticket", "read_shop_date", "read_cash_accounts", "read_sku_price"),
    "facilities": ("read_ticket", "read_shop_date"),
    "customer_service": ("read_ticket", "list_sizes_on_hand"),
}


async def list_open_tickets() -> dict:
    """Read the open tickets from the MCP server. Does not invent a board."""

    return await call_shop_tool("list_open_tickets", {})


async def read_ticket(ticket_id: int) -> dict:
    """Read one ticket from the MCP server by id."""

    return await call_shop_tool("read_ticket", {"ticket_id": ticket_id})


async def read_shop_date() -> dict:
    """Read desk.date_today from the MCP server. That date is the shop's today."""

    return await call_shop_tool("read_shop_date", {})


async def read_cash_accounts() -> dict:
    """Read cash account balances from the MCP server. This does not move money."""

    return await call_shop_tool("read_cash_accounts", {})


async def read_sku_price(sku: str) -> dict:
    """Read unit cost and list price for one SKU from the MCP server."""

    return await call_shop_tool("read_sku_price", {"sku": sku})


async def list_sizes_on_hand(sku: str) -> dict:
    """Read every size of one SKU from the MCP server."""

    return await call_shop_tool("list_sizes_on_hand", {"sku": sku})


def _ask_tool(target: Role):
    label = target.replace("_", " ")

    async def ask_teammate(ctx: RunContext[DeskDeps], task: str) -> str:
        return await _delegate(ctx, target, task)

    ask_teammate.__name__ = f"ask_{target}"
    ask_teammate.__doc__ = (
        f"Hand one task to {label}. "
        "They can ask the other agents and can read the shop through the MCP tools. "
        "Ask only when the task is their job. Do not ask every teammate."
    )
    return ask_teammate


async def _delegate(ctx: RunContext[DeskDeps], target: Role, task: str) -> str:
    deps = ctx.deps
    caller: Role = deps.stack[-1] if deps.stack else "boss"
    if target in deps.stack:
        note = (
            f"{target} is already on this task. "
            "Answer from the facts you have instead of asking them again."
        )
        append_step(
            {
                "run_id": deps.run_id,
                "agent": caller,
                "step": "handoff_refused",
                "tool": f"ask_{target}",
                "detail": note,
            }
        )
        return note
    if len(deps.stack) >= MAX_DEPTH or len(deps.delegations) >= MAX_HANDOFFS:
        note = "Handoff limit reached. Give your best answer from the facts already in hand."
        append_step(
            {
                "run_id": deps.run_id,
                "agent": caller,
                "step": "handoff_refused",
                "tool": f"ask_{target}",
                "detail": note,
            }
        )
        return note

    handoff = Delegation(from_role=caller, to_role=target, task=task)
    deps.delegations.append(handoff)
    deps.stack.append(target)
    append_step(
        {
            "run_id": deps.run_id,
            "agent": caller,
            "step": "handoff",
            "tool": f"ask_{target}",
            "detail": task,
        }
    )
    try:
        handoff.reply = await _run_agent(target, task, deps)
    except Exception as exc:
        handoff.reply = f"{target} hit an error: {type(exc).__name__}: {exc}"[:400]
        append_step(
            {
                "run_id": deps.run_id,
                "agent": target,
                "step": "error",
                "detail": handoff.reply,
            }
        )
    finally:
        deps.stack.pop()
    return handoff.reply


def _audit_node(role: Role, run_id: str, node) -> None:
    if Agent.is_model_request_node(node):
        append_step({"run_id": run_id, "agent": role, "step": "model_request"})
        return
    if not Agent.is_call_tools_node(node):
        return
    parts = node.model_response.parts
    calls = [part for part in parts if isinstance(part, ToolCallPart)]
    if calls:
        for part in calls:
            args = part.args
            if hasattr(part, "args_as_dict"):
                try:
                    args = part.args_as_dict()
                except Exception:
                    args = part.args
            append_step(
                {
                    "run_id": run_id,
                    "agent": role,
                    "step": "tool_call",
                    "tool": part.tool_name,
                    "args": args,
                }
            )
        return
    text = " ".join(
        part.content for part in parts if isinstance(part, TextPart) and part.content.strip()
    )
    if text:
        append_step({"run_id": run_id, "agent": role, "step": "reply", "detail": text})


async def _run_agent(role: Role, task: str, deps: DeskDeps) -> str:
    """One agent's loop. Each step is appended to the audit trail before the next step."""

    append_step(
        {
            "run_id": deps.run_id,
            "agent": role,
            "step": "loop_start",
            "detail": task,
        }
    )
    async with AGENTS[role].iter(
        task,
        deps=deps,
        usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
    ) as run:
        async for node in run:
            _audit_node(role, deps.run_id, node)
        output = run.result.output if run.result else ""
        if run.result is not None:
            for row in tool_returns(run.result):
                append_step({"run_id": deps.run_id, "agent": role, "step": "tool_result", **row})
    append_step(
        {
            "run_id": deps.run_id,
            "agent": role,
            "step": "loop_end",
            "detail": output,
        }
    )
    return output


AGENTS = _agents()


def team_links() -> dict[str, list[str]]:
    """Who each agent can ask, taken from the tools on the live agents."""

    links: dict[str, list[str]] = {}
    for role, agent in AGENTS.items():
        names = sorted(agent._function_toolset.tools)
        links[role] = [name.removeprefix("ask_") for name in names if name.startswith("ask_")]
    return links


def model_name_in_use() -> str:
    model = AGENTS["boss"].model
    named = getattr(model, "model_name", None) or getattr(model, "model_id", None)
    return str(named or MODEL_NAME)


async def run_desk(task: str) -> TeamResult:
    """Start at the Boss. The Boss's loop can hand the task to any teammate."""

    deps = DeskDeps(run_id=uuid.uuid4().hex[:12], stack=["boss"])
    try:
        answer = await _run_agent("boss", task, deps)
    except Exception as exc:
        answer = f"boss hit an error: {type(exc).__name__}: {exc}"[:400]
        append_step(
            {
                "run_id": deps.run_id,
                "agent": "boss",
                "step": "error",
                "detail": answer,
            }
        )
    return TeamResult(
        answer=answer,
        delegations=deps.delegations,
        llm_name=MODEL_NAME,
        run_id=deps.run_id,
    )
