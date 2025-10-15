"""
Pricing, Discount, and Enrollment related Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PricingCreate(BaseModel):
    """Schema for creating course pricing"""
    course_id: str
    country: str
    currency_symbol: str
    price: float


class DiscountCreate(BaseModel):
    """Schema for creating discount codes"""
    code: str
    discount_type: str  # "percentage" or "flat"
    value: float
    course_id: Optional[str] = None  # null = global
    is_global: bool = False
    valid_from: Optional[datetime] = datetime.utcnow()
    valid_to: Optional[datetime] = None


class EnrollmentCreate(BaseModel):
    """Schema for enrolling in a course"""
    discount_code: Optional[str] = None
    country: Optional[str] = None
