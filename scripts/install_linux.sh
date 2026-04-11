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
    echo "Error: python3 no esta instalado." >&2
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
