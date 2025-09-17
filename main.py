"""
Multi-tenant SaaS FastAPI Application
"""
from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from src.utils.config import get_settings
from src.routes.auth.router import router as auth_router

settings = get_settings()


security_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Enter JWT token in the format: Bearer {token}",
    auto_error=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting MLG SaaS API...")
    yield
    # Shutdown
    print("🛑 Shutting down MLG SaaS API...")


app = FastAPI(
    title="MLG Multi-tenant SaaS API",
    description="A comprehensive multi-tenant SaaS platform for MLG",
    version="1.0.0",
    docs_url=f"{settings.API_BASE_PATH}/docs",
    openapi_url=f"{settings.API_BASE_PATH}/openapi.json",
    lifespan=lifespan
)


app.openapi_components = {
    "securitySchemes": {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
        }
    }
}


origins = [
    "http://localhost:3000",
    "http://localhost:5173"    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],       
)





@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agra Heritage SaaS API",
        "version": "1.0.0"
    }

@app.get("/")
def test():
    return {
        "message": "Welcome to MLG Backend ",
        "docs": f"{settings.API_BASE_PATH}/docs",
        "version": "1.0.0"
    }


app.include_router(auth_router, prefix=f"{settings.API_BASE_PATH}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.debug
    )
