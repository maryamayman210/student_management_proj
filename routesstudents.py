from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin, require_student_or_admin, check_student_access
from app.auth import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/")
def get_all_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    return {"message": "Admin can view all students"}


@router.get("/{student_id}")
def get_student_by_id(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student_or_admin)
):
    check_student_access(student_id, current_user)
    return {"message": f"Allowed to view student {student_id}"}


@router.post("/")
def create_student(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    return {"message": "Admin can create student"}


@router.put("/{student_id}")
def update_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student_or_admin)
):
    check_student_access(student_id, current_user)
    return {"message": f"Allowed to update student {student_id}"}


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    return {"message": f"Admin can delete student {student_id}"}