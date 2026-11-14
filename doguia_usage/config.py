"""Pastas por sistema e configuração. Nenhuma chave de API é gravada aqui."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Ctx

DEFAULTS = {"host": "", "every": 60, "bridge": "http://127.0.0.1:8737", "disabled": [], "deepseek_budget": 0}


def config_dir(ctx: Ctx) -> Path:
    if ctx.platform == "win32":
        return Path(ctx.env.get("APPDATA") or ctx.home / "AppData/Roaming") / "doguia-usage"
    if ctx.platform == "darwin":
        return ctx.home / "Library/Application Support/doguia-usage"
    return Path(ctx.env.get("XDG_CONFIG_HOME") or ctx.home / ".config") / "doguia-usage"


def load(ctx: Ctx) -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads((config_dir(ctx) / "config.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save(ctx: Ctx, cfg: dict) -> None:
    folder = config_dir(ctx)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "config.tmp"
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    tmp.replace(folder / "config.json")
