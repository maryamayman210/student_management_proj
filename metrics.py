from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge
from fastapi.responses import HTMLResponse
from pathlib import Path
from collections import deque
from datetime import datetime

router = APIRouter(prefix="/metrics", tags=["Monitoring"])

# تعريف Metrics (مرة واحدة فقط)
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_TIME = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('http_active_requests', 'Active HTTP requests')

# تخزين مؤقت للـ metrics
request_metrics = deque(maxlen=1000)
total_requests = 0
total_response_time = 0
error_count = 0

def log_request_metric(method: str, path: str, status: int, time_taken: float):
    global total_requests, total_response_time, error_count
    total_requests += 1
    total_response_time += time_taken
    if status >= 400:
        error_count += 1
    
    request_metrics.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "method": method,
        "path": path,
        "status": status,
        "time_taken": round(time_taken, 3)
    })

@router.get("/prometheus")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/")
async def get_metrics():
    """Custom metrics endpoint for dashboard"""
    avg_time = (total_response_time / total_requests * 1000) if total_requests > 0 else 0
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "total_requests": total_requests,
        "avg_response_time": round(avg_time, 2),
        "error_rate": round(error_rate, 2),
        "recent_logs": list(request_metrics)[-50:]
    }

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_path = Path("app/static/dashboard.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>Dashboard not found</h1>")