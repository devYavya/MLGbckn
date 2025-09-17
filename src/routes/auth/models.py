from pydantic import BaseModel,EmailStr,validator
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from datetime import datetime 
from uuid import uuid4,UUID
from src.utils.config import get_settings
from typing import Optional, List, Literal
from fastapi import HTTPException, Request
import pytz

def now_ist():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

settings=get_settings() 

# Allowed admin emails (only these emails can register as admin)


# client = AsyncIOMotorClient(settings.MONGODB_URI)
# db = client.mobibharatSaaS  # New database for SaaS
# super_admins_collection = db.super_admins

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client.mlg_saas  # New database for SaaS
users_collection = db.users

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_verified: bool = False
    status: str = "active"
    role: str = "user"
    created_at: datetime = Field(default_factory=now_ist)
    last_login: datetime = Field(default_factory=now_ist)

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"  # Default role is 'user'

class AdminRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    admin_token: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# class UserOut(BaseModel):
#     username: str
#     email: str

# class UserOut(BaseModel):
#     user_id: str
#     id: int
#     username: str
#     email: EmailStr
#     status: str
#     role: str
#     created_at: Optional[datetime]
#     last_login: Optional[datetime]

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_admin: bool
    is_verified: bool
    status: str
    role: str
    company_id: Optional[str] = None
    employee_id: Optional[str] = None
    created_at: datetime
    last_login: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None   # "active" or "inactive"
    role: Optional[str] = None     # "user" or "company_admin"
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None
    employee_id: Optional[str] = None

class StatusUpdate(BaseModel):
    user_id: str
    status: Literal["active", "inactive"]