"""
Enrollments router - handles course enrollment and subscription management
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.models.enrollment_schemas import EnrollmentCreate
from src.utils.auth_helpers import get_current_user, supabase

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("/{course_id}")
def enroll_in_course(
    course_id: str,
    payload: EnrollmentCreate,
    current_user=Depends(get_current_user)
):
    """
    Enroll student in a course - Student only
    """
    if current_user["role"] != "student":
        raise HTTPException(403, "Only students can enroll in courses")

    user_id = current_user.get("sub")

    # 🔹 1. Check if already enrolled
    existing = supabase.table("enrollments")\
        .select("*")\
        .eq("student_id", user_id)\
        .eq("course_id", course_id)\
        .execute()

    if existing.data:
        raise HTTPException(400, "Already enrolled in this course")

    # 🔹 2. Check if course exists
    course = supabase.table("courses")\
        .select("*")\
        .eq("id", course_id)\
        .single()\
        .execute()

    if not course.data:
        raise HTTPException(404, "Course not found")

    # 🔹 3. Determine country (from payload or user profile)
    country = getattr(payload, "country", None)

    # 🔹 4. Fetch pricing
    pricing_query = supabase.table("course_pricing").select("*").eq("course_id", course_id)

    # If country is provided, filter by it
    if country:
        pricing_query = pricing_query.eq("country", country)

    pricing_response = pricing_query.execute()

    if not pricing_response.data or len(pricing_response.data) == 0:
        # fallback: get first available pricing
        fallback = supabase.table("course_pricing")\
            .select("*")\
            .eq("course_id", course_id)\
            .execute()

        if not fallback.data or len(fallback.data) == 0:
            raise HTTPException(404, "Pricing not found for this course")

        pricing = fallback.data[0]
    else:
        pricing = pricing_response.data[0]

    price_paid = float(pricing.get("price", 0))
    currency_symbol = pricing.get("currency_symbol", "₹")
    duration_months = int(pricing.get("duration_months") or course.data.get("duration_months", 6))

    # 🔹 5. Apply discount (if any)
    discount_value = 0
    if payload.discount_code:
        discount = supabase.table("discounts")\
            .select("*")\
            .eq("code", payload.discount_code)\
            .single()\
            .execute()

        if discount.data:
            valid_from = datetime.fromisoformat(discount.data.get("valid_from"))
            valid_to = discount.data.get("valid_to")
            now = datetime.utcnow()

            if valid_from <= now and (not valid_to or datetime.fromisoformat(valid_to) >= now):
                discount_type = discount.data.get("discount_type")
                discount_value = float(discount.data.get("value", 0))

                if discount_type == "percentage":
                    price_paid = price_paid * (1 - discount_value / 100)
                else:
                    price_paid = max(0, price_paid - discount_value)

    # 🔹 6. Calculate expiry
    enrolled_at = datetime.utcnow()
    expires_at = enrolled_at + relativedelta(months=duration_months)

    # 🔹 7. Insert enrollment record
    enrollment_data = {
        "student_id": user_id,
        "course_id": course_id,
        "payment_status": "paid",
        "amount": float(price_paid),
        "currency_symbol": currency_symbol,
        "created_at": enrolled_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "discount_applied": float(discount_value)
    }

    result = supabase.table("enrollments").insert(enrollment_data).execute()

    return {
        "message": f"Enrolled successfully using pricing for {country or 'default'}",
        "enrollment": result.data,
        "expires_at": expires_at.isoformat()
    }

@router.get("/me")
def get_my_enrollments(current_user=Depends(get_current_user)):
    """
    Get my enrolled courses - Student only
    """
    if current_user["role"] != "student":
        raise HTTPException(403, "Only students can view enrollments")
    
    user_id = current_user.get("sub")
    
    # Get enrollments with course details
    enrollments = supabase.table("enrollments")\
        .select("*, courses(*)")\
        .eq("student_id", user_id)\
        .execute()
    
    return {"enrollments": enrollments.data}


@router.get("/{course_id}/status")
def check_enrollment_status(course_id: str, current_user=Depends(get_current_user)):
    """
    Check enrollment status for a course
    """
    user_id = current_user.get("sub")
    
    enrollment = supabase.table("enrollments")\
        .select("*")\
        .eq("student_id", user_id)\
        .eq("course_id", course_id)\
        .single()\
        .execute()
    
    if not enrollment.data:
        return {"enrolled": False, "status": None}
    
    # Check if expired
    expires_at = datetime.fromisoformat(enrollment.data.get("expires_at"))
    now = datetime.utcnow()
    
    if expires_at < now:
        # Update status to expired
        supabase.table("enrollments")\
            .update({"status": "expired"})\
            .eq("id", enrollment.data.get("id"))\
            .execute()
        
        return {
            "enrolled": True,
            "status": "expired",
            "expires_at": expires_at.isoformat()
        }
    
    return {
        "enrolled": True,
        "status": enrollment.data.get("status"),
        "expires_at": expires_at.isoformat()
    }


@router.post("/renew/{course_id}")
def renew_enrollment(course_id: str, current_user=Depends(get_current_user)):
    """
    Renew subscription for a course - Student only
    """
    if current_user["role"] != "student":
        raise HTTPException(403, "Only students can renew enrollments")
    
    user_id = current_user.get("sub")
    
    # Get existing enrollment
    enrollment = supabase.table("enrollments")\
        .select("*")\
        .eq("student_id", user_id)\
        .eq("course_id", course_id)\
        .single()\
        .execute()
    
    if not enrollment.data:
        raise HTTPException(404, "Enrollment not found")
    
    # Get course details for pricing
    course = supabase.table("courses")\
        .select("*")\
        .eq("id", course_id)\
        .single()\
        .execute()
    
    if not course.data:
        raise HTTPException(404, "Course not found")
    
    # Calculate new expiry
    current_expires = datetime.fromisoformat(enrollment.data.get("expires_at"))
    now = datetime.utcnow()
    
    # If already expired, start from now
    start_date = max(current_expires, now)
    new_expires_at = start_date + relativedelta(months=course.data.get("duration_months", 6))
    
    # Update enrollment
    result = supabase.table("enrollments").update({
        "expires_at": new_expires_at.isoformat(),
        "status": "active",
        "price_paid": enrollment.data.get("price_paid") + course.data.get("price", 0)
    }).eq("id", enrollment.data.get("id")).execute()
    
    return {
        "message": "Enrollment renewed successfully",
        "new_expires_at": new_expires_at.isoformat(),
        "enrollment": result.data
    }
