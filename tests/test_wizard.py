import json, sys, tempfile, unittest, unittest.mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doguia_usage import config, platforms, wizard
from doguia_usage.model import Ctx, Row


def respostas(*itens):
    fila = list(itens)
    def read(prompt):
        if not fila:
            raise EOFError
        return fila.pop(0)
    return read


class Mescla(unittest.TestCase):
    ANTES = {"model": "opus", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "say pronto"}]}],
                                        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "x"}]}]}}

    def test_preserva_o_resto_e_nao_duplica(self):
        uma = wizard.merge_claude(self.ANTES, "/usr/bin/doguia-usage", "bars", True)
        duas = wizard.merge_claude(uma, "/usr/bin/doguia-usage", "bars", True)
        self.assertEqual(uma, duas)
        self.assertEqual(duas["model"], "opus")
        self.assertEqual(duas["hooks"]["PreToolUse"], self.ANTES["hooks"]["PreToolUse"])
        self.assertEqual(duas["statusLine"], {"type": "command", "command": "/usr/bin/doguia-usage statusline --style bars"})
        stop = [h["command"] for g in duas["hooks"]["Stop"] for h in g["hooks"]]
        self.assertEqual(stop, ["say pronto", "/usr/bin/doguia-usage notify"])
        for ev in wizard.HOOK_EVENTS:
            self.assertEqual(sum("notify" in h["command"] for g in duas["hooks"][ev] for h in g["hooks"]), 1)
        self.assertNotIn("statusLine", self.ANTES)  # não mexe no original

    def test_hooks_malformados_e_estilo_padrao(self):
        s = wizard.merge_claude({"hooks": []}, "dg", "compact", True)
        self.assertEqual(s["statusLine"]["command"], "dg statusline")
        self.assertEqual(set(s["hooks"]), set(wizard.HOOK_EVENTS))
        self.assertNotIn("hooks", wizard.merge_claude({}, "dg", "compact", False))

    def test_linha_de_shell(self):
        self.assertEqual(platforms.shell_line(["C:\\Program Files\\D\\doguia-usage.exe"], "win32"), '"C:/Program Files/D/doguia-usage.exe"')
        self.assertEqual(platforms.shell_line(["/opt/a b/doguia-usage"], "linux"), "'/opt/a b/doguia-usage'")


class Assistente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".claude").mkdir()
        (self.home / ".claude/settings.json").write_text(json.dumps({"model": "opus"}))
        self.ctx = Ctx(home=self.home, env={"XDG_CONFIG_HOME": str(self.home / "cfg")}, platform="linux")
        self.sent, self.installed, self.out = {}, [], []
        patches = [
            unittest.mock.patch.object(wizard.device, "find", lambda saved="": "192.168.31.15"),
            unittest.mock.patch.object(wizard.device, "probe", lambda h, timeout=2.5: h == "10.0.0.9"),
            unittest.mock.patch.object(wizard.device, "send", lambda h, d, timeout=5.0: self.sent.update(d, host=h)),
            unittest.mock.patch.object(wizard.device, "notify", lambda *a, **k: None),
            unittest.mock.patch.object(wizard.providers, "collect_all", lambda ctx: {"claude": [Row("Claude 5 h", 42)]}),
            unittest.mock.patch.object(wizard.providers, "read_bridge", lambda url: None),
            unittest.mock.patch.object(wizard.platforms.linux, "install", lambda home, cmd: self.installed.append(cmd) or "unit"),
            unittest.mock.patch.object(wizard.platforms, "program", lambda: ["/usr/bin/doguia-usage"]),
        ]
        for p in patches:
            p.start(); self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def rodar(self, *itens):
        ask = wizard.Ask(read=respostas(*itens), say=lambda *a: self.out.append(" ".join(map(str, a))))
        return wizard.run(self.ctx, ask)

    def test_fluxo_completo(self):
        # aparelho achado: sim; painel 1; animação 3; DeepSeek 20; status line: sim, estilo bars; hooks: sim; início: sim
        self.assertEqual(self.rodar("", "1", "3", "20", "", "1", "", ""), 0)
        cfg = config.load(self.ctx)
        self.assertEqual((cfg["host"], cfg["view"], cfg["claude_style"], cfg["deepseek_budget"]), ("192.168.31.15", 1, 3, 20.0))
        settings = json.loads((self.home / ".claude/settings.json").read_text())
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(settings["statusLine"]["command"], "/usr/bin/doguia-usage statusline --style bars")
        self.assertTrue((self.home / ".claude/settings.json.doguia-bak").exists())
        self.assertEqual(self.installed[0][-1], "run")
        self.assertEqual((self.sent["host"], self.sent["uview"], self.sent["claude_style"]), ("192.168.31.15", 1, 3))

    def test_ip_digitado_e_status_line_de_outro(self):
        (self.home / ".claude/settings.json").write_text(json.dumps({"statusLine": {"type": "command", "command": "meu-script"}}))
        # recusa o achado, digita IP errado e depois o certo; mantém a status line alheia; sem hooks; sem início automático
        self.rodar("n", "1.2.3.4", "10.0.0.9", "", "", "abc", "", "n", "n")
        self.assertEqual(config.load(self.ctx)["host"], "10.0.0.9")
        self.assertEqual(config.load(self.ctx)["deepseek_budget"], 0)
        self.assertFalse((self.home / ".claude/settings.json.doguia-bak").exists())  # nada a gravar
        self.assertEqual(self.installed, [])
        self.assertTrue(any("não respondeu" in l for l in self.out))

    def test_cancelar_no_meio(self):
        self.assertEqual(self.rodar(""), 1)  # acaba a entrada (Ctrl+D) na escolha do painel
        self.assertTrue(any("cancelada" in l for l in self.out))
        self.assertEqual(self.sent, {})

    def test_settings_invalido_nao_e_tocado(self):
        (self.home / ".claude/settings.json").write_text("{ isto não é json")
        self.rodar("", "0", "0", "0", "n")
        self.assertEqual((self.home / ".claude/settings.json").read_text(), "{ isto não é json")
        self.assertTrue(any("Nada foi alterado" in l for l in self.out))


if __name__ == "__main__":
    unittest.main()
