# doguia-usage

Mostra no DoguIA Display o consumo de Claude Code, Codex, Antigravity (agy), OpenCode e DeepSeek. Roda no computador,
em Windows, Linux ou macOS, e envia só percentuais, valores e tempo de renovação para o aparelho. A conexão é por IP
na rede local: o aparelho não tem BLE.

## Instalar

Baixe o instalador do seu sistema na release `usage-v*` mais recente. Todos trazem o Python dentro: não é preciso instalar
mais nada. No fim, o instalador abre o assistente de configuração.

| Sistema | Arquivo | Observação |
|---|---|---|
| Windows 10/11 | `doguia-usage-<v>-windows-x64-setup.exe` | Instala só para o usuário, sem administrador, e põe o comando no PATH. Atalhos no menu Iniciar: Configurar, Diagnóstico e Desinstalar |
| macOS (Apple Silicon) | `doguia-usage-<v>-macos-arm64.pkg` | Sem assinatura da Apple: botão direito > Abrir. Instala `/usr/local/bin/doguia-usage` e a pasta `Aplicativos/DoguIA Usage` |
| Debian, Ubuntu, Mint | `doguia-usage_<v>_amd64.deb` | `sudo apt install ./doguia-usage_<v>_amd64.deb`, depois `doguia-usage configurar` com o seu usuário |
| Outros Linux | `doguia-usage-<v>-linux-x64.tar.gz` | Descompacte e rode `./install.sh` (vai para `~/.local/bin`, sem sudo). `./uninstall.sh` remove |
| Qualquer sistema com Python 3.9+ | `doguia-usage.pyz` | `python doguia-usage.pyz configurar` |
| Com `uv` ou `pipx` | | `uv tool install .` ou `pipx install .` |

Macs Intel: use o `.pyz` (precisa do Python 3.9 ou mais novo).

## Assistente de configuração

    doguia-usage configurar

Abre também ao rodar o programa sem argumentos num terminal (duplo clique no Windows) e no fim dos instaladores. Em seis
passos:

1. acha o display na rede, ou pede o IP;
2. escolhe o estilo do painel e a animação do indicador do Claude;
3. mostra as IAs detectadas neste computador e o crédito do DeepSeek;
4. configura o Claude Code: status line (de onde vêm os limites) e hooks dos avisos no letreiro. Mexe só nessas
   chaves do `~/.claude/settings.json` e guarda o anterior em `settings.json.doguia-bak`. Uma status line de outro
   programa só é trocada se você confirmar;
5. liga o início automático;
6. envia uma vez para testar.

Pode rodar de novo quando quiser: não duplica os hooks.

## Usar sem o assistente

    doguia-usage setup       # acha o aparelho na rede e salva o IP
    doguia-usage doctor      # mostra o que foi detectado, sem enviar nada
    doguia-usage once        # coleta e envia uma vez
    doguia-usage install     # liga o início automático

Também é possível escolher o estilo visual no display com `--view` (`0` barras, `1` cartões em grade, `2` foco no maior consumo):

    doguia-usage once --view 1
    doguia-usage setup --view 2

`setup` tenta `doguiadisplay.local` e depois procura na rede local. Se não achar, use `setup --host 192.168.x.x`.
Se o roteador trocar o IP do aparelho, o programa procura de novo sozinho depois de 3 falhas.

Para remover: `doguia-usage uninstall`.

## De onde vem cada dado

| Ferramenta | Fonte | Na tela |
|---|---|---|
| Claude Code | `rate_limits` da status line ou ponte ai-dev-meter | Janelas de 5 h e 7 dias |
| Codex | `rate_limits` nas sessões de `~/.codex/sessions` | Janelas de 5 h e 7 dias |
| Antigravity | `userStatus` em `state.vscdb` | Modelo mais usado |
| OpenCode | Mensagens de hoje em `opencode.db` | Custo do dia, ou tokens se for grátis |
| DeepSeek | Saldo oficial com `DEEPSEEK_API_KEY`, ou OpenCode | Saldo, ou consumo do dia |

Nenhum coletor abre arquivo de login. O OpenCode é lido sem tocar nas tabelas `account` e `credential`, e o Antigravity
sem a chave `oauthToken`. A chave do DeepSeek só existe no ambiente e nunca é gravada.

### Claude Code

Coloque em `~/.claude/settings.json`:

    {"statusLine": {"type": "command", "command": "doguia-usage statusline"}}

O Claude Code só envia os limites nas contas Pro e Max, e os números só atualizam enquanto ele está aberto. Sem a status
line, o programa usa a ponte ai-dev-meter, um programa à parte e opcional, se ela estiver rodando no mesmo PC.

### Avisos do Claude Code no letreiro

`doguia-usage notify` lê o evento de um hook do Claude Code e avisa o aparelho (firmware 1.1.7 ou mais nova):

| Evento | Na tela |
|---|---|
| `Stop` | "Claude terminou em <pasta>", e o pet comemora |
| `Notification` | "Claude esperando você em <pasta>" ou "Claude pede permissão em <pasta>", com o letreiro âmbar e o pet chamando |
| `UserPromptSubmit`, `SessionEnd` | Apaga o aviso |

Coloque em `~/.claude/settings.json`, um bloco por evento (`Stop`, `Notification`, `UserPromptSubmit`, `SessionEnd`):

    {"hooks": {"Stop": [{"hooks": [{"type": "command", "timeout": 5,
      "command": "doguia-usage notify --host 192.168.x.x"}]}]}}

Repita `--host` para avisar mais de um aparelho. Sem `--host`, usa o IP salvo pelo `setup`. O comando não imprime nada
e nunca falha: no `UserPromptSubmit` a saída iria para o contexto do Claude, e um aparelho desligado não pode travar o
Claude Code. Para testar sem hook: `doguia-usage notify --kind info --text "Olá"`.

### DeepSeek

O DeepSeek cobra por uso e não tem janela de limite. Para ver uma barra, informe quanto colocou de crédito:

    doguia-usage setup --deepseek-budget 20

## Gerar os pacotes

    python packaging/build.py              # dist/doguia-usage.pyz
    python packaging/build.py --binary     # também o executável deste sistema, em build/bin
    python packaging/build.py --installer  # também o instalador deste sistema, em dist/
    python -m unittest discover -s tests

Precisa do PyInstaller; no Windows também do Inno Setup 6 (`choco install innosetup`), e no macOS do `pkgbuild` (vem
com o sistema). O PyInstaller não compila para outro sistema: o workflow `.github/workflows/companion.yml` gera os
instaladores de Windows, Linux e macOS ao criar uma tag `usage-v1.1.0`, instala cada um no próprio runner para testar e
publica a release com `SHA256SUMS.txt`. Os scripts de cada instalador ficam em `packaging/linux`, `packaging/macos` e
`packaging/windows`.

No Windows, o início automático usa `doguia-usage-bg.exe`, uma cópia sem janela de console, e grava o que aconteceria
no console em `%APPDATA%\doguia-usage\run.log`. Só um `doguia-usage run` envia por vez (trava em `run.lock`).

## Organização

    doguia_usage/providers/<ferramenta>/   um coletor por pasta
    doguia_usage/platforms/                início automático de cada sistema
    doguia_usage/device.py                 descoberta e envio por HTTP
    doguia_usage/wizard.py                 assistente de configuração
    packaging/                             pacote .pyz, executável e instaladores

## Painel visual e editor do Display

Execute `doguia-usage painel` para abrir a configuração guiada e o editor de ajustes e composição de tela. Instalação em Windows, macOS e Linux, uso e empacotamento estão em [INSTALACAO.md](INSTALACAO.md).

Para abrir a partir do código sem pip ou bibliotecas extras, use `py -3 iniciar.py` (Windows) ou `python3 iniciar.py` (macOS/Linux). O iniciador cria uma cópia portátil estável, abre o painel e preserva os ajustes. Os instaladores nativos já incluem Python.

## Instalar com um único pacote

O fluxo recomendado é o ZIP `doguia-instalar-universal.zip`: extraia e abra **Instalar DoguIA**. Ele detecta Windows/macOS/Linux, confere a integridade e usa o instalador nativo incluído. Não precisa de Python ou internet durante a instalação. Veja a cobertura e os comandos em [INSTALACAO.md](INSTALACAO.md). O CI monta esse ZIP somente quando os quatro instaladores estiverem disponíveis.
