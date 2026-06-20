from pydantic import BaseModel
from typing import Optional


class CustomerCreate(BaseModel):
    full_name: str
    email: str
    address: Optional[str] = None


class InvoiceCreate(BaseModel):
    account_id: int
    billing_period_start: str
    billing_period_end: str
    total_kwh: float