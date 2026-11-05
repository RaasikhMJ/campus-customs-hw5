# Campus Customs harness

Shop date for every due-date check is `desk.date_today`: **2026-08-31**.

MCP tools and the backend open `data/campus_customs_new.db` only, through `shop_db.connect()`. `data/campus_customs.db` is the untouched reset source. `shop_db.reset_working_copy()` replaces the working copy from that original file.

## Shop rules

1. `desk.date_today` is today. Overdue means a due date before that day, not before the real calendar date.
2. Vendor lead times come from `vendors.lead_days`. They are not guessed.
3. A vendor with an open unpaid invoice does not ship new product.
4. A human must approve every till move. A customer order collects list price into checking. A rent notice or vendor bill pays out, and that pay also marks the lease or invoice.
5. If checking cannot cover a payment, the pay is refused. The balance never goes negative.
6. Ticket 101 collects the Bulldog tee at list price. It does not pay invoice 501. That reprint bill stays open until a separate pay is approved.
7. Reset `campus_customs_new.db` from the original file before a full run of the tickets.
8. Do not email customers or call vendors. Customer Service drafts stay on the board.

---

## desk

Fields: `date_today`, `notes`

Agents treat `date_today` as today and use it to decide what is overdue.

## tickets

Fields: `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at`

This is the board the agents work, and `sku`, `lease_id`, and `invoice_id` point at the other tables.

## inventory

Fields: `sku`, `name`, `size`, `qty`, `location`

Agents check `qty` by SKU and size to see whether a ticket can be filled from the rack.

## pricing

Fields: `sku`, `unit_cost`, `list_price`

Agents use cost and list price to judge the margin on a discount or a reorder.

## vendors

Fields: `id`, `name`, `specialty`, `lead_days`

Agents use this table to choose who can restock and how many days the shipment takes.

## invoices

Fields: `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`

An open bill blocks that vendor from shipping, and `due_date` tells Accounting if it is overdue.

## leases

Fields: `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`

Rent tickets land here for the space, the landlord, the amount, and the next due date.

## cash_accounts

Fields: `name`, `balance`, `date`

This is the cash a payment may spend, and the pay tool must refuse if `balance` would go negative.

## payments

Fields: `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`

A row is written only after a human approves a payment, naming who approved it and which bill was paid.

---

## How the three open tickets link

Shop date: 2026-08-31. Checking balance: $3,400.00.

### Ticket 101 — customer order

Tauhid Zaman wants 1 Classic Bulldog Tee (`CC-TEE-WHITE`), size S. Status `open`.

- Inventory: size S has **qty 0** in Aisle B. Sizes M/L/XL are in stock.
- Pricing: unit cost $8.00, list price $28.00.
- Invoice 501 is attached. It is **open**, $840.00, due **2026-08-28** (3 days before the shop date), described as a rush reprint of `CC-TEE-WHITE` size S.
- That invoice belongs to vendor 1, Bulldog Print Co (apparel reprint, lead time 5 days). An open unpaid invoice means this vendor does not ship new product until it is paid.

### Ticket 102 — rent notice

Elm City Properties says shop rent is due in 2 days. Status `open`. No SKU and no invoice.

- Lease 1: Chapel Street shop, landlord Elm City Properties, monthly rent **$2,400.00**, next due **2026-09-02** (2 days after the shop date).
- Paying it from checking would leave $1,000.00. No payment row exists yet.

### Ticket 103 — price override

Yale AI Club wants 20 Basic Hoodie Big Yale (`CC-HOOD-NAVY`), size M, at a bulk discount. Status `open`. No lease and no invoice.

- Inventory: size M has **qty 8** in Aisle A, so the rack is short 12 hoodies. S/L/XL of the same SKU are in stock, but not in the requested size.
- Pricing: unit cost $22.00, list price $58.00.
- No vendor invoice is tied to this ticket.

---

## MCP tools

### read_vendor_invoice

Reads `invoices` and `vendors`. Unlocks ticket 101.

Tauhid's order for one `CC-TEE-WHITE` in size S points at invoice 501, the open $840 rush reprint, so this tool is what shows that bill is unpaid and that Bulldog Print Co (5-day lead) is the vendor who would have to print it.

### read_lease

Reads `leases`. Unlocks ticket 102.

Elm City's rent notice names no amount of its own and points at lease 1, so this tool is what returns the Chapel Street shop's $2,400 monthly rent and the 2026-09-02 due date.

### check_size_on_hand

Reads `inventory`. Unlocks ticket 103.

The Yale AI Club wants 20 `CC-HOOD-NAVY` hoodies in size M, so this tool is what returns that size's on-hand quantity and shows the rack has 8, not 20.

Every shop tool reads `data/campus_customs_new.db` through the MCP server. No agent opens that file on its own. Slack, Shopify, QuickBooks, and the other outside products in the elite stack are not connected. The shop database does not have their data, and this desk does not email customers or move cash.

### list_open_tickets

Reads `tickets` where status is open. Unlocks the board for the Boss: tickets 101, 102, and 103, with the sku, lease, or invoice each one points at.

### read_ticket

Reads `tickets`. Unlocks whichever ticket id the team was given, so a department sees the requester, the qty asked, and the foreign key instead of guessing them.

### read_shop_date

Reads `desk`. Unlocks the overdue check on ticket 101 (invoice due 2026-08-28) and ticket 102 (rent due 2026-09-02). The shop date is 2026-08-31.

### read_cash_accounts

Reads `cash_accounts`. Unlocks the pay-or-refuse check on ticket 101 ($840) and ticket 102 ($2,400). Checking starts at $3,400. The tool does not deduct it.

### read_sku_price

Reads `pricing`. Unlocks ticket 103's discount: `CC-HOOD-NAVY` costs $22 and lists at $58. It does not invent a margin beyond those two numbers.

### list_sizes_on_hand

Reads `inventory`. Unlocks the rest of the size run for ticket 101 and ticket 103, so Inventory can say which other sizes are on the rack without inventing them.

---

## Agents

The ask still goes to the department that owns the row. The other four can be asked. Tools below are the ones attached to that agent. The first three shop tools remain on every agent so a fact is read from the server instead of guessed.

### Boss — Chief Executive Officer / General Manager

Prompt: `backend/prompts/boss.md`

- `list_open_tickets` reads `tickets`. This is the board before Boss assigns 101, 102, or 103.
- `read_ticket` reads `tickets`. One ticket's sku, lease_id, or invoice_id.
- `read_shop_date` reads `desk`. Today for the overdue check.
- `check_size_on_hand` reads `inventory`. `read_vendor_invoice` reads `invoices` and `vendors`. `read_lease` reads `leases`.

### Inventory — Director of Inventory & Merchandising

Prompt: `backend/prompts/inventory.md`

- `check_size_on_hand` and `list_sizes_on_hand` read `inventory`. Ticket 101 size S is 0. Ticket 103 size M is 8 against an ask of 20.
- `read_sku_price` reads `pricing`. Cost and list price only. No forecast.
- `read_vendor_invoice` reads `invoices` and `vendors`. Ticket 101 cannot be restocked while invoice 501 is open.
- `read_ticket` reads `tickets`.

### Accounting — Director of Accounting & Finance

Prompt: `backend/prompts/accounting.md`

- `read_vendor_invoice` reads `invoices` and `vendors`. Ticket 101's $840 bill is prepared, not sent.
- `read_cash_accounts` reads `cash_accounts`. Checking is $3,400 before any approval.
- `read_shop_date` reads `desk`. Invoice 501 is due before that date.
- `read_sku_price` reads `pricing`. Ticket 103's discount is judged from $22 cost and $58 list.
- `read_lease` reads `leases`. Ticket 102's $2,400 rent is the other payment to prepare.
- `read_ticket` reads `tickets`.

### Facilities — Director of Facilities & Store Operations

Prompt: `backend/prompts/facilities.md`

- `read_lease` reads `leases`. Ticket 102 is lease 1, Chapel Street, $2,400, next due 2026-09-02.
- `read_shop_date` reads `desk`. Rent is not overdue on 2026-08-31.
- `read_ticket` reads `tickets`.
- `read_vendor_invoice` and `check_size_on_hand` stay available so a merchandise fact is not invented. Those rows belong to Accounting and Inventory.

### Customer Service — Director of Customer Experience

Prompt: `backend/prompts/customer_service.md`

- `read_ticket` reads `tickets`. The draft uses the requester and the notes.
- `check_size_on_hand` and `list_sizes_on_hand` read `inventory`. A size is named only when that row's qty is above zero.
- `read_vendor_invoice` and `read_lease` stay available. Customer Service does not promise a paid bill or email the landlord.

---

## Safety

Customers and vendors stay off the wire. Customer Service writes a draft and leaves it on the board. No agent emails a customer or calls a vendor.

Money does not move inside an agent loop. There is no pay tool on the MCP server. Accounting and Facilities may recommend a payment. The human owner is the only one who can authorize a till move. A payment that would push checking below zero is refused. A customer-order approval collects list price. It does not pay a vendor invoice that happens to sit on the same ticket.

Shop numbers come from `data/campus_customs_new.db` through the MCP server. A figure that no tool returned is not a fact.

Token use is capped in `backend/agents/team.py` so one desk run stays small:

- Each agent loop may call `gpt-6-luna` at most 4 times (`REQUEST_LIMIT`).
- A handoff chain may go Boss, then Inventory, Customer Service, and Accounting, then it stops (`MAX_DEPTH` 4). Ticket 103 uses that chain once. Accounting's invoice returns up the chain, so the Boss is not asked again.
- One desk run may contain at most 4 handoffs (`MAX_HANDOFFS`).
- A failed model call is retried once, not in a loop.

At that ceiling a run is 4 model calls for the Boss plus 4 calls for each of 4 handoffs, which is 20 calls, and most tickets should stop well before that. Each audit line is clipped, and `output/audit_trail.json` is appended to, not rewritten, so a run is not repeated just to recover the log.

---

## API routes

From `backend/`, `uvicorn main:app --reload --port 8000` serves `http://localhost:8000`.

- `GET /tickets` — returns tickets 101, 102, and 103 and whether each is open or resolved.
- `POST /tickets/{ticket_id}/run` — runs the agent team on that ticket and does not move cash.
- `GET /events` — recent agent events: what each agent said and which tools they used.
- `POST /payments/{ticket_id}/approve` — the human approve click. Ticket 101 adds the tee's list price to checking. Ticket 102 lowers checking by the rent and marks the lease. A pay that would go negative is refused. Ticket 103 fulfills 20 size M. Twenty or more is 10% off list, so the club pays $1,044. Size M has 8, so the click also pays Bulldog invoice 501 and the cost of the 12 missing hoodies, then the rack shows that size fulfilled.
- `GET /cash` — the current checking balance from `cash_accounts`.
- `POST /reset` — copies `data/campus_customs.db` over `data/campus_customs_new.db` for a fresh run.

---

## Dashboard

From `frontend/`, `npm run dev` opens the React desk at `http://localhost:5173`. That page calls `http://localhost:8000`. The shop allows that Vite origin.

The top is one collage of real Trinidad and Tobago shores. Under it, checking is the till, read from `GET /cash`. The three tickets come from `GET /tickets`. Picking one and starting the team calls `POST /tickets/{ticket_id}/run`. While it runs, the five chairs fill from `GET /events`: Boss, Inventory, Accounting, Facilities, and Customer Service, each with its own towel color. When the run finishes, the card stamp says Resolved and a short summary lists who spoke and which tools they used. The approval bar calls `POST /payments/{ticket_id}/approve`. On the Bulldog tee it says the list price is coming in. On rent it says the rent is leaving. The till changes only after that human click. On the hoodie, the bar is 20 size M at 10% off, plus the printer bill and the missing pieces.

The three resolved runs are appended in `output/audit_trail.json`. They were not rewritten over older lines.
