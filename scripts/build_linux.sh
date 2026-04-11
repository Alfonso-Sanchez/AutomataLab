#!/usr/bin/env bash

set -euo pipefail

APP_NAME="AutomataLab"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
VENV_DIR="$PROJECT_ROOT/.venv-build"

echo "==> Preparando entorno de build para Linux"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 no esta instalado." >&2
    exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$PROJECT_ROOT/requirements.txt" pyinstaller

echo "==> Generando ejecutable Linux con PyInstaller"

rm -rf "$BUILD_DIR/$APP_NAME" "$DIST_DIR/$APP_NAME"

pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "$APP_NAME" \
    "$PROJECT_ROOT/main.py"

echo
echo "Build completado."
echo "Binario disponible en: $DIST_DIR/$APP_NAME/$APP_NAME"
