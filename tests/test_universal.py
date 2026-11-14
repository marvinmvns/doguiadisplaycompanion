"""Instalador universal: plataformas, integridade e instalação isolada."""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('universal', ROOT/'packaging/universal.py')
universal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(universal)


class PacoteUniversal(unittest.TestCase):
    def test_recusa_pacote_incompleto(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'Faltam instaladores'):
                universal.montar(Path(tmp), Path(tmp)/'resultado.zip')
            self.assertFalse((Path(tmp)/'resultado.zip').exists())

    def test_bundle_tem_quatro_destinos_e_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            for target, name in universal.TARGETS.items():
                (pasta/name).write_bytes(target.encode())
            out = universal.montar(pasta, pasta/'resultado.zip')
            with ZipFile(out) as z:
                rows = z.read('DoguIA/pacotes.tsv').decode().splitlines()
                self.assertEqual(len(rows), 4)
                for row in rows:
                    target, name, checksum = row.split('\t')
                    self.assertEqual(checksum, hashlib.sha256(z.read('DoguIA/pacotes/'+name)).hexdigest())
                self.assertTrue(z.getinfo('DoguIA/Instalar-DoguIA.command').external_attr >> 16 & 0o111)
                self.assertIn('DoguIA/Instalar-DoguIA.cmd', z.namelist())

    @unittest.skipIf(os.name == 'nt', 'Shell POSIX')
    def test_arquivo_alterado_nao_e_executado(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            (base/'pacotes').mkdir()
            (base/'pacotes/a.tar.gz').write_bytes(b'alterado')
            (base/'pacotes.tsv').write_text('linux-x64\ta.tar.gz\t'+'0'*64+'\n')
            shutil.copy2(ROOT/'packaging/universal/Instalar-DoguIA.command',base/'instalar.command')
            binpath=base/'bin';binpath.mkdir()
            uname=binpath/'uname';uname.write_text('#!/bin/sh\ncase "$1" in -s) echo Linux;; *) echo x86_64;; esac\n');uname.chmod(0o755)
            env=dict(os.environ, PATH=str(binpath)+os.pathsep+os.environ['PATH'])
            r=subprocess.run(['sh',str(base/'instalar.command'),'--verificar'],env=env,capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('incompleto ou alterado',r.stderr)

    @unittest.skipIf(os.name == 'nt', 'Shell POSIX')
    def test_instalacao_e_atualizacao_preservam_configuracao(self):
        with tempfile.TemporaryDirectory(prefix='doguia com espaços ') as tmp:
            base=Path(tmp); origem=base/'origem'; origem.mkdir()
            for name in ('install.sh','uninstall.sh','doguia-usage.desktop'):
                shutil.copy2(ROOT/'packaging/linux'/name,origem/name)
            (origem/'doguia-usage').write_text('#!/bin/sh\necho versao-1\n')
            (origem/'doguia-usage').chmod(0o755)
            (origem/'README.md').write_text('manual')
            fake=base/'ferramentas';fake.mkdir()
            (fake/'systemctl').write_text('#!/bin/sh\nexit 1\n');(fake/'systemctl').chmod(0o755)
            env=dict(os.environ,XDG_BIN_HOME=str(base/'bin com espaços'),XDG_DATA_HOME=str(base/'dados'),DOGUIA_SEM_ASSISTENTE='1',PATH=str(fake)+os.pathsep+os.environ['PATH'])
            env['XDG_CONFIG_HOME']=str(base/'configuracoes')
            config=base/'configuracoes/doguia-usage/config.json';config.parent.mkdir(parents=True);config.write_text('{"host":"192.168.1.2"}')
            for version in (1,2):
                (origem/'doguia-usage').write_text(f'#!/bin/sh\necho versao-{version}\n')
                r=subprocess.run(['sh',str(origem/'install.sh')],env=env,capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
                exe=Path(env['XDG_BIN_HOME'])/'doguia-usage'
                self.assertIn(f'versao-{version}',exe.read_text())
            desktop=(base/'dados/applications/doguia-usage.desktop').read_text()
            self.assertIn(f'Exec="{exe}" painel',desktop)
            self.assertTrue((base/'dados/doguia-usage/uninstall.sh').is_file())
            self.assertEqual(config.read_text(),'{"host":"192.168.1.2"}')
