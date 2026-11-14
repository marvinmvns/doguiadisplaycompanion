#!/usr/bin/env python3
"""Monta o ZIP offline universal apenas quando todos os instaladores estiverem presentes."""
import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT/'doguia_usage/__init__.py').read_text()).group(1)
TARGETS = {'linux-x64':f'doguia-usage-{VERSION}-linux-x64.tar.gz',
           'windows-x64':f'doguia-usage-{VERSION}-windows-x64-setup.exe',
           'macos-arm64':f'doguia-usage-{VERSION}-macos-arm64.pkg',
           'macos-x64':f'doguia-usage-{VERSION}-macos-x64.pkg'}


def montar(origem, saida, targets=None):
    targets = targets or list(TARGETS)
    faltam = [TARGETS[t] for t in targets if not (origem/TARGETS[t]).is_file()]
    if faltam:
        raise ValueError('Faltam instaladores nativos: ' + ', '.join(faltam))
    saida.parent.mkdir(parents=True, exist_ok=True)
    manifesto = []
    with ZipFile(saida, 'w', ZIP_DEFLATED) as pacote:
        for target in targets:
            arquivo = origem/TARGETS[target]
            digest = hashlib.sha256(arquivo.read_bytes()).hexdigest()
            manifesto.append(f'{target}\t{arquivo.name}\t{digest}\n')
            pacote.write(arquivo, 'DoguIA/pacotes/'+arquivo.name)
        for arquivo in (ROOT/'packaging/universal').iterdir():
            if arquivo.is_file():
                info = ZipInfo('DoguIA/'+arquivo.name)
                info.create_system = 3
                info.external_attr = (0o100755 if arquivo.suffix == '.command' else 0o100644) << 16
                info.compress_type = ZIP_DEFLATED
                pacote.writestr(info, arquivo.read_bytes())
        pacote.writestr('DoguIA/pacotes.tsv', ''.join(manifesto))
        pacote.write(ROOT/'INSTALACAO.md', 'DoguIA/INSTALACAO.md')
    return saida


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'dist')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--target', choices=list(TARGETS), help='Gera pacote local de teste, sem chamá-lo universal')
    args = parser.parse_args()
    nome = f'doguia-instalar-{VERSION}-' + (f'teste-{args.target}' if args.target else 'universal') + '.zip'
    try:
        print(montar(args.input, args.output or ROOT/'dist'/nome, [args.target] if args.target else None))
    except ValueError as exc:
        parser.error(str(exc))
