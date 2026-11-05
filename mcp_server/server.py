"""Campus Customs MCP server.

Every agent calls these tools. They read data/campus_customs_new.db and
nothing else. They do not invent rows.

Run from this folder:  python server.py
"""

from __future__ import annotations

from fastmcp import FastMCP

from db import connect

mcp = FastMCP("campus-customs")


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    """Read the working copy. Writes, payments, and customer messages are refused."""
    if not sql.lstrip().upper().startswith("SELECT"):
        raise RuntimeError("MCP tools are read-only. They cannot change cash or contact a customer.")
    conn = connect()
    try:
        conn.execute("PRAGMA query_only = ON")
        found = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in found]


@mcp.tool
def read_vendor_invoice(invoice_id: int) -> dict:
    """Return one invoice and its vendor from campus_customs_new.db.

    Use this for ticket 101, which points at an invoice_id. The result is
    that invoice's amount, due date, status, and description, plus the
    vendor's name, specialty, and lead_days. If the id is not in invoices,
    found is false.
    """
    rows = _rows(
        """
        SELECT
            invoices.id,
            invoices.vendor_id,
            invoices.amount,
            invoices.due_date,
            invoices.status,
            invoices.description,
            vendors.name AS vendor_name,
            vendors.specialty,
            vendors.lead_days
        FROM invoices
        LEFT JOIN vendors ON vendors.id = invoices.vendor_id
        WHERE invoices.id = ?
        """,
        (invoice_id,),
    )
    if not rows:
        return {"found": False, "invoice_id": invoice_id}
    return {"found": True, **rows[0]}


@mcp.tool
def read_lease(lease_id: int) -> dict:
    """Return one lease from campus_customs_new.db.

    Use this for ticket 102, which points at a lease_id. The result is that
    lease's space, landlord, monthly rent, and next due date. If the id is
    not in leases, found is false.
    """
    rows = _rows(
        """
        SELECT id, space_name, landlord, monthly_rent, next_due, notes
        FROM leases
        WHERE id = ?
        """,
        (lease_id,),
    )
    if not rows:
        return {"found": False, "lease_id": lease_id}
    return {"found": True, **rows[0]}


@mcp.tool
def check_size_on_hand(sku: str, size: str) -> dict:
    """Return the inventory row for one SKU and size from campus_customs_new.db.

    Use this for ticket 103, which names a sku, a size, and a qty. The result
    is that size's name, qty, and location. If that SKU and size are not in
    inventory, found is false.
    """
    rows = _rows(
        """
        SELECT sku, name, size, qty, location
        FROM inventory
        WHERE sku = ? AND size = ?
        """,
        (sku, size),
    )
    if not rows:
        return {"found": False, "sku": sku, "size": size}
    return {"found": True, **rows[0]}


@mcp.tool
def list_open_tickets() -> dict:
    """Return every open ticket on the board from campus_customs_new.db.

    Boss uses this to see tickets 101, 102, and 103 before assigning work.
    Each row is the ticket's type, requester, subject, sku, size, qty,
    lease_id, invoice_id, status, notes, and created_at.
    """
    rows = _rows(
        """
        SELECT id, type, requester, subject, sku, size, qty, lease_id,
               invoice_id, status, notes, created_at
        FROM tickets
        WHERE status = 'open'
        ORDER BY id
        """
    )
    return {"count": len(rows), "tickets": rows}


@mcp.tool
def read_ticket(ticket_id: int) -> dict:
    """Return one ticket from campus_customs_new.db.

    Use the id from the board. The row points at a sku, a lease, or an
    invoice when those columns are filled. found is false when the id
    is not in tickets.
    """
    rows = _rows(
        """
        SELECT id, type, requester, subject, sku, size, qty, lease_id,
               invoice_id, status, notes, created_at
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,),
    )
    if not rows:
        return {"found": False, "ticket_id": ticket_id}
    return {"found": True, **rows[0]}


@mcp.tool
def read_shop_date() -> dict:
    """Return the shop's today from the desk table.

    date_today is the only date used to decide what is overdue.
    found is false when the desk has no row.
    """
    rows = _rows("SELECT date_today, notes FROM desk")
    if not rows:
        return {"found": False}
    return {"found": True, **rows[0]}


@mcp.tool
def read_cash_accounts() -> dict:
    """Return every cash account from campus_customs_new.db.

    Accounting uses the checking balance before it recommends a payment.
    This tool does not move money.
    """
    rows = _rows("SELECT name, balance, date FROM cash_accounts ORDER BY name")
    return {"accounts": rows}


@mcp.tool
def read_sku_price(sku: str) -> dict:
    """Return unit cost and list price for one SKU from the pricing table.

    Accounting uses this for ticket 103, the bulk hoodie discount.
    found is false when the SKU is not in pricing.
    """
    rows = _rows(
        "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?",
        (sku,),
    )
    if not rows:
        return {"found": False, "sku": sku}
    return {"found": True, **rows[0]}


@mcp.tool
def list_sizes_on_hand(sku: str) -> dict:
    """Return every size row for one SKU from inventory.

    Inventory uses this to see the size run, not just the one size a
    ticket asked for. found is false when the SKU is not in inventory.
    """
    rows = _rows(
        """
        SELECT sku, name, size, qty, location
        FROM inventory
        WHERE sku = ?
        ORDER BY size
        """,
        (sku,),
    )
    return {"found": bool(rows), "sku": sku, "sizes": rows}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
