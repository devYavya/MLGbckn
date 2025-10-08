"""
DEPRECATED: This file has been refactored into separate router files.

New Structure:
==============

Models (Pydantic Schemas):
--------------------------
- src/models/auth_schemas.py       → Authentication schemas
- src/models/course_schemas.py     → Course, Module, Lesson schemas
- src/models/user_schemas.py       → User profile schemas
- src/models/enrollment_schemas.py → Enrollment, Pricing, Discount schemas

Routers (API Endpoints):
------------------------
- src/routers/auth.py         → Authentication (signup, login, register)
- src/routers/courses.py      → Course management (CRUD for courses, modules, lessons)
- src/routers/admin.py        → Admin operations (approvals, pricing, discounts)
- src/routers/enrollments.py  → Enrollment management (enroll, renew, status)
- src/routers/profiles.py     → User profiles (get, update)
- src/routers/teachers.py     → Teacher features (my courses, enrollment stats)

Main Application:
-----------------
- main.py → FastAPI app with all routers

All endpoints have been moved to their respective files.
This file should no longer be used.
"""
