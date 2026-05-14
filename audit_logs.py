from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.dependencies import require_admin
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit_log import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/", response_model=List[AuditLogResponse])
def get_all_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """استرجاع كل سجلات المراجعة (لأدمن فقط)"""
    logs = AuditService.get_all(db, skip, limit)
    return logs

@router.get("/users/{user_id}")
def get_user_audit_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """استرجاع سجلات المراجعة لمستخدم معين (لأدمن فقط)"""
    logs = AuditService.get_by_user(db, user_id, skip, limit)
    return logs