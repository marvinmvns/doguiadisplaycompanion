"""OpenCode: custo e tokens do dia nas mensagens do banco local, somente leitura.

Não há janela de limite, então a linha não tem barra. As tabelas `account` e `credential` nunca são lidas.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from ...model import Ctx, Row, money


def db_path(ctx: Ctx) -> Path:
    base = Path(ctx.env.get("XDG_DATA_HOME") or ctx.home / ".local/share")
    return base / "opencode" / "opencode.db"


def today_messages(ctx: Ctx) -> Iterator[dict]:
    path = db_path(ctx)
    if not path.is_file():
        return
    start = datetime.fromtimestamp(ctx.now).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=2)
    try:
        con.execute("PRAGMA query_only = 1")
        for (data,) in con.execute("SELECT data FROM message WHERE time_created >= ?", (int(start * 1000),)):
            try:
                msg = json.loads(data)
            except ValueError:
                continue
            if isinstance(msg, dict):
                yield msg
    finally:
        con.close()


def total_tokens(msg: dict) -> int:
    t = msg.get("tokens") or {}
    cache = t.get("cache") or {}
    return int(t.get("input") or 0) + int(t.get("output") or 0) + int(t.get("reasoning") or 0) + int(cache.get("write") or 0)


def short(n: int) -> str:
    return f"{n / 1e6:.1f}M" if n >= 1_000_000 else f"{n // 1000}k" if n >= 1000 else str(n)


def summarize(messages: Iterator[dict]) -> Dict[str, Tuple[float, int]]:
    out: Dict[str, Tuple[float, int]] = {}
    for m in messages:
        if m.get("role") != "assistant":
            continue
        cost, tokens = out.get(m.get("providerID") or "", (0.0, 0))
        out[m.get("providerID") or ""] = (cost + float(m.get("cost") or 0), tokens + total_tokens(m))
    return out


def collect(ctx: Ctx) -> List[Row]:
    totals = summarize(today_messages(ctx))
    if not totals:
        return []
    cost = sum(c for c, _ in totals.values())
    tokens = sum(t for _, t in totals.values())
    return [Row("OpenCode hoje", text=money(cost) if cost >= 0.01 else short(tokens))]
