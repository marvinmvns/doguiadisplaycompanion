"""Diagnóstico local das dependências, sem ler credenciais nem alterar serviços."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from . import config


def verificar(ctx):
    itens = []
    itens.append({'nome':'Python incluído no aplicativo' if getattr(sys, 'frozen', False) else 'Python ' + sys.version.split()[0], 'ok':sys.version_info >= (3,9), 'ajuda':'O companion usa somente a biblioteca padrão; não é necessário instalar bibliotecas.'})
    pasta = config.config_dir(ctx)
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=pasta):
            pass
        itens.append({'nome':'Pasta de configuração disponível', 'ok':True, 'ajuda':str(pasta)})
    except OSError:
        itens.append({'nome':'Pasta de configuração sem acesso', 'ok':False, 'ajuda':'Execute com seu usuário e confira as permissões de ' + str(pasta)})
    if ctx.platform.startswith('linux'):
        ativo = False
        if shutil.which('systemctl'):
            try:
                ativo = subprocess.run(['systemctl','--user','show-environment'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode == 0
            except (OSError, subprocess.SubprocessError):
                pass
        itens.append({'nome':'Início automático com systemd', 'ok':ativo, 'opcional':True, 'ajuda':'Disponível na sua sessão.' if ativo else 'Entre em uma sessão de usuário com systemd. Enquanto isso, execute doguia-usage run para enviar consumo; o painel e os testes continuam disponíveis.'})
    elif ctx.platform == 'darwin':
        itens.append({'nome':'Início automático com LaunchAgent', 'ok':bool(shutil.which('launchctl')), 'opcional':True, 'ajuda':'Ative na etapa Integrar usando sua sessão de usuário.'})
    elif ctx.platform == 'win32':
        itens.append({'nome':'Início automático no Windows', 'ok':True, 'opcional':True, 'ajuda':'Usa o início de sessão do seu usuário, sem administrador.'})
    return {'itens':itens, 'sistema': {'win32':'Windows','darwin':'macOS'}.get(ctx.platform,'Linux'), 'pronto':all(x['ok'] for x in itens if not x.get('opcional'))}
