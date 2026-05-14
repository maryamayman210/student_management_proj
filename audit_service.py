from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from fastapi import Request

class AuditService:
    
    @staticmethod
    def log(
        db: Session,
        user_id: int,
        action: str,
        resource: str,
        resource_id: int = None,
        details: str = None,
        request: Request = None
    ):
        ip_address = None
        if request:
            ip_address = request.client.host if request.client else None
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_resource(db: Session, resource: str, resource_id: int = None):
        query = db.query(AuditLog).filter(AuditLog.resource == resource)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        return query.order_by(AuditLog.created_at.desc()).all()