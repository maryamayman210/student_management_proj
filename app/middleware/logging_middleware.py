import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from prometheus_client import Counter, Histogram, Gauge

# استورد الـ metrics من ملف metrics.py بدل ما تعرفهم تاني
from app.api.v1.endpoints.metrics import REQUEST_COUNT, REQUEST_TIME, ACTIVE_REQUESTS

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.api.v1.endpoints.metrics import (
    REQUEST_COUNT,
    REQUEST_TIME,
    ACTIVE_REQUESTS
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # زيادة عدد الطلبات النشطة
        ACTIVE_REQUESTS.inc()

        try:
            logger.info(f"Request: {request.method} {request.url.path}")

            # تنفيذ الطلب
            response = await call_next(request)

            process_time = time.time() - start_time

            # ---------------- METRICS ----------------
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()

            REQUEST_TIME.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(process_time)

            # ---------------- RESPONSE ----------------
            response.headers["X-Process-Time"] = str(round(process_time, 4))

            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )

            return response

        except Exception as e:
            logger.error(
                f"Error in request {request.method} {request.url.path}: {str(e)}"
            )
            raise

        finally:
            # مهم جدًا: يضمن عدم كسر العدّاد حتى لو حصل error
            ACTIVE_REQUESTS.dec()