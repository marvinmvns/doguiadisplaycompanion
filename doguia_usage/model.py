"""Tipos comuns: uma linha do painel e o contexto entregue a cada coletor."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

STALE_AFTER = 3600  # dado de log sem atualizar há 1 h aparece como antigo


@dataclass
class Row:
    label: str  # até 14 bytes na tela
    pct: int = -1  # -1: sem barra
    text: str = ""  # até 8 bytes; substitui o percentual à direita
    reset_in: int = 0  # segundos até renovar
    old: bool = False


@dataclass
class Ctx:
    home: Path = field(default_factory=Path.home)
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))
    now: float = field(default_factory=time.time)
    platform: str = field(default_factory=lambda: __import__("sys").platform)
    state_dir: Optional[Path] = None
    cfg: dict = field(default_factory=dict)
    bridge: Optional[dict] = None  # resposta da ponte ai-dev-meter, se estiver rodando


def clamp_pct(value) -> int:
    return max(0, min(100, int(round(float(value)))))


def parse_time(value) -> Optional[float]:
    """Aceita época em segundos ou milissegundos e texto ISO 8601."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value) / (1000 if value > 1e11 else 1)
    from datetime import datetime

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def money(value: float) -> str:
    return f"${value:.2f}" if value < 1000 else f"${value:.0f}"
