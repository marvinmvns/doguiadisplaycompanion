"""Confere o iniciador universal com o instalador nativo deste runner, sem instalá-lo."""
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from universal import ROOT, montar


def conferir():
    sistema = {'win32':'windows','darwin':'macos'}.get(sys.platform,'linux')
    arq = {'amd64':'x64','x86_64':'x64','aarch64':'arm64'}.get(platform.machine().lower(),platform.machine().lower())
    with tempfile.TemporaryDirectory(prefix='doguia universal ') as tmp:
        pasta = Path(tmp)
        arquivo = montar(ROOT/'dist', pasta/'teste.zip', [f'{sistema}-{arq}'])
        with ZipFile(arquivo) as z:
            z.extractall(pasta)
        if sistema == 'windows':
            cmd = ['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(pasta/'DoguIA/Instalar-DoguIA.ps1'),'-Verificar']
        else:
            cmd = ['sh',str(pasta/'DoguIA/Instalar-DoguIA.command'),'--verificar']
        subprocess.run(cmd,check=True)


if __name__ == '__main__':
    conferir()
