#!/bin/sh
# Funciona no macOS e no Linux, a partir da pasta extraída do projeto.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$here/iniciar.py"
fi
printf '%s\n' 'Python não encontrado.' 'Use o instalador DoguIA que inclui Python, ou instale Python 3.9+ por https://www.python.org/downloads/.' 'Ajuda: https://www.doguia.com.br/ajuda/display/'
exit 1
