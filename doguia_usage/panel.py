"""Painel local multiplataforma, servido pela biblioteca padrão do Python."""
from __future__ import annotations

import ipaddress
import json
import math
import secrets
import subprocess
import threading
import time
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import config, device, platforms, providers, wizard
from .model import Ctx


def host_validado(value):
    value = str(value).strip()
    if value == device.HOSTNAME:
        return value
    try:
        ip = ipaddress.IPv4Address(value)
        if ip.is_private and not ip.is_loopback and not ip.is_unspecified:
            return str(ip)
    except ValueError:
        pass
    raise ValueError("Informe o IP local do Display ou doguiadisplay.local.")


def validar_config(data):
    out = dict(data)
    out['host'] = host_validado(out.get('host', ''))
    for key, lo, hi in [('every', 10, 3600), ('view', 0, 3), ('claude_style', 0, 3)]:
        value = float(out.get(key, 60 if key == 'every' else 0))
        if not math.isfinite(value) or value != int(value) or not lo <= value <= hi:
            raise ValueError(f'{key}: use um inteiro de {lo} a {hi}.')
        out[key] = int(value)
    value = float(out.get('deepseek_budget', 0))
    if not math.isfinite(value) or value < 0:
        raise ValueError('Informe um orçamento positivo ou zero.')
    out['deepseek_budget'] = value
    if not isinstance(out.get('disabled', []), list) or any(x not in ('claude', 'codex', 'agy', 'opencode', 'deepseek') for x in out.get('disabled', [])):
        raise ValueError('Seleção de ferramentas inválida.')
    if not isinstance(out.get('bridge', ''), str):
        raise ValueError('O endereço da ponte deve ser um texto.')
    return {k: v for k, v in out.items() if k in (*config.DEFAULTS, 'view', 'claude_style')}


class Painel:
    def __init__(self, ctx=None):
        self.ctx = ctx or Ctx()
        self.lock = threading.Lock()

    def contexto(self):
        ctx = self.ctx
        ctx.now = time.time()
        ctx.cfg = config.load(ctx)
        ctx.state_dir = config.config_dir(ctx)
        ctx.bridge = providers.read_bridge(ctx.cfg.get('bridge') or '')
        return ctx

    def aparelho(self, route, data=None):
        host = host_validado(config.load(self.ctx).get('host', ''))
        if not device.probe(host):
            raise ValueError('O endereço não respondeu como DoguIA Display. Confira a rede e o IP.')
        body = urlencode(data).encode() if data is not None else None
        req = Request(f'http://{host}/api/{route}', data=body)
        with urlopen(req, timeout=12) as response:
            content = response.read(128000)
        try:
            return json.loads(content)
        except ValueError:
            return {'mensagem': content.decode('utf-8', errors='replace')}

    def executar(self, action, data):
        with self.lock:
            ctx = self.contexto()
            if action == 'ambiente':
                from .environment import verificar
                return verificar(ctx)
            if action == 'estado':
                return {'config': ctx.cfg, 'sistema': ctx.platform}
            if action == 'buscar':
                return {'host': device.find(ctx.cfg.get('host', '')) or ''}
            if action == 'salvar':
                cfg = validar_config(data)
                config.save(ctx, {**ctx.cfg, **cfg})
                return {'mensagem': 'Configuração salva neste computador.'}
            if action == 'coletar':
                return {k: [asdict(r) for r in rows] for k, rows in providers.collect_all(ctx).items()}
            if action == 'testar':
                from .cli import rows_of, push
                host = host_validado(ctx.cfg.get('host', ''))
                if not device.probe(host):
                    raise ValueError('Display sem resposta. Confira o IP e a rede Wi-Fi.')
                rows = rows_of(ctx)
                if rows:
                    push(host, rows, ctx.cfg.get('view'), ctx.cfg.get('claude_style'))
                device.notify(host, 'info', 'DoguIA conectado ao computador')
                return {'mensagem': 'Conexão e aviso enviados ao Display.' + (' Consumo enviado.' if rows else ' Ainda não há dados de consumo; use uma IA e teste novamente.')}
            if action == 'automatico':
                mod = platforms.module(ctx.platform)
                result = mod.install(ctx.home, platforms.command()) if data.get('ativo') else mod.uninstall(ctx.home)
                return {'mensagem': 'Início automático atualizado.', 'local': str(result or '')}
            if action == 'claude':
                style = data.get('style')
                if style not in ('compact', 'bars', 'badge', 'full', None):
                    raise ValueError('Estilo inválido.')
                path = wizard.claude_dir(ctx) / 'settings.json'
                settings = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
                if not isinstance(settings, dict):
                    raise ValueError('settings.json do Claude inválido.')
                backup = wizard.write_json(path, wizard.merge_claude(settings, platforms.shell_line(platforms.program(), ctx.platform), style, bool(data.get('hooks'))))
                return {'mensagem': 'Claude configurado.', 'backup': str(backup or '')}
            if action in ('config', 'custom', 'state', 'info'):
                return self.aparelho(action)
            if action in ('gravar-config', 'gravar-custom'):
                schema = json.loads(resources.files('doguia_usage').joinpath('web/schemas.json').read_text(encoding='utf-8'))[action[7:]]['properties']
                if not data or any(k not in schema or schema[k].get('readOnly') for k in data):
                    raise ValueError('Ajustes desconhecidos ou vazios.')
                for key, value in data.items():
                    rule = schema[key]
                    if rule.get('type') in ('integer', 'number'):
                        try:
                            number = float(value)
                        except (ValueError, TypeError):
                            raise ValueError(f'{key}: informe um número.')
                        if not math.isfinite(number) or (rule['type'] == 'integer' and number != int(number)):
                            raise ValueError(f'{key}: número inválido.')
                        if number < rule.get('minimum', -math.inf) or number > rule.get('maximum', math.inf):
                            raise ValueError(f'{key}: valor fora da faixa permitida.')
                        if 'enum' in rule and number not in rule['enum']:
                            raise ValueError(f'{key}: escolha uma opção disponível.')
                    elif not isinstance(value, str) or len(value) > rule.get('maxLength', 32000):
                        raise ValueError(f'{key}: texto inválido ou muito longo.')
                return self.aparelho(action[7:], data)
            raise ValueError('Operação desconhecida.')


def servidor(port=0, ctx=None):
    painel, token = Painel(ctx), secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def responder(self, code, content, mime='application/json'):
            body = content if isinstance(content, bytes) else json.dumps(content, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def local(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.local():
                return self.responder(403, {'erro': 'Origem inválida.'})
            files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css'), '/schemas.json': ('schemas.json', 'application/json'), '/pet.png': ('pet.png', 'image/png')}
            files.update({'/logo.svg': ('logo.svg', 'image/svg+xml'), '/display.webp': ('display.webp', 'image/webp'), '/inter.woff2': ('inter.woff2', 'font/woff2'), '/funnel-display.woff2': ('funnel-display.woff2', 'font/woff2')})
            if self.path == '/sessao':
                return self.responder(200, {'token': token})
            if self.path not in files:
                return self.responder(404, {'erro': 'Página não encontrada.'})
            name, mime = files[self.path]
            self.responder(200, resources.files('doguia_usage').joinpath('web/' + name).read_bytes(), mime)

        def do_POST(self):
            if not self.local() or self.headers.get('X-Doguia-Token') != token:
                return self.responder(403, {'erro': 'Sessão inválida. Reabra o painel.'})
            try:
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 32000:
                    raise ValueError('Pedido inválido.')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict) or not self.path.startswith('/api/'):
                    raise ValueError('Pedido inválido.')
                self.responder(200, painel.executar(self.path[5:], data))
            except (ValueError, OSError, TypeError, subprocess.SubprocessError) as exc:
                self.responder(400, {'erro': str(exc)})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def run(args):
    server = servidor(args.port)
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Painel DoguIA: {url}\nCtrl+C encerra o painel.')
    if not args.sem_navegador:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
