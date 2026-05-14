from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import require_admin
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog
from datetime import datetime
import platform

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """الحصول على حالة النظام (لأدمن فقط)"""
    
    total_users = db.query(User).count()
    total_students = db.query(Student).count()
    total_audit_logs = db.query(AuditLog).count()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "total_users": total_users,
            "total_students": total_students,
            "total_audit_logs": total_audit_logs
        },
        "system": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": platform.node()
        }
    }