"""
Запросы к служебному API AITUNNEL (баланс и т.д.)
https://aitunnel.ru/docs/api/balance
"""
import logging
import time
from typing import Any, Optional

import httpx

from backend.config import settings
from backend.aitunnel_context import effective_aitunnel_api_key

logger = logging.getLogger("competitor_monitor.aitunnel")

_BALANCE_CACHE_TTL = 45.0
_balance_cache: dict[str, tuple[float, dict[str, Any]]] = {}


class AITunnelService:
    """Клиент для не-OpenAI эндпоинтов AITUNNEL."""

    def _headers(self) -> dict[str, str]:
        key = effective_aitunnel_api_key()
        if not key:
            raise ValueError("AITUNNEL_API_KEY не задан")
        return {"Authorization": f"Bearer {key}"}

    def _balance_url(self) -> str:
        base = settings.aitunnel_base_url.rstrip("/")
        return f"{base}/aitunnel/balance"

    async def get_balance(self, *, force_refresh: bool = False) -> dict[str, Any]:
        key = effective_aitunnel_api_key()
        if not key:
            raise ValueError("AITUNNEL_API_KEY не задан")

        cache_id = key[-8:]
        now = time.monotonic()
        cached = _balance_cache.get(cache_id)
        if not force_refresh and cached is not None:
            cached_at, data = cached
            if (now - cached_at) < _BALANCE_CACHE_TTL:
                return data

        logger.info("Запрос баланса AITUNNEL")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self._balance_url(),
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("AITUNNEL balance HTTP %s: %s", e.response.status_code, e)
            raise
        except httpx.RequestError as e:
            logger.error("AITUNNEL balance request error: %s", e)
            raise

        _balance_cache[cache_id] = (now, data)
        logger.info("Баланс получен: %.2f ₽", float(data.get("balance", 0)))
        return data


aitunnel_service = AITunnelService()
