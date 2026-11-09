"""
Сервис для работы с AITUNNEL (OpenAI-совместимый API)
https://aitunnel.ru/docs/api-reference
"""
import base64
import json
import re
import time
import logging
from typing import Optional, Union

from openai import OpenAI

from backend.config import settings
from backend.aitunnel_context import effective_aitunnel_api_key
from backend.models.schemas import (
    CompetitorAnalysis,
    ImageAnalysis,
    OsintReport,
    OsintReviewPlatform,
    OsintReviewStatistics,
    OsintSentimentPercent,
    OsintSource,
)

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.openai")


class OpenAIService:
    """Сервис для анализа через AITUNNEL"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация AI сервиса (AITUNNEL)")
        logger.info(f"  Base URL: {settings.aitunnel_base_url}")
        logger.info(f"  Модель текста: {settings.aitunnel_model}")
        logger.info(f"  Модель vision: {settings.aitunnel_vision_model}")
        key = settings.aitunnel_api_key
        logger.info(f"  API ключ (.env): {'*' * 10}...{key[-4:] if key else 'НЕ ЗАДАН'}")
        logger.info("  Ключ из клиента: заголовок X-AITunnel-API-Key")

        self._client_key: Optional[str] = None
        self.client = OpenAI(api_key="placeholder", base_url=settings.aitunnel_base_url)
        self.model = settings.aitunnel_model
        self.vision_model = settings.aitunnel_vision_model
        
        logger.info("AI сервис инициализирован успешно ✓")
        logger.info("=" * 50)

    def _get_client(self) -> OpenAI:
        key = effective_aitunnel_api_key()
        if not key:
            raise ValueError("AITUNNEL API ключ не задан (укажите в .env или передайте заголовок)")
        if self._client_key != key:
            self.client = OpenAI(
                api_key=key,
                base_url=settings.aitunnel_base_url,
            )
            self._client_key = key
        return self.client
    
    def _message_content(self, content: Union[str, list, None]) -> str:
        """Текст ответа модели (строка или список частей)."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if text:
                        parts.append(str(text))
                elif part:
                    parts.append(str(part))
            return "\n".join(parts).strip()
        return str(content).strip()

    def _parse_json_response(self, content: Union[str, list, None]) -> dict:
        """Извлечь JSON из ответа модели (markdown, обёртка, только JSON)."""
        text = self._message_content(content)
        logger.debug("Парсинг JSON ответа, длина: %d символов", len(text))
        if not text:
            logger.warning("Пустой ответ модели, JSON не извлечь")
            return {}

        candidates: list[str] = [text]

        for block in re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
            block = block.strip()
            if block:
                candidates.append(block)

        brace = text.find("{")
        if brace >= 0:
            candidates.append(text[brace:])

        decoder = json.JSONDecoder()
        for raw in candidates:
            snippet = raw.strip()
            if not snippet:
                continue
            try:
                data = json.loads(snippet)
                if isinstance(data, dict):
                    logger.debug("JSON распарсен, ключей: %d", len(data))
                    return data
            except json.JSONDecodeError:
                pass
            if "{" in snippet:
                start = snippet.find("{")
                try:
                    data, _ = decoder.raw_decode(snippet[start:])
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    continue

        logger.warning("Ошибка парсинга JSON: валидный объект не найден")
        logger.debug("Превью ответа: %s...", text[:300])
        return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        logger.info("=" * 50)
        logger.info("📝 АНАЛИЗ ТЕКСТА КОНКУРЕНТА")
        logger.info(f"  Длина текста: {len(text)} символов")
        logger.info(f"  Превью: {text[:100]}...")
        logger.info(f"  Модель: {self.model}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу. Проанализируй предоставленный текст конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение 1", "уникальное предложение 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Краткое резюме анализа"
}

Важно:
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Будь конкретен и практичен в рекомендациях"""

        start_time = time.time()
        logger.info("  Отправка запроса к API...")
        
        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            raw_content = response.choices[0].message.content
            content = self._message_content(raw_content)
            logger.info(f"  Длина ответа: {len(content)} символов")
            logger.debug(f"  Использовано токенов: {response.usage.total_tokens if response.usage else 'N/A'}")
            
            data = self._parse_json_response(raw_content)
            
            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_offers=data.get("unique_offers", []),
                recommendations=data.get("recommendations", []),
                summary=data.get("summary", "")
            )
            
            logger.info(f"  Результат: {len(result.strengths)} сильных, {len(result.weaknesses)} слабых сторон")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        logger.info("=" * 50)
        logger.info("🖼️ АНАЛИЗ ИЗОБРАЖЕНИЯ")
        logger.info(f"  Размер base64: {len(image_base64)} символов")
        logger.info(f"  MIME тип: {mime_type}")
        logger.info(f"  Модель: {self.vision_model}")
        
        system_prompt = """Ты — эксперт по визуальному маркетингу и дизайну. Проанализируй изображение конкурента (баннер, сайт, упаковка товара и т.д.) и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "marketing_insights": ["инсайт 1", "инсайт 2", ...],
    "visual_style_score": 7,
    "visual_style_analysis": "Анализ визуального стиля конкурента",
    "recommendations": ["рекомендация 1", "рекомендация 2", ...]
}

Важно:
- visual_style_score от 0 до 10
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Оценивай: цветовую палитру, типографику, композицию, UX/UI элементы"""

        start_time = time.time()
        logger.info("  Отправка запроса к Vision API...")
        
        try:
            response = self._get_client().chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            raw_content = response.choices[0].message.content
            content = self._message_content(raw_content)
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(raw_content)
            result = ImageAnalysis(
                description=data.get("description", ""),
                marketing_insights=data.get("marketing_insights", []),
                visual_style_score=data.get("visual_style_score", 5),
                visual_style_analysis=data.get("visual_style_analysis", ""),
                recommendations=data.get("recommendations", []),
            )
            
            logger.info(f"  Результат: оценка стиля {result.visual_style_score}/10")
            logger.info(f"  Инсайтов: {len(result.marketing_insights)}, рекомендаций: {len(result.recommendations)}")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str]
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        logger.info("📄 Анализ распарсенного контента")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Абзац: {paragraph[:50] if paragraph else 'N/A'}...")
        
        content_parts = []
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            logger.warning("  ⚠ Контент пустой, возвращаем пустой анализ")
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)
    
    async def analyze_website_screenshot(
        self,
        screenshot_base64: str,
        url: str,
        title: Optional[str] = None,
        h1: Optional[str] = None,
        first_paragraph: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Комплексный анализ сайта конкурента по скриншоту"""
        logger.info("=" * 50)
        logger.info("🌐 КОМПЛЕКСНЫЙ АНАЛИЗ САЙТА")
        logger.info(f"  URL: {url}")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Размер скриншота: {len(screenshot_base64)} символов base64")
        logger.info(f"  Модель: {self.vision_model}")
        
        # Формируем контекст из извлечённых данных
        context_parts = [f"URL сайта: {url}"]
        if title:
            context_parts.append(f"Title страницы: {title}")
        if h1:
            context_parts.append(f"Главный заголовок (H1): {h1}")
        if first_paragraph:
            context_parts.append(f"Текст на странице: {first_paragraph[:300]}")
        
        context = "\n".join(context_parts)
        logger.debug(f"  Контекст:\n{context}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу и UX/UI дизайну. Проанализируй скриншот сайта конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение/фича 1", "уникальное предложение/фича 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Комплексное резюме анализа сайта конкурента"
}

При анализе обращай внимание на:
- Дизайн и визуальный стиль (цвета, шрифты, композиция)
- UX/UI: навигация, расположение элементов, CTA кнопки
- Контент: заголовки, тексты, призывы к действию
- Уникальные торговые предложения (УТП)
- Целевая аудитория (на кого ориентирован сайт)
- Технологичность и современность дизайна

Важно:
- Каждый массив должен содержать 4-6 конкретных пунктов
- Пиши на русском языке
- Будь конкретен и практичен
- Давай actionable рекомендации"""

        start_time = time.time()
        logger.info("  Отправка скриншота в Vision API...")
        
        try:
            response = self._get_client().chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Проведи комплексный конкурентный анализ этого сайта:\n\n{context}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            raw_content = response.choices[0].message.content
            content = self._message_content(raw_content)
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(raw_content)
            
            summary = data.get("summary", "")
            if not data:
                summary = content[:2000] if content else "Не удалось разобрать ответ модели"

            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_offers=data.get("unique_offers", []),
                recommendations=data.get("recommendations", []),
                summary=summary,
            )
            
            logger.info(f"  Результат:")
            logger.info(f"    - Сильных сторон: {len(result.strengths)}")
            logger.info(f"    - Слабых сторон: {len(result.weaknesses)}")
            logger.info(f"    - УТП: {len(result.unique_offers)}")
            logger.info(f"    - Рекомендаций: {len(result.recommendations)}")
            logger.info(f"  Резюме: {result.summary[:100]}...")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise

    def _osint_from_dict(self, data: dict) -> OsintReport:
        stats_raw = data.get("review_statistics") or {}
        sentiment_raw = stats_raw.get("sentiment_percent") or {}
        platforms = [
            OsintReviewPlatform(
                platform=p.get("platform", ""),
                rating_estimate=p.get("rating_estimate"),
                notes=p.get("notes", ""),
            )
            for p in stats_raw.get("by_platform") or []
        ]
        stats = OsintReviewStatistics(
            overview=stats_raw.get("overview", ""),
            estimated_total_reviews=stats_raw.get("estimated_total_reviews", ""),
            average_rating_estimate=stats_raw.get("average_rating_estimate"),
            sentiment_percent=OsintSentimentPercent(
                positive=float(sentiment_raw.get("positive", 0) or 0),
                neutral=float(sentiment_raw.get("neutral", 0) or 0),
                negative=float(sentiment_raw.get("negative", 0) or 0),
            ),
            by_platform=platforms,
            top_positive_themes=stats_raw.get("top_positive_themes") or [],
            top_negative_themes=stats_raw.get("top_negative_themes") or [],
        )
        links = [
            OsintSource(
                title=s.get("title", ""),
                url=s.get("url", ""),
                snippet=s.get("snippet", ""),
            )
            for s in data.get("key_source_links") or []
            if s.get("url")
        ]
        return OsintReport(
            summary=data.get("summary", ""),
            company_overview=data.get("company_overview", ""),
            web_and_social_findings=data.get("web_and_social_findings") or [],
            review_statistics=stats,
            key_insights=data.get("key_insights") or [],
            risks=data.get("risks") or [],
            recommendations=data.get("recommendations") or [],
            key_source_links=links,
        )

    async def analyze_osint(
        self,
        company_name: str,
        company_details: Optional[str],
        search_context: str,
    ) -> OsintReport:
        """Сводка OSINT по результатам веб-поиска."""
        logger.info("🔍 OSINT AI-синтез для «%s»", company_name)
        details_block = company_details.strip() if company_details else "не указаны"

        system_prompt = """Ты — OSINT-аналитик. По результатам веб-поиска составь сводку о компании.
Используй ТОЛЬКО факты из блока «Результаты поиска». Не выдумывай URL.
Если данных мало — честно укажи ограничения. Оценки отзывов — приблизительные, со словом «оценочно».

Формат ответа (строго JSON):
{
    "summary": "краткая сводка 2-4 предложения",
    "company_overview": "что удалось установить о компании",
    "web_and_social_findings": ["найденное в сети и соцсетях", ...],
    "review_statistics": {
        "overview": "текстовая статистика по отзывам",
        "estimated_total_reviews": "диапазон или оценка, напр. 50-200",
        "average_rating_estimate": 4.2,
        "sentiment_percent": {"positive": 50, "neutral": 30, "negative": 20},
        "by_platform": [{"platform": "Яндекс", "rating_estimate": 4.5, "notes": "..."}],
        "top_positive_themes": ["..."],
        "top_negative_themes": ["..."]
    },
    "key_insights": ["..."],
    "risks": ["..."],
    "recommendations": ["..."],
    "key_source_links": [{"title": "кратко", "url": "https://...", "snippet": ""}]
}

В key_source_links — до 4 URL из контекста. Массивы по 2-4 пункта, без длинных цитат.
Пиши на русском."""

        user_content = (
            f"Компания: {company_name}\n"
            f"Реквизиты/уточнения: {details_block}\n\n"
            f"Результаты поиска:\n{search_context}"
        )

        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=5000,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = self._parse_json_response(content)
        if not data:
            logger.warning("OSINT: пустой JSON, используем заготовку")
            data = {
                "summary": "Сводка сформирована частично: ответ модели не удалось разобрать. "
                "Используйте блок «Источники» ниже.",
                "company_overview": "",
                "web_and_social_findings": [],
                "review_statistics": {"overview": "Нет агрегированной статистики"},
            }
        return self._osint_from_dict(data)


# Глобальный экземпляр
logger.info("Создание глобального экземпляра OpenAI сервиса...")
openai_service = OpenAIService()
