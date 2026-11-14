"""LaunchAgent do usuário."""
from __future__ import annotations

import os
import plistlib
import subprocess
from pathlib import Path
from typing import List

LABEL = "br.com.doguia.usage"


def plist_path(home: Path) -> Path:
    return home / "Library/LaunchAgents" / f"{LABEL}.plist"


def plist_bytes(cmd: List[str]) -> bytes:
    return plistlib.dumps({"Label": LABEL, "ProgramArguments": cmd, "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 30})


def install(home: Path, cmd: List[str]) -> str:
    path = plist_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(plist_bytes(cmd))
    target = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", target, str(path)], check=False, capture_output=True)
    subprocess.run(["launchctl", "bootstrap", target, str(path)], check=True)
    return str(path)


def uninstall(home: Path) -> None:
    path = plist_path(home)
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)], check=False, capture_output=True)
    path.unlink(missing_ok=True)
