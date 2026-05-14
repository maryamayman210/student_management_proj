from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import os

from app.database import Base, engine
from app.routes import auth_router, students_router, admin_router, monitoring_router
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.logger import app_logger

# Create DB tables
Base.metadata.create_all(bind=engine)
os.makedirs("logs", exist_ok=True)

app = FastAPI(
    title="Student Management System",
    description="A full-featured backend system for managing university students with secure JWT authentication, role-based access control, Redis caching, and comprehensive monitoring.",
    version="1.0.0",
    contact={"name": "Admin", "email": "admin@university.edu"},
    license_info={"name": "MIT"},
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    app_logger.warning(f"Validation error on {request.url}: {errors}")
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    app_logger.error(f"DB integrity error: {exc}")
    return JSONResponse(status_code=409, content={"detail": "Database integrity error. Duplicate entry or constraint violation."})


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    app_logger.critical(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(admin_router)
app.include_router(monitoring_router)


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "🎓 Student Management System API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/monitoring/health",
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup():
    app_logger.info("=" * 60)
    app_logger.info("Student Management System started")
    app_logger.info("Docs available at: http://localhost:8000/docs")
    app_logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    app_logger.info("Student Management System shutting down")
