import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger import app_logger

# In-memory metrics store
request_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "endpoints": {},
    "response_times": [],
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_metrics["total_requests"] += 1

        # Process request
        try:
            response: Response = await call_next(request)
        except Exception as e:
            request_metrics["total_errors"] += 1
            app_logger.error(f"Unhandled exception: {e}")
            raise

        process_time = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code

        # Track metrics
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in request_metrics["endpoints"]:
            request_metrics["endpoints"][endpoint] = {"count": 0, "errors": 0, "total_time": 0}
        request_metrics["endpoints"][endpoint]["count"] += 1
        request_metrics["endpoints"][endpoint]["total_time"] += process_time
        if status_code >= 400:
            request_metrics["endpoints"][endpoint]["errors"] += 1
            request_metrics["total_errors"] += 1

        # Keep last 100 response times
        request_metrics["response_times"].append(process_time)
        if len(request_metrics["response_times"]) > 100:
            request_metrics["response_times"].pop(0)

        # Log
        log_level = "WARNING" if status_code >= 400 else "INFO"
        log_msg = (
            f"REQUEST | {request.method} {request.url.path} "
            f"status={status_code} time={process_time}ms "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        if log_level == "WARNING":
            app_logger.warning(log_msg)
        else:
            app_logger.info(log_msg)

        response.headers["X-Process-Time"] = str(process_time)
        return response
