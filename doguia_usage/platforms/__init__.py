"""Início automático por usuário, sem administrador. Cada sistema fica no próprio módulo."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from . import linux, macos, windows


def module(platform: str = sys.platform):
    return windows if platform == "win32" else macos if platform == "darwin" else linux


BACKGROUND_EXE = "doguia-usage-bg.exe"  # cópia sem janela de console, gerada só para Windows


def program() -> List[str]:
    """Como chamar este programa em primeiro plano: binário empacotado, arquivo .pyz ou módulo instalado."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    entry = Path(sys.argv[0]).resolve()
    if entry.suffix == ".pyz":
        return [sys.executable, str(entry)]
    return [sys.executable, "-m", "doguia_usage"]


def command() -> List[str]:
    """Comando do início automático. No Windows prefere o executável sem console, senão fica uma janela aberta."""
    if getattr(sys, "frozen", False) and sys.platform == "win32":
        quiet = Path(sys.executable).with_name(BACKGROUND_EXE)
        if quiet.exists():
            return [str(quiet), "run"]
    return program() + ["run"]


def shell_line(parts: List[str], platform: str = sys.platform) -> str:
    """Linha para o shell do Claude Code (bash, inclusive o Git Bash do Windows, que aceita C:/...)."""
    if platform == "win32":
        return " ".join('"%s"' % p.replace("\\", "/") for p in parts)
    import shlex

    return shlex.join(parts)
