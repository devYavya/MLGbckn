"""
Courses router - handles course, module, and lesson management
"""
from fastapi import APIRouter, HTTPException, Depends, Form,Request
from typing import List, Optional
from src.models.course_schemas import (
    CourseCreate,
    ModuleCreate,
    LessonCreate,
    CourseOut,
    LessonOut,
    ModuleOut
)
import json
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
async def create_lessons(
    request: Request,
    module_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    resources: Optional[str] = Form(None),  # as JSON string
    order_no: Optional[int] = Form(1),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
):
    """
    Create one or more lessons for a module.
    - If a file is uploaded: uploads video + creates single lesson
    - If JSON payload is provided: creates multiple lessons
    - Teacher only
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create lessons")

    try:
        # 📦 Case 1: JSON payload (no file upload)
        if request.headers.get("content-type", "").startswith("application/json"):
            payload = await request.json()

            if not isinstance(payload, list):
                raise HTTPException(status_code=400, detail="Expected a list of lessons")

            lessons_data = []
            for lesson in payload:
                lesson_obj = LessonCreate(**lesson)
                lesson_dict = lesson_obj.dict()
                if lesson_dict.get("video_url"):
                    lesson_dict["video_url"] = str(lesson_dict["video_url"])
                lessons_data.append(lesson_dict)

            lessons = supabase.table("lessons").insert(lessons_data).execute()
            return {"message": "Lessons created successfully", "lessons": lessons.data}

        # 🎥 Case 2: Multipart form (single file upload)
        elif file:
            if not module_id or not title:
                raise HTTPException(status_code=400, detail="module_id and title are required when uploading video")

            timestamp = int(time.time())
            filename = f"lessons/{timestamp}_{file.filename}"

            # Upload to your storage bucket
            blob = bucket.blob(filename)
            blob.upload_from_file(file.file, content_type=file.content_type)
            blob.make_public()
            video_url = blob.public_url

            # Convert resources (if sent as JSON string)
            resources_data = None
            if resources:
                try:
                    resources_data = json.loads(resources)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON format in 'resources' field")

            lesson_data = {
                "module_id": module_id,
                "title": title,
                "description": description,
                "duration": duration,
                "resources": resources_data,
                "order_no": order_no,
                "video_url": video_url,
            }

            lesson = supabase.table("lessons").insert(lesson_data).execute()
            return {"message": "Lesson uploaded and saved successfully", "lesson": lesson.data}

        else:
            raise HTTPException(status_code=400, detail="Either upload a file or send JSON lesson data")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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


# @router.post("/upload-lesson-video")
# async def upload_lesson_video(
#     module_id: str,
#     title: str,
#     file: UploadFile = File(...),
#     current_user=Depends(get_current_user)
# ):
#     if current_user["role"] != "teacher":
#         raise HTTPException(403, "Only teachers can upload videos")

#     timestamp = int(time.time())
#     filename = f"lessons/{timestamp}_{file.filename}"

#     blob = bucket.blob(filename)
#     blob.upload_from_file(file.file, content_type=file.content_type)
#     blob.make_public()

#     video_url = blob.public_url

#     lesson = supabase.table("lessons").insert({
#         "module_id": module_id,
#         "title": title,
#         "video_url": video_url
#     }).execute()

#     return {"message": "Lesson uploaded and saved", "lesson": lesson.data}


@router.patch("/courses/{course_id}")
async def update_course(
    course_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),  # optional thumbnail
    current_user=Depends(get_current_user),
):
    """
    Partially update a course (Teacher only)
    - Allows updating title, description, and thumbnail
    - Ignores empty file fields safely
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update courses")

    update_data = {}

    # Update simple fields
    if title:
        update_data["title"] = title
    if description:
        update_data["description"] = description

    # ✅ Handle thumbnail upload safely
    if file and file.filename:
        try:
            timestamp = int(time.time())
            filename = f"thumbnails/{timestamp}_{file.filename}"
            blob = bucket.blob(filename)
            blob.upload_from_file(file.file, content_type=file.content_type)
            blob.make_public()
            update_data["thumbnail_url"] = blob.public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading thumbnail: {str(e)}")

    # Ensure at least one field is being updated
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # ✅ Perform update
    result = supabase.table("courses").update(update_data).eq("id", course_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Course not found or update failed")

    return {"message": "Course updated successfully", "course": result.data[0]}


# ==========================================================
# 🔹 PATCH MODULE
# ==========================================================
@router.patch("/modules/{module_id}")
async def update_module(
    module_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    order_no: Optional[int] = Form(None),
    current_user=Depends(get_current_user),
):
    """
    Partially update a module (Teacher only)
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update modules")

    update_data = {}
    if title:
        update_data["title"] = title
    if description:
        update_data["description"] = description
    if order_no is not None:
        update_data["order_no"] = order_no

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = supabase.table("modules").update(update_data).eq("id", module_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Module not found or update failed")

    return {"message": "Module updated successfully", "module": result.data[0]}


# ==========================================================
# 🔹 PATCH LESSON
# ==========================================================
@router.patch("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    order_no: Optional[int] = Form(None),
    resources: Optional[str] = Form(None),  # JSON string
    file: Optional[UploadFile] = File(None),  # optional new video upload
    current_user=Depends(get_current_user),
):
    """
    Partially update a lesson (Teacher only)
    - Supports updating video, metadata, and resources
    - Ignores empty file fields safely
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update lessons")

    update_data = {}

    # ✅ Update metadata fields
    if title:
        update_data["title"] = title
    if description:
        update_data["description"] = description
    if duration is not None:
        update_data["duration"] = duration
    if order_no is not None:
        update_data["order_no"] = order_no

    # ✅ Parse resources JSON safely
    if resources:
        try:
            update_data["resources"] = json.loads(resources)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for 'resources'")

    # ✅ Handle video upload safely
    if file and file.filename:
        try:
            timestamp = int(time.time())
            filename = f"lessons/{timestamp}_{file.filename}"
            blob = bucket.blob(filename)
            blob.upload_from_file(file.file, content_type=file.content_type)
            blob.make_public()
            update_data["video_url"] = blob.public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # ✅ Perform update in Supabase
    try:
        result = supabase.table("lessons").update(update_data).eq("id", lesson_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Lesson not found or update failed")

    return {"message": "Lesson updated successfully", "lesson": result.data[0]}



# ==========================================================
#  DELETE COURSE
# ==========================================================
@router.delete("/courses/{course_id}")
async def delete_course(course_id: str, current_user=Depends(get_current_user)):
    """
    Delete a course (Teacher only)
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete courses")

    try:
        result = supabase.table("courses").delete().eq("id", course_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database delete failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Course not found or already deleted")

    return {"message": "Course deleted successfully", "deleted_course": result.data[0]}


# ==========================================================
# DELETE MODULE
# ==========================================================
@router.delete("/modules/{module_id}")
async def delete_module(module_id: str, current_user=Depends(get_current_user)):
    """
    Delete a module (Teacher only)
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete modules")

    try:
        result = supabase.table("modules").delete().eq("id", module_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database delete failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Module not found or already deleted")

    return {"message": "Module deleted successfully", "deleted_module": result.data[0]}


# ==========================================================
# 🗑️ DELETE LESSON
# ==========================================================
@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, current_user=Depends(get_current_user)):
    """
    Delete a lesson (Teacher only)
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete lessons")

    try:
        result = supabase.table("lessons").delete().eq("id", lesson_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database delete failed: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Lesson not found or already deleted")

    return {"message": "Lesson deleted successfully", "deleted_lesson": result.data[0]}
