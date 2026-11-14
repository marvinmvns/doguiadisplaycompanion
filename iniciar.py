#!/usr/bin/env python3
"""Prepara uma cópia portátil estável e abre o painel, sem pip ou bibliotecas externas."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipapp


def destino():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'DoguIA Companion'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/DoguIA Companion'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'doguia-companion'


def preparar(origem, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / 'doguia-usage.pyz'
    with tempfile.TemporaryDirectory(dir=pasta) as tmp:
        shutil.copytree(origem / 'doguia_usage', Path(tmp) / 'doguia_usage', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        zipapp.create_archive(tmp, pasta / 'doguia-usage.novo', main='doguia_usage.cli:main', compressed=True)
    (pasta / 'doguia-usage.novo').replace(arquivo)
    return arquivo


def main():
    if sys.version_info < (3, 9):
        print('Use Python 3.9 ou mais novo, ou o instalador DoguIA que já inclui Python.')
        return 1
    try:
        arquivo = preparar(Path(__file__).resolve().parent, destino())
        print('DoguIA pronto em: ' + str(arquivo), flush=True)
        print('Abrindo o painel. Mantenha esta janela aberta durante a configuração.', flush=True)
        return subprocess.call([sys.executable, str(arquivo), 'painel'])
    except (OSError, KeyboardInterrupt) as exc:
        print('Não foi possível abrir o painel: ' + str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())
