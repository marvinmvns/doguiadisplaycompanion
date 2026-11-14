"""DeepSeek: API paga por uso, sem janela de limite.

Com `DEEPSEEK_API_KEY` no ambiente, consulta o saldo oficial; a chave nunca é gravada. Sem ela, mostra os tokens do dia
vindos do OpenCode, quando ele usa DeepSeek. Com `deepseek_budget`, a barra mostra quanto do orçamento já foi gasto.
"""
from __future__ import annotations

import json
import urllib.request
from typing import List, Optional, Tuple

from ...model import Ctx, Row, clamp_pct, money

URL = "https://api.deepseek.com/user/balance"
SYMBOL = {"USD": "$", "CNY": "¥"}


def parse_balance(data: dict) -> Optional[Tuple[str, float]]:
    infos = data.get("balance_infos") or []
    infos = sorted(infos, key=lambda i: i.get("currency") != "USD")
    for info in infos:
        try:
            return info.get("currency") or "USD", float(info["total_balance"])  # o valor vem como texto
        except (KeyError, TypeError, ValueError):
            continue
    return None


def balance(key: str) -> Optional[Tuple[str, float]]:
    req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return parse_balance(json.load(r))


def collect(ctx: Ctx) -> List[Row]:
    from ..opencode import short, summarize, today_messages

    key = ctx.env.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        try:
            got = balance(key)
        except OSError as e:
            print(f"deepseek: {type(e).__name__}", flush=True)
            got = None
        if got:
            cur, value = got
            text = money(value) if cur == "USD" else f"{SYMBOL.get(cur, '')}{value:.2f}"
            budget = float(ctx.cfg.get("deepseek_budget") or 0)
            pct = clamp_pct(100 * (1 - value / budget)) if budget > 0 else -1
            return [Row("DeepSeek saldo", pct, text=text)]
    cost, tokens = summarize(today_messages(ctx)).get("deepseek", (0.0, 0))
    if tokens:
        return [Row("DeepSeek hoje", text=money(cost) if cost >= 0.01 else short(tokens))]
    return []
