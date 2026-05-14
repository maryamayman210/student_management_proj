from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from fastapi import HTTPException, status
from app.models.models import Student, AuditLog, User
from app.schemas.schemas import StudentCreate, StudentUpdate, StudentAdminUpdate
from app.logger import app_logger


def create_audit_log(db: Session, student_id: Optional[int], performed_by: int, action: str, details: str = None):
    log = AuditLog(
        student_id=student_id,
        performed_by=performed_by,
        action=action,
        details=details,
    )
    db.add(log)
    db.commit()
    app_logger.info(f"AUDIT - action='{action}' student_id={student_id} by user_id={performed_by} | {details}")


def get_students(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    department: Optional[str] = None,
    min_gpa: Optional[float] = None,
    max_gpa: Optional[float] = None,
    year: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    query = db.query(Student)

    if department:
        query = query.filter(Student.department == department)
    if min_gpa is not None:
        query = query.filter(Student.gpa >= min_gpa)
    if max_gpa is not None:
        query = query.filter(Student.gpa <= max_gpa)
    if year is not None:
        query = query.filter(Student.year == year)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(search_term),
                Student.last_name.ilike(search_term),
                Student.email.ilike(search_term),
                Student.student_id.ilike(search_term),
            )
        )
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)

    total = query.count()
    pages = (total + page_size - 1) // page_size
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "students": students,
    }


def get_student_by_id(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with id {student_id} not found")
    return student


def get_student_by_user_id(db: Session, user_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.user_id == user_id).first()


def create_student(db: Session, data: StudentCreate, performed_by: int) -> Student:
    # Check uniqueness
    if db.query(Student).filter(Student.student_id == data.student_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student ID already exists")
    if db.query(Student).filter(Student.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if data.user_id and db.query(Student).filter(Student.user_id == data.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already linked to a student record")

    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)

    create_audit_log(db, student.id, performed_by, "CREATE", f"Created student {student.student_id}")
    app_logger.info(f"Student created: id={student.id} student_id={student.student_id}")
    return student


def update_student(db: Session, student_id: int, data: StudentUpdate | StudentAdminUpdate, performed_by: int) -> Student:
    student = get_student_by_id(db, student_id)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    changes = []
    for field, value in update_data.items():
        old = getattr(student, field, None)
        if old != value:
            changes.append(f"{field}: {old} → {value}")
            setattr(student, field, value)

    db.commit()
    db.refresh(student)

    create_audit_log(db, student.id, performed_by, "UPDATE", "; ".join(changes) if changes else "No changes")
    app_logger.info(f"Student updated: id={student.id} changes: {changes}")
    return student


def delete_student(db: Session, student_id: int, performed_by: int) -> bool:
    student = get_student_by_id(db, student_id)
    create_audit_log(db, student.id, performed_by, "DELETE", f"Deleted student {student.student_id}")
    db.delete(student)
    db.commit()
    app_logger.info(f"Student deleted: id={student_id}")
    return True


def get_audit_logs(db: Session, student_id: Optional[int] = None, page: int = 1, page_size: int = 20):
    query = db.query(AuditLog)
    if student_id:
        query = query.filter(AuditLog.student_id == student_id)
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "logs": logs}
