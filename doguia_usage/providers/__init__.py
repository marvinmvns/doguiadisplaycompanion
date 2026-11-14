"""Cada ferramenta fica na própria pasta e expõe `collect(ctx)`: nada aqui lê login, token ou conteúdo de conversa."""
from __future__ import annotations

import json
import urllib.request
from typing import Dict, List, Optional

from ..model import Ctx, Row
from . import agy, claude, codex, deepseek, opencode

ALL = {"claude": claude, "codex": codex, "agy": agy, "opencode": opencode, "deepseek": deepseek}


def read_bridge(url: str) -> Optional[dict]:
    """A ponte ai-dev-meter é opcional: quando roda no mesmo PC, entrega números que já mede."""
    if not url:
        return None
    try:
        with urllib.request.urlopen(url + "/api/v1/providers", timeout=2) as r:
            data = json.load(r)
            return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def collect_all(ctx: Ctx) -> Dict[str, List[Row]]:
    out: Dict[str, List[Row]] = {}
    for name, mod in ALL.items():
        if name in (ctx.cfg.get("disabled") or []):
            continue
        try:
            out[name] = mod.collect(ctx)
        except Exception as e:  # um coletor quebrado não derruba os outros
            print(f"{name}: {type(e).__name__}: {e}", flush=True)
            out[name] = []
    return out


def bridge_rows(ctx: Ctx, name: str, labels: Dict[str, str]) -> List[Row]:
    rows: List[Row] = []
    for q in ((ctx.bridge or {}).get(name) or {}).get("quotas") or []:
        used = q.get("used_pct") or {}
        label = labels.get(q.get("id"))
        if label is None or used.get("value") is None:
            continue
        rows.append(Row(label, round(used["value"]), reset_in=int(q.get("reset_in") or 0), old=bool(used.get("stale"))))
    return rows
