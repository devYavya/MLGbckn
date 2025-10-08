"""
Course, Module, and Lesson related Pydantic schemas
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List


class CourseCreate(BaseModel):
    """Schema for creating a new course"""
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None


class ModuleCreate(BaseModel):
    """Schema for creating a new module"""
    course_id: str  # UUID string
    title: str
    description: Optional[str] = None
    order_no: Optional[int] = 1


class LessonCreate(BaseModel):
    """Schema for creating a new lesson"""
    module_id: str  # UUID string
    title: str
    description: Optional[str] = None
    video_url: Optional[HttpUrl] = None
    duration: Optional[int] = None  # in minutes/seconds
    resources: Optional[Dict] = {}  # JSON for extra files, links
    order_no: Optional[int] = 1


class LessonOut(BaseModel):
    """Schema for lesson output"""
    id: str
    module_id: str
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    resources: Optional[Dict] = {}
    order_no: int


class ModuleOut(BaseModel):
    """Schema for module output with lessons"""
    id: str
    course_id: str
    title: str
    description: Optional[str] = None
    order_no: int
    lessons: List[LessonOut] = []


class CourseOut(BaseModel):
    """Schema for complete course output with modules and lessons"""
    id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_by: str
    modules: List[ModuleOut] = []


class CoursePrice(BaseModel):
    """Schema for setting course price"""
    price: float
    currency_symbol: str = "INR"
    duration_months: int = 6
    category: Optional[str] = None
