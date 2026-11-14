"""Conversa com o aparelho só por HTTP na rede local: ele não tem BLE."""
from __future__ import annotations

import ipaddress
import json
import socket
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from .model import Row

MAX_ROWS = 7
HOSTNAME = "doguiadisplay.local"


def probe(host: str, timeout: float = 2.5) -> bool:
    """Reconhece o aparelho por /api/info, que não conta como contato do dono."""
    try:
        with urllib.request.urlopen(f"http://{host}/api/info", timeout=timeout) as r:
            return json.load(r).get("product") == "doguia-display"
    except (OSError, ValueError):
        return False


def local_ip() -> Optional[str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:  # UDP sem enviar nada: só descobre a interface de saída
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def scan(ip: Optional[str] = None, timeout: float = 2.5) -> Optional[str]:
    """Procura na /24 local. O aparelho responde em até ~1 s, porque atende entre um quadro e outro."""
    ip = ip or local_ip()
    if not ip:
        return None
    hosts = [str(h) for h in ipaddress.ip_network(ip + "/24", strict=False).hosts() if str(h) != ip]
    with ThreadPoolExecutor(48) as pool:
        for host, ok in zip(hosts, pool.map(lambda h: probe(h, timeout), hosts)):
            if ok:
                return host
    return None


def find(saved: str = "") -> Optional[str]:
    for host in filter(None, (saved, HOSTNAME)):
        if probe(host):
            return host
    return scan()


def form(rows: List[Row]) -> dict:
    """Linhas genéricas (l0..l6) e, para firmware antigo, os campos de Claude e Codex."""
    rows = [r for r in rows if r.pct >= 0 or r.text][:MAX_ROWS]
    data: dict = {}
    for i, r in enumerate(rows):
        data[f"l{i}"] = r.label[:14]
        data[f"p{i}"] = r.pct
        if r.text:
            data[f"t{i}"] = r.text[:8]
        if r.reset_in:
            data[f"r{i}"] = int(r.reset_in)
        if r.old:
            data[f"o{i}"] = 1
    legacy = {"Claude 5 h": "c5", "Claude 7 dias": "c7", "Codex 5 h": "x5", "Codex 7 dias": "x7"}
    for r in rows:
        key = legacy.get(r.label)
        if key is None or r.pct < 0 or (r.old and key[0] == "c"):
            continue
        data[key] = r.pct
        if r.reset_in:
            data[key + "r"] = int(r.reset_in)
        if r.old and key[0] == "x":
            data["xold"] = 1
    return data


def send(host: str, data: dict, timeout: float = 5.0) -> None:
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(f"http://{host}/api/usage", data=body, timeout=timeout) as r:
        r.read()


def notify(host: str, kind: str, text: str = "", timeout: float = 2.0) -> None:
    """Aviso no letreiro: done, wait, info ou clear. Timeout curto: quem chama é um hook do Claude Code."""
    data = {"kind": kind}
    if text:
        data["text"] = text[:95]
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(f"http://{host}/api/notify", data=body, timeout=timeout) as r:
        r.read()
