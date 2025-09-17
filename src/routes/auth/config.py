from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request,Depends
from typing import Dict, List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from pytz import InvalidTimeError
from fastapi import status
import pytz
import uuid
from fastapi.responses import JSONResponse
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from src.routes.auth.config import hash_password, create_access_token2,create_access_token,verify_password,get_logged_user
from src.routes.auth.models import users_collection,User

from src.utils.config import get_settings

settings=get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ist = pytz.timezone("Asia/Kolkata")
ist_now = datetime.now(ist)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token2(data: dict, expires_delta: timedelta = None):
    expiration = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    data.update({"exp": expiration})
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_logged_user(request: Request):
    """
    Extracts and verifies JWT from Authorization header.
    Returns user info if token is valid.
    """

    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ENCRYPTION_ALGORITHM],
            options={"verify_exp": True}
        )

        user_id = payload.get("user_id")
        username = payload.get("sub")

        if not user_id or not isinstance(username, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"user_id": user_id, "username": username}

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    

async def register_user_service(user: User, status_code=status.HTTP_201_CREATED):
 
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    existing_email = await users_collection.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔐 Hash password
    hashed_password = hash_password(user.password)

    # 🔢 Get next auto-increment user ID


    # 📦 Build user document
    user_dict = user.dict()
    user_dict["id"] = str(uuid4())
    user_dict["password"] = hashed_password


    # 💾 Insert into DB
    await users_collection.insert_one(user_dict)

    return JSONResponse(
        status_code=201,
        content={
            "message": "User registered successfully"
        }
    )


def get_current_user(request: Request) -> dict:
    """
    Dependency to get current user from JWT token
    """
    # Extract and validate JWT token
    auth_header = request.headers.get("authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Must start with 'Bearer '"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ENCRYPTION_ALGORITHM]
        )
        
        user_id = payload.get("user_id")
        company_id = payload.get("company_id")
        role = payload.get("role")
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user_id"
            )
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": role,
            "company_id": company_id,
            "permissions": payload.get("permissions", []),
            "is_super_admin": role == "super_admin"
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )


bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

def require_role(role: str):
    async def role_checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Only {role} role can access this route."
            )
        return user
    return role_checker