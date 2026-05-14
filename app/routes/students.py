import json
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import User, UserRole, Department
from app.schemas.schemas import (
    StudentCreate, StudentUpdate, StudentAdminUpdate,
    StudentResponse, PaginatedStudentResponse, MessageResponse, AuditLogResponse
)
from app.services.auth import get_current_active_user, require_admin
from app.services import (
    get_students, get_student_by_id, get_student_by_user_id,
    create_student, update_student, delete_student, get_audit_logs,
    get_cache, set_cache, delete_cache, delete_pattern
)
from app.logger import app_logger

router = APIRouter(prefix="/api/students", tags=["Students"])


def _invalidate_student_cache(student_id: int = None):
    delete_pattern("students:list:*")
    if student_id:
        delete_cache(f"students:{student_id}")


# ─── GET All Students (Admin only, with filters + pagination) ─────────────────

@router.get("", response_model=PaginatedStudentResponse)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    department: Optional[Department] = None,
    min_gpa: Optional[float] = Query(None, ge=0, le=4),
    max_gpa: Optional[float] = Query(None, ge=0, le=4),
    year: Optional[int] = Query(None, ge=1, le=6),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all students with filters and pagination. Admin only."""
    cache_key = f"students:list:{page}:{page_size}:{department}:{min_gpa}:{max_gpa}:{year}:{search}:{is_active}"
    cached = get_cache(cache_key)
    if cached:
        app_logger.debug(f"Serving students list from cache")
        return cached

    result = get_students(db, page, page_size, department, min_gpa, max_gpa, year, search, is_active)
    # Serialize for cache
    serializable = {
        **result,
        "students": [
            {k: str(v) if hasattr(v, 'value') else v for k, v in s.__dict__.items() if not k.startswith("_")}
            for s in result["students"]
        ]
    }
    set_cache(cache_key, serializable)
    return result


# ─── GET My Profile (Student) ─────────────────────────────────────────────────

@router.get("/me", response_model=StudentResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the student profile of the currently logged-in student."""
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admin users don't have student profiles. Use /api/students/{id}")
    student = get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="No student profile linked to your account")
    return student


# ─── GET Single Student ───────────────────────────────────────────────────────

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a student by ID. Admin can access all; students can only access their own."""
    cache_key = f"students:{student_id}"
    cached = get_cache(cache_key)
    if cached:
        # Enforce student access control on cached data
        if current_user.role == UserRole.student:
            my_student = get_student_by_user_id(db, current_user.id)
            if not my_student or my_student.id != student_id:
                raise HTTPException(status_code=403, detail="Access denied: You can only view your own profile")
        return cached

    student = get_student_by_id(db, student_id)

    # Access control: students can only view their own profile
    if current_user.role == UserRole.student:
        my_student = get_student_by_user_id(db, current_user.id)
        if not my_student or my_student.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied: You can only view your own profile")

    serializable = {k: str(v) if hasattr(v, 'value') else v for k, v in student.__dict__.items() if not k.startswith("_")}
    set_cache(cache_key, serializable)
    return student


# ─── POST Create Student (Admin only) ────────────────────────────────────────

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_new_student(
    data: StudentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new student record. Admin only."""
    student = create_student(db, data, current_user.id)
    _invalidate_student_cache()
    return student


# ─── PUT Update Student ───────────────────────────────────────────────────────

@router.put("/{student_id}", response_model=StudentResponse)
def update_student_record(
    student_id: int,
    data: StudentAdminUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update any student record. Admin only (full update)."""
    student = update_student(db, student_id, data, current_user.id)
    _invalidate_student_cache(student_id)
    return student


@router.put("/me/update", response_model=StudentResponse)
def update_my_profile(
    data: StudentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Students can update limited fields of their own profile."""
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admins should use /api/students/{id}")
    my_student = get_student_by_user_id(db, current_user.id)
    if not my_student:
        raise HTTPException(status_code=404, detail="No student profile linked to your account")
    student = update_student(db, my_student.id, data, current_user.id)
    _invalidate_student_cache(my_student.id)
    return student


# ─── DELETE Student (Admin only) ─────────────────────────────────────────────

@router.delete("/{student_id}", response_model=MessageResponse)
def delete_student_record(
    student_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a student record. Admin only."""
    delete_student(db, student_id, current_user.id)
    _invalidate_student_cache(student_id)
    return {"message": f"Student {student_id} deleted successfully"}


# ─── Audit Logs (Admin only) ──────────────────────────────────────────────────

@router.get("/{student_id}/audit-logs", response_model=dict)
def get_student_audit_logs(
    student_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get audit logs for a specific student. Admin only."""
    return get_audit_logs(db, student_id, page, page_size)
