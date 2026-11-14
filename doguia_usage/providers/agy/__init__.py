"""Antigravity (agy): cota que o próprio IDE guarda em `state.vscdb`, somente leitura.

Lê apenas a chave `antigravityUnifiedStateSync.userStatus`, nunca `oauthToken`. O formato não é documentado: qualquer
erro de leitura resulta em nenhuma linha, jamais em zero. Decodificador adaptado do ai-dev-meter do usuário.
"""
from __future__ import annotations

import base64
import os
import re
import sqlite3
import struct
from pathlib import Path
from typing import Any, List, Optional

from ...model import STALE_AFTER, Ctx, Row, clamp_pct

KEY = "antigravityUnifiedStateSync.userStatus"


# ---- minimal protobuf wire decoder ---------------------------------------

def _varint(b: bytes, i: int) -> tuple:
    r = s = 0
    while True:
        if i >= len(b) or s > 63:
            raise ValueError("truncated varint")
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        s += 7
        if c < 0x80:
            return r, i


def fields(b: bytes) -> list:
    """[(field_no, wire_type, value)]; value is int (varint), bytes (len /
    fixed32 / fixed64). Raises ValueError on malformed input."""
    out: list = []
    i = 0
    while i < len(b):
        key, i = _varint(b, i)
        f, w = key >> 3, key & 7
        if f == 0:
            raise ValueError("field 0")
        if w == 0:
            v, i = _varint(b, i)
        elif w == 1:
            v, i = b[i:i + 8], i + 8
        elif w == 2:
            n, i = _varint(b, i)
            v, i = b[i:i + n], i + n
        elif w == 5:
            v, i = b[i:i + 4], i + 4
        else:
            raise ValueError(f"wire type {w}")
        if i > len(b):
            raise ValueError("truncated")
        out.append((f, w, v))
    return out


def _first(fs: list, no: int, wire: Optional[int] = None) -> Any:
    for f, w, v in fs:
        if f == no and (wire is None or w == wire):
            return v
    return None


def _all(fs: list, no: int, wire: Optional[int] = None) -> list:
    return [v for f, w, v in fs if f == no and (wire is None or w == wire)]


def _str(v: Any) -> Optional[str]:
    if isinstance(v, (bytes, bytearray)):
        try:
            return bytes(v).decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None


def _b64(v: Any) -> bytes:
    if isinstance(v, (bytes, bytearray)):
        v = bytes(v).decode("ascii", errors="strict")
    v = str(v).strip()
    return base64.b64decode(v + "=" * (-len(v) % 4), validate=False)


def unwrap_sentinel(value: Any) -> Optional[bytes]:
    """ItemTable value -> inner message bytes (base64 envelope of a
    {key, {base64 payload}} pair). None when the shape is not recognised."""
    try:
        outer = fields(_b64(value))
        entry = _first(outer, 1, 2)
        if entry is None:
            return None
        inner = fields(entry)
        holder = _first(inner, 2, 2)
        if holder is None:
            return None
        payload = _first(fields(holder), 1, 2)
        if payload is None:
            return None
        return _b64(payload)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return None


def decode_user_status(value: Any) -> Optional[dict]:
    """{plan, tier, models:[{label, id, remaining, reset_at}]} or None."""
    raw = unwrap_sentinel(value)
    if raw is None:
        return None
    try:
        top = fields(raw)
        models = []
        cfg = _first(top, 33, 2)
        for mb in (_all(fields(cfg), 1, 2) if cfg is not None else []):
            mf = fields(mb)
            label = _str(_first(mf, 1, 2))
            if not label:
                continue
            mid = None
            idb = _first(mf, 2, 2)
            if idb is not None:
                mid = _first(fields(idb), 1, 0)
            q = _first(mf, 15, 2)
            remaining = reset = None
            if q is not None:
                qf = fields(q)
                fr = _first(qf, 1, 5)
                remaining = struct.unpack("<f", fr)[0] if fr is not None and len(fr) == 4 else 0.0
                rb = _first(qf, 2, 2)
                if rb is not None:
                    reset = _first(fields(rb), 1, 0)
            models.append({"label": label, "id": mid, "remaining": remaining,
                           "reset_at": float(reset) if reset else None})
        plan = tier = None
        pb = _first(top, 36, 2)
        if pb is not None:
            pf = fields(pb)
            tier = _str(_first(pf, 1, 2))
            plan = _str(_first(pf, 3, 2)) or _str(_first(pf, 2, 2))
        return {"plan": plan, "tier": tier, "models": models}
    except (ValueError, struct.error):
        return None


def family(label: str) -> str:
    """'Gemini 3.8 Flash (High)' vira 'Gemini Flash': versões e esforços contam juntos."""
    s = re.sub(r"\(.*?\)", " ", label)
    toks = [t for t in s.split() if not re.fullmatch(r"\d+(\.\d+)*", t)]
    return " ".join(toks) or label.strip()


def state_paths(ctx: Ctx) -> List[Path]:
    names = ("Antigravity IDE", "Antigravity")
    if ctx.platform == "win32":
        base = Path(ctx.env.get("APPDATA") or ctx.home / "AppData/Roaming")
    elif ctx.platform == "darwin":
        base = ctx.home / "Library/Application Support"
    else:
        base = Path(ctx.env.get("XDG_CONFIG_HOME") or ctx.home / ".config")
    return [base / n / "User/globalStorage/state.vscdb" for n in names]


def read_value(db: Path) -> Any:
    uri = db.resolve().as_uri()
    for suffix in ("?mode=ro", "?mode=ro&immutable=1"):  # imutável quando o IDE segura o arquivo
        try:
            con = sqlite3.connect(uri + suffix, uri=True, timeout=0.5)
            try:
                row = con.execute("SELECT value FROM ItemTable WHERE key = ?", (KEY,)).fetchone()
                return row[0] if row else None
            finally:
                con.close()
        except sqlite3.Error:
            continue
    return None


def rows_from(status: dict, at: float, now: float) -> List[Row]:
    """Uma linha com o modelo mais usado: a tela é pequena e esse é o limite que trava primeiro."""
    best = None
    for m in status.get("models") or []:
        if m.get("remaining") is None:
            continue
        used, reset = 100.0 * (1.0 - float(m["remaining"])), m.get("reset_at")
        if reset and now >= reset:
            used, reset = 0.0, None
        if best is None or used > best[0]:
            best = (used, reset)
    if best is None:
        return []
    used, reset = best
    return [Row("Antigravity", clamp_pct(used), reset_in=int(reset - now) if reset else 0, old=now - at > STALE_AFTER * 24)]


def collect(ctx: Ctx) -> List[Row]:
    for path in state_paths(ctx):
        if path.is_file():
            value = read_value(path)
            status = decode_user_status(value) if value is not None else None
            if status:
                return rows_from(status, path.stat().st_mtime, ctx.now)
    return []
