"""Claude Code: lê o que o próprio CLI publica na status line, sem abrir `.credentials.json`.

`doguia-usage statusline` recebe `rate_limits` pelo stdin e guarda só percentuais e horários. O campo pode faltar em
algumas versões e planos, e `resets_at` já apareceu como época e como ISO 8601. Sem ele, usa a ponte ai-dev-meter.
"""
from __future__ import annotations

import json
from typing import List, Optional

from ...model import STALE_AFTER, Ctx, Row, clamp_pct, parse_time

CACHE = "claude_rate_limits.json"
WINDOWS = (("five_hour", "Claude 5 h"), ("seven_day", "Claude 7 dias"))


def store(ctx: Ctx, payload: dict) -> bool:
    limits = payload.get("rate_limits")
    if not isinstance(limits, dict) or ctx.state_dir is None:
        return False
    keep = {}
    for key, _ in WINDOWS:
        node = limits.get(key)
        if isinstance(node, dict):
            pct = node.get("used_percentage", node.get("used_percent"))
            if pct is not None:
                keep[key] = {"pct": float(pct), "reset": parse_time(node.get("resets_at"))}
    if not keep:
        return False
    ctx.state_dir.mkdir(parents=True, exist_ok=True)
    tmp = ctx.state_dir / (CACHE + ".tmp")
    tmp.write_text(json.dumps({"at": ctx.now, "windows": keep}), encoding="utf-8")
    tmp.replace(ctx.state_dir / CACHE)
    return True


def _from_cache(ctx: Ctx) -> List[Row]:
    if ctx.state_dir is None:
        return []
    try:
        data = json.loads((ctx.state_dir / CACHE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = []
    for key, label in WINDOWS:
        node = (data.get("windows") or {}).get(key)
        if not node:
            continue
        reset: Optional[float] = node.get("reset")
        if reset and reset <= ctx.now:  # a janela já renovou desde a última leitura
            rows.append(Row(label, 0, old=True))
            continue
        rows.append(Row(label, clamp_pct(node["pct"]), reset_in=int(reset - ctx.now) if reset else 0, old=ctx.now - data.get("at", 0) > STALE_AFTER))
    return rows


def collect(ctx: Ctx) -> List[Row]:
    from .. import bridge_rows

    cached = _from_cache(ctx)
    if cached and not all(r.old for r in cached):
        return cached
    return bridge_rows(ctx, "claude", {"5h": "Claude 5 h", "week": "Claude 7 dias"}) or cached
