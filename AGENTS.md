# DoguIA Display Companion

Repositório independente do companion. Código, interface e documentação em português.
Python >= 3.9, somente biblioteca padrão em execução; não ler credenciais das ferramentas.

- Testes: `python -m unittest discover -s tests`.
- Painel: `python -m doguia_usage painel`.
- Pacote: `python packaging/build.py`; nativos: `--installer`.
- Universal: `python packaging/universal.py --input <pasta>`; exige quatro instaladores.
- CI constrói e testa Windows x64, Linux x64, macOS Intel/ARM. Tags `usage-v*` publicam releases.
- Assets visuais e fontes são locais, com origens e licenças em `doguia_usage/web/ASSETS.md`.
- Firmware e OTA pertencem a https://github.com/marvinmvns/doguiadisplay ; não gravar aparelhos como parte de builds do companion.
