"""
OSINT-сводка: веб-поиск + синтез отчёта через AITUNNEL.
"""
import asyncio
import logging
from typing import Optional

from backend.models.schemas import OsintReport, OsintSource
from backend.services.openai_service import openai_service
from backend.services.web_search_service import web_search_service

logger = logging.getLogger("competitor_monitor.osint")

RESULTS_PER_QUERY = 4
MAX_SOURCES = 12
MAX_SNIPPET_LEN = 220


def _build_queries(company_name: str, company_details: Optional[str]) -> list[str]:
    name = company_name.strip()
    extra = (company_details or "").strip()
    base = f"{name} {extra}".strip() if extra else name
    return [
        f"{base} отзывы клиентов",
        f"{base} рейтинг отзывы",
        f"{name} соцсети ВКонтакте Telegram Instagram",
        f"{name} репутация компания",
        f"{base} Яндекс карты отзывы 2gis",
    ]


def _merge_sources(hit_lists: list[list[dict]]) -> list[dict]:
    seen: set[str] = set()
    merged: list[dict] = []
    for hits in hit_lists:
        for hit in hits:
            url = hit.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            merged.append(hit)
            if len(merged) >= MAX_SOURCES:
                return merged
    return merged


def _format_hits_for_llm(sources: list[dict]) -> str:
    blocks = []
    for i, src in enumerate(sources, 1):
        snippet = (src.get("snippet", "") or "")[:MAX_SNIPPET_LEN]
        blocks.append(
            f"[{i}] {src.get('title', '')}\n"
            f"URL: {src.get('url', '')}\n"
            f"Фрагмент: {snippet}"
        )
    text = "\n\n".join(blocks) if blocks else "(Результаты поиска не найдены)"
    return text[:9000]


class OsintService:
    async def build_summary(
        self,
        company_name: str,
        company_details: Optional[str] = None,
    ) -> tuple[OsintReport, list[OsintSource]]:
        queries = _build_queries(company_name, company_details)
        logger.info("OSINT: %d поисковых запросов для «%s»", len(queries), company_name)

        hit_lists = await asyncio.gather(
            *[
                asyncio.to_thread(
                    web_search_service.search, q, RESULTS_PER_QUERY
                )
                for q in queries
            ]
        )
        raw = _merge_sources(list(hit_lists))
        context = _format_hits_for_llm(raw)

        report = await openai_service.analyze_osint(
            company_name=company_name,
            company_details=company_details,
            search_context=context,
        )

        sources = [
            OsintSource(
                title=h.get("title", ""),
                url=h.get("url", ""),
                snippet=h.get("snippet", ""),
            )
            for h in raw
        ]

        # Ссылки из отчёта модели (если есть) дополняют список
        for src in report.key_source_links:
            if src.url and src.url not in {s.url for s in sources}:
                sources.append(src)

        return report, sources[:MAX_SOURCES]


osint_service = OsintService()
