"""Ключ AITUNNEL для текущего HTTP-запроса (заголовок X-AITunnel-API-Key)."""
from contextvars import ContextVar
from typing import Optional

from backend.config import settings

aitunnel_api_key_ctx: ContextVar[Optional[str]] = ContextVar(
    "aitunnel_api_key", default=None
)


def effective_aitunnel_api_key() -> str:
    """Ключ из заголовка запроса или из .env сервера."""
    header_key = (aitunnel_api_key_ctx.get() or "").strip()
    if header_key:
        return header_key
    return (settings.aitunnel_api_key or "").strip()
