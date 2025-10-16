"""
Courses router - handles course, module, and lesson management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from src.models.course_schemas import (
    CourseCreate,
    ModuleCreate,
    LessonCreate,
    CourseOut,
    LessonOut,
    ModuleOut
)
from src.utils.auth_helpers import get_current_user, supabase
from fastapi import File, UploadFile, HTTPException, Depends
import time
from src.utils.firebase_client import bucket
router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseOut)
async def create_course(
    title: str,
    description: Optional[str] = None,
    file: Optional[UploadFile] = File(None),  # thumbnail upload
    current_user=Depends(get_current_user)
):
    """
    Create a new course (Teacher only)
    Optionally upload a thumbnail image to Firebase
    """
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create courses")

    thumbnail_url = None

    #  If user uploaded a thumbnail file
    if file:
        try:
            timestamp = int(time.time())
            filename = f"thumbnails/{timestamp}_{file.filename}"

            blob = bucket.blob(filename)
            blob.upload_from_file(file.file, content_type=file.content_type)
            blob.make_public()  

            thumbnail_url = blob.public_url
        except Exception as e:
            raise HTTPException(500, f"Error uploading thumbnail: {str(e)}")

    # ✅ Save course record in Supabase
    result = supabase.table("courses").insert({
        "title": title,
        "description": description,
        "thumbnail_url": thumbnail_url,
        "created_by": current_user["sub"]
    }).execute()

    if not result.data:
        raise HTTPException(500, "Error creating course")

    return result.data[0]



@router.post("/modules")
def create_modules(payload: List[ModuleCreate], current_user=Depends(get_current_user)):
    """
    Create multiple modules for a course - Teacher only
    """
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create modules")
    
    data = [module.dict() for module in payload]
    inserted = supabase.table("modules").insert(data).execute()
    return {"message": "Modules created", "modules": inserted.data}


@router.post("/lessons")
def create_lesson(payload: List[LessonCreate], current_user=Depends(get_current_user)):
    """
    Create multiple lessons for a module - Teacher only
    """
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can create lessons")

    # Convert HttpUrl to string before inserting
    data = []
    for lesson in payload:
        lesson_dict = lesson.dict()
        if lesson_dict.get("video_url"):
            lesson_dict["video_url"] = str(lesson_dict["video_url"])
        data.append(lesson_dict)
    
    lessons = supabase.table("lessons").insert(data).execute()
    return {"message": "Lessons created", "lessons": lessons.data}


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: str, current_user=Depends(get_current_user)):
    """
    Get full course details (course + modules + lessons)
    Accessible to students/teachers/admins
    """
    # 1. Fetch course
    course = supabase.table("courses")\
        .select("*")\
        .eq("id", course_id)\
        .single()\
        .execute()
    
    if not course.data:
        raise HTTPException(404, "Course not found")

    # 2. Fetch modules
    modules = supabase.table("modules")\
        .select("*")\
        .eq("course_id", course_id)\
        .order("order_no")\
        .execute().data

    # 3. For each module, fetch lessons
    for module in modules:
        lessons = supabase.table("lessons")\
            .select("*")\
            .eq("module_id", module["id"])\
            .order("order_no")\
            .execute().data
        module["lessons"] = lessons

    # 4. Attach modules to course
    course.data["modules"] = modules

    return course.data


@router.get("")
def list_courses(
    category: Optional[str] = None,
    search: Optional[str] = None,
    teacher: Optional[str] = None
):
    """
    List all available courses with filters
    """
    query = supabase.table("courses").select("*")
    
    if category:
        query = query.eq("category", category)
    
    if teacher:
        query = query.eq("created_by", teacher)
    
    if search:
        query = query.ilike("title", f"%{search}%")
    
    courses = query.execute()
    return {"courses": courses.data}


@router.get("/{course_id}/modules")
def get_course_modules(course_id: str):
    """
    Get all modules of a course
    """
    modules = supabase.table("modules")\
        .select("*")\
        .eq("course_id", course_id)\
        .order("order_no")\
        .execute()
    
    return {"modules": modules.data}


@router.get("/modules/{module_id}/lessons")
def get_module_lessons(module_id: str):
    """
    Get all lessons of a module
    """
    lessons = supabase.table("lessons")\
        .select("*")\
        .eq("module_id", module_id)\
        .order("order_no")\
        .execute()
    
    return {"lessons": lessons.data}


@router.get("/{course_id}/price")
def get_course_price(course_id: str, country: str):
    """
    Get course price for a specific country.
    If not found, fallback to first available pricing.
    """
    # Try to get pricing for the specific country
    response = supabase.table("course_pricing")\
        .select("country, currency_symbol, price, duration_months")\
        .eq("course_id", course_id)\
        .eq("country", country)\
        .execute()

    # If not found, fallback to default or first pricing
    if not response.data or len(response.data) == 0:
        fallback = supabase.table("course_pricing")\
            .select("country, currency_symbol, price, duration_months")\
            .eq("course_id", course_id)\
            .execute()

        if not fallback.data or len(fallback.data) == 0:
            raise HTTPException(404, "Pricing not set for this course in any region")

        return {
            "message": f"No pricing for '{country}'. Showing default pricing.",
            "price": fallback.data[0]
        }

    # Return the matching record
    return {
        "message": f"Pricing found for '{country}'",
        "price": response.data[0]
    }


@router.post("/upload-lesson-video")
async def upload_lesson_video(
    module_id: str,
    title: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
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
        "video_url": video_url
    }).execute()

    return {"message": "Lesson uploaded and saved", "lesson": lesson.data}
