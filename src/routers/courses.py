"""
Courses router - handles course, module, and lesson management
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import List, Optional
from src.models.course_schemas import (
    CourseCreate, ModuleCreate, LessonCreate,
    CourseOut, LessonOut, ModuleOut
)
from src.utils.auth_helpers import get_current_user, supabase
from src.utils.firebase_client import bucket
import time

router = APIRouter(prefix="/courses", tags=["Courses"])


# ============================
# 📘  COURSE MANAGEMENT
# ============================
@router.post("", response_model=CourseOut)
def create_course(payload: CourseCreate, current_user=Depends(get_current_user)):
    """Create a new course (Teacher only)"""
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create courses")

    result = supabase.table("courses").insert({
        "title": payload.title,
        "description": payload.description,
        "thumbnail_url": str(payload.thumbnail_url) if payload.thumbnail_url else None,
        "created_by": current_user["sub"]
    }).execute()

    return result.data[0]


@router.get("", response_model=List[CourseOut])
def list_courses(
    category: Optional[str] = None,
    search: Optional[str] = None,
    teacher: Optional[str] = None
):
    """List all available courses with optional filters"""
    query = supabase.table("courses").select("*")

    if category:
        query = query.eq("category", category)
    if teacher:
        query = query.eq("created_by", teacher)
    if search:
        query = query.ilike("title", f"%{search}%")

    courses = query.execute().data
    return courses


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: str, current_user=Depends(get_current_user)):
    """Fetch complete course with all modules and lessons"""
    course = supabase.table("courses").select("*").eq("id", course_id).single().execute().data
    if not course:
        raise HTTPException(404, "Course not found")

    # Fetch all modules for this course
    modules = supabase.table("modules").select("*").eq("course_id", course_id).order("order_no").execute().data

    # For each module, attach lessons
    for module in modules:
        lessons = supabase.table("lessons").select("*").eq("module_id", module["id"]).order("order_no").execute().data
        module["lessons"] = lessons

    course["modules"] = modules
    return course


# ============================
# 🧩  MODULE MANAGEMENT
# ============================
@router.post("/modules", response_model=List[ModuleOut])
def create_modules(payload: List[ModuleCreate], current_user=Depends(get_current_user)):
    """Create multiple modules under a course (Teacher only)"""
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create modules")

    data = [m.dict() for m in payload]
    result = supabase.table("modules").insert(data).execute()
    return result.data


@router.get("/{course_id}/modules", response_model=List[ModuleOut])
def get_course_modules(course_id: str):
    """Fetch all modules of a course"""
    modules = supabase.table("modules").select("*").eq("course_id", course_id).order("order_no").execute().data

    # Attach lessons
    for m in modules:
        lessons = supabase.table("lessons").select("*").eq("module_id", m["id"]).order("order_no").execute().data
        m["lessons"] = lessons
    return modules


# ============================
# 🎥  LESSON MANAGEMENT
# ============================
@router.post("/lessons", response_model=List[LessonOut])
def create_lessons(payload: List[LessonCreate], current_user=Depends(get_current_user)):
    """Create multiple lessons under a module (Teacher only)"""
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create lessons")

    data = []
    for lesson in payload:
        item = lesson.dict()
        if item.get("video_url"):
            item["video_url"] = str(item["video_url"])
        data.append(item)

    lessons = supabase.table("lessons").insert(data).execute().data
    return lessons


@router.get("/modules/{module_id}/lessons", response_model=List[LessonOut])
def get_module_lessons(module_id: str):
    """Fetch all lessons for a module"""
    lessons = supabase.table("lessons").select("*").eq("module_id", module_id).order("order_no").execute().data
    return lessons


# ============================
# 💰  COURSE PRICING
# ============================
@router.get("/{course_id}/price")
def get_course_price(course_id: str, country: str):
    """Get localized price for a course"""
    record = supabase.table("course_pricing")\
        .select("country, currency_symbol, price")\
        .eq("course_id", course_id)\
        .eq("country", country)\
        .single()\
        .execute()

    if not record.data:
        raise HTTPException(404, "Pricing not found for this course in your region")

    return record.data


# ============================
# ☁️  VIDEO UPLOAD (Firebase)
# ============================
@router.post("/upload-lesson-video", response_model=LessonOut)
async def upload_lesson_video(
    module_id: str,
    title: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """Upload a lesson video to Firebase & save lesson"""
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can upload videos")

    timestamp = int(time.time())
    filename = f"lessons/{timestamp}_{file.filename}"

    blob = bucket.blob(filename)
    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()

    video_url = blob.public_url

    lesson = supabase.table("lessons").insert({
        "module_id": module_id,
        "title": title,
        "video_url": video_url,
        "order_no": 1
    }).execute().data[0]

    return lesson
