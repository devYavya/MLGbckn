from fastapi import APIRouter, Depends, HTTPException, Request, status, Header,Query
from uuid import UUID

from src.routes.auth.models import UserRegister,users_collection,User,UserLogin,TokenResponse,AdminRegister
from src.routes.auth.config import hash_password,create_access_token,verify_password,get_current_user,require_role
from datetime import timedelta
from src.utils.config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])

settings = get_settings()

@router.post("/admin-register")
async def register_admin(admin: AdminRegister):
    # Validate admin token
    if admin.admin_token != settings.SUPER_ADMIN_SEED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token. Only authorized personnel can register as admin."
        )
    
    # Check if email is in allowed admin emails list
    if admin.email not in settings.ALLOWED_ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not authorized for admin registration."
        )
    
    # Check if admin already exists (one-time registration only)
    existing_admin = await users_collection.find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin already exists. Only one admin can be registered."
        )
    
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": admin.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(admin.password)

    # Create new admin user
    new_admin = User(
        first_name=admin.first_name,
        last_name=admin.last_name,
        email=admin.email,
        password=hashed_password,
        role="admin",
        is_admin=True,
        is_verified=True
    )

    # Convert to dict with UUIDs as strings
    admin_dict = new_admin.dict()
    admin_dict["id"] = str(new_admin.id)

    await users_collection.insert_one(admin_dict)
    return {
        "message": "Admin registered successfully",
        "admin_id": str(new_admin.id),
        "name": f"{new_admin.first_name} {new_admin.last_name}",
        "role": "admin"
    }


@router.post("/register")
async def register_user(user: UserRegister):
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(user.password)

    if getattr(user, "role", None) == "admin":
        raise HTTPException(status_code=400, detail="You cannot register as admin")


    # Create new user
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role if hasattr(user, 'role') else "user",
        password=hashed_password,
    )
    new_user = User(
    first_name=user.first_name,
    last_name=user.last_name,
    email=user.email,
    role=user.role if hasattr(user, 'role') else "user",
    password=hashed_password,
)

# Convert to dict with UUIDs as strings
    user_dict = new_user.dict()
    user_dict["id"] = str(new_user.id)

    await users_collection.insert_one(user_dict)
    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "name": f"{new_user.first_name} {new_user.last_name}"
    }



@router.post("/login", response_model=TokenResponse)
async def login_user(user: UserLogin):
    # Find user by email
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user["id"], "email": db_user["email"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"]  # fresh from DB
    }

@router.get("/user")
async def user_dashboard(user=Depends(require_role("user"))):
    return {"msg": f"Welcome to User Dashboard, {user['first_name']}!"}


@router.get("/teacher")
async def teacher_dashboard(user=Depends(require_role("teacher"))):
    return {"msg": f"Welcome to Teacher Dashboard, {user['first_name']}!"}

@router.get("/admin")
async def admin_dashboard(user=Depends(require_role("admin"))):
    return {"msg": f"Welcome to Admin Dashboard, {user['first_name']}!"}