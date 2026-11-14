import json, plistlib, sqlite3, sys, tempfile, unittest, unittest.mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doguia_usage import config, device, platforms
from doguia_usage.model import Ctx, Row, parse_time
from doguia_usage.providers import agy, claude, codex, deepseek, opencode
from doguia_usage.platforms import linux, macos, windows

NOW = 1_800_000_000.0


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup)
        self.home = Path(self.t.name)
        self.ctx = Ctx(home=self.home, env={}, now=NOW, platform="linux", state_dir=self.home / "state", cfg={})


class Claude(Base):
    def test_status_line_com_epoca_e_iso(self):
        p = {"rate_limits": {"five_hour": {"used_percentage": 41.6, "resets_at": NOW + 3600}, "seven_day": {"used_percentage": 12, "resets_at": "2027-02-15T08:00:00Z"}}}
        self.assertTrue(claude.store(self.ctx, p))
        r = claude.collect(self.ctx)
        self.assertEqual([(x.label, x.pct) for x in r], [("Claude 5 h", 42), ("Claude 7 dias", 12)])
        self.assertEqual(r[0].reset_in, 3600)
        self.assertFalse(r[0].old)

    def test_campo_ausente_nao_grava(self):
        self.assertFalse(claude.store(self.ctx, {"model": {}}))
        self.assertEqual(claude.collect(self.ctx), [])

    def test_janela_renovada_e_dado_velho(self):
        claude.store(self.ctx, {"rate_limits": {"five_hour": {"used_percentage": 80, "resets_at": NOW + 10}}})
        self.ctx.now = NOW + 20
        r = claude.collect(self.ctx)
        self.assertEqual((r[0].pct, r[0].old), (0, True))

    def test_usa_a_ponte_sem_status_line(self):
        self.ctx.bridge = {"claude": {"quotas": [{"id": "5h", "used_pct": {"value": 11.0, "stale": False}, "reset_in": 99}]}}
        r = claude.collect(self.ctx)
        self.assertEqual((r[0].label, r[0].pct, r[0].reset_in), ("Claude 5 h", 11, 99))

    def test_nao_toca_em_credenciais(self):
        (self.home / ".claude").mkdir(); cred = self.home / ".claude/.credentials.json"; cred.write_text("{}")
        cred.chmod(0)
        self.assertEqual(claude.collect(self.ctx), [])


class Codex(Base):
    def write(self, lines):
        d = self.home / ".codex/sessions/2027/01/15"; d.mkdir(parents=True)
        (d / "a.jsonl").write_text("\n".join(json.dumps(x) for x in lines))

    def event(self, limits, ts=None):
        return {"timestamp": ts or NOW - 60, "type": "event_msg", "payload": {"type": "token_count", "rate_limits": limits}}

    def test_janelas(self):
        self.write([self.event({"primary": {"used_percent": 30, "window_minutes": 300, "resets_at": NOW + 600},
                                "secondary": {"used_percent": 70.4, "window_minutes": 10080, "resets_in_seconds": 7200}})])
        r = codex.collect(self.ctx)
        self.assertEqual([(x.label, x.pct, x.old) for x in r], [("Codex 5 h", 30, False), ("Codex 7 dias", 70, False)])
        self.assertEqual(r[0].reset_in, 600)
        self.assertEqual(r[1].reset_in, 7140)

    def test_ultimo_com_dado_vence_o_nulo(self):
        self.write([self.event({"secondary": {"used_percent": 5, "window_minutes": 10080}}), self.event({"primary": None, "secondary": None})])
        self.assertEqual(codex.collect(self.ctx)[0].pct, 5)

    def test_antigo(self):
        self.write([self.event({"secondary": {"used_percent": 5, "window_minutes": 10080}}, ts=NOW - 7200)])
        self.assertTrue(codex.collect(self.ctx)[0].old)

    def test_codex_home_e_linha_quebrada(self):
        d = self.home / "alt/sessions/2027/01/15"; d.mkdir(parents=True)
        (d / "a.jsonl").write_text('{"rate_limits": quebrado\n' + json.dumps(self.event({"secondary": {"used_percent": 9}})))
        self.ctx.env["CODEX_HOME"] = str(self.home / "alt")
        self.assertEqual(codex.collect(self.ctx)[0].pct, 9)

    def test_sem_pasta(self):
        self.assertEqual(codex.collect(self.ctx), [])


class Agy(Base):
    def test_caminhos_por_sistema(self):
        self.ctx.platform = "darwin"; self.assertIn("Library/Application Support", agy.state_paths(self.ctx)[0].as_posix())
        self.ctx.platform = "win32"; self.ctx.env["APPDATA"] = "/w/Roaming"; self.assertEqual(agy.state_paths(self.ctx)[0].parts[1:3], ("w", "Roaming"))

    def test_escolhe_o_mais_usado_e_renovado_zera(self):
        s = {"models": [{"remaining": 0.9, "reset_at": NOW + 100}, {"remaining": 0.25, "reset_at": NOW + 500}, {"remaining": None}]}
        r = agy.rows_from(s, NOW, NOW)
        self.assertEqual((r[0].pct, r[0].reset_in), (75, 500))
        self.assertEqual(agy.rows_from({"models": [{"remaining": 0.0, "reset_at": NOW - 1}]}, NOW, NOW)[0].pct, 0)

    def test_banco_invalido_nao_vira_zero(self):
        p = agy.state_paths(self.ctx)[0]; p.parent.mkdir(parents=True)
        c = sqlite3.connect(p); c.execute("create table ItemTable(key text, value blob)")
        c.execute("insert into ItemTable values(?,?)", (agy.KEY, "lixo"))
        c.execute("insert into ItemTable values(?,?)", ("oauthToken", "segredo")); c.commit(); c.close()
        self.assertEqual(agy.collect(self.ctx), [])

    def test_decodifica_protobuf(self):
        import base64, struct
        def vi(n):
            o = b""
            while True:
                b = n & 127; n >>= 7
                if n: o += bytes([b | 128])
                else: return o + bytes([b])
        def ld(f, b): return vi(f << 3 | 2) + vi(len(b)) + b
        quota = vi(1 << 3 | 5) + struct.pack("<f", .5) + ld(2, vi(1 << 3) + vi(int(NOW + 50)))
        model = ld(1, b"Gemini 3.8 Flash (High)") + ld(15, quota)
        status = ld(33, ld(1, model))
        env = ld(1, ld(1, b"userStatusSentinelKey") + ld(2, ld(1, base64.b64encode(status))))
        st = agy.decode_user_status(base64.b64encode(env).decode())
        self.assertEqual(agy.rows_from(st, NOW, NOW)[0].pct, 50)


class OpenCode(Base):
    def db(self, rows):
        p = opencode.db_path(self.ctx); p.parent.mkdir(parents=True)
        c = sqlite3.connect(p); c.execute("create table message(id, session_id, time_created, time_updated, data)")
        c.execute("create table credential(secret)"); c.execute("insert into credential values('x')")
        for at, d in rows: c.execute("insert into message values(1,1,?,?,?)", (at, at, d if isinstance(d, str) else json.dumps(d)))
        c.commit(); c.close()

    def m(self, prov, cost, inp=1000):
        return {"role": "assistant", "providerID": prov, "cost": cost, "tokens": {"input": inp, "output": 500, "cache": {"read": 99999, "write": 100}}}

    def test_soma_so_hoje_e_ignora_lixo(self):
        now = int(NOW * 1000)
        self.db([(now - 1000, self.m("anthropic", 1.5)), (now - 1000, self.m("deepseek", .25)), (now - 2 * 86400000, self.m("x", 99)), (now - 1000, "lixo"), (now - 1000, {"role": "user"})])
        r = opencode.collect(self.ctx)
        self.assertEqual((r[0].label, r[0].pct, r[0].text), ("OpenCode hoje", -1, "$1.75"))

    def test_gratis_mostra_tokens(self):
        self.db([(int(NOW * 1000) - 1000, self.m("opencode", 0, 5_000_000))])
        self.assertEqual(opencode.collect(self.ctx)[0].text, "5.0M")

    def test_sem_banco(self):
        self.assertEqual(opencode.collect(self.ctx), [])


class DeepSeek(Base):
    def test_saldo_em_texto(self):
        self.assertEqual(deepseek.parse_balance({"balance_infos": [{"currency": "CNY", "total_balance": "110.00"}, {"currency": "USD", "total_balance": "7.5"}]}), ("USD", 7.5))
        self.assertIsNone(deepseek.parse_balance({"balance_infos": [{"currency": "USD"}]}))

    def test_orcamento_vira_barra_e_chave_nao_e_gravada(self):
        self.ctx.env["DEEPSEEK_API_KEY"] = "sk-teste-secreta"; self.ctx.cfg["deepseek_budget"] = 10
        orig = deepseek.balance; deepseek.balance = lambda k: ("USD", 2.5); self.addCleanup(lambda: setattr(deepseek, "balance", orig))
        r = deepseek.collect(self.ctx)
        self.assertEqual((r[0].label, r[0].pct, r[0].text), ("DeepSeek saldo", 75, "$2.50"))
        config.save(self.ctx, self.ctx.cfg)
        self.assertNotIn("sk-teste", (config.config_dir(self.ctx) / "config.json").read_text())

    def test_sem_chave_usa_opencode(self):
        OpenCode.db(self, [(int(NOW * 1000) - 1, OpenCode.m(self, "deepseek", 0, 2000))])
        self.assertEqual(deepseek.collect(self.ctx)[0].label, "DeepSeek hoje")

    def test_sem_nada(self):
        self.assertEqual(deepseek.collect(self.ctx), [])


class Device(unittest.TestCase):
    def test_formulario(self):
        d = device.form([Row("Claude 5 h", 11, reset_in=60), Row("Codex 7 dias", 100, old=True), Row("OpenCode hoje", text="$1.75"), Row("vazio")])
        self.assertEqual((d["l0"], d["p0"], d["r0"]), ("Claude 5 h", 11, 60))
        self.assertEqual((d["c5"], d["c5r"], d["x7"], d["xold"], d["o1"]), (11, 60, 100, 1, 1))
        self.assertEqual((d["p2"], d["t2"]), (-1, "$1.75"))
        self.assertNotIn("l3", d)

    def test_limite_de_linhas_e_claude_antigo(self):
        d = device.form([Row("Claude 5 h", 5, old=True)] + [Row(f"x{i}", i) for i in range(9)])
        self.assertNotIn("c5", d); self.assertIn("l6", d); self.assertNotIn("l7", d)


class Avisos(unittest.TestCase):
    def test_eventos_do_claude_code(self):
        from doguia_usage.cli import hook_notice
        self.assertEqual(hook_notice({"hook_event_name": "Stop", "cwd": "/home/a/doguia-display/"}), ("done", "Claude terminou em doguia-display"))
        self.assertEqual(hook_notice({"hook_event_name": "Notification", "cwd": "C:\\w\\app", "message": "Claude needs your permission to use Bash"}), ("wait", "Claude pede permissão em app"))
        self.assertEqual(hook_notice({"hook_event_name": "Notification", "message": "Claude is waiting for your input"}), ("wait", "Claude esperando você em o projeto"))
        self.assertEqual(hook_notice({"hook_event_name": "UserPromptSubmit"}), ("clear", ""))
        self.assertIsNone(hook_notice({"hook_event_name": "PreToolUse"}))

    def test_sem_saida_e_sem_falha(self):
        import io
        from contextlib import redirect_stdout
        from doguia_usage import cli
        out = io.StringIO()
        with unittest.mock.patch.object(sys, "stdin", io.StringIO('{"hook_event_name":"Stop","cwd":"/x"}')), redirect_stdout(out), \
             self.assertRaises(SystemExit) as e:
            cli.main(["notify", "--host", "127.0.0.1:9"])  # porta fechada: falha engolida
        self.assertEqual((e.exception.code, out.getvalue()), (0, ""))


class Sistemas(unittest.TestCase):
    def test_pastas(self):
        c = Ctx(home=Path("/h"), env={}, platform="darwin"); self.assertIn("Application Support", config.config_dir(c).as_posix())
        c = Ctx(home=Path("/h"), env={"APPDATA": "/a"}, platform="win32"); self.assertEqual(config.config_dir(c).as_posix(), "/a/doguia-usage")
        c = Ctx(home=Path("/h"), env={}, platform="linux"); self.assertEqual(config.config_dir(c).as_posix(), "/h/.config/doguia-usage")

    def test_arquivos_de_inicio(self):
        cmd = ["/o p/python", "-m", "doguia_usage", "run"]
        self.assertIn("ExecStart='/o p/python' -m doguia_usage run", linux.unit_text(cmd))
        p = plistlib.loads(macos.plist_bytes(cmd)); self.assertEqual(p["ProgramArguments"], cmd); self.assertTrue(p["KeepAlive"])
        self.assertIn('"/o p/python"', windows.run_value(cmd))
        self.assertIs(platforms.module("win32"), windows); self.assertIs(platforms.module("darwin"), macos); self.assertIs(platforms.module("linux"), linux)

    def test_tempo(self):
        self.assertEqual(parse_time(1800000000000), 1800000000.0)
        self.assertEqual(parse_time("2027-01-15T08:00:00Z"), parse_time("2027-01-15T08:00:00+00:00"))
        self.assertIsNone(parse_time("x")); self.assertIsNone(parse_time(None))


if __name__ == "__main__":
    unittest.main()
