# Builds e publicação

Este repositório é independente do firmware. A raiz contém o pacote Python, frontend local, testes, instaladores e documentação de download. Não precisa clonar o repositório do Display para construir.

## Local

Python 3.9+ para testes e `.pyz`:

```sh
python -m unittest discover -s tests
python packaging/build.py
python packaging/smoke.py dist/doguia-usage.pyz
```

Instalador do sistema atual: instale `pyinstaller==6.15.0` e execute `python packaging/build.py --installer`. Windows também requer Inno Setup 6; macOS usa `pkgbuild`; Linux usa `dpkg-deb` para o `.deb`. Os pacotes nativos precisam ser construídos no sistema correspondente.

## GitHub Actions

O workflow `companion.yml` executa em pushes de `main`, pull requests, manualmente e tags `usage-v*`:

1. Testa o código em Linux, Windows, macOS Apple Silicon e macOS Intel.
2. Gera instaladores nativos, confere o iniciador universal e testa o aplicativo instalado.
3. Junta os quatro instaladores em `doguia-instalar-universal.zip`. Recusa uma plataforma ausente.
4. Em tags, publica todos os instaladores, o ZIP universal, `.pyz` e `SHA256SUMS.txt` na release.

Nos pushes sem tag, os pacotes ficam nos artefatos de Actions. Publicação ocorre somente após a matriz e o pacote universal passarem.

## Nova versão

1. Atualize a mesma versão em `doguia_usage/__init__.py` e `pyproject.toml`.
2. Atualize documentação e valide os testes.
3. Envie o commit para `main` e crie uma tag correspondente, por exemplo `usage-v1.2.0`.
4. Envie a tag e acompanhe Actions até a publicação da release.

Os links de `DOWNLOAD.md` usam `/releases/latest` e acompanham automaticamente a release estável. O firmware tem numeração e pipeline separados.
