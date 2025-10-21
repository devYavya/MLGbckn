"""
Admin router - handles admin operations like pricing, discounts, user management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from src.models.enrollment_schemas import PricingCreate, DiscountCreate
from src.models.course_schemas import CoursePrice
from src.models.user_schemas import RoleChange
from src.utils.auth_helpers import get_current_user, prepare_for_supabase, supabase

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/approve-teacher")
def approve_teacher(email: str, current_user: dict = Depends(get_current_user)):
    """
    Approve teacher application - Super Admin only
    """
    if current_user.get("role") != "super_admin":
        raise HTTPException(403, "Only super_admin can approve teachers")

    # Get teacher application
    app = supabase.table("teacher_applications")\
        .select("*")\
        .eq("email", email)\
        .single()\
        .execute()
    
    if not app.data:
        raise HTTPException(404, "Application not found")

    # Create user
    user = supabase.auth.sign_up({
        "email": email,
        "password": "Test@1234",
        "email_confirm": True
    })

    if not user.user:
        raise HTTPException(500, "Failed to create teacher user")

    # Create profile
    supabase.table("profiles").insert({
        "id": user.user.id,
        "role": "teacher",
        "first_name": app.data["first_name"],
        "last_name": app.data["last_name"],
        "mobile_no": app.data["mobile_no"],
        "languages_mastered": app.data["languages_mastered"],
        "teaching_experience": app.data["teaching_experience"],
        "timezone": app.data["timezone"]
    }).execute()

    # Update application status
    supabase.table("teacher_applications")\
        .update({"status": "approved"})\
        .eq("email", email)\
        .execute()

    return {"message": "Teacher approved and account created", "user_id": user.user.id}





@router.post("/set-price/{course_id}")
def set_course_price(
    course_id: str,
    payload: CoursePrice,
    current_user=Depends(get_current_user)
):
    """
    Set or update course pricing per country - Super Admin only and teachers
    """
    if current_user["role"] not in ["super_admin", "teacher"]:
        raise HTTPException(403, "Only super_admin or teacher can set prices")


    country = payload.country or "India"

    # 🔹 Step 1: Check if pricing already exists for this course + country
    existing = supabase.table("course_pricing")\
        .select("*")\
        .eq("course_id", course_id)\
        .eq("country", country)\
        .execute()

    # 🔹 Step 2: If exists → UPDATE
    if existing.data and len(existing.data) > 0:
        pricing_id = existing.data[0].get("id")

        update_result = supabase.table("course_pricing")\
            .update({
                "price": payload.price,
                "currency_symbol": payload.currency_symbol,
                "duration_months": payload.duration_months,
            })\
            .eq("id", pricing_id)\
            .execute()

        if not update_result.data:
            raise HTTPException(500, "Failed to update existing pricing")

        return {
            "message": f"Pricing updated successfully for {country}",
            "pricing": update_result.data
        }

    # 🔹 Step 3: If not exists → UPSERT (create new)
    else:
        insert_result = supabase.table("course_pricing").insert({
            "course_id": course_id,
            "country": country,
            "price": payload.price,
            "currency_symbol": payload.currency_symbol,
            "duration_months": payload.duration_months
        }).execute()

        if not insert_result.data:
            raise HTTPException(500, "Failed to create new pricing")

        return {
            "message": f"Pricing added successfully for {country}",
            "pricing": insert_result.data
        }


@router.post("/discounts")
def create_discount(payload: DiscountCreate, current_user=Depends(get_current_user)):
    """
    Create or update discount code - Super Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can create discounts")

    # 🔹 Step 1: Check if discount code already exists
    existing = supabase.table("discounts")\
        .select("*")\
        .eq("code", payload.code)\
        .execute()

    # Prepare data for database
    discount_data = {
        "code": payload.code,
        "discount_type": payload.discount_type,
        "applies_to": payload.applies_to,
        "valid_until": payload.valid_until.isoformat() if payload.valid_until else None,
        "is_global": payload.is_global,
        "course_id": payload.course_id,
        "category": payload.category,
        "usage_limit": payload.usage_limit,
        "max_uses": payload.max_uses,
    }

    # Add valid_from if provided
    if payload.valid_from:
        discount_data["valid_from"] = payload.valid_from.isoformat()

    # Add value or percentage based on discount_type
    if payload.discount_type == "percentage" and payload.percentage is not None:
        discount_data["percentage"] = payload.percentage
    elif payload.discount_type == "flat" and payload.value is not None:
        discount_data["value"] = payload.value
    elif payload.value is not None:
        discount_data["value"] = payload.value

    # 🔹 Step 2: If exists → UPDATE
    if existing.data and len(existing.data) > 0:
        discount_id = existing.data[0].get("id")

        update_result = supabase.table("discounts")\
            .update(discount_data)\
            .eq("id", discount_id)\
            .execute()

        if not update_result.data:
            raise HTTPException(500, "Failed to update existing discount")

        return {
            "message": f"Discount code '{payload.code}' updated successfully",
            "discount": update_result.data[0]
        }

    # 🔹 Step 3: If not exists → INSERT (create new)
    else:
        insert_result = supabase.table("discounts").insert(discount_data).execute()

        if not insert_result.data:
            raise HTTPException(500, "Failed to create new discount")

        return {
            "message": f"Discount code '{payload.code}' created successfully",
            "discount": insert_result.data[0]
        }


@router.get("/discounts")
def list_discounts(current_user=Depends(get_current_user)):
    """
    List all discount codes - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can view discounts")
    
    discounts = supabase.table("discounts").select("*").execute()
    return {"discounts": discounts.data}


@router.get("/teacher-applications")
def get_teacher_applications(
    status: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    List teacher applications - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can view applications")
    
    query = supabase.table("teacher_applications").select("*")
    
    if status:
        query = query.eq("status", status)
    else:
        query = query.eq("status", "pending")
    
    applications = query.execute()
    return {"applications": applications.data}


@router.get("/users")
def list_all_users(
    role: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    List all users with roles - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can view users")
    
    query = supabase.table("profiles").select("*")
    
    if role:
        query = query.eq("role", role)
    
    users = query.execute()
    return {"users": users.data}


@router.put("/change-role/{user_id}")
def change_user_role(
    user_id: str,
    payload: RoleChange,
    current_user=Depends(get_current_user)
):
    """
    Change user role - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can change roles")
    
    # Validate role
    if payload.new_role not in ["student", "teacher", "super_admin"]:
        raise HTTPException(400, "Invalid role")
    
    # Update role
    result = supabase.table("profiles").update({
        "role": payload.new_role
    }).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(404, "User not found")
    
    return {
        "message": f"Role changed to {payload.new_role} successfully",
        "user": result.data
    }
