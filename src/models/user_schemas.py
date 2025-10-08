"""
User profile related Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List


class ProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_no: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    languages_interested: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None


class RoleChange(BaseModel):
    """Schema for changing user role"""
    new_role: str  # "student", "teacher", "super_admin"
