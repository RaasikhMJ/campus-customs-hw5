"""Campus Customs desk API.

From this folder:

    uvicorn main:app --reload --port 8000

The board calls http://localhost:8000. Agents prepare a payment. Only
POST /payments/{ticket_id}/approve changes checking.
"""

from __future__ import annotations

import json
import sqlite3

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import run_desk
from audit import AUDIT_PATH
from db import connect, reset_working_copy

app = FastAPI(title="Campus Customs", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TICKET_IDS = (101, 102, 103)


class ApproveBody(BaseModel):
    approved_by: str = Field(default="owner", max_length=80)


def _cents(value: float) -> int:
    return int(round(float(value) * 100))


def _ticket_row(row: sqlite3.Row) -> dict:
    status = row["status"]
    return {
        "id": row["id"],
        "type": row["type"],
        "requester": row["requester"],
        "subject": row["subject"],
        "sku": row["sku"],
        "size": row["size"],
        "qty": row["qty"],
        "lease_id": row["lease_id"],
        "invoice_id": row["invoice_id"],
        "status": status,
        "open": status == "open",
        "resolved": status == "resolved",
        "notes": row["notes"],
    }


def _tickets(conn: sqlite3.Connection) -> list[dict]:
    marks = ",".join("?" for _ in TICKET_IDS)
    found = conn.execute(
        f"SELECT * FROM tickets WHERE id IN ({marks}) ORDER BY id",
        TICKET_IDS,
    ).fetchall()
    listed = []
    for row in found:
        item = _ticket_row(row)
        move = _cash_move(conn, row)
        if move is not None:
            move = {
                key: move[key]
                for key in ("direction", "kind", "ref_id", "amount", "label", "detail", "already")
                if key in move
            }
        item["cash_move"] = move
        listed.append(item)
    return listed


def _cash_row(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT name, balance, date FROM cash_accounts WHERE name = 'checking'"
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Checking account is missing.")
    return {"name": row["name"], "balance": row["balance"], "date": row["date"]}


def _one_ticket(conn: sqlite3.Connection, ticket_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No ticket {ticket_id}.")
    return row


def _task(row: sqlite3.Row) -> str:
    qty = "none" if row["qty"] is None else row["qty"]
    lease_id = "none" if row["lease_id"] is None else row["lease_id"]
    invoice_id = "none" if row["invoice_id"] is None else row["invoice_id"]
    return (
        f"Work ticket {row['id']} only. "
        f"Type {row['type']}. Requester {row['requester']}. Subject {row['subject']}. "
        f"SKU {row['sku'] or 'none'}, size {row['size'] or 'none'}, qty {qty}. "
        f"Lease id {lease_id}. Invoice id {invoice_id}. "
        f"Notes: {row['notes'] or 'none'}. "
        "Read the shop through your tools. Do not email a customer or call a vendor. "
        "Do not send a payment. On a customer order, the human collects list price. "
        "A vendor invoice on that ticket is not the sale. "
        "Prepare rent or a vendor bill only when this ticket is that bill, "
        "and leave the cash move to the human owner."
        + (
            " This is a bulk price override. Fulfill the requested size and quantity. "
            "Do not substitute another size. An order of 20 or more is 10% off list. That is the owner's rule. "
            "Call Inventory once. Inventory counts the shortfall, asks Customer Service once, "
            "and Customer Service asks Accounting once. "
            "The customer invoice and the reprint cost come back in that reply. Write one owner note and stop."
            if row["type"] == "price_override"
            else ""
        )
    )


def _bulk_sale(conn: sqlite3.Connection, ticket: sqlite3.Row) -> dict | None:
    """Fulfill the requested size. Twenty or more is 10% off list. The shortfall is a reprint."""

    price = conn.execute(
        "SELECT unit_cost, list_price FROM pricing WHERE sku = ?",
        (ticket["sku"],),
    ).fetchone()
    if price is None:
        raise HTTPException(status_code=404, detail=f"No list price for {ticket['sku']}.")
    asked = int(ticket["qty"] or 0)
    asked_size = ticket["size"] or ""
    if asked <= 0 or not asked_size:
        return None
    on_size = conn.execute(
        "SELECT name, qty FROM inventory WHERE sku = ? AND size = ?",
        (ticket["sku"], asked_size),
    ).fetchone()
    if on_size is None:
        raise HTTPException(
            status_code=404,
            detail=f"No {ticket['sku']} in size {asked_size}.",
        )
    on_hand = int(on_size["qty"])
    taken = conn.execute(
        "SELECT amount FROM payments WHERE kind = 'sale' AND ref_id = ?",
        (ticket["id"],),
    ).fetchone()
    if taken is not None:
        balance = _cash_row(conn)["balance"]
        rate = 0.10 if asked >= 20 else 0.0
        off = "10% off list" if rate else "list price"
        return {
            "direction": "in",
            "kind": "sale",
            "ref_id": int(ticket["id"]),
            "amount": taken["amount"],
            "label": f"{on_size['name']}, size {asked_size}, {asked} at {off}",
            "detail": (
                f"Already recorded. ${taken['amount']:,.2f} came in for "
                f"{asked} size {asked_size} at {off}. Checking is ${balance:,.2f}."
            ),
            "already": True,
        }
    short = max(0, asked - on_hand)
    rate = 0.10 if asked >= 20 else 0.0
    sale_cents = _cents(float(price["list_price"]) * asked * (1 - rate))
    reprint_cents = _cents(price["unit_cost"]) * short
    bill = conn.execute(
        """
        SELECT invoices.id, invoices.amount, invoices.status, vendors.name
        FROM invoices
        JOIN vendors ON vendors.id = invoices.vendor_id
        WHERE invoices.id = 501
        """
    ).fetchone()
    bill_cents = 0
    if short > 0 and bill is not None and bill["status"] == "open":
        bill_cents = _cents(bill["amount"])
    legs: list[dict] = [
        {
            "direction": "in",
            "kind": "sale",
            "ref_id": int(ticket["id"]),
            "amount": sale_cents / 100,
        }
    ]
    if bill_cents > 0:
        legs.append(
            {
                "direction": "out",
                "kind": "invoice",
                "ref_id": int(bill["id"]),
                "amount": bill_cents / 100,
            }
        )
    if reprint_cents > 0:
        legs.append(
            {
                "direction": "out",
                "kind": "reprint",
                "ref_id": int(ticket["id"]),
                "amount": reprint_cents / 100,
            }
        )
    off = "10% off list" if rate else "list price"
    parts = [
        f"${sale_cents / 100:,.2f} comes in for {asked} size {asked_size} at {off}.",
        f"Size {asked_size} has {on_hand} on the rack.",
    ]
    if short > 0:
        parts.append(f"The {short} short are a reprint at cost, ${reprint_cents / 100:,.2f}.")
    if bill_cents > 0:
        parts.append(
            f"${bill_cents / 100:,.2f} pays {bill['name']} invoice {bill['id']} "
            "so that printer will ship."
        )
    balance_cents = _cents(_cash_row(conn)["balance"])
    end_cents = balance_cents + sale_cents - bill_cents - reprint_cents
    parts.append(f"The till ends at ${end_cents / 100:,.2f}.")
    return {
        "direction": "in",
        "kind": "sale",
        "ref_id": int(ticket["id"]),
        "amount": sale_cents / 100,
        "label": f"{on_size['name']}, size {asked_size}, {asked} at {off}",
        "detail": " ".join(parts),
        "already": taken is not None,
        "legs": legs,
        "stock": {
            "sku": ticket["sku"],
            "size": asked_size,
            "qty_after": on_hand + short - asked,
        },
    }


def _cash_move(conn: sqlite3.Connection, ticket: sqlite3.Row) -> dict | None:
    """The human cash action for this ticket. None when the ticket has no till move."""

    if ticket["type"] == "customer_order" and ticket["sku"]:
        price = conn.execute(
            "SELECT list_price FROM pricing WHERE sku = ?",
            (ticket["sku"],),
        ).fetchone()
        if price is None:
            raise HTTPException(status_code=404, detail=f"No list price for {ticket['sku']}.")
        qty = int(ticket["qty"] or 0)
        if qty <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Ticket {ticket['id']} has no quantity to collect.",
            )
        amount_cents = _cents(price["list_price"]) * qty
        taken = conn.execute(
            "SELECT id FROM payments WHERE kind = 'sale' AND ref_id = ?",
            (ticket["id"],),
        ).fetchone()
        return {
            "direction": "in",
            "kind": "sale",
            "ref_id": int(ticket["id"]),
            "amount": amount_cents / 100,
            "label": f"{ticket['subject']}, {qty} at the list price",
            "already": taken is not None,
        }

    if ticket["type"] == "price_override" and ticket["sku"]:
        return _bulk_sale(conn, ticket)

    if ticket["invoice_id"] is not None:
        bill = conn.execute(
            "SELECT id, amount, status, description FROM invoices WHERE id = ?",
            (ticket["invoice_id"],),
        ).fetchone()
        if bill is None:
            raise HTTPException(status_code=404, detail="That invoice is not in the shop.")
        return {
            "direction": "out",
            "kind": "invoice",
            "ref_id": int(bill["id"]),
            "amount": _cents(bill["amount"]) / 100,
            "label": bill["description"] or f"Invoice {bill['id']}",
            "already": bill["status"] != "open",
        }

    if ticket["lease_id"] is not None:
        lease = conn.execute(
            "SELECT id, monthly_rent, space_name, landlord FROM leases WHERE id = ?",
            (ticket["lease_id"],),
        ).fetchone()
        if lease is None:
            raise HTTPException(status_code=404, detail="That lease is not in the shop.")
        paid = conn.execute(
            "SELECT id FROM payments WHERE kind = 'lease' AND ref_id = ?",
            (lease["id"],),
        ).fetchone()
        return {
            "direction": "out",
            "kind": "lease",
            "ref_id": int(lease["id"]),
            "amount": _cents(lease["monthly_rent"]) / 100,
            "label": f"{lease['space_name']} rent, {lease['landlord']}",
            "already": paid is not None,
        }

    return None


def _events(limit: int) -> list[dict]:
    if not AUDIT_PATH.is_file() or AUDIT_PATH.stat().st_size == 0:
        return []
    try:
        parsed = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    grouped: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    for row in parsed:
        if not isinstance(row, dict):
            continue
        key = (str(row.get("run_id") or ""), str(row.get("agent") or ""))
        if key not in grouped:
            grouped[key] = {
                "time": row.get("time") or "",
                "run_id": key[0],
                "agent": key[1],
                "said": "",
                "tools": [],
            }
            order.append(key)
        bucket = grouped[key]
        if row.get("time"):
            bucket["time"] = row["time"]
        step = row.get("step")
        detail = row.get("detail") or ""
        if step in ("reply", "loop_end") and detail:
            bucket["said"] = detail
        elif step == "error" and detail and not bucket["said"]:
            bucket["said"] = detail
        tool = row.get("tool") or ""
        if tool and tool not in bucket["tools"]:
            bucket["tools"].append(tool)
    return [grouped[key] for key in order][-limit:]


@app.get("/tickets")
def list_tickets():
    """The three desk tickets, each marked open or resolved."""

    conn = connect()
    try:
        return {"tickets": _tickets(conn)}
    finally:
        conn.close()


@app.post("/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int):
    """Run the agent team on one ticket. This route does not move cash."""

    conn = connect()
    try:
        ticket = _one_ticket(conn, ticket_id)
        task = _task(ticket)
    finally:
        conn.close()
    result = await run_desk(task)
    return {
        "ticket_id": ticket_id,
        "run_id": result.run_id,
        "answer": result.answer,
        "delegations": [item.model_dump() for item in result.delegations],
        "llm_name": result.llm_name,
        "cash_changed": False,
    }


@app.get("/events")
def recent_events(limit: int = Query(default=40, ge=1, le=200)):
    """What each agent said, and which tools that agent used, newest runs last."""

    return {"events": _events(limit)}


@app.post("/payments/{ticket_id}/approve")
def approve_payment(ticket_id: int, body: ApproveBody = Body(default_factory=ApproveBody)):
    """Human approval. This is the only route that changes checking."""

    approved_by = body.approved_by.strip() or "owner"
    conn = connect()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        ticket = _one_ticket(conn, ticket_id)
        move = _cash_move(conn, ticket)
        if move is None:
            raise HTTPException(
                status_code=400,
                detail=f"Ticket {ticket_id} has no sale, invoice, or lease. Cash was not changed.",
            )
        if move["already"]:
            raise HTTPException(
                status_code=409,
                detail=f"Ticket {ticket_id} already moved cash. Nothing was written again.",
            )
        amount_cents = _cents(move["amount"])
        if amount_cents <= 0:
            raise HTTPException(status_code=400, detail="This approval has no dollar amount.")
        cash = _cash_row(conn)
        balance_cents = _cents(cash["balance"])
        shop_date = conn.execute("SELECT date_today FROM desk").fetchone()["date_today"]
        legs = move.get("legs") or [
            {
                "direction": move["direction"],
                "kind": move["kind"],
                "ref_id": move["ref_id"],
                "amount": move["amount"],
            }
        ]
        running = balance_cents
        for leg in legs:
            leg_cents = _cents(leg["amount"])
            if leg["direction"] == "in":
                running += leg_cents
            elif leg_cents > running:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Checking has ${balance_cents / 100:.2f}. "
                        "This order would take the till below zero, so nothing was written."
                    ),
                )
            else:
                running -= leg_cents
        new_cents = running
        kind = move["kind"]
        ref_id = move["ref_id"]
        label = move["label"]
        conn.execute(
            "UPDATE cash_accounts SET balance = ?, date = ? WHERE name = 'checking'",
            (new_cents / 100, shop_date),
        )
        cursor = None
        for leg in legs:
            if leg["kind"] == "invoice":
                conn.execute(
                    "UPDATE invoices SET status = 'paid' WHERE id = ?",
                    (leg["ref_id"],),
                )
            elif leg["kind"] == "lease":
                conn.execute(
                    "UPDATE leases SET notes = ? WHERE id = ?",
                    (
                        f"Paid {shop_date} from checking, approved by {approved_by}.",
                        leg["ref_id"],
                    ),
                )
            cursor = conn.execute(
                """
                INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by)
                VALUES (?, ?, ?, 'checking', ?, ?)
                """,
                (leg["kind"], leg["ref_id"], leg["amount"], shop_date, approved_by),
            )
        stock = move.get("stock")
        if stock is not None:
            conn.execute(
                "UPDATE inventory SET qty = ? WHERE sku = ? AND size = ?",
                (stock["qty_after"], stock["sku"], stock["size"]),
            )
        conn.commit()
        return {
            "approved": True,
            "ticket_id": ticket_id,
            "payment_id": cursor.lastrowid,
            "direction": move["direction"],
            "kind": kind,
            "ref_id": ref_id,
            "label": label,
            "detail": move.get("detail") or "",
            "amount": amount_cents / 100,
            "account": "checking",
            "paid_at": shop_date,
            "approved_by": approved_by,
            "balance_before": balance_cents / 100,
            "balance_after": new_cents / 100,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/cash")
def checking_balance():
    """Current checking balance from cash_accounts."""

    conn = connect()
    try:
        return _cash_row(conn)
    finally:
        conn.close()


@app.post("/reset")
def reset_database():
    """Replace the working database with the original file. The audit trail stays."""

    reset_working_copy()
    conn = connect()
    try:
        return {
            "reset": True,
            "database": "campus_customs_new.db",
            "cash": _cash_row(conn),
            "tickets": _tickets(conn),
        }
    finally:
        conn.close()
