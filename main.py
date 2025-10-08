"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.config import get_settings
from src.routers import (
    auth_router,
    courses_router,
    admin_router,
    enrollments_router,
    profiles_router,
    teachers_router
)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="MLG Multi-tenant SaaS API",
    description="A comprehensive multi-tenant SaaS platform for MLG",
    version="1.0.0",
    docs_url=f"{settings.API_BASE_PATH}/docs",
    openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router, prefix=settings.API_BASE_PATH)
app.include_router(courses_router, prefix=settings.API_BASE_PATH)
app.include_router(admin_router, prefix=settings.API_BASE_PATH)
app.include_router(enrollments_router, prefix=settings.API_BASE_PATH)
app.include_router(profiles_router, prefix=settings.API_BASE_PATH)
app.include_router(teachers_router, prefix=settings.API_BASE_PATH)


@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "Welcome to GuruSchool API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.debug
    )
