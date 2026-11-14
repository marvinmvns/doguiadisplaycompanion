"""Comandos: configurar, setup, doctor, once, run, statusline, notify, install, uninstall."""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from . import __version__, config, device, platforms, providers
from .model import Ctx, Row, parse_time
from .providers import claude

ORDER = ("claude", "codex", "agy", "deepseek", "opencode")


def context() -> Ctx:
    ctx = Ctx()
    ctx.cfg = config.load(ctx)
    ctx.state_dir = config.config_dir(ctx)
    ctx.bridge = providers.read_bridge(ctx.cfg.get("bridge") or "")
    return ctx


def rows_of(ctx: Ctx) -> List[Row]:
    found = providers.collect_all(ctx)
    return [r for name in ORDER for r in found.get(name, [])]


def show(rows: List[Row], say=print) -> None:
    for r in rows:
        value = r.text or (f"{r.pct}%" if r.pct >= 0 else "-")
        extra = (f"  renova em {r.reset_in // 3600}h{r.reset_in % 3600 // 60:02d}" if r.reset_in else "") + ("  (antigo)" if r.old else "")
        say(f"  {r.label:<15}{value:>8}{extra}")


def cmd_setup(args) -> int:
    ctx = context()
    host = args.host or device.find(ctx.cfg.get("host") or "")
    if not host or not device.probe(host):
        print("Aparelho não encontrado na rede. Informe o IP: doguia-usage setup --host 192.168.x.x")
        return 1
    ctx.cfg["host"] = host
    if args.deepseek_budget is not None:
        ctx.cfg["deepseek_budget"] = args.deepseek_budget
    if getattr(args, "view", None) is not None:
        ctx.cfg["view"] = args.view
    if getattr(args, "claude_style", None) is not None:
        ctx.cfg["claude_style"] = args.claude_style
    config.save(ctx, ctx.cfg)
    print(f"Aparelho em {host}. Configuração em {config.config_dir(ctx)}")
    return 0


def cmd_doctor(args) -> int:
    ctx = context()
    host = ctx.cfg.get("host") or ""
    print(f"doguia-usage {__version__} em {sys.platform}, Python {sys.version.split()[0]}")
    print(f"Aparelho: {host or 'não configurado'} ({'responde' if host and device.probe(host) else 'sem resposta'})")
    print(f"Ponte ai-dev-meter: {'ativa' if ctx.bridge else 'não encontrada (opcional)'}")
    found = providers.collect_all(ctx)
    for name in ORDER:
        print(f"{name}:" + ("" if found.get(name) else " sem dados"))
        show(found.get(name, []))
    return 0


def push(host: str, rows: List[Row], view: Optional[int] = None, claude_style: Optional[int] = None) -> None:
    data = device.form(rows)
    if not data:
        raise ValueError("nenhuma ferramenta com dados")
    if view is not None:
        data["uview"] = int(view)
    if claude_style is not None:
        data["claude_style"] = int(claude_style)
    device.send(host, data)


def cmd_once(args) -> int:
    ctx = context()
    host = args.host or ctx.cfg.get("host") or device.find()
    rows = rows_of(ctx)
    show(rows)
    if not host:
        print("Aparelho não encontrado. Rode: doguia-usage setup")
        return 1
    view = getattr(args, "view", None)
    if view is None:
        view = ctx.cfg.get("view")
    cstyle = getattr(args, "claude_style", None)
    if cstyle is None:
        cstyle = ctx.cfg.get("claude_style")
    try:
        push(host, rows, view=view, claude_style=cstyle)
    except (OSError, ValueError) as e:
        print(f"falhou: {e}")
        return 1
    print(f"Enviado a {host}")
    return 0


def background_log() -> None:
    """Sem console (executável do Windows sem janela): a saída vai para run.log, com no máximo ~256 KB."""
    if sys.stdout is not None:
        return
    path = config.config_dir(Ctx()) / "run.log"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if path.exists() and path.stat().st_size > 256 * 1024 else "a"
        sys.stdout = sys.stderr = open(path, mode, encoding="utf-8", buffering=1)
    except OSError:
        pass


def single_instance(folder) -> Optional[object]:
    """Trava em run.lock: o instalador e o assistente podem iniciar o run de novo. None se outro já roda."""
    folder.mkdir(parents=True, exist_ok=True)
    f = open(folder / "run.lock", "a+")
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f  # fica aberto enquanto o processo viver


def cmd_run(args) -> int:
    background_log()
    lock = single_instance(config.config_dir(Ctx()))
    if lock is None:
        print("Outro doguia-usage run já está enviando.", flush=True)
        return 0
    fails = 0
    while True:
        ctx = context()
        host = args.host or ctx.cfg.get("host") or ""
        view = getattr(args, "view", None)
        if view is None:
            view = ctx.cfg.get("view")
        cstyle = getattr(args, "claude_style", None)
        if cstyle is None:
            cstyle = ctx.cfg.get("claude_style")
        try:
            if not host or fails >= 3:  # o roteador pode ter trocado o IP do aparelho
                found = device.find(host)
                if found and found != host:
                    host = ctx.cfg["host"] = found
                    config.save(ctx, ctx.cfg)
                    print(f"Aparelho em {host}", flush=True)
            if not host:
                raise OSError("aparelho não encontrado")
            push(host, rows_of(ctx), view=view, claude_style=cstyle)
            fails = 0
        except (OSError, ValueError) as e:
            fails += 1
            print(f"falhou: {e}", flush=True)
        time.sleep(max(10, int(args.every or ctx.cfg.get("every") or 60)))


def cmd_statusline(args) -> int:
    """Para `statusLine.command` do Claude Code: guarda o limite e imprime uma linha curta."""
    ctx = Ctx()
    ctx.state_dir = config.config_dir(ctx)
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    claude.store(ctx, payload if isinstance(payload, dict) else {})
    limits = (payload.get("rate_limits") or {}) if isinstance(payload, dict) else {}
    style = getattr(args, "style", "compact")
    items = []
    for k, label in claude.WINDOWS:
        data = limits.get(k)
        if isinstance(data, dict) and data.get("used_percentage") is not None:
            pct = round(data["used_percentage"])
            res = parse_time(data.get("resets_at"))  # época ou ISO 8601
            short = "5h" if "5" in label else ("7d" if "7" in label else label[7:])
            items.append((short, pct, res))
    if not items:
        print("DoguIA")
        return 0
    if style == "badge":
        txt = " · ".join(f"{name}: {pct}%" for name, pct, _ in items)
        print(f"⚡ Claude [{txt}]")
    elif style == "bars":
        parts = []
        for name, pct, _ in items:
            filled = min(10, max(0, int(round(pct / 10))))
            bar = "█" * filled + "░" * (10 - filled)
            parts.append(f"{name} [{bar}] {pct}%")
        print("Claude " + " · ".join(parts))
    elif style == "full":
        now = time.time()
        parts = []
        for name, pct, res in items:
            rem = ""
            if res:
                diff = max(0, int(res - now))
                if diff >= 86400:
                    rem = f" (renova {diff // 86400}d{diff % 86400 // 3600}h)"
                elif diff:
                    rem = f" (renova {diff // 3600}h{diff % 3600 // 60:02d})"
            parts.append(f"{name}: {pct}%{rem}")
        print("Claude " + " · ".join(parts))
    else:  # compact
        print(" | ".join(f"{name}: {pct}%" for name, pct, _ in items))
    return 0


def hook_notice(event: dict) -> Optional[Tuple[str, str]]:
    """Evento de hook do Claude Code -> (kind, texto). None: evento que não vira aviso."""
    name = event.get("hook_event_name") or ""
    proj = (event.get("cwd") or "").replace("\\", "/").rstrip("/").rsplit("/", 1)[-1] or "o projeto"  # Windows também
    if name == "Stop":
        return "done", f"Claude terminou em {proj}"
    if name == "Notification":
        msg = (event.get("message") or "").lower()
        return "wait", f"Claude pede permissão em {proj}" if "permission" in msg else f"Claude esperando você em {proj}"
    if name in ("UserPromptSubmit", "SessionEnd"):
        return "clear", ""
    return None


def cmd_notify(args) -> int:
    """Para hooks do Claude Code. Nunca imprime nada nem falha: no UserPromptSubmit a saída iria para o contexto."""
    if args.kind:
        notice: Optional[Tuple[str, str]] = (args.kind, args.text or "")
    else:
        try:
            event = json.load(sys.stdin)
        except ValueError:
            return 0
        notice = hook_notice(event if isinstance(event, dict) else {})
    if not notice:
        return 0
    hosts = args.host or [config.load(Ctx()).get("host") or device.HOSTNAME]
    def one(host: str) -> None:
        try:
            device.notify(host, *notice)
        except (OSError, ValueError):
            pass  # aparelho fora da rede: o Claude Code segue sem esperar
    with ThreadPoolExecutor(len(hosts)) as pool:
        list(pool.map(one, hosts))
    return 0


def cmd_install(args) -> int:
    ctx = context()
    if not ctx.cfg.get("host"):
        print("Configure antes: doguia-usage setup")
        return 1
    print("Início automático em", platforms.module().install(ctx.home, platforms.command()))
    return 0


def cmd_uninstall(args) -> int:
    platforms.module().uninstall(Ctx().home)
    print("Início automático removido")
    return 0


def cmd_wizard(args) -> int:
    from . import wizard

    return wizard.run(pause=args.pausar)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="doguia-usage", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("configurar", aliases=["wizard"], help="assistente: aparelho, estilo, Claude Code e início automático")
    s.add_argument("--pausar", action="store_true", help="espera Enter no fim (atalhos que abrem uma janela)")
    s.set_defaults(fn=cmd_wizard)
    from . import panel
    s = sub.add_parser("painel", help="abre o assistente visual e editor do Display")
    s.add_argument("--port", type=int, default=0)
    s.add_argument("--sem-navegador", action="store_true")
    s.set_defaults(fn=panel.run)
    s = sub.add_parser("setup", help="acha o aparelho e salva o IP")
    s.add_argument("--host")
    s.add_argument("--deepseek-budget", type=float, help="orçamento em dólares para a barra do DeepSeek")
    s.add_argument("--view", type=int, choices=(0, 1, 2, 3), help="estilo do painel: 0 barras, 1 cartões, 2 foco/destaque, 3 doguia animado")
    s.add_argument("--claude-style", type=int, choices=(0, 1, 2, 3), help="animação do indicador de tokens: 0 plasma, 1 gamer/sprint, 2 holograma seguidor, 3 reator orbital")
    s.set_defaults(fn=cmd_setup)
    sub.add_parser("doctor", help="mostra o que foi detectado, sem enviar nada").set_defaults(fn=cmd_doctor)
    s = sub.add_parser("once", help="coleta e envia uma vez")
    s.add_argument("--host")
    s.add_argument("--view", type=int, choices=(0, 1, 2, 3), help="estilo do painel: 0 barras, 1 cartões, 2 foco/destaque, 3 doguia animado")
    s.add_argument("--claude-style", type=int, choices=(0, 1, 2, 3), help="animação do indicador de tokens: 0 plasma, 1 gamer/sprint, 2 holograma seguidor, 3 reator orbital")
    s.set_defaults(fn=cmd_once)
    s = sub.add_parser("run", help="envia sempre")
    s.add_argument("--host")
    s.add_argument("--every", type=int)
    s.add_argument("--view", type=int, choices=(0, 1, 2, 3), help="estilo do painel: 0 barras, 1 cartões, 2 foco/destaque, 3 doguia animado")
    s.add_argument("--claude-style", type=int, choices=(0, 1, 2, 3), help="animação do indicador de tokens: 0 plasma, 1 gamer/sprint, 2 holograma seguidor, 3 reator orbital")
    s.set_defaults(fn=cmd_run)
    s = sub.add_parser("statusline", help="comando para a status line do Claude Code")
    s.add_argument("--style", choices=("compact", "badge", "bars", "full"), default="compact", help="estilo do texto na status line")
    s.set_defaults(fn=cmd_statusline)
    s = sub.add_parser("notify", help="hook do Claude Code: avisa no letreiro quando ele termina ou espera você")
    s.add_argument("--host", action="append", help="repita para avisar mais de um aparelho")
    s.add_argument("--kind", choices=("done", "wait", "info", "clear"), help="aviso manual, sem ler o evento do stdin")
    s.add_argument("--text")
    s.set_defaults(fn=cmd_notify)
    sub.add_parser("install", help="liga o início automático").set_defaults(fn=cmd_install)
    sub.add_parser("uninstall", help="desliga o início automático").set_defaults(fn=cmd_uninstall)
    args = p.parse_args(argv)
    if not args.cmd:  # duplo clique no executável abre o assistente; num pipe, só a ajuda
        if sys.stdin is not None and sys.stdin.isatty():
            args = p.parse_args(["painel"])
        else:
            p.print_help()
            sys.exit(2)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consoles antigos do Windows
    sys.exit(args.fn(args))
