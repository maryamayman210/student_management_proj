from sqlalchemy.orm import Session
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.cache_service import cache_service
import json

class StudentService:
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 10, department: str = None, gpa_min: float = None):
        """استرجاع كل الطلاب مع فلترة و Pagination"""
        query = db.query(Student)
        
        if department:
            query = query.filter(Student.department == department)
        if gpa_min:
            query = query.filter(Student.gpa >= gpa_min)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, student_id: int):
        """استرجاع طالب بـ ID مع Cache"""
        cache_key = f"student:{student_id}"
        
        # 1. تجربة الكاش أولاً
        cached = cache_service.get(cache_key)
        if cached:
            # ✅ إصلاح: إذا كان cached dict, نحوله لكائن Student مؤقت
            if isinstance(cached, dict):
                # نرجع كائن Student عادي (مش dict)
                student = db.query(Student).filter(Student.id == student_id).first()
                if student:
                    return student
            else:
                return cached
        
        # 2. Cache Miss - استرجاع من قاعدة البيانات
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            # 3. تخزين في الكاش (كـ dict)
            cache_service.set(cache_key, {
                "id": student.id,
                "user_id": student.user_id,
                "name": student.name,
                "department": student.department,
                "gpa": student.gpa,
                "enrolled_year": student.enrolled_year,
            })
        return student  # ✅ نرجع الـ object مش الـ dict
    
    @staticmethod
    def get_by_user_id(db: Session, user_id: int):
        """استرجاع طالب بـ user_id"""
        return db.query(Student).filter(Student.user_id == user_id).first()
    
    @staticmethod
    def create(db: Session, student: StudentCreate):
        """إنشاء طالب جديد"""
        db_student = Student(**student.model_dump())
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        # مسح الكاش المرتبط
        cache_service.delete_pattern("students:all")
        cache_service.delete_pattern("student:")
        return db_student
    
    @staticmethod
    def update(db: Session, student_id: int, student_update: StudentUpdate):
        """تحديث بيانات طالب"""
        # ✅ إصلاح: نجيب الـ object من الـ DB مباشرة (نتجنب الكاش)
        db_student = db.query(Student).filter(Student.id == student_id).first()
        if not db_student:
            return None
        
        update_data = student_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_student, field, value)
        
        db.commit()
        db.refresh(db_student)
        
        # تحديث الكاش بعد التعديل
        cache_service.set(f"student:{student_id}", {
            "id": db_student.id,
            "user_id": db_student.user_id,
            "name": db_student.name,
            "department": db_student.department,
            "gpa": db_student.gpa,
            "enrolled_year": db_student.enrolled_year,
        })
        cache_service.delete_pattern("students:all")
        return db_student
    
    @staticmethod
    def delete(db: Session, student_id: int):
        """حذف طالب"""
        db_student = db.query(Student).filter(Student.id == student_id).first()
        if not db_student:
            return False
        
        db.delete(db_student)
        db.commit()
        
        # مسح الكاش
        cache_service.delete(f"student:{student_id}")
        cache_service.delete_pattern("students:all")
        return True