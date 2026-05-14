from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Student, AuditLog
from app.schemas.schemas import HealthResponse
from app.services.auth import require_admin, get_current_active_user
from app.services.cache import get_cache_info, REDIS_AVAILABLE
from app.middleware.logging_middleware import request_metrics
import statistics

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Public health check endpoint."""
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    cache_status = "available" if REDIS_AVAILABLE else "unavailable"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "cache": cache_status,
        "version": "1.0.0",
    }


@router.get("/metrics")
def get_metrics(current_user: User = Depends(require_admin)):
    """Get application metrics. Admin only."""
    times = request_metrics["response_times"]
    avg_time = round(statistics.mean(times), 2) if times else 0
    p95_time = round(sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max(times, default=0), 2)

    top_endpoints = sorted(
        [
            {
                "endpoint": ep,
                "count": data["count"],
                "errors": data["errors"],
                "avg_time": round(data["total_time"] / data["count"], 2) if data["count"] > 0 else 0,
                "error_rate": round(data["errors"] / data["count"] * 100, 1) if data["count"] > 0 else 0,
            }
            for ep, data in request_metrics["endpoints"].items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    return {
        "total_requests": request_metrics["total_requests"],
        "total_errors": request_metrics["total_errors"],
        "error_rate": round(request_metrics["total_errors"] / max(request_metrics["total_requests"], 1) * 100, 2),
        "avg_response_time_ms": avg_time,
        "p95_response_time_ms": p95_time,
        "top_endpoints": top_endpoints,
        "cache": get_cache_info(),
    }


@router.get("/stats")
def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get database statistics. Admin only."""
    total_users = db.query(User).count()
    total_students = db.query(Student).count()
    active_students = db.query(Student).filter(Student.is_active == True).count()
    total_audits = db.query(AuditLog).count()

    # GPA distribution
    from sqlalchemy import func
    gpa_data = db.query(
        func.avg(Student.gpa).label("avg_gpa"),
        func.min(Student.gpa).label("min_gpa"),
        func.max(Student.gpa).label("max_gpa"),
    ).first()

    dept_counts = db.query(Student.department, func.count(Student.id)).group_by(Student.department).all()

    return {
        "total_users": total_users,
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": total_students - active_students,
        "total_audit_logs": total_audits,
        "gpa_stats": {
            "average": round(float(gpa_data.avg_gpa or 0), 2),
            "min": float(gpa_data.min_gpa or 0),
            "max": float(gpa_data.max_gpa or 0),
        },
        "students_by_department": {dept.value if hasattr(dept, 'value') else dept: count for dept, count in dept_counts},
    }
