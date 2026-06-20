from fastapi import APIRouter, HTTPException
from models.postgres import CustomerCreate, InvoiceCreate
from sqlalchemy import text

from db.postgres import engine

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/test")
def test_postgres():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM customers"))
        count = result.scalar()

    return {
        "postgres_connected": True,
        "customer_count": count
    }


@router.get("/customers")
def list_customers():
    query = text("""
        SELECT customer_id, full_name, email, address, created_at
        FROM customers
        ORDER BY customer_id;
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return {
        "customers": [dict(row) for row in rows]
    }


@router.post("/customers")
def create_customer(customer: CustomerCreate):
    query = text("""
        INSERT INTO customers (full_name, email, address)
        VALUES (:full_name, :email, :address)
        RETURNING customer_id, full_name, email, address, created_at;
    """)

    try:
        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "address": customer.address
                }
            ).mappings().one()

        return dict(row)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not create customer: {str(exc)}"
        )


@router.get("/accounts")
def list_accounts():
    query = text("""
        SELECT
            ba.account_id,
            ba.meter_id,
            ba.active,
            c.full_name,
            c.email,
            t.tariff_name,
            t.price_per_kwh
        FROM billing_accounts ba
        JOIN customers c ON ba.customer_id = c.customer_id
        JOIN tariffs t ON ba.tariff_id = t.tariff_id
        ORDER BY ba.account_id;
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return {
        "accounts": [dict(row) for row in rows]
    }


@router.post("/invoices")
def create_invoice(invoice: InvoiceCreate):
    tariff_query = text("""
        SELECT t.price_per_kwh
        FROM billing_accounts ba
        JOIN tariffs t ON ba.tariff_id = t.tariff_id
        WHERE ba.account_id = :account_id
        AND ba.active = TRUE;
    """)

    insert_query = text("""
        INSERT INTO invoices (
            account_id,
            billing_period_start,
            billing_period_end,
            total_kwh,
            amount_due
        )
        VALUES (
            :account_id,
            :billing_period_start,
            :billing_period_end,
            :total_kwh,
            :amount_due
        )
        RETURNING invoice_id, account_id, total_kwh, amount_due, created_at;
    """)

    with engine.begin() as connection:
        tariff_row = connection.execute(
            tariff_query,
            {"account_id": invoice.account_id}
        ).mappings().first()

        if tariff_row is None:
            raise HTTPException(
                status_code=404,
                detail="Billing account not found or inactive"
            )

        amount_due = float(tariff_row["price_per_kwh"]) * invoice.total_kwh

        row = connection.execute(
            insert_query,
            {
                "account_id": invoice.account_id,
                "billing_period_start": invoice.billing_period_start,
                "billing_period_end": invoice.billing_period_end,
                "total_kwh": invoice.total_kwh,
                "amount_due": amount_due
            }
        ).mappings().one()

    return dict(row)


@router.get("/invoices")
def list_invoices():
    query = text("""
        SELECT
            i.invoice_id,
            i.account_id,
            c.full_name,
            ba.meter_id,
            i.billing_period_start,
            i.billing_period_end,
            i.total_kwh,
            i.amount_due,
            i.created_at
        FROM invoices i
        JOIN billing_accounts ba ON i.account_id = ba.account_id
        JOIN customers c ON ba.customer_id = c.customer_id
        ORDER BY i.invoice_id;
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    return {
        "invoices": [dict(row) for row in rows]
    }