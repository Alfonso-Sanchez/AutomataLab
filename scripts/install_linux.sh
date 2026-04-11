#!/usr/bin/env bash

set -euo pipefail

APP_NAME="AutomataLab"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/share/automatalab}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/.local/share/applications}"
VENV_DIR="$INSTALL_DIR/.venv"
ENTRYPOINT="$INSTALL_DIR/main.py"
LAUNCHER="$BIN_DIR/automatalab"
DESKTOP_FILE="$DESKTOP_DIR/automatalab.desktop"

echo "==> Instalando $APP_NAME en Linux"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: No se encontro 'python3' en el sistema." >&2
    echo "CAUSA: la aplicacion y el instalador dependen de Python 3." >&2
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

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "ERROR: El modulo 'venv' no esta disponible en tu instalacion de Python." >&2
    echo "CAUSA: este instalador crea un entorno virtual para aislar dependencias." >&2
    echo >&2
    echo "CORRECCION: instala el paquete de venv segun tu distribucion y vuelve a ejecutar este script." >&2
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
    echo "CAUSA: AutomataLab es una aplicacion grafica basada en Tkinter." >&2
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

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"

echo "==> Copiando archivos del proyecto"
rm -rf "$INSTALL_DIR/core" "$INSTALL_DIR/gui"
cp -f "$PROJECT_ROOT/main.py" "$INSTALL_DIR/main.py"
cp -f "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/requirements.txt"
cp -rf "$PROJECT_ROOT/core" "$INSTALL_DIR/core"
cp -rf "$PROJECT_ROOT/gui" "$INSTALL_DIR/gui"

echo "==> Creando entorno virtual"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$INSTALL_DIR/requirements.txt"

echo "==> Creando lanzador"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$VENV_DIR/bin/python" "$ENTRYPOINT" "\$@"
EOF
chmod +x "$LAUNCHER"

if command -v update-desktop-database >/dev/null 2>&1; then
    UPDATE_DESKTOP_DB="yes"
else
    UPDATE_DESKTOP_DB="no"
fi

echo "==> Creando acceso directo de escritorio"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Generador y verificador de lenguajes formales
Exec=$LAUNCHER
Terminal=false
Categories=Education;Development;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

if [ "$UPDATE_DESKTOP_DB" = "yes" ]; then
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo
echo "Instalacion completada."
echo "Puedes abrir la app ejecutando: $LAUNCHER"
echo "Si el comando 'automatalab' no se reconoce, agrega $BIN_DIR a tu PATH."
