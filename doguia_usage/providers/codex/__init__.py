"""Codex CLI: `rate_limits` que o próprio CLI grava nos eventos `token_count` das sessões, sem abrir `auth.json`."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from ...model import STALE_AFTER, Ctx, Row, clamp_pct, parse_time

MAX_FILES = 40


def _sessions(ctx: Ctx) -> Iterator[Path]:
    root = Path(ctx.env.get("CODEX_HOME") or ctx.home / ".codex") / "sessions"
    if not root.is_dir():
        return
    seen = 0
    for year in sorted(root.iterdir(), reverse=True):
        for month in sorted(year.iterdir(), reverse=True) if year.is_dir() else ():
            for day in sorted(month.iterdir(), reverse=True) if month.is_dir() else ():
                if not day.is_dir():
                    continue
                for f in sorted(day.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
                    yield f
                    seen += 1
                    if seen >= MAX_FILES:
                        return


def _latest(path: Path) -> Optional[Tuple[dict, float]]:
    found = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"rate_limits"' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            payload = event.get("payload") or {}
            limits = payload.get("rate_limits") or (payload.get("info") or {}).get("rate_limits")
            if isinstance(limits, dict) and (limits.get("primary") or limits.get("secondary")):
                found = (limits, parse_time(event.get("timestamp")) or path.stat().st_mtime)
    return found


def _row(node: dict, at: float, now: float) -> Optional[Row]:
    pct = node.get("used_percent")
    if pct is None:
        return None
    minutes = node.get("window_minutes") or 0
    label = "Codex 5 h" if minutes and minutes <= 360 else "Codex 7 dias"
    reset = parse_time(node.get("resets_at"))
    if reset is None and node.get("resets_in_seconds") is not None:
        reset = at + float(node["resets_in_seconds"])
    if reset and reset <= now:
        return Row(label, 0, old=True)
    return Row(label, clamp_pct(pct), reset_in=int(reset - now) if reset else 0, old=now - at > STALE_AFTER)


def collect(ctx: Ctx) -> List[Row]:
    for path in _sessions(ctx):
        hit = _latest(path)
        if hit:
            limits, at = hit
            rows = [_row(limits[k], at, ctx.now) for k in ("primary", "secondary") if isinstance(limits.get(k), dict)]
            return sorted((r for r in rows if r), key=lambda r: r.label != "Codex 5 h")
    return []
