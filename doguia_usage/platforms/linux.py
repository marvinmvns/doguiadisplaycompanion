"""systemd --user."""
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import List

UNIT = "doguia-usage.service"


def unit_path(home: Path) -> Path:
    return home / ".config/systemd/user" / UNIT


def unit_text(cmd: List[str]) -> str:
    return ("[Unit]\nDescription=Consumo de IA para o DoguIA Display\nAfter=network-online.target\n\n"
            f"[Service]\nExecStart={shlex.join(cmd)}\nRestart=always\nRestartSec=30\n\n[Install]\nWantedBy=default.target\n")


def install(home: Path, cmd: List[str]) -> str:
    path = unit_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit_text(cmd), encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", UNIT], check=True)
    return str(path)


def uninstall(home: Path) -> None:
    subprocess.run(["systemctl", "--user", "disable", "--now", UNIT], check=False)
    unit_path(home).unlink(missing_ok=True)
