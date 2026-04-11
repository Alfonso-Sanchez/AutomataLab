#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_CMD="python3.12"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
MIN_PYTHON_VERSION="3.12.13"

show_python_help() {
    echo "ERROR: No se encontro '$PYTHON_CMD' en el sistema." >&2
    echo "CAUSA: este script necesita Python $MIN_PYTHON_VERSION o superior para crear o usar el entorno virtual." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install software-properties-common -y" >&2
    echo "  sudo add-apt-repository ppa:deadsnakes/ppa" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install python3.12 python3.12-venv python3.12-dev python3-tk -y" >&2
}

show_python_version_help() {
    local current_version="$1"
    echo "ERROR: La version de Python es demasiado antigua: $current_version" >&2
    echo "CAUSA: AutomataLab en Debian/Ubuntu requiere Python $MIN_PYTHON_VERSION o superior." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install software-properties-common -y" >&2
    echo "  sudo add-apt-repository ppa:deadsnakes/ppa" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install python3.12 python3.12-venv python3.12-dev python3-tk -y" >&2
    echo "  y luego verifica: $PYTHON_CMD --version" >&2
}

show_venv_help() {
    echo "ERROR: El modulo 'venv' no esta disponible en tu instalacion de Python." >&2
    echo "CAUSA: el script necesita crear un entorno virtual en '$VENV_DIR'." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y python3.12-venv" >&2
}

show_tk_help() {
    echo "ERROR: Python 3.12 esta instalado, pero falta Tkinter." >&2
    echo "CAUSA: AutomataLab es una aplicacion grafica basada en Tkinter." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y python3-tk" >&2
}

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
    show_python_help
    exit 1
fi

PYTHON_VERSION="$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
    show_python_version_help "$PYTHON_VERSION"
    exit 1
fi

if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1; then
    show_venv_help
    exit 1
fi

if ! $PYTHON_CMD -c "import tkinter" >/dev/null 2>&1; then
    show_tk_help
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creando entorno virtual en $VENV_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

echo "==> Actualizando pip e instalando dependencias en el entorno"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PIP_BIN" install -r "$PROJECT_ROOT/requirements.txt"

echo "==> Iniciando AutomataLab"
exec "$PYTHON_BIN" "$PROJECT_ROOT/main.py" "$@"
