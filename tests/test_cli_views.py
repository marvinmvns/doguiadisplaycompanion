import io, json, sys, tempfile, unittest, unittest.mock
from contextlib import redirect_stdout
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doguia_usage import cli
from doguia_usage.model import Row


class StatusLine(unittest.TestCase):
    def linha(self, style, payload, agora=None):
        class Args:
            pass
        Args.style = style
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as t, \
             unittest.mock.patch.object(cli.config, "config_dir", lambda ctx: Path(t)), \
             unittest.mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             unittest.mock.patch.object(cli.time, "time", lambda: agora or 0), redirect_stdout(out):
            self.assertEqual(cli.cmd_statusline(Args()), 0)
        return out.getvalue().strip()

    PAYLOAD = {"rate_limits": {"five_hour": {"used_percentage": 42.0, "resets_at": 1700003600},
                               "seven_day": {"used_percentage": 18.0, "resets_at": 1700086400}}}

    def test_estilos(self):
        self.assertEqual(self.linha("compact", self.PAYLOAD), "5h: 42% | 7d: 18%")
        self.assertEqual(self.linha("badge", self.PAYLOAD), "⚡ Claude [5h: 42% · 7d: 18%]")
        self.assertEqual(self.linha("bars", self.PAYLOAD), "Claude 5h [████░░░░░░] 42% · 7d [██░░░░░░░░] 18%")

    def test_status_line_com_epoca_e_iso(self):
        agora = 1700000000
        iso = {"rate_limits": {"five_hour": {"used_percentage": 42, "resets_at": "2023-11-14T23:13:20Z"},
                               "seven_day": {"used_percentage": 18, "resets_at": 1700086400000}}}  # ms
        self.assertEqual(self.linha("full", iso, agora), "Claude 5h: 42% (renova 1h00) · 7d: 18% (renova 1d0h)")
        self.assertEqual(self.linha("full", self.PAYLOAD, agora), "Claude 5h: 42% (renova 1h00) · 7d: 18% (renova 1d0h)")

    def test_sem_limites(self):
        self.assertEqual(self.linha("bars", {}), "DoguIA")


class Envio(unittest.TestCase):
    def test_push_com_estilo_do_painel(self):
        sent = {}
        with unittest.mock.patch.object(cli.device, "send", lambda host, data: sent.update(data)):
            cli.push("192.168.1.10", [Row(label="Claude 5 h", pct=42)], view=3, claude_style=1)
        self.assertEqual((sent["uview"], sent["claude_style"]), (3, 1))

    def test_push_sem_estilo_nao_manda_campos(self):
        sent = {}
        with unittest.mock.patch.object(cli.device, "send", lambda host, data: sent.update(data)):
            cli.push("h", [Row(label="Claude 5 h", pct=42)])
        self.assertNotIn("uview", sent); self.assertNotIn("claude_style", sent)


if __name__ == "__main__":
    unittest.main()

class Intervalo(unittest.TestCase):
    def test_loop_respeita_intervalo_de_dez_segundos(self):
        from types import SimpleNamespace
        ctx = SimpleNamespace(cfg={'host':'192.168.1.10','every':10})
        class Encerrar(Exception):
            pass
        args = SimpleNamespace(host=None, every=None)
        with unittest.mock.patch.object(cli,'background_log'), \
             unittest.mock.patch.object(cli,'single_instance',return_value=object()), \
             unittest.mock.patch.object(cli,'context',return_value=ctx), \
             unittest.mock.patch.object(cli,'rows_of',return_value=[Row('Codex',25)]), \
             unittest.mock.patch.object(cli,'push') as push, \
             unittest.mock.patch.object(cli.time,'sleep',side_effect=Encerrar) as pause:
            with self.assertRaises(Encerrar):
                cli.cmd_run(args)
            push.assert_called_once()
            pause.assert_called_once_with(10)
