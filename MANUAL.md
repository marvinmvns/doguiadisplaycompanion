# Manual do doguia-usage

Para quem tem um DoguIA Display e quer ver na tela o consumo das ferramentas de IA. A versão com imagens está em
https://www.doguia.com.br/ajuda/display/#ia. Para desenvolver ou empacotar o programa, veja o [`README.md`](README.md).

## O que ele faz

O `doguia-usage` roda no seu computador e envia ao relógio, a cada 60 segundos, quanto você já usou de Claude Code,
Codex, Antigravity, OpenCode e DeepSeek. Ele também avisa no letreiro quando o Claude Code termina ou espera por você.

- O computador e o relógio precisam estar na mesma rede Wi-Fi. Nada passa pela internet.
- Só saem do computador percentuais, valores e o tempo até renovar. Conversas, código e senhas não são lidos.
- O relógio guarda os números só na memória. Depois de 15 minutos sem envio, o painel sai da tela.
- Com 90% ou mais de uso em alguma janela, o letreiro avisa.

## Instalar

Há dois caminhos. Os dois terminam no mesmo assistente.

**Instalador do seu sistema** (traz o Python dentro), na release `usage-v*`:

| Sistema | Arquivo | Como instalar |
|---|---|---|
| Windows 10/11 | `doguia-usage-<v>-windows-x64-setup.exe` | Abra o arquivo. Instala só para o seu usuário, sem administrador |
| macOS (Apple Silicon) | `doguia-usage-<v>-macos-arm64.pkg` | Botão direito > Abrir, porque não tem assinatura da Apple |
| Debian, Ubuntu, Mint | `doguia-usage_<v>_amd64.deb` | `sudo apt install ./doguia-usage_<v>_amd64.deb`, depois `doguia-usage configurar` |
| Outros Linux | `doguia-usage-<v>-linux-x64.tar.gz` | Descompacte e rode `./install.sh` |

**Arquivo único `doguia-usage.pyz`** (25 KB, precisa do Python 3.9 ou mais novo), publicado em
https://www.doguia.com.br/ajuda/display/baixar/doguia-usage.pyz:

1. Guarde o arquivo numa pasta fixa: `C:\DoguIA` no Windows, `~/doguia` no macOS e no Linux.
2. Abra o assistente: `py C:\DoguIA\doguia-usage.pyz configurar` no Windows, ou
   `python3 ~/doguia/doguia-usage.pyz configurar` no macOS e no Linux.

Não mova o `.pyz` depois de configurar: o início automático e o Claude Code guardam o caminho dele. Se mudar de
pasta, rode `configurar` de novo. Com o `.pyz`, leia `doguia-usage` nos comandos abaixo como o comando completo acima.

## O assistente

    doguia-usage configurar

Em cada pergunta, a resposta entre colchetes ou em maiúscula é a sugerida: basta apertar Enter. Ctrl+C cancela sem
desfazer o que já foi salvo, e você pode rodar de novo quando quiser.

| Passo | O que acontece |
|---|---|
| 1. Aparelho | Procura o relógio na rede (até 15 s). Se não achar, pede o IP, que aparece no app do roteador |
| 2. Tela de consumo | Você escolhe o estilo do painel e a animação do indicador do Claude |
| 3. Ferramentas de IA | Mostra o que foi encontrado neste computador e pergunta o crédito do DeepSeek, em dólares |
| 4. Claude Code | Liga a status line (de onde vêm os limites) e os avisos no letreiro |
| 5. Início automático | O envio passa a começar junto com o computador, sem janela e sem administrador |
| 6. Teste | Envia uma vez. O painel aparece no relógio e o letreiro mostra "DoguIA Usage configurado" |

## Estilos do painel

| `--view` | Estilo | O que mostra |
|---|---|---|
| 0 | Barras | Uma linha por ferramenta, com a barra, o percentual e o tempo até renovar |
| 1 | Cartões | Blocos em grade, com os números em destaque |
| 2 | Destaque | A ferramenta de maior consumo em tamanho grande |
| 3 | DoguIA animado | O pet no quarto reagindo ao consumo, com o indicador do Claude na parede |

No estilo 3, `--claude-style` escolhe a animação: 0 plasma, 1 barra gamer, 2 holograma que segue o pet, 3 reator
orbital.

    doguia-usage setup --view 3 --claude-style 2

Também dá para trocar pelo app DoguIA, em Ajustes > Uso de IA, na página do relógio. Para ver o painel o tempo todo,
escolha o modo de tela IA no app.

## Claude Code

O assistente mexe só nas chaves `statusLine` e `hooks` de `~/.claude/settings.json` e guarda o arquivo anterior em
`settings.json.doguia-bak`. Uma status line de outro programa só é trocada se você confirmar.

**Limites.** O Claude Code informa as janelas de 5 horas e de 7 dias pela status line. Só contas Pro e Max recebem
esses limites, e os números só mudam enquanto o Claude Code está aberto.

| `--style` | No rodapé do Claude Code |
|---|---|
| `compact` | `5h: 42% \| 7d: 18%` |
| `bars` | `Claude 5h [████░░░░░░] 42%` |
| `badge` | `⚡ Claude [5h: 42% · 7d: 18%]` |
| `full` | `Claude 5h: 42% (renova 1h30)` |

**Avisos no letreiro** (firmware 1.1.7 ou mais nova):

| Quando | No relógio |
|---|---|
| O Claude terminou | "Claude terminou em <pasta>", e o pet comemora |
| O Claude espera você | "Claude esperando você em <pasta>" ou "Claude pede permissão em <pasta>", com o letreiro âmbar |
| Você respondeu ou fechou a sessão | O aviso some |

Para testar: `doguia-usage notify --kind info --text "Olá"`. Para configurar à mão, veja o [`README.md`](README.md).

## De onde vem cada número

| Ferramenta | De onde vem | Na tela |
|---|---|---|
| Claude Code | Limites que o próprio Claude Code informa pela status line | Janelas de 5 horas e de 7 dias |
| Codex | Limites gravados nas sessões, em `~/.codex/sessions` | Janelas de 5 horas e de 7 dias |
| Antigravity | O estado de uso guardado pelo programa | O modelo mais usado |
| OpenCode | As mensagens de hoje no banco local | Custo do dia, ou tokens se for gratuito |
| DeepSeek | O saldo oficial, com `DEEPSEEK_API_KEY` no ambiente, ou o uso pelo OpenCode | Saldo, ou consumo do dia |

Nenhum arquivo de login é aberto. No OpenCode, as tabelas de conta e credencial ficam de fora. No Antigravity, o token
de acesso não é lido. A chave do DeepSeek nunca é gravada.

## Comandos

| Comando | Para quê |
|---|---|
| `configurar` | Abre o assistente |
| `doctor` | Mostra o que foi detectado e se o relógio responde, sem enviar nada |
| `once` | Coleta e envia uma vez |
| `run` | Envia sem parar, a cada 60 segundos. É o que o início automático usa |
| `setup` | Acha o relógio e salva o IP. Aceita `--host`, `--view`, `--claude-style` e `--deepseek-budget` |
| `install` / `uninstall` | Liga ou desliga o início automático |
| `statusline` | Usado pelo Claude Code. Aceita `--style` |
| `notify` | Usado pelos avisos do Claude Code, ou à mão com `--kind` e `--text` |

Se o roteador trocar o IP do relógio, o programa procura de novo sozinho depois de três envios sem resposta.

## Onde ficam os arquivos

| Sistema | Configuração | Início automático |
|---|---|---|
| Windows | `%APPDATA%\doguia-usage` | Chave Run do usuário |
| macOS | `~/Library/Application Support/doguia-usage` | Agente em `~/Library/LaunchAgents` |
| Linux | `~/.config/doguia-usage` | Serviço de usuário do systemd, `doguia-usage.service` |

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| O painel de IA está vazio ou sumiu | Rode `doguia-usage doctor` e depois `doguia-usage once`. O relógio esquece os números ao reiniciar |
| O programa não acha o relógio | Confira se os dois estão na mesma rede, fora de rede de convidados e de VPN. Depois: `doguia-usage setup --host 192.168.x.x` |
| Os limites do Claude não aparecem | Só existem em contas Pro e Max, com o Claude Code aberto e a status line do DoguIA ligada |
| Mudei o `.pyz` de pasta e parou | Rode `configurar` de novo no lugar novo |

## Remover

1. `doguia-usage uninstall` desliga o início automático.
2. Restaure `settings.json.doguia-bak`, ou apague as entradas que citam `doguia-usage` em `~/.claude/settings.json`.
3. Apague o programa e a pasta de configuração.
