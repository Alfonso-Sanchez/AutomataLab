#!/usr/bin/env bash

set -euo pipefail

APP_NAME="AutomataLab"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
VENV_DIR="$PROJECT_ROOT/.venv-build"

echo "==> Preparando entorno de build para Linux"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: No se encontro 'python3' en el sistema." >&2
    echo "CAUSA: PyInstaller y la aplicacion dependen de Python 3 para generar el ejecutable." >&2
    echo >&2
    echo "CORRECCION: instala Python 3 segun tu distribucion y vuelve a ejecutar este script." >&2
    echo >&2
    echo "  Debian / Ubuntu" >&2
    echo "    sudo apt update && sudo apt install -y python3 python3-venv python3-tk" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    sudo dnf install -y python3 python3-tkinter" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    sudo pacman -S python tk" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    sudo zypper install python3 python3-tk" >&2
    exit 1
fi

if ! command -v objdump >/dev/null 2>&1; then
    echo "ERROR: No se encontro 'objdump' en el sistema." >&2
    echo "CAUSA: PyInstaller necesita 'objdump' para analizar binarios durante el build en Linux." >&2
    echo >&2
    echo "CORRECCION: instala el paquete 'binutils' segun tu distribucion y vuelve a ejecutar este script." >&2
    echo >&2
    echo "  Debian / Ubuntu" >&2
    echo "    sudo apt update && sudo apt install -y binutils" >&2
    echo >&2
    echo "  Fedora / RHEL / CentOS" >&2
    echo "    sudo dnf install -y binutils" >&2
    echo >&2
    echo "  Arch / Manjaro" >&2
    echo "    sudo pacman -S binutils" >&2
    echo >&2
    echo "  openSUSE" >&2
    echo "    sudo zypper install binutils" >&2
    exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "ERROR: El modulo 'venv' no esta disponible en tu instalacion de Python." >&2
    echo "CAUSA: el script de build crea un entorno virtual aislado para instalar PyInstaller." >&2
    echo >&2
    echo "CORRECCION: instala el soporte de venv segun tu distribucion y vuelve a ejecutar este script." >&2
    echo >&2
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
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: Python 3 esta instalado, pero falta Tkinter." >&2
    echo "CAUSA: AutomataLab es una aplicacion grafica basada en Tkinter y PyInstaller debe poder importarla durante el build." >&2
    echo >&2
    echo "CORRECCION: instala el paquete de Tkinter segun tu distribucion y vuelve a ejecutar este script." >&2
    echo >&2
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
