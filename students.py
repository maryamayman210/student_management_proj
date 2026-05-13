from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.api.dependencies import get_current_user, require_admin
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.student_service import StudentService
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=List[StudentResponse])
def get_all_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    department: Optional[str] = None,
    gpa_min: Optional[float] = Query(None, ge=0, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """استرجاع كل الطلاب (لأدمن فقط)"""
    students = StudentService.get_all(db, skip, limit, department, gpa_min)
    return students

@router.get("/me", response_model=StudentResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الطالب يشوف بروفايله فقط"""
    student = StudentService.get_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student

@router.put("/me", response_model=StudentResponse)
def update_my_profile(
    student_update: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث البروفايل الخاص بي (للطالب فقط)"""
    student = StudentService.get_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    # الطالب يعدل فقط name, department
    update_data = student_update.model_dump(exclude_unset=True)
    allowed_fields = ["name", "department"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    for field, value in filtered_data.items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    # تسجيل في audit log
    AuditService.log(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        resource="student",
        resource_id=student.id,
        details=f"Student updated their own profile"
    )
    
    return student

@router.get("/{student_id}", response_model=StudentResponse)
def get_student_by_id(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """استرجاع طالب بـ ID (الطالب يشوف نفسه فقط، الأدمن يشوف أي حد)"""
    student = StudentService.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if current_user.role != "admin" and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return student

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """إنشاء طالب جديد (لأدمن فقط)"""
    existing = StudentService.get_by_user_id(db, student.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already has a student profile")
    
    return StudentService.create(db, student)

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث طالب (الأدمن يعدل أي حد، الطالب يعدل نفسه جزئياً)"""
    student = StudentService.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if current_user.role != "admin" and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user.role == "student":
        student_update = StudentUpdate(
            name=student_update.name,
            department=student_update.department
        )
    
    updated = StudentService.update(db, student_id, student_update)
    return updated

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """حذف طالب (لأدمن فقط)"""
    deleted = StudentService.delete(db, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")
    return None

@router.get("/{student_id}/audit-logs")
def get_student_audit_logs(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """استرجاع سجلات المراجعة لطالب معين (لأدمن فقط)"""
    student = StudentService.get_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    logs = AuditService.get_by_resource(db, "student", student_id)
    return logs