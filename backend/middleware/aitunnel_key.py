from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.aitunnel_context import aitunnel_api_key_ctx

HEADER_NAME = "X-AITunnel-API-Key"


class AITunnelKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        raw = request.headers.get(HEADER_NAME, "").strip()
        token = None
        if raw:
            token = aitunnel_api_key_ctx.set(raw)
        try:
            return await call_next(request)
        finally:
            if token is not None:
                aitunnel_api_key_ctx.reset(token)
