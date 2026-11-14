"""Contratos do painel, persistência e envio ao Display simulado."""
import json
import tempfile
import threading
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from doguia_usage import config, panel
from doguia_usage.model import Ctx, Row


class PainelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ctx = Ctx(home=Path(self.tmp.name), env={}, platform='linux')
        self.painel = panel.Painel(self.ctx)

    def tearDown(self):
        self.tmp.cleanup()

    def test_configuracao_e_validacao(self):
        self.painel.executar('salvar', {'host': '192.168.31.15', 'every': 30, 'disabled': ['agy']})
        self.assertEqual(config.load(self.ctx)['every'], 30)
        for bad in [{'host':'example.com'}, {'host':'127.0.0.1'}, {'host':'192.168.1.2','every':0}, {'host':'192.168.1.2','every':float('nan')}]:
            with self.assertRaises(ValueError):
                self.painel.executar('salvar', bad)
        self.assertEqual(config.load(self.ctx)['every'], 30)

    @patch('doguia_usage.panel.device.probe', return_value=True)
    @patch('doguia_usage.panel.urlopen')
    def test_display_recebe_apenas_campos_alterados(self, request, probe):
        config.save(self.ctx, {'host': '192.168.31.15'})
        request.return_value.__enter__.return_value = BytesIO(b'{"ok":true}')
        self.assertTrue(self.painel.executar('gravar-config', {'bri': 55})['ok'])
        req = request.call_args.args[0]
        self.assertEqual(req.full_url, 'http://192.168.31.15/api/config')
        self.assertEqual(req.data, b'bri=55')
        with self.assertRaises(ValueError):
            self.painel.executar('gravar-custom', {'firmware': 'x'})

    @patch('doguia_usage.panel.Painel.aparelho')
    def test_editor_recusa_valores_invalidos_antes_da_rede(self, aparelho):
        for action, data in [
            ('gravar-config', {'bri':101}),
            ('gravar-config', {'bri':'nan'}),
            ('gravar-config', {'bri':3.5}),
            ('gravar-config', {'name':'x'*100}),
            ('gravar-custom', {'preset':99}),
            ('gravar-custom', {'pet_act_name':'dance'}),
        ]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.painel.executar(action, data)
        aparelho.assert_not_called()

    @patch('doguia_usage.panel.device.notify')
    @patch('doguia_usage.cli.push')
    @patch('doguia_usage.cli.rows_of', return_value=[Row('Codex 5 h', 25)])
    @patch('doguia_usage.panel.device.probe', return_value=True)
    def test_envio_consumo(self, probe, rows, push, notify):
        config.save(self.ctx, {'host': '192.168.31.15', 'view': 2})
        self.assertIn('Consumo enviado', self.painel.executar('testar', {})['mensagem'])
        push.assert_called_once_with('192.168.31.15', rows.return_value, 2, None)
        notify.assert_called_once()

    def test_http_sessao_assets_e_origem(self):
        server = panel.servidor(ctx=self.ctx)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            for path in ('/', '/app.js', '/style.css', '/pet.png', '/schemas.json'):
                with urlopen(url+path) as r:
                    self.assertEqual(r.status, 200)
                    self.assertTrue(r.read())
            token = json.load(urlopen(url+'/sessao'))['token']
            with self.assertRaises(HTTPError) as err:
                urlopen(Request(url+'/api/estado', data=b'{}'))
            self.assertEqual(err.exception.code, 403)
            req = Request(url+'/api/estado', data=b'{}', headers={'X-Doguia-Token': token})
            self.assertIn('config', json.load(urlopen(req)))
            req = Request(url+'/sessao', headers={'Host':'site-externo.test'})
            with self.assertRaises(HTTPError):
                urlopen(req)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

class IntegracaoHTTP(unittest.TestCase):
    def test_leitura_e_edicao_com_servidor_display(self):
        """Tráfego HTTP real; só o endereço é redirecionado ao simulador local."""
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import parse_qs
        ajustes = {'bri': 40, 'name': 'DoguIA'}
        pedidos = []

        class Display(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                pedidos.append(('GET', self.path))
                payload = {'product':'doguia-display'} if self.path == '/api/info' else ajustes
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                pedidos.append(('POST', self.path))
                data = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
                ajustes.update({k:v[0] for k,v in data.items()})
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok":true}')

        display = ThreadingHTTPServer(('127.0.0.1',0), Display)
        thread = threading.Thread(target=display.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                ctx = Ctx(home=Path(tmp), env={}, platform='linux')
                config.save(ctx, {'host':'192.168.31.15'})
                painel = panel.Painel(ctx)
                with patch.object(panel, 'host_validado', return_value=f'127.0.0.1:{display.server_port}'):
                    self.assertEqual(painel.executar('config', {})['bri'], 40)
                    painel.executar('gravar-config', {'bri':65})
                    self.assertEqual(painel.executar('config', {})['bri'], '65')
                    self.assertEqual(ajustes['name'], 'DoguIA')
            self.assertIn(('POST','/api/config'), pedidos)
            self.assertEqual(pedidos.count(('GET','/api/info')),3)
        finally:
            display.shutdown()
            display.server_close()
            thread.join()
