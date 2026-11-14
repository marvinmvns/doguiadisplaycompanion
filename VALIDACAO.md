# Validação da versão 1.2.0

Companion segregado em https://github.com/marvinmvns/doguiadisplaycompanion, sem dependência de checkout do firmware.

## Build e publicação

[Execução da release usage-v1.2.0](https://github.com/marvinmvns/doguiadisplaycompanion/actions/runs/43543329272).

| Plataforma | Testes Python | Instalador construído | Aplicativo instalado e painel HTTP | Iniciador universal |
|---|---|---|---|---|
| Ubuntu 22.04 x64 | Passou | `.deb`, `.tar.gz`, `.pyz` | Passou | Passou |
| Windows x64 | Passou | `.exe` | Passou | Passou |
| macOS Apple Silicon | Passou | `.pkg` | Passou | Passou |
| macOS Intel | Passou | `.pkg` | Passou | Passou |

O job universal reuniu os quatro instaladores, conferiu o ZIP e passou. O pipeline publica o ZIP universal, instaladores individuais, `.pyz` e manifesto SHA-256 na release, somente após essas verificações.

## Conferências locais

- 54 testes Python passaram no repositório independente.
- Wizard e editor conferidos no Chrome em desktop e 390 px: cinco etapas, diagnóstico do ambiente, leitura/aplicação de ajustes simulados, busca, campos de leitura bloqueados e ausência de overflow horizontal.
- Instalação e atualização reais do ZIP Linux em diretórios isolados, inclusive caminhos com espaços. Atalho, desinstalador e painel instalado conferidos.
- Fontes, logo, foto do Display, scripts, estilos e schemas presentes nos pacotes e servidos sem depender de internet.
- Valores inválidos e pacote adulterado são recusados antes de aplicar alterações.

## Limites

A comunicação e edição do Display foram testadas com simulação HTTP. O aparelho conhecido em `192.168.31.15` não estava acessível na bancada; essa validação física não é substituída pelos testes de instalação.

Os testes de Windows/macOS ocorreram nos runners nativos do GitHub Actions. A interface foi conferida visualmente no Chrome Linux; não houve inspeção visual manual de cada instalador em computadores pessoais. Os pacotes não têm assinatura comercial Microsoft/Apple.

O repositório não grava firmware nem publica OTA. Firmware e conversão do relógio permanecem em [doguiadisplay](https://github.com/marvinmvns/doguiadisplay).
