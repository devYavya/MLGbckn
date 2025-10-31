"""
Routers package - exports all API routers
"""
from .ai import router as ai_router
from .auth import router as auth_router
from .courses import router as courses_router
from .admin import router as admin_router
from .enrollments import router as enrollments_router
from .profiles import router as profiles_router
from .teachers import router as teachers_router

__all__ = [
    "auth_router",
    "courses_router",
    "admin_router",
    "enrollments_router",
    "profiles_router",
    "teachers_router",
    "ai_router"
]
