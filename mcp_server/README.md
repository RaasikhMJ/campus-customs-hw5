# Campus Customs MCP server

Agents read the shop through this server. The file is `data/campus_customs_new.db`. The original `data/campus_customs.db` is never opened.

From this folder, `python server.py` starts the server.

## Guardrails

These are enforced in code, not only in the prompts.

- Every tool is a `SELECT`. `_rows` rejects anything else, and the connection is `query_only`. The server cannot pay a bill, change a balance, or mark a ticket emailed.
- There is no email tool and no vendor-call tool. Customer Service drafts stay on the board.
- Cash is a balance read (`read_cash_accounts`). A payment still needs the human owner. A payment that would push checking below zero is refused by the shop rules, and this server has no tool that could do it.
- One desk run calls `gpt-6-luna` at most 4 times per agent, with at most 4 handoffs and a chain of Boss plus two more agents (`backend/agents/team.py`).

## Tools

Nine tools. Each one reads `data/campus_customs_new.db`.

| Tool | Tables |
|---|---|
| `list_open_tickets` | `tickets` |
| `read_ticket` | `tickets` |
| `read_shop_date` | `desk` |
| `read_cash_accounts` | `cash_accounts` |
| `read_sku_price` | `pricing` |
| `list_sizes_on_hand` | `inventory` |
| `check_size_on_hand` | `inventory` |
| `read_vendor_invoice` | `invoices`, `vendors` |
| `read_lease` | `leases` |
