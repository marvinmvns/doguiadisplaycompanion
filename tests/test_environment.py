"""Preparação sem dependências e diagnóstico com diretórios isolados."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from doguia_usage.environment import verificar
from doguia_usage.model import Ctx


class Ambiente(unittest.TestCase):
    def test_linux_sem_systemd_nao_impede_painel(self):
        with tempfile.TemporaryDirectory() as tmp, patch('doguia_usage.environment.shutil.which', return_value=None):
            report = verificar(Ctx(home=Path(tmp), env={}, platform='linux'))
            self.assertTrue(report['pronto'])
            self.assertFalse(report['itens'][-1]['ok'])
            self.assertTrue(report['itens'][-1]['opcional'])

    def test_pasta_sem_permissao_indica_como_resolver(self):
        with tempfile.TemporaryDirectory() as tmp, patch('doguia_usage.environment.tempfile.TemporaryFile', side_effect=PermissionError):
            report = verificar(Ctx(home=Path(tmp), env={}, platform='darwin'))
            self.assertFalse(report['pronto'])
            self.assertIn('permissões', report['itens'][1]['ajuda'])

    def test_iniciador_produz_copia_portatil_com_assets(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('iniciar', root/'iniciar.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            archive = module.preparar(root, Path(tmp)/'pasta com espaços')
            with ZipFile(archive) as z:
                for item in ['logo.svg','display.webp','inter.woff2','funnel-display.woff2']:
                    self.assertTrue(z.read('doguia_usage/web/'+item))
            result = subprocess.run([sys.executable,str(archive),'painel','--help'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('sem-navegador', result.stdout)
