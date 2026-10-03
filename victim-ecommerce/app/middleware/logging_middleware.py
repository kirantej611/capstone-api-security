import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("victim_ecommerce.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000  # ms
        
        # Log the request
        logger.info(
            f"{client_ip} - \"{method} {path}{'?' + query if query else ''}\" "
            f"{response.status_code} {process_time:.1f}ms"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.1f}ms"
        
        return response
