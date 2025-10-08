from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Union
from datetime import datetime
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError, ExpiredSignatureError
import os
from fastapi.security import OAuth2PasswordBearer
from src.utils.config import get_settings
import requests  # HTTP requests library
# from src.routes.courses.models import (
#     Course, Lesson, courses_collection, lessons_collection,
#     CourseCreate, CourseUpdate, CourseResponse,
#     LessonCreate, LessonUpdate, LessonResponse
# )
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from supabase import create_client, Client
from pydantic import BaseModel, EmailStr, constr

  # Initialize settings
settings = get_settings()

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

bearer_scheme = HTTPBearer(auto_error=True)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Decode token (audience check disabled)
        payload = jwt.decode(
            token.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user id")

        # ✅ Fetch role from profiles table
        profile = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if not profile.data:
            raise HTTPException(status_code=401, detail="User profile not found")

        # Merge profile role into payload
        payload["role"] = profile.data["role"]

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    

def prepare_for_supabase(data: dict) -> dict:
    """
    Convert Pydantic model data to Supabase-ready dictionary.
    Handles datetime, HttpUrl, and other non-JSON-serializable types.
    """
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            # Convert datetime to ISO format string
            cleaned_data[key] = value.isoformat()
        elif hasattr(value, '__str__') and 'HttpUrl' in str(type(value)):
            # Convert HttpUrl to string
            cleaned_data[key] = str(value)
        elif isinstance(value, list):
            # Handle lists (might contain objects that need conversion)
            cleaned_data[key] = [
                prepare_for_supabase(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, dict):
            # Recursively clean nested dictionaries
            cleaned_data[key] = prepare_for_supabase(value)
        else:
            cleaned_data[key] = value
    return cleaned_data

