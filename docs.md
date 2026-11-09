# 📚 Документация API - Мониторинг конкурентов

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Описание API](#описание-api)
3. [Примеры запросов](#примеры-запросов)
4. [OSINT-сводка](#osint-сводка)
5. [Мультимодальные функции](#мультимодальные-функции)
6. [Модели данных](#модели-данных)

---

## Структура проекта

```
CompetitorAI/
│
├── backend/                     # FastAPI
│   ├── main.py
│   ├── config.py
│   ├── aitunnel_context.py      # ключ из заголовка X-AITunnel-API-Key
│   ├── models/schemas.py
│   └── services/
│       ├── openai_service.py    # AITUNNEL
│       ├── aitunnel_service.py  # баланс
│       ├── parser_service.py    # Playwright / HTTP
│       ├── web_search_service.py
│       ├── osint_service.py     # OSINT-сводка
│       └── history_service.py
│
├── frontend/                    # веб-UI (вкладка «Сводка по OSINT»)
├── desktop/README.md            # Windows .exe (WebView2), бинарник — в Releases
├── scripts/install_browsers.sh  # Chromium для backend (Linux/macOS)
├── run.py
├── requirements.txt
├── env.example.txt
├── README.md
└── docs.md
```

`history.json` создаётся локально и в git не попадает. Windows `.exe` — в [Releases](https://github.com/magga-worker/CompetitorAI/releases).

---

## Описание API

### Базовый URL

```
http://localhost:<API_PORT>
```

Порт задаётся в `.env` (`API_PORT`, по умолчанию `8000`). Скопируйте [env.example.txt](env.example.txt) в `.env` — **не коммитьте `.env`**.

### Аутентификация AITUNNEL

- Ключ в `.env` сервера: `AITUNNEL_API_KEY`
- Либо заголовок на каждый запрос: `X-AITunnel-API-Key: <ваш_ключ>` (Windows `.exe` хранит ключ локально)

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (веб-интерфейс) |
| POST | `/analyze_text` | Анализ текста конкурента |
| POST | `/analyze_image` | Анализ изображения конкурента |
| POST | `/parse_demo` | Парсинг и анализ сайта по URL |
| POST | `/osint_summary` | OSINT-сводка по компании / теме |
| GET | `/history` | Получение истории запросов |
| DELETE | `/history` | Очистка истории запросов |
| GET | `/api/aitunnel/balance` | Баланс AITUNNEL |
| GET | `/health` | Проверка работоспособности |
| GET | `/docs` | Swagger UI документация |
| GET | `/redoc` | ReDoc документация |

---

## Примеры запросов

### 1. Анализ текста (`POST /analyze_text`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Наша компания предлагает уникальные решения для бизнеса. Мы работаем на рынке 10 лет и обслуживаем более 1000 клиентов. Наши преимущества: быстрая доставка, гарантия качества, индивидуальный подход к каждому клиенту."
  }'
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "strengths": [
      "Долгий опыт работы на рынке (10 лет)",
      "Большая клиентская база (1000+ клиентов)",
      "Комплексный подход к обслуживанию"
    ],
    "weaknesses": [
      "Отсутствие конкретных цен",
      "Нет упоминания о технологиях",
      "Общие формулировки без специфики"
    ],
    "unique_offers": [
      "Индивидуальный подход к каждому клиенту",
      "Гарантия качества"
    ],
    "recommendations": [
      "Добавить конкретные цифры и кейсы",
      "Указать уникальные технологические преимущества",
      "Включить отзывы клиентов"
    ],
    "summary": "Компания позиционирует себя как надёжного партнёра с опытом, но маркетинговые материалы требуют конкретизации для повышения конверсии."
  },
  "error": null
}
```

### 2. Анализ изображения (`POST /analyze_image`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_image" \
  -F "file=@banner.jpg"
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "description": "Рекламный баннер с изображением продукта на синем градиентном фоне. Крупный заголовок белым шрифтом, кнопка CTA оранжевого цвета.",
    "marketing_insights": [
      "Чёткая визуальная иерархия привлекает внимание",
      "Контрастная цветовая схема выделяет CTA",
      "Минималистичный дизайн не перегружает восприятие"
    ],
    "visual_style_score": 7,
    "visual_style_analysis": "Современный корпоративный стиль с хорошим балансом элементов. Типографика читабельна, но можно улучшить отступы.",
    "recommendations": [
      "Добавить социальное доказательство (отзывы, рейтинги)",
      "Увеличить размер CTA кнопки",
      "Рассмотреть A/B тестирование цветов"
    ]
  },
  "error": null
}
```

### 3. Парсинг сайта (`POST /parse_demo`)

Парсинг выполняется через **Playwright**: Chromium скачивается в каталог `.browsers` проекта (`bash scripts/install_browsers.sh`). Если браузер не установлен, используется HTTP-fallback без скриншота (текстовый AI-анализ).

**Запрос:**
```bash
curl -X POST "http://localhost:8000/parse_demo" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "example.com"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "h1": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples in documents.",
    "analysis": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "unique_offers": ["..."],
      "recommendations": ["..."],
      "summary": "..."
    }
  },
  "error": null
}
```

### 4. OSINT-сводка (`POST /osint_summary`)

Ищет открытые упоминания компании (DuckDuckGo HTML: отзывы, рейтинг, соцсети, репутация), затем модель собирает структурированный отчёт. Источники возвращаются списком со ссылками.

**Запрос:**
```bash
curl -X POST "http://localhost:8000/osint_summary" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Пример ООО",
    "company_details": "ИНН 7700000000, Москва"
  }'
```

Поле `company_details` необязательно: ИНН, город, бренд, юр. адрес.

**Ответ (сокращённо):**
```json
{
  "success": true,
  "company_name": "Пример ООО",
  "report": {
    "summary": "Краткое резюме по открытым источникам",
    "company_overview": "Чем занимается компания по найденным страницам",
    "web_and_social_findings": ["Сайт и страницы в соцсетях..."],
    "review_statistics": {
      "overview": "Оценки и тон отзывов по площадкам",
      "estimated_total_reviews": "сотни",
      "average_rating_estimate": 4.2,
      "sentiment_percent": { "positive": 60, "neutral": 25, "negative": 15 },
      "by_platform": [
        { "platform": "2GIS", "rating_estimate": 4.3, "notes": "..." }
      ],
      "top_positive_themes": ["сервис"],
      "top_negative_themes": ["сроки"]
    },
    "key_insights": ["..."],
    "risks": ["..."],
    "recommendations": ["..."],
    "key_source_links": [
      { "title": "Отзывы", "url": "https://example.com", "snippet": "..." }
    ]
  },
  "sources": [
    { "title": "...", "url": "https://...", "snippet": "..." }
  ],
  "error": null
}
```

В истории тип запроса: `osint`.

### 5. Получение истории (`GET /history`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00",
      "request_type": "text",
      "request_summary": "Наша компания предлагает уникальные решения...",
      "response_summary": "Компания позиционирует себя как надёжного партнёра..."
    }
  ],
  "total": 1
}
```

### 6. Очистка истории (`DELETE /history`)

**Запрос:**
```bash
curl -X DELETE "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "success": true,
  "message": "История очищена"
}
```

### 7. Проверка здоровья (`GET /health`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "Competitor Monitor",
  "version": "1.0.0"
}
```

---

## OSINT-сводка

Вкладка веб-интерфейса **«Сводка по OSINT»** и эндпоинт `POST /osint_summary`.

**Как устроено**

1. По названию компании (и опциональным реквизитам) формируются поисковые запросы: отзывы, рейтинг, соцсети, репутация, карты.
2. `web_search_service` собирает сниппеты (до 12 уникальных URL).
3. `openai_service.analyze_osint` строит отчёт: обзор, находки в вебе/соцсетях, оценка отзывов (тональность, площадки), риски и рекомендации.
4. В ответе — `report` и плоский список `sources` со ссылками.

Это **не** скрытый доступ к закрытым данным: только то, что находится публичным поиском, плюс интерпретация LLM. Результаты зависят от выдачи поиска и могут быть неполными.

**Минимум:** `company_name` от 2 символов.

---

## Мультимодальные функции

### Поддержка текста

Приложение анализирует любой текстовый контент конкурентов:
- Описания продуктов
- Тексты с лендингов
- Рекламные объявления
- Посты в социальных сетях
- Email рассылки

**Минимальная длина текста:** 10 символов

### Поддержка изображений

Поддерживаемые форматы:
- JPEG/JPG
- PNG
- GIF
- WebP

**Что можно анализировать:**
- Рекламные баннеры
- Скриншоты сайтов
- Фотографии упаковки
- Креативы для социальных сетей
- Логотипы и фирменный стиль

**Максимальный размер:** 10MB (рекомендуется до 4MB для быстрой обработки)

### Парсинг веб-страниц

Автоматически извлекаемые элементы:
- `<title>` — заголовок страницы
- `<h1>` — главный заголовок
- Первый значимый `<p>` — первый абзац (минимум 50 символов)

**Особенности:**
- Автоматическое добавление протокола `https://`
- Playwright Chromium в `.browsers` (скрипт `scripts/install_browsers.sh`, Linux/macOS)
- Без Chromium — HTTP-fallback без скриншота
- Таймаут: `PARSER_TIMEOUT` (по умолчанию 20 с)
- Windows `.exe` парсит через встроенный WebView2, не через `.browsers`

---

## Модели данных

### TextAnalysisRequest
```typescript
{
  text: string  // Минимум 10 символов
}
```

### ParseDemoRequest
```typescript
{
  url: string  // URL сайта для парсинга
}
```

### OsintRequest
```typescript
{
  company_name: string     // минимум 2 символа
  company_details?: string // ИНН, город, бренд и т.п.
}
```

### OsintReport
```typescript
{
  summary: string
  company_overview: string
  web_and_social_findings: string[]
  review_statistics: {
    overview: string
    estimated_total_reviews: string
    average_rating_estimate?: number  // 0–5
    sentiment_percent: { positive: number, neutral: number, negative: number }
    by_platform: { platform: string, rating_estimate?: number, notes: string }[]
    top_positive_themes: string[]
    top_negative_themes: string[]
  }
  key_insights: string[]
  risks: string[]
  recommendations: string[]
  key_source_links: { title: string, url: string, snippet: string }[]
}
```

### CompetitorAnalysis
```typescript
{
  strengths: string[]      // Сильные стороны
  weaknesses: string[]     // Слабые стороны
  unique_offers: string[]  // Уникальные предложения
  recommendations: string[] // Рекомендации
  summary: string          // Общее резюме
}
```

### ImageAnalysis
```typescript
{
  description: string           // Описание изображения
  marketing_insights: string[]  // Маркетинговые инсайты
  visual_style_score: number    // Оценка 0-10
  visual_style_analysis: string // Анализ стиля
  recommendations: string[]     // Рекомендации
}
```

### HistoryItem
```typescript
{
  id: string              // UUID записи
  timestamp: datetime     // Время запроса
  request_type: string    // "text" | "image" | "parse" | "osint"
  request_summary: string // Краткое описание запроса
  response_summary: string // Краткое описание ответа
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Некорректный запрос (неверный формат, короткий текст) |
| 422 | Ошибка валидации данных |
| 500 | Внутренняя ошибка сервера |

---

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `AITUNNEL_API_KEY` | API ключ [AITUNNEL](https://aitunnel.ru/) | - |
| `AITUNNEL_BASE_URL` | Базовый URL API | `https://api.aitunnel.ru/v1` |
| `AITUNNEL_MODEL` | Модель для текста | `claude-haiku-5.5` |
| `AITUNNEL_VISION_MODEL` | Модель для изображений | `claude-haiku-5.5` |
| `API_HOST` | Хост сервера | `0.0.0.0` |
| `API_PORT` | Порт сервера | `8000` |
| `PARSER_TIMEOUT` | Таймаут парсинга (сек) | `20` |
| `PLAYWRIGHT_BROWSERS_PATH` | Каталог Chromium для Playwright | `<корень проекта>/.browsers` |

### AITUNNEL

Проект использует [AITUNNEL](https://aitunnel.ru/) — OpenAI-совместимый API (по умолчанию Claude Haiku 5.5).
- Без VPN, оплата в рублях
- [Документация](https://aitunnel.ru/docs/api-reference)

### Настройки истории

- Максимум записей: **10**
- Файл хранения: `history.json`
- Формат: JSON с UTF-8 кодировкой

---

## Безопасность

⚠️ **Важно:**
- Не храните API ключи в коде
- Используйте `.env` файл для секретов
- Добавьте `.env` в `.gitignore`
- В продакшене используйте HTTPS
- Настройте CORS для конкретных доменов

