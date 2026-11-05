"""Types for the Campus Customs desk team."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]

ROLES: tuple[Role, ...] = (
    "boss",
    "inventory",
    "accounting",
    "facilities",
    "customer_service",
)

ROLE_LABELS: dict[Role, str] = {
    "boss": "Boss, Chief Executive Officer / General Manager",
    "inventory": "Inventory, Director of Inventory & Merchandising",
    "accounting": "Accounting, Director of Accounting & Finance",
    "facilities": "Facilities, Director of Facilities & Store Operations",
    "customer_service": "Customer Service, Director of Customer Experience",
}


class Delegation(BaseModel):
    """One handoff from one role to another during a desk run."""

    from_role: Role
    to_role: Role
    task: str
    reply: str = ""


class TeamResult(BaseModel):
    """What the Boss returns after the team has worked a ticket."""

    lead: Role = "boss"
    answer: str
    delegations: list[Delegation] = Field(default_factory=list)
    llm_name: str
    run_id: str = ""
