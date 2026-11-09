# Мониторинг конкурентов — AI-ассистент

MVP для анализа конкурентной среды: текст, изображения, парсинг сайтов, OSINT-сводка. Веб-интерфейс (FastAPI) и отдельное Windows-приложение (`CompetitorAI.exe` со встроенным Edge WebView2).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![AITUNNEL](https://img.shields.io/badge/LLM-AITUNNEL-purple.svg)

## Возможности

- **Анализ текста** — сильные/слабые стороны, УТП, рекомендации
- **Анализ изображений** — маркетинг и визуальный стиль (vision)
- **Парсинг сайта** — Playwright (скриншот + контент) или HTTP-fallback
- **Сводка по OSINT** — поиск по открытым источникам, отзывы, соцсети, ссылки
- **История** — последние 10 запросов
- **Баланс AITUNNEL** — в шапке веб-UI; в Windows `.exe` — ввод своего API-ключа

## Быстрый старт

### 1. Клонирование и окружение

```bash
git clone https://github.com/magga-worker/CompetitorAI.git
cd CompetitorAI

python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows (только если запускаете backend из исходников)
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Секреты и конфигурация

**Файл `.env` в git не попадает** (см. `.gitignore`).

```bash
cp env.example.txt .env
# отредактируйте .env: ключ AITUNNEL, при необходимости API_PORT
```

Минимум для AI:

- `AITUNNEL_API_KEY` — в `.env` на сервере; Windows `.exe` может работать со своим ключом без ключа в `.env`
- `AITUNNEL_BASE_URL`, модели — см. [env.example.txt](env.example.txt)

Порт сервера задаётся `API_PORT` в `.env` (по умолчанию **8000**).

### 3. Chromium для парсинга (Linux / macOS)

Нужен только для **веб-backend** (`python run.py`) и полного парсинга сайтов через Playwright. Каталог `.browsers/` не коммитится.

```bash
# из корня проекта, с активированным venv
bash scripts/install_browsers.sh
```

При сбое headless на Linux: `sudo .venv/bin/playwright install-deps chromium`.

Windows-сборка **не использует** этот Chromium: внутри `.exe` уже встроен Edge WebView2.

### 4. Запуск веб-версии

```bash
python run.py
```

Откройте в браузере: `http://localhost:<API_PORT>` (см. вывод в консоли).  
Swagger: `http://localhost:<API_PORT>/docs`.

### 5. Windows Desktop

Приложение собрано в один portable `.exe` со встроенным браузером (Edge WebView2) — Python, .NET и отдельный Chromium на целевой машине не нужны.

Скачать: [Releases](https://github.com/magga-worker/CompetitorAI/releases) — `CompetitorAI.exe` (в git не лежит).

При первом запуске — форма «Введите API ключ» / «Сохранить ключ»; ключ хранится локально в зашифрованном виде.  
В настройках можно сменить модель и OpenAI-совместимого провайдера. Баланс счёта отображается только для AITUNNEL.

Подробнее: [desktop/README.md](desktop/README.md).

## Технологии

- **Backend:** FastAPI, uvicorn, Playwright, BeautifulSoup, httpx
- **LLM:** [AITUNNEL](https://aitunnel.ru/) (OpenAI-совместимый API)
- **Frontend:** HTML / CSS / JavaScript
- **Windows-клиент:** portable `.exe`, Edge WebView2

## Документация

- [docs.md](docs.md) — эндпоинты и примеры (включая OSINT)
- [desktop/README.md](desktop/README.md) — Windows `.exe`

## Требования

- Python 3.9+ — для запуска backend из исходников
- Интернет (AITUNNEL, парсинг, OSINT-поиск)
- Chromium через Playwright — только для полного парсинга в веб-версии (раздел 3)
- Windows 10+ и WebView2 — для готового `.exe` из Releases

## Лицензия

MIT (файл [LICENSE](LICENSE)).
