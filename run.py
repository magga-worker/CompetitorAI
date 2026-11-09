"""
Скрипт запуска приложения Мониторинг конкурентов
"""
import uvicorn
import logging
from backend.config import settings, logger

# Настраиваем уровень логирования
logging.getLogger("competitor_monitor").setLevel(logging.INFO)

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("🚀 МОНИТОРИНГ КОНКУРЕНТОВ - AI Ассистент")
    print("=" * 60)
    print()
    print(f"📍 Веб-интерфейс:  http://localhost:{settings.api_port}")
    print(f"📚 Документация:   http://localhost:{settings.api_port}/docs")
    print(f"📖 ReDoc:          http://localhost:{settings.api_port}/redoc")
    print()
    print(f"🤖 Модель текста:  {settings.aitunnel_model}")
    print(f"👁️ Модель vision:  {settings.aitunnel_vision_model}")
    print(f"🔑 AITUNNEL:       {'✓ Настроен' if settings.aitunnel_api_key else '✗ НЕ ЗАДАН!'}")
    print()
    print("-" * 60)
    print("Логи запросов будут отображаться ниже...")
    print("-" * 60)
    print()
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
