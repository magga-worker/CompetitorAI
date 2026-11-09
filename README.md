# Мониторинг конкурентов — AI-ассистент

MVP для анализа конкурентной среды: текст, изображения, парсинг сайтов, OSINT-сводка. Веб-интерфейс и опциональный desktop-клиент (PyQt6).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![AITUNNEL](https://img.shields.io/badge/LLM-AITUNNEL-purple.svg)

## Возможности

- **Анализ текста** — сильные/слабые стороны, УТП, рекомендации
- **Анализ изображений** — маркетинг и визуальный стиль (vision)
- **Парсинг сайта** — Playwright (скриншот + контент) или HTTP-fallback
- **Сводка по OSINT** — обзор по открытым источникам со ссылками
- **История** — последние 10 запросов
- **Баланс AITUNNEL** — в шапке веб-UI; в desktop — баланс или ввод своего API-ключа

## Быстрый старт

### 1. Клонирование и окружение

```bash
git clone <url-репозитория>
cd PEm08   # или имя вашей папки

python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Секреты и конфигурация

**В репозиторий не попадает файл `.env`** — он в `.gitignore`.

```bash
cp env.example.txt .env
# отредактируйте .env: ключ AITUNNEL, при необходимости API_PORT
```

Минимум для AI:

- `AITUNNEL_API_KEY` — можно оставить пустым на сервере и передавать ключ клиентом (заголовок `X-AITunnel-API-Key`), см. [desktop/README.md](desktop/README.md)
- `AITUNNEL_BASE_URL`, модели — см. [env.example.txt](env.example.txt)

Порт сервера задаётся `API_PORT` в `.env` (по умолчанию **8000**).

### 3. Chromium для парсинга

```bash
# Linux / macOS (из корня проекта, с активированным venv)
bash scripts/install_browsers.sh
```

Windows (из корня, venv активен):

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.browsers"
.venv\Scripts\playwright install chromium
```

Каталог `.browsers/` тоже не коммитится — браузер ставится после клона.

### 4. Запуск

```bash
python run.py
```

Откройте в браузере: `http://localhost:<API_PORT>` (см. вывод в консоли).  
Swagger: `http://localhost:<API_PORT>/docs`.

### 5. Windows Desktop 

Приложение собрано в один portable `.exe` со встроенным браузером (Edge WebView2) — Python, .NET и браузеры на целевой машине не нужны.

Скачать: [Releases](https://github.com/magga-worker/CompetitorAI/releases) — `CompetitorAI.exe` (в git не лежит).

При первом запуске выходит форма «Введите API ключ» / «Сохранить ключ»; ключ хранится в файле конфигурации в зашифрованном виде.
Настройки конфигурации позволяют также изменить модель и OpenAI-совместимого провайдера (баланс счета аккаунта отображается только с AITunel)


## Технологии

- **Backend:** FastAPI, uvicorn, Playwright, BeautifulSoup, httpx
- **LLM:** [AITUNNEL](https://aitunnel.ru/) (OpenAI-совместимый API)
- **Frontend:** HTML / CSS / JavaScript
- **Desktop:** PyQt6, requests, PyInstaller (сборка на Windows)

## Документация

- [docs.md](docs.md) — эндпоинты и примеры
- [desktop/README.md](desktop/README.md) — клиент и `.exe`

## Требования

- Python 3.9+
- Интернет (AITUNNEL, парсинг, OSINT-поиск)
- Для полного парсинга сайтов — установленный Chromium (см. выше)

## Лицензия

MIT (см. файл `LICENSE`, если добавлен в репозиторий).
