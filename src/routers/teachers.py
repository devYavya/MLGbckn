"""
Teachers router - handles teacher-specific operations
"""
from fastapi import APIRouter, HTTPException, Depends
from src.utils.auth_helpers import get_current_user, supabase

router = APIRouter(prefix="/teacher", tags=["teachers"])


@router.get("/my-courses")
def get_teacher_courses(current_user=Depends(get_current_user)):
    """
    Get courses created by teacher - Teacher only
    """
    if current_user["role"] != "teacher":
        raise HTTPException(403, "Only teachers can access this")
    
    teacher_id = current_user.get("sub")
    
    courses = supabase.table("courses")\
        .select("*")\
        .eq("created_by", teacher_id)\
        .execute()
    
    return {"courses": courses.data}


@router.get("/course/{course_id}/enrollments")
def get_course_enrollments(course_id: str, current_user=Depends(get_current_user)):
    """
    Get enrollment stats for a course - Teacher only
    """
    if current_user["role"] not in ["teacher", "super_admin"]:
        raise HTTPException(403, "Access denied")
    
    # If teacher, verify ownership
    if current_user["role"] == "teacher":
        course = supabase.table("courses")\
            .select("created_by")\
            .eq("id", course_id)\
            .single()\
            .execute()
        
        if course.data.get("created_by") != current_user.get("sub"):
            raise HTTPException(403, "Not your course")
    
    # Get enrollments with student details
    enrollments = supabase.table("enrollments")\
        .select("*, profiles(*)")\
        .eq("course_id", course_id)\
        .execute()
    
    return {
        "total_enrollments": len(enrollments.data),
        "enrollments": enrollments.data
    }
