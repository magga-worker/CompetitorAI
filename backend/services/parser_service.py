"""
Сервис для парсинга веб-страниц через Playwright (Chromium в .browsers).
При недоступности браузера — HTTP + BeautifulSoup без скриншота.
"""
import base64
import asyncio
import logging
import time
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from backend.config import settings

logger = logging.getLogger("competitor_monitor.parser")

_HTTP_FALLBACK = "__HTTP_FALLBACK__"
_CHROMIUM_LAUNCH_ARGS = (
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
)


def _browsers_installed() -> bool:
    path = settings.playwright_browsers_path
    if not path:
        return False
    from pathlib import Path

    root = Path(path)
    if not root.is_dir():
        return False
    return any(root.glob("chromium-*"))


class ParserService:
    """Парсинг веб-страниц: Playwright + скриншот."""

    def __init__(self) -> None:
        logger.info("=" * 50)
        logger.info("Инициализация Parser сервиса")
        logger.info("  Timeout: %s сек", settings.parser_timeout)
        logger.info("  User-Agent: %s...", settings.parser_user_agent[:50])
        logger.info("  PLAYWRIGHT_BROWSERS_PATH: %s", settings.playwright_browsers_path)

        self.timeout = settings.parser_timeout
        self.timeout_ms = settings.parser_timeout * 1000
        self._executor = ThreadPoolExecutor(max_workers=2)

        if _browsers_installed():
            logger.info("  Playwright Chromium: найден в .browsers")
        else:
            logger.warning(
                "  Chromium в .browsers не найден — парсинг без скриншота (HTTP-fallback). "
                "Запустите: bash scripts/install_browsers.sh"
            )

        logger.info("Parser сервис инициализирован ✓")
        logger.info("=" * 50)

    async def _parse_playwright(
        self, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        logger.info("=" * 50)
        logger.info("🔍 ПАРСИНГ САЙТА (Playwright): %s", url)
        total_start = time.time()
        browser = None

        try:
            async with async_playwright() as pw:
                logger.info("  🌐 Запуск Chromium...")
                browser = await pw.chromium.launch(
                    headless=True,
                    args=list(_CHROMIUM_LAUNCH_ARGS),
                )
                context = await browser.new_context(
                    user_agent=settings.parser_user_agent,
                    viewport={"width": 1920, "height": 1080},
                )
                page = await context.new_page()

                logger.info("  📄 Загрузка страницы...")
                page_start = time.time()
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )
                logger.info("  ✓ Страница загружена за %.2f сек", time.time() - page_start)

                await page.wait_for_selector("body", timeout=self.timeout_ms)
                await asyncio.sleep(2)

                title = await page.title()
                logger.info("  📌 Title: %s...", (title or "N/A")[:60])

                h1 = None
                if await page.locator("h1").count() > 0:
                    h1 = (await page.locator("h1").first.inner_text()).strip() or None
                    logger.info("  📌 H1: %s...", (h1 or "N/A")[:60])

                first_paragraph = None
                paragraphs = page.locator("p")
                count = await paragraphs.count()
                for i in range(min(count, 30)):
                    text = (await paragraphs.nth(i).inner_text()).strip()
                    if len(text) > 50:
                        first_paragraph = text[:500]
                        logger.info("  📌 Первый абзац (p[%s]): %s...", i, first_paragraph[:60])
                        break

                logger.info("  📸 Создание скриншота...")
                screenshot_start = time.time()
                screenshot_bytes = await page.screenshot(type="png", full_page=False)
                logger.info(
                    "  ✓ Скриншот за %.2f сек (%.1f KB)",
                    time.time() - screenshot_start,
                    len(screenshot_bytes) / 1024,
                )

                await context.close()
                await browser.close()
                browser = None

                logger.info("  ✅ ПАРСИНГ ЗАВЕРШЁН за %.2f сек", time.time() - total_start)
                logger.info("=" * 50)
                return title, h1, first_paragraph, screenshot_bytes, None

        except PlaywrightTimeout:
            logger.error("  ✗ TIMEOUT за %.2f сек", time.time() - total_start)
            logger.error("=" * 50)
            return None, None, None, None, "Превышено время ожидания загрузки страницы"

        except PlaywrightError as e:
            error_msg = str(e)
            logger.error("  ✗ Playwright: %s", error_msg[:300])

            if any(
                hint in error_msg
                for hint in (
                    "Executable doesn't exist",
                    "Please run the following command",
                    "playwright install",
                )
            ):
                logger.error("=" * 50)
                return None, None, None, None, _HTTP_FALLBACK

            if "ERR_NAME_NOT_RESOLVED" in error_msg:
                return None, None, None, None, "Не удалось найти сайт по указанному адресу"
            if "ERR_CONNECTION_REFUSED" in error_msg:
                return None, None, None, None, "Соединение отклонено сервером"
            if "ERR_CONNECTION_TIMED_OUT" in error_msg:
                return None, None, None, None, "Превышено время ожидания соединения"

            logger.error("=" * 50)
            return None, None, None, None, f"Ошибка браузера: {error_msg[:200]}"

        except Exception as e:
            logger.error("  ✗ Ошибка: %s", e)
            logger.error("=" * 50)
            return None, None, None, None, f"Ошибка при загрузке страницы: {str(e)[:200]}"

        finally:
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass

    def _parse_http(
        self, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        logger.info("  📡 HTTP-fallback (без Chromium): %s", url)
        headers = {
            "User-Agent": settings.parser_user_agent,
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
        try:
            with httpx.Client(
                timeout=float(self.timeout),
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return None, None, None, None, f"HTTP {exc.response.status_code} при загрузке страницы"
        except httpx.RequestError as exc:
            return None, None, None, None, f"Не удалось загрузить страницу: {exc}"

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else None

        h1 = None
        h1_tag = soup.find("h1")
        if h1_tag:
            h1 = h1_tag.get_text(" ", strip=True)

        first_paragraph = None
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if len(text) > 50:
                first_paragraph = text[:500]
                break

        logger.info("  ✅ HTTP-парсинг: title=%s", (title or "N/A")[:60])
        return title, h1, first_paragraph, None, None

    async def parse_url(
        self, url: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        original_url = url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            logger.info("  URL дополнен протоколом: %s -> %s", original_url, url)

        logger.info("🚀 Запуск парсинга: %s", url)
        loop = asyncio.get_event_loop()

        if not _browsers_installed():
            return await loop.run_in_executor(self._executor, self._parse_http, url)

        result = await self._parse_playwright(url)
        if result[4] == _HTTP_FALLBACK:
            logger.warning("  Повтор через HTTP-fallback")
            return await loop.run_in_executor(self._executor, self._parse_http, url)
        return result

    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def close(self) -> None:
        logger.info("Закрытие Parser сервиса...")
        self._executor.shutdown(wait=False)
        logger.info("Parser сервис закрыт ✓")


logger.info("Создание глобального экземпляра Parser сервиса...")
parser_service = ParserService()
