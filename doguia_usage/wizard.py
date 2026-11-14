"""Assistente de configuração: aparelho, estilo do painel, Claude Code e início automático, em perguntas curtas.

Abre com `doguia-usage configurar`, ao rodar o programa sem argumentos num terminal e no fim dos instaladores.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from . import __version__, config, device, platforms, providers
from .model import Ctx

VIEWS = ((0, "barras"), (1, "cartões em grade"), (2, "foco no maior consumo"), (3, "DoguIA animado"))
CLAUDE_STYLES = ((0, "plasma"), (1, "gamer / sprint"), (2, "holograma seguidor"), (3, "reator orbital"))
STATUS_STYLES = (("compact", "5h: 42% | 7d: 18%"), ("bars", "Claude 5h [████░░░░░░] 42%"),
                 ("badge", "⚡ Claude [5h: 42% · 7d: 18%]"), ("full", "Claude 5h: 42% (renova 1h30)"))
HOOK_EVENTS = ("Stop", "Notification", "UserPromptSubmit", "SessionEnd")


class Cancel(Exception):
    pass


class Ask:
    """Perguntas no terminal. `read` é trocável para os testes."""

    def __init__(self, read: Callable[[str], str] = input, say: Callable[..., None] = print):
        self.read, self.say = read, say

    def text(self, prompt: str, default: str = "") -> str:
        try:
            got = self.read(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancel()
        return got or default

    def yes(self, prompt: str, default: bool = True) -> bool:
        while True:
            got = self.text(prompt + (" (S/n)" if default else " (s/N)")).lower()
            if not got:
                return default
            if got[0] in "sy":
                return True
            if got[0] == "n":
                return False

    def choose(self, prompt: str, options: Sequence[Tuple[object, str]], default: int = 0):
        self.say(prompt)
        for i, (_, label) in enumerate(options):
            self.say(f"  {i}) {label}")
        while True:
            got = self.text("Escolha", str(default))
            if got.isdigit() and int(got) < len(options):
                return options[int(got)][0]


def step(ask: Ask, n: int, title: str) -> None:
    ask.say(f"\n[{n}/6] {title}")


# --- Claude Code ------------------------------------------------------------------------------------------------------

def claude_dir(ctx: Ctx) -> Path:
    return Path(ctx.env.get("CLAUDE_CONFIG_DIR") or ctx.home / ".claude")


def ours(entry) -> bool:
    cmd = str(entry.get("command", "")) if isinstance(entry, dict) else ""
    return "doguia-usage" in cmd or "doguia_usage" in cmd


def merge_claude(settings: dict, prog: str, statusline: Optional[str], hooks: bool) -> dict:
    """Devolve uma cópia do settings.json com a status line e os hooks do doguia-usage. O resto fica como estava."""
    s = copy.deepcopy(settings)
    if statusline:
        cmd = f"{prog} statusline" + ("" if statusline == "compact" else f" --style {statusline}")
        s["statusLine"] = {"type": "command", "command": cmd}
    if hooks:
        if not isinstance(s.get("hooks"), dict):
            s["hooks"] = {}
        for event in HOOK_EVENTS:
            groups = s["hooks"].get(event)
            groups = [g for g in groups if isinstance(g, dict)] if isinstance(groups, list) else []
            for g in groups:  # tira entradas antigas nossas, para não duplicar ao rodar de novo
                if isinstance(g.get("hooks"), list):
                    g["hooks"] = [h for h in g["hooks"] if not ours(h)]
            groups = [g for g in groups if g.get("hooks")]
            groups.append({"hooks": [{"type": "command", "command": f"{prog} notify", "timeout": 5}]})
            s["hooks"][event] = groups
    return s


def write_json(path: Path, data: dict) -> Optional[Path]:
    """Grava com backup do original. Devolve o caminho do backup, se havia arquivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = path.with_name(path.name + ".doguia-bak")
        shutil.copy2(path, backup)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return backup


def setup_claude(ctx: Ctx, ask: Ask) -> None:
    folder = claude_dir(ctx)
    if not folder.exists() and not shutil.which("claude"):
        ask.say("Claude Code não encontrado neste computador. Pulando.")
        return
    path = folder / "settings.json"
    try:
        settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(settings, dict):
            raise ValueError("não é um objeto")
    except (OSError, ValueError) as e:
        ask.say(f"Não consegui ler {path} ({e}). Nada foi alterado; veja o README para configurar à mão.")
        return
    prog = platforms.shell_line(platforms.program(), ctx.platform)
    current = settings.get("statusLine") if isinstance(settings.get("statusLine"), dict) else None
    style = None
    ask.say("A status line do Claude Code é de onde vêm os limites de 5 h e 7 dias (contas Pro e Max).")
    if current and not ours(current):
        ask.say(f"Já existe outra status line: {current.get('command')}")
        want = ask.yes("Trocar pela do DoguIA?", False)
    else:
        want = ask.yes("Usar a status line do DoguIA?", True)
    if want:
        style = ask.choose("Estilo do texto na status line:", STATUS_STYLES, 0)
    hooks = ask.yes("Avisar no letreiro quando o Claude terminar ou esperar você (hooks)?", True)
    if not style and not hooks:
        return
    backup = write_json(path, merge_claude(settings, prog, style, hooks))
    ask.say(f"Gravado em {path}" + (f" (cópia do anterior em {backup.name})" if backup else ""))


# --- Passos -----------------------------------------------------------------------------------------------------------

def pick_device(ctx: Ctx, ask: Ask) -> Optional[str]:
    saved = ctx.cfg.get("host") or ""
    ask.say("Procurando o DoguIA Display na rede (pode levar uns 15 s)...")
    host = device.find(saved)
    if host:
        ask.say(f"Encontrado em {host}.")
        if ask.yes("Usar este aparelho?", True):
            return host
    else:
        ask.say("Não encontrei. O display e o computador precisam estar na mesma rede Wi-Fi.")
        ask.say("O IP aparece na tela do display e no app do roteador.")
    while True:
        typed = ask.text("IP do display (vazio para procurar de novo, - para pular)")
        if typed == "-":
            return None
        if not typed:
            host = device.find(saved)
            if host:
                ask.say(f"Encontrado em {host}.")
                return host
            ask.say("Ainda não encontrei.")
            continue
        if device.probe(typed):
            return typed
        ask.say(f"{typed} não respondeu como um DoguIA Display.")


def detected(ctx: Ctx, ask: Ask) -> int:
    from .cli import ORDER, show

    found = providers.collect_all(ctx)
    n = 0
    for name in ORDER:
        rows = found.get(name, [])
        n += bool(rows)
        ask.say(f"  {name}:" + ("" if rows else " sem dados"))
        show(rows, ask.say)
    return n


def autostart(ctx: Ctx, ask: Ask) -> None:
    if not ask.yes("Enviar o consumo sempre, iniciando junto com o computador?", True):
        return
    try:
        where = platforms.module(ctx.platform).install(ctx.home, platforms.command())
        ask.say(f"Início automático ligado: {where}")
    except (OSError, subprocess.CalledProcessError) as e:
        ask.say(f"Não consegui ligar o início automático ({e}). Rode à mão: doguia-usage run")


def test_send(ctx: Ctx, ask: Ask, host: str) -> None:
    from .cli import push, rows_of

    try:
        push(host, rows_of(ctx), view=ctx.cfg.get("view"), claude_style=ctx.cfg.get("claude_style"))
        ask.say("Consumo enviado. Confira a tela do display.")
    except ValueError:
        ask.say("Nenhuma IA com dados ainda: a tela atualiza quando houver uso.")
    except OSError as e:
        ask.say(f"O envio falhou ({e}).")
        return
    try:
        device.notify(host, "info", "DoguIA Usage configurado")
    except (OSError, ValueError):
        pass  # firmware sem /api/notify


def run(ctx: Optional[Ctx] = None, ask: Optional[Ask] = None, pause: bool = False) -> int:
    ask = ask or Ask()
    if ctx is None:
        ctx = Ctx()
    ctx.cfg = config.load(ctx)
    ctx.state_dir = config.config_dir(ctx)
    ctx.bridge = providers.read_bridge(ctx.cfg.get("bridge") or "")
    ask.say(f"DoguIA Usage {__version__}: assistente de configuração. Ctrl+C cancela a qualquer momento.")
    code = 0
    try:
        step(ask, 1, "Aparelho")
        host = pick_device(ctx, ask)
        if host:
            ctx.cfg["host"] = host
        step(ask, 2, "Tela de consumo")
        views = [v for v, _ in VIEWS]
        ctx.cfg["view"] = ask.choose("Estilo do painel:", VIEWS, views.index(ctx.cfg["view"]) if ctx.cfg.get("view") in views else 0)
        styles = [v for v, _ in CLAUDE_STYLES]
        ctx.cfg["claude_style"] = ask.choose("Animação do indicador do Claude:", CLAUDE_STYLES,
                                             styles.index(ctx.cfg["claude_style"]) if ctx.cfg.get("claude_style") in styles else 0)
        step(ask, 3, "Ferramentas de IA neste computador")
        detected(ctx, ask)
        budget = ask.text("Crédito do DeepSeek em dólares, para a barra (0 se não usa)", str(ctx.cfg.get("deepseek_budget") or 0))
        try:
            ctx.cfg["deepseek_budget"] = max(0.0, float(budget.replace(",", ".")))
        except ValueError:
            ask.say("Valor inválido; mantive o anterior.")
        config.save(ctx, ctx.cfg)
        ask.say(f"Configuração salva em {config.config_dir(ctx)}")
        step(ask, 4, "Claude Code")
        setup_claude(ctx, ask)
        step(ask, 5, "Início automático")
        if host:
            autostart(ctx, ask)
        else:
            ask.say("Sem aparelho escolhido: rode este assistente de novo quando o display estiver na rede.")
        step(ask, 6, "Teste")
        if host:
            test_send(ctx, ask, host)
        ask.say("\nPronto. Para rever: doguia-usage doctor. Para mudar algo: doguia-usage configurar.")
    except Cancel:
        ask.say("\nConfiguração cancelada. O que já foi salvo continua valendo.")
        code = 1
    if pause:
        try:
            ask.read("Pressione Enter para fechar.")
        except (EOFError, KeyboardInterrupt):
            pass
    return code
