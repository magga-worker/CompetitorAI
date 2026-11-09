"""
Pydantic схемы для API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# === Запросы ===

class TextAnalysisRequest(BaseModel):
    """Запрос на анализ текста"""
    text: str = Field(..., min_length=10, description="Текст для анализа")


class ParseDemoRequest(BaseModel):
    """Запрос на парсинг URL"""
    url: str = Field(..., description="URL для парсинга")


# === Ответы ===

class CompetitorAnalysis(BaseModel):
    """Структурированный анализ конкурента"""
    strengths: List[str] = Field(default_factory=list, description="Сильные стороны")
    weaknesses: List[str] = Field(default_factory=list, description="Слабые стороны")
    unique_offers: List[str] = Field(default_factory=list, description="Уникальные предложения")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    summary: str = Field("", description="Общее резюме")


class ImageAnalysis(BaseModel):
    """Анализ изображения"""
    description: str = Field("", description="Описание изображения")
    marketing_insights: List[str] = Field(default_factory=list, description="Маркетинговые инсайты")
    visual_style_score: int = Field(0, ge=0, le=10, description="Оценка визуального стиля (0-10)")
    visual_style_analysis: str = Field("", description="Анализ визуального стиля")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")


class ParsedContent(BaseModel):
    """Результат парсинга страницы"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    """Ответ на анализ текста"""
    success: bool
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Ответ на анализ изображения"""
    success: bool
    analysis: Optional[ImageAnalysis] = None
    error: Optional[str] = None


class ParseDemoResponse(BaseModel):
    """Ответ на парсинг"""
    success: bool
    data: Optional[ParsedContent] = None
    error: Optional[str] = None


# === История ===

class HistoryItem(BaseModel):
    """Элемент истории"""
    id: str
    timestamp: datetime
    request_type: str  # "text", "image", "parse"
    request_summary: str
    response_summary: str


class HistoryResponse(BaseModel):
    """Ответ со списком истории"""
    items: List[HistoryItem]
    total: int


class AITunnelBalanceResponse(BaseModel):
    """Баланс аккаунта AITUNNEL (рубли)"""
    balance: float = Field(..., description="Баланс аккаунта, ₽")
    budget: Optional[float] = Field(None, description="Остаток бюджета ключа, ₽")


# === OSINT ===

class OsintRequest(BaseModel):
    """Запрос OSINT-сводки по компании"""
    company_name: str = Field(..., min_length=2, description="Название компании")
    company_details: Optional[str] = Field(
        None,
        description="ИНН, юр. адрес, бренд, город и другие уточнения",
    )


class OsintSource(BaseModel):
    """Ссылка на источник из поиска или отчёта"""
    title: str = ""
    url: str
    snippet: str = ""


class OsintReviewPlatform(BaseModel):
    platform: str = ""
    rating_estimate: Optional[float] = Field(None, ge=0, le=5)
    notes: str = ""


class OsintSentimentPercent(BaseModel):
    positive: float = Field(0, ge=0, le=100)
    neutral: float = Field(0, ge=0, le=100)
    negative: float = Field(0, ge=0, le=100)


class OsintReviewStatistics(BaseModel):
    overview: str = ""
    estimated_total_reviews: str = ""
    average_rating_estimate: Optional[float] = Field(None, ge=0, le=5)
    sentiment_percent: OsintSentimentPercent = Field(default_factory=OsintSentimentPercent)
    by_platform: List[OsintReviewPlatform] = Field(default_factory=list)
    top_positive_themes: List[str] = Field(default_factory=list)
    top_negative_themes: List[str] = Field(default_factory=list)


class OsintReport(BaseModel):
    summary: str = ""
    company_overview: str = ""
    web_and_social_findings: List[str] = Field(default_factory=list)
    review_statistics: OsintReviewStatistics = Field(default_factory=OsintReviewStatistics)
    key_insights: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    key_source_links: List[OsintSource] = Field(default_factory=list)


class OsintSummaryResponse(BaseModel):
    success: bool
    company_name: str
    report: Optional[OsintReport] = None
    sources: List[OsintSource] = Field(default_factory=list)
    error: Optional[str] = None

