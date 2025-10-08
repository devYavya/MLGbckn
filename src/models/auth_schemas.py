"""
Authentication related Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List


class UserAuth(BaseModel):
    """Basic user authentication schema"""
    email: str
    password: str


class StudentSignup(BaseModel):
    """Student registration schema"""
    email: EmailStr
    password: constr(min_length=8)
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    mobile_no: Optional[str] = None
    country: Optional[str] = None
    languages_interested: Optional[List[str]] = []
    learning_goals: Optional[List[str]] = []
    timezone: Optional[str] = None


class TeacherSignup(BaseModel):
    """Teacher registration schema"""
    email: EmailStr
    password: constr(min_length=8)
    first_name: constr(min_length=1)
    last_name: constr(min_length=1)
    mobile_no: Optional[str] = None
    languages_mastered: Optional[List[str]] = []
    teaching_experience: int = 0
    timezone: Optional[str] = None


class TeacherApplication(BaseModel):
    """Teacher application schema"""
    email: EmailStr
    first_name: str
    last_name: str
    mobile_no: Optional[str] = None
    languages_mastered: Optional[List[str]] = []
    teaching_experience: int = 0
    timezone: Optional[str] = None


class SuperAdminSignup(BaseModel):
    """Super admin registration schema"""
    email: EmailStr
    password: constr(min_length=8)
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    mobile_no: Optional[str] = ""
    timezone: str = "UTC"
