"""Chave Run do usuário: dispensa administrador, ao contrário do Agendador de Tarefas ao fazer logon."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
NAME = "DoguIAUsage"


def run_value(cmd: List[str]) -> str:
    cmd = list(cmd)
    exe = Path(cmd[0])
    if exe.name.lower() == "python.exe" and (exe.parent / "pythonw.exe").exists():
        cmd[0] = str(exe.parent / "pythonw.exe")  # sem janela de console
    return subprocess.list2cmdline(cmd)


def install(home: Path, cmd: List[str]) -> str:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, run_value(cmd))
    subprocess.Popen(cmd, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    return "HKCU\\" + RUN_KEY + "\\" + NAME


def uninstall(home: Path) -> None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, NAME)
    except FileNotFoundError:
        pass
