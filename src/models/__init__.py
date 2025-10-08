"""
Models package - exports all schemas
"""
from .auth_schemas import (
    UserAuth,
    StudentSignup,
    TeacherSignup,
    TeacherApplication,
    SuperAdminSignup
)
from .course_schemas import (
    CourseCreate,
    ModuleCreate,
    LessonCreate,
    LessonOut,
    ModuleOut,
    CourseOut,
    CoursePrice
)
from .user_schemas import (
    ProfileUpdate,
    RoleChange
)
from .enrollment_schemas import (
    PricingCreate,
    DiscountCreate,
    EnrollmentCreate
)

__all__ = [
    # Auth schemas
    "UserAuth",
    "StudentSignup",
    "TeacherSignup",
    "TeacherApplication",
    "SuperAdminSignup",
    # Course schemas
    "CourseCreate",
    "ModuleCreate",
    "LessonCreate",
    "LessonOut",
    "ModuleOut",
    "CourseOut",
    "CoursePrice",
    # User schemas
    "ProfileUpdate",
    "RoleChange",
    # Enrollment schemas
    "PricingCreate",
    "DiscountCreate",
    "EnrollmentCreate",
]
