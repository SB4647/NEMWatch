import re
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from nemwatch.observability.logging import correlation_id
from nemwatch.observability.metrics import HTTP_DURATION, HTTP_REQUESTS

VALID_CORRELATION_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class CorrelationMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("X-Correlation-ID", "")
        active_id = supplied if VALID_CORRELATION_ID.fullmatch(supplied) else str(uuid4())
        token = correlation_id.set(active_id)
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Correlation-ID"] = active_id
            return response
        finally:
            route = request.scope.get("route")
            route_name = getattr(route, "path", "unmatched")
            HTTP_REQUESTS.labels(request.method, route_name, f"{status // 100}xx").inc()
            HTTP_DURATION.labels(request.method, route_name).observe(time.perf_counter() - started)
            correlation_id.reset(token)
