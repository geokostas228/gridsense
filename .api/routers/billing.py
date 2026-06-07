from fastapi import APIRouter
from sqlalchemy import text

from db.postgres import engine

router = APIRouter()

@router.get("/billing/test")
def test_postgres():

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT COUNT(*) FROM customers")
        )

        count = result.scalar()

    return {
        "postgres_connected": True,
        "customer_count": count
    }