"""
Profiles router - handles user profile management
"""
from fastapi import APIRouter, HTTPException, Depends
from src.models.user_schemas import ProfileUpdate
from src.utils.auth_helpers import get_current_user, supabase

router = APIRouter(prefix="/profile", tags=["profiles"])


@router.get("/me")
def get_my_profile(current_user=Depends(get_current_user)):
    """
    Get current user profile
    """
    user_id = current_user.get("sub")
    
    profile = supabase.table("profiles")\
        .select("*")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    if not profile.data:
        raise HTTPException(404, "Profile not found")
    
    return {"profile": profile.data}


@router.put("/update")
def update_profile(payload: ProfileUpdate, current_user=Depends(get_current_user)):
    """
    Update user profile
    """
    user_id = current_user.get("sub")
    
    # Only update non-null fields
    update_data = payload.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(400, "No fields to update")
    
    result = supabase.table("profiles")\
        .update(update_data)\
        .eq("id", user_id)\
        .execute()
    
    return {"message": "Profile updated successfully", "profile": result.data}
