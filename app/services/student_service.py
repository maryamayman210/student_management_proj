from sqlalchemy.orm import Session
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.cache_service import cache_service


class StudentService:

    # ---------- HELPER ----------
    @staticmethod
    def _to_dict(student: Student):
        """تحويل الـ ORM object إلى dict موحد"""
        return {
            "id": student.id,
            "user_id": student.user_id,
            "name": student.name,
            "department": student.department,
            "gpa": student.gpa,
            "enrolled_year": student.enrolled_year,
            "created_at": student.created_at,
            "updated_at": student.updated_at,
        }

    # ---------- GET ALL ----------
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 10,
                department: str = None, gpa_min: float = None):

        cache_key = f"students:all:{skip}:{limit}:{department}:{gpa_min}"

        cached = cache_service.get(cache_key)
        if cached:
            return cached

        query = db.query(Student)

        if department:
            query = query.filter(Student.department == department)
        if gpa_min:
            query = query.filter(Student.gpa >= gpa_min)

        result = query.offset(skip).limit(limit).all()

        data = [StudentService._to_dict(s) for s in result]

        cache_service.set(cache_key, data, expire=60)
        return data

    # ---------- GET BY ID ----------
    @staticmethod
    def get_by_id(db: Session, student_id: int):

        cache_key = f"student:{student_id}"

        cached = cache_service.get(cache_key)
        if cached:
            return cached

        student = db.query(Student).filter(Student.id == student_id).first()

        if not student:
            return None

        data = StudentService._to_dict(student)

        cache_service.set(cache_key, data, expire=60)
        return data

    # ---------- CREATE ----------
    @staticmethod
    def create(db: Session, student: StudentCreate):

        db_student = Student(**student.model_dump())
        db.add(db_student)
        db.commit()
        db.refresh(db_student)

        cache_service.delete_pattern("students:all")
        return StudentService._to_dict(db_student)

    # ---------- UPDATE ----------
    @staticmethod
    def update(db: Session, student_id: int, student_update: StudentUpdate):

        db_student = db.query(Student).filter(Student.id == student_id).first()
        if not db_student:
            return None

        for key, value in student_update.model_dump(exclude_unset=True).items():
            setattr(db_student, key, value)

        db.commit()
        db.refresh(db_student)

        cache_service.delete(f"student:{student_id}")
        cache_service.delete_pattern("students:all")

        return StudentService._to_dict(db_student)

    # ---------- DELETE ----------
    @staticmethod
    def delete(db: Session, student_id: int):

        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False

        db.delete(student)
        db.commit()

        cache_service.delete(f"student:{student_id}")
        cache_service.delete_pattern("students:all")

        return True