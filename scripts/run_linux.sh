#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
MIN_PYTHON_VERSION="3.12.13"

show_python_help() {
    echo "ERROR: No se encontro 'python3' en el sistema." >&2
    echo "CAUSA: este script necesita Python $MIN_PYTHON_VERSION o superior para crear o usar el entorno virtual." >&2
    echo >&2
    echo "CORRECCION:" >&2
    echo "  Debian / Ubuntu" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y luego python3-venv y python3-tk" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y luego python3-tkinter" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y luego tk" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y luego python3-tk" >&2
}

show_python_version_help() {
    local current_version="$1"
    echo "ERROR: La version de Python es demasiado antigua: $current_version" >&2
    echo "CAUSA: AutomataLab en Linux requiere Python $MIN_PYTHON_VERSION o superior." >&2
    echo >&2
    echo "CORRECCION:" >&2
    echo "  Debian / Ubuntu" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y asegúrate de que 'python3 --version' lo use" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y asegúrate de que 'python3 --version' lo use" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    actualiza el sistema o instala Python $MIN_PYTHON_VERSION+ y asegúrate de que 'python3' apunte a esa version" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    instala Python $MIN_PYTHON_VERSION+ y asegúrate de que 'python3 --version' lo use" >&2
}

show_venv_help() {
    echo "ERROR: El modulo 'venv' no esta disponible en tu instalacion de Python." >&2
    echo "CAUSA: el script necesita crear un entorno virtual en '$VENV_DIR'." >&2
    echo >&2
    echo "CORRECCION:" >&2
    echo "  Debian / Ubuntu" >&2
    echo "    sudo apt update && sudo apt install -y python3-venv" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    sudo dnf install -y python3" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    sudo pacman -S python" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    sudo zypper install python3" >&2
}

show_tk_help() {
    echo "ERROR: Python 3 esta instalado, pero falta Tkinter." >&2
    echo "CAUSA: AutomataLab es una aplicacion grafica basada en Tkinter." >&2
    echo >&2
    echo "CORRECCION:" >&2
    echo "  Debian / Ubuntu" >&2
    echo "    sudo apt update && sudo apt install -y python3-tk" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    sudo dnf install -y python3-tkinter" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    sudo pacman -S tk" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    sudo zypper install python3-tk" >&2
}

if ! command -v python3 >/dev/null 2>&1; then
    show_python_help
    exit 1
fi

PYTHON_VERSION="$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
    show_python_version_help "$PYTHON_VERSION"
    exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    show_venv_help
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    show_tk_help
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creando entorno virtual en $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "==> Actualizando pip e instalando dependencias en el entorno"
"$PYTHON_BIN" -m pip install --upgrade pip
"$PIP_BIN" install -r "$PROJECT_ROOT/requirements.txt"

echo "==> Iniciando AutomataLab"
exec "$PYTHON_BIN" "$PROJECT_ROOT/main.py" "$@"
