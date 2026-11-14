"""Confere o painel do executável instalado ou .pyz, sem alterar o usuário."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


def conferir(command):
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, HOME=tmp, USERPROFILE=tmp, APPDATA=tmp, XDG_CONFIG_HOME=tmp)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen([*command, 'painel', '--sem-navegador', '--port', str(port)], env=env, stdout=log, stderr=log)
            url = f'http://127.0.0.1:{port}'
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read().decode(errors='replace'))
                    try:
                        with urlopen(url+'/sessao', timeout=1) as response:
                            token = json.load(response)['token']
                        break
                    except OSError:
                        time.sleep(.2)
                else:
                    raise RuntimeError('O painel empacotado não iniciou em 20 segundos.')
                for route, mime in [('/', 'text/html'), ('/app.js', 'text/javascript'), ('/style.css', 'text/css'), ('/pet.png', 'image/png'), ('/schemas.json', 'application/json'), ('/logo.svg', 'image/svg+xml'), ('/display.webp', 'image/webp'), ('/inter.woff2', 'font/woff2'), ('/funnel-display.woff2', 'font/woff2')]:
                    with urlopen(url+route, timeout=5) as response:
                        assert response.headers['Content-Type'].startswith(mime), route
                        assert response.read(), route
                req = Request(url+'/api/estado', data=b'{}', headers={'X-Doguia-Token':token})
                with urlopen(req, timeout=5) as response:
                    assert 'config' in json.load(response)
                print('Painel empacotado: HTML, JS, CSS, pet, schemas e sessão HTTP conferidos.')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    path = Path(sys.argv[1]).resolve()
    conferir([sys.executable, str(path)] if path.suffix == '.pyz' else [str(path)])
