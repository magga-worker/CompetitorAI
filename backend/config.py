"""
Конфигурация приложения
"""
import os
import logging
import sys
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_BROWSERS_PATH = PROJECT_ROOT / ".browsers"


# === Настройка логирования ===
def setup_logging():
    """Настройка логирования для всего приложения"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    return logging.getLogger("competitor_monitor")

logger = setup_logging()


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # AITUNNEL (OpenAI-совместимый API)
    aitunnel_api_key: str = os.getenv("AITUNNEL_API_KEY", "")
    aitunnel_base_url: str = os.getenv("AITUNNEL_BASE_URL", "https://api.aitunnel.ru/v1")
    aitunnel_model: str = os.getenv("AITUNNEL_MODEL", "claude-haiku-5.5")
    aitunnel_vision_model: str = os.getenv(
        "AITUNNEL_VISION_MODEL",
        os.getenv("AITUNNEL_IMAGE_MODEL", "claude-haiku-5.5"),
    )
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    history_file: str = "history.json"
    max_history_items: int = 10
    
    # Парсер: Playwright Chromium в .browsers, иначе HTTP-fallback
    parser_timeout: int = int(os.getenv("PARSER_TIMEOUT", "20"))
    parser_user_agent: str = os.getenv(
        "PARSER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    playwright_browsers_path: str = os.getenv(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(_DEFAULT_BROWSERS_PATH),
    )
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", settings.playwright_browsers_path)
