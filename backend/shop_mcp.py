"""Shop facts for the agents. Every read goes through the Campus Customs MCP server."""

from __future__ import annotations

from typing import Any

from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parent.parent

_PYTHON = ROOT / "mcp_server" / ".venv" / "bin" / "python"
_SERVER = ROOT / "mcp_server" / "server.py"


async def call_shop_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one tool on the MCP server. The server reads campus_customs_new.db."""
    if not _PYTHON.is_file():
        raise FileNotFoundError(f"MCP Python is missing: {_PYTHON}")
    client = Client(StdioTransport(command=str(_PYTHON), args=[str(_SERVER)]))
    async with client:
        result = await client.call_tool(name, arguments)
    data = result.data
    if isinstance(data, dict):
        return data
    return {"result": data}
