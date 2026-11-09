"""
Поиск в интернете через DuckDuckGo HTML (без платных API).
"""
import logging
from typing import Optional
from urllib.parse import unquote, urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup

from backend.config import settings

logger = logging.getLogger("competitor_monitor.search")

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


def _normalize_url(href: str) -> Optional[str]:
    if not href:
        return None
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href and "uddg=" in href:
        parsed = parse_qs(urlparse(href).query)
        uddg = parsed.get("uddg", [None])[0]
        if uddg:
            href = unquote(uddg)
    if not href.startswith("http"):
        return None
    return href


class WebSearchService:
    """Синхронный поиск (вызывать через asyncio.to_thread)."""

    def __init__(self) -> None:
        self.user_agent = settings.parser_user_agent
        self.timeout = settings.parser_timeout

    def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        logger.info("Поиск: %s", query[:120])
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
        try:
            with httpx.Client(timeout=float(self.timeout), follow_redirects=True) as client:
                response = client.post(
                    DDG_HTML_URL,
                    data={"q": query, "b": ""},
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Ошибка поиска «%s»: %s", query[:60], exc)
            return []

        soup = BeautifulSoup(response.text, "lxml")
        items: list[dict[str, str]] = []

        for block in soup.select(".result"):
            if len(items) >= max_results:
                break
            link = block.select_one("a.result__a")
            snippet_el = block.select_one("a.result__snippet") or block.select_one(
                ".result__snippet"
            )
            if not link:
                continue
            url = _normalize_url(link.get("href", ""))
            if not url:
                continue
            title = link.get_text(strip=True)
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            items.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "query": query,
                }
            )

        logger.info("  Найдено: %d", len(items))
        return items


web_search_service = WebSearchService()
