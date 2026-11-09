#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Сначала создайте venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

export PLAYWRIGHT_BROWSERS_PATH="$ROOT/.browsers"
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
echo "Установка пакета playwright..."
.venv/bin/pip install -q playwright

echo "Скачивание Chromium (~100+ МБ)..."
.venv/bin/playwright install chromium

echo ""
echo "Готово. При ошибках headless на Linux выполните (может потребовать sudo):"
echo "  sudo .venv/bin/playwright install-deps chromium"
