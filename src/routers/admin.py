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
    user = supabase.auth.admin.create_user({
        "email": email,
        "password": "Temp@12345",
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


@router.post("/set-pricing")
def set_pricing(payload: PricingCreate, current_user=Depends(get_current_user)):
    """
    Set course pricing for a specific country - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only admin can control pricing")

    record = supabase.table("course_pricing").upsert({
        "course_id": payload.course_id,
        "country": payload.country,
        "currency_symbol": payload.currency_symbol,
        "price": payload.price
    }).execute()

    return {"message": "Pricing updated", "pricing": record.data}


@router.post("/set-price/{course_id}")
def set_course_price(
    course_id: str, 
    payload: CoursePrice, 
    current_user=Depends(get_current_user)
):
    """
    Set course price and duration - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can set prices")
    
    result = supabase.table("courses").update({
        "price": payload.price,
        "currency_symbol": payload.currency_symbol,
        "duration_months": payload.duration_months,
        "category": payload.category
    }).eq("id", course_id).execute()
    
    return {"message": "Price updated successfully", "course": result.data}


@router.post("/discounts")
def create_discount(payload: DiscountCreate, current_user=Depends(get_current_user)):
    """
    Create discount code - Admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(403, "Only super_admin can create discounts")

    discount_data = prepare_for_supabase(payload.dict())
    discount = supabase.table("discounts").insert(discount_data).execute()
    
    return {"message": "Discount created", "discount": discount.data}


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
