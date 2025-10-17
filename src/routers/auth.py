"""
Authentication router - handles user registration and login
"""
from fastapi import APIRouter, HTTPException, Depends
from src.models.auth_schemas import (
    UserAuth,
    StudentSignup,
    TeacherSignup,
    TeacherApplication,
    SuperAdminSignup
)
from src.utils.auth_helpers import get_current_user, supabase
from src.utils.config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

# Whitelist for super admin registration
WHITELISTED_SUPERADMINS = ["founder@example.com", "ceo@example.com"]


@router.post("/register/student")
async def register_student(payload: StudentSignup):
    """
    Register a new student user
    """
    # 1) Create user using sign_up
    result = supabase.auth.sign_up({
        "email": payload.email,
        "password": payload.password
    })

    if getattr(result, "error", None):
        raise HTTPException(status_code=400, detail=str(result.error))

    user = getattr(result, "user", None)
    if not user:
        raise HTTPException(status_code=400, detail="Signup failed")

    # 2) Insert profile with role = "student"
    profile_payload = {
        "id": user.id if hasattr(user, "id") else user.user.id,
        "role": "student",
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "mobile_no": payload.mobile_no,
        "country": payload.country,
        "languages_interested": payload.languages_interested or [],
        "learning_goals": payload.learning_goals or [],
        "timezone": payload.timezone
    }
    supabase.table("profiles").insert(profile_payload).execute()

    return {"message": "Student registered successfully", "user_id": profile_payload["id"]}


@router.post("/register/teacher")
async def register_teacher(payload: dict):
    """
    Teacher registration - invite only
    """
    # Check invite
    invite = supabase.table("invites")\
        .select("*")\
        .eq("email", payload["email"])\
        .eq("role", "teacher")\
        .single()\
        .execute()
    
    if not invite.data:
        raise HTTPException(status_code=403, detail="No valid invite found")

    # Create Supabase auth account
    user = supabase.auth.sign_up({
        "email": payload["email"],
        "password": payload["password"]
    })

    # Store teacher profile
    supabase.table("profiles").insert({
        "id": user.user.id,
        "role": "teacher",
        "first_name": payload["first_name"],
        "last_name": payload["last_name"],
        "mobile_no": payload["mobile_no"],
        "languages_mastered": payload.get("languages_mastered", []),
        "teaching_experience": payload.get("teaching_experience", 0),
        "timezone": payload.get("timezone")
    }).execute()

    # Mark invite as used
    supabase.table("invites")\
        .update({"used": True})\
        .eq("email", payload["email"])\
        .execute()

    return {"message": "Teacher registered successfully", "user_id": user.user.id}


@router.post("/apply-teacher")
def apply_teacher(payload: TeacherApplication):
    """
    Submit teacher application.
    If a user with the same email has already applied, show an appropriate message.
    """
    try:
        # Step 1: Check if an application already exists
        existing = (
            supabase.table("teacher_applications")
            .select("*")
            .eq("email", payload.email)
            .single()
            .execute()
        )

        if existing.data:
            return {
                "message": "You have already submitted an application.",
                "status": "duplicate"
            }

        # Step 2: Insert new application if not found
        application = (
            supabase.table("teacher_applications")
            .insert({
                "email": payload.email,
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "mobile_no": payload.mobile_no,
                "languages_mastered": payload.languages_mastered or [],
                "teaching_experience": payload.teaching_experience,
                "timezone": payload.timezone,
            })
            .execute()
        )

        return {
            "message": "Application submitted successfully.",
            "status": "pending"
        }

    except Exception as e:
        return {
            "message": "An error occurred while processing your application.",
            "error": str(e)
        }



@router.post("/register/super-admin")
def register_super_admin(payload: SuperAdminSignup):
    """
    Register super admin - whitelist only
    """
    # 1. Check whitelist
    if payload.email not in WHITELISTED_SUPERADMINS:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to register as super admin"
        )

    # 2. Create user with auto-confirmed email
    user = supabase.auth.admin.create_user({
        "email": payload.email,
        "password": payload.password,
        "email_confirm": True
    })

    if not user.user:
        raise HTTPException(500, "Failed to create super_admin user")

    # 3. Save profile with role = super_admin
    supabase.table("profiles").insert({
        "id": user.user.id,
        "role": "super_admin",
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "mobile_no": payload.mobile_no,
        "timezone": payload.timezone
    }).execute()

    return {"message": "Super Admin created successfully", "user_id": user.user.id}


@router.post("/signup")
def signup(user: UserAuth):
    """
    General user signup with auto-confirm
    """
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "email_confirm": True
        })
        
        if response and hasattr(response, 'user') and response.user:
            return {
                "message": "User created successfully",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        error_message = str(e)
        if "already registered" in error_message.lower() or "already exists" in error_message.lower():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        elif "invalid" in error_message.lower():
            raise HTTPException(status_code=400, detail="Invalid email or password format")
        else:
            raise HTTPException(status_code=500, detail=f"Error creating user: {error_message}")


@router.post("/signup-regular")
def signup_regular(user: UserAuth):
    """
    Regular signup (requires email confirmation if enabled)
    """
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })
        
        if response and hasattr(response, 'user') and response.user:
            return {
                "message": "User created successfully. Please check your email for verification.",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        error_message = str(e)
        if "already registered" in error_message.lower():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        else:
            raise HTTPException(status_code=500, detail=f"Error creating user: {error_message}")


@router.post("/login")
def login(user: UserAuth):
    """
    User login
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        
        if response and hasattr(response, 'session') and response.session:
            return {
                "message": "Login successful",
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        error_message = str(e)
        if "invalid" in error_message.lower() or "credentials" in error_message.lower():
            raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            raise HTTPException(status_code=500, detail=f"Error logging in: {error_message}")
