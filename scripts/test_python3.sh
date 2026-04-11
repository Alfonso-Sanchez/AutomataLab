#!/usr/bin/env bash

set -euo pipefail

MIN_VERSION="3.12.13"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3: NO ENCONTRADO"
    exit 1
fi

PYTHON3_VERSION="$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")"

echo "python3 encontrado: $PYTHON3_VERSION"

if python3 -c "import sys; sys.exit(0 if sys.version_info[:3] >= (3, 12, 13) else 1)"; then
    echo "Resultado: VALIDO"
    echo "python3 sirve para AutomataLab."
    exit 0
fi

echo "Resultado: NO VALIDO"
echo "python3 no sirve para AutomataLab."
echo "Se requiere al menos Python $MIN_VERSION."
exit 1
