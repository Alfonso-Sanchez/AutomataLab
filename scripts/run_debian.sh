#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
MIN_PYTHON_VERSION="3.12.13"
PYTHON_CMD=""

select_python() {
    if command -v python3.12 >/dev/null 2>&1; then
        if python3.12 -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
            PYTHON_CMD="python3.12"
            return 0
        fi
    fi

    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
            PYTHON_CMD="python3"
            return 0
        fi
    fi

    return 1
}

show_python_help() {
    echo "ERROR: No se encontro una version valida de Python para ejecutar AutomataLab." >&2
    echo "CAUSA: este script necesita Python $MIN_PYTHON_VERSION o superior." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install software-properties-common -y" >&2
    echo "  sudo add-apt-repository ppa:deadsnakes/ppa" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install python3.12 python3.12-venv python3.12-dev python3-tk -y" >&2
    echo >&2
    echo "Este ejecutador automatico solo vale para sistemas donde exista:" >&2
    echo "  - python3.12 >= $MIN_PYTHON_VERSION, o" >&2
    echo "  - python3 >= $MIN_PYTHON_VERSION por defecto" >&2
}

show_python_version_help() {
    local python3_version="$1"
    local python312_version="$2"
    echo "ERROR: La version de Python disponible es demasiado antigua." >&2
    if [ -n "$python312_version" ]; then
        echo "python3.12 detectado: $python312_version" >&2
    fi
    if [ -n "$python3_version" ]; then
        echo "python3 detectado: $python3_version" >&2
    fi
    echo "CAUSA: AutomataLab en Debian/Ubuntu requiere Python $MIN_PYTHON_VERSION o superior." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install software-properties-common -y" >&2
    echo "  sudo add-apt-repository ppa:deadsnakes/ppa" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install python3.12 python3.12-venv python3.12-dev python3-tk -y" >&2
    echo "  y luego verifica: python3.12 --version" >&2
    echo >&2
    echo "Este ejecutador automatico solo vale para sistemas donde exista:" >&2
    echo "  - python3.12 >= $MIN_PYTHON_VERSION, o" >&2
    echo "  - python3 >= $MIN_PYTHON_VERSION por defecto" >&2
}

show_venv_help() {
    echo "ERROR: El modulo 'venv' no esta disponible en tu instalacion de Python." >&2
    echo "CAUSA: el script necesita crear un entorno virtual en '$VENV_DIR'." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y python3.12-venv" >&2
    echo "  y luego verifica: $PYTHON_CMD -m venv --help" >&2
}

show_tk_help() {
    echo "ERROR: Python 3.12 esta instalado, pero falta Tkinter." >&2
    echo "CAUSA: AutomataLab es una aplicacion grafica basada en Tkinter." >&2
    echo >&2
    echo "CORRECCION PARA DEBIAN / UBUNTU:" >&2
    echo "  sudo apt update" >&2
    echo "  sudo apt install -y python3-tk" >&2
    echo "  y luego verifica: $PYTHON_CMD -c \"import tkinter\"" >&2
}

PYTHON3_VERSION=""
PYTHON312_VERSION=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON3_VERSION="$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
fi
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON312_VERSION="$(python3.12 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
fi

if ! select_python; then
    if [ -z "$PYTHON3_VERSION" ] && [ -z "$PYTHON312_VERSION" ]; then
        show_python_help
    else
        show_python_version_help "$PYTHON3_VERSION" "$PYTHON312_VERSION"
    fi
    exit 1
fi

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
    show_python_help
    exit 1
fi

PYTHON_VERSION="$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
    show_python_version_help "$PYTHON3_VERSION" "$PYTHON312_VERSION"
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

echo "==> Iniciando AutomataLab con $PYTHON_CMD ($PYTHON_VERSION)"
exec "$PYTHON_BIN" "$PROJECT_ROOT/main.py" "$@"
