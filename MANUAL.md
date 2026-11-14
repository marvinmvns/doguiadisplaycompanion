# Manual do DoguIA Companion

Para quem tem um DoguIA Display e quer ver na tela o consumo das ferramentas de IA. A versão com as telas de cada
etapa está em https://www.doguia.com.br/ajuda/display/#ia. Para instalar de outras formas, veja
[`INSTALACAO.md`](INSTALACAO.md); para a referência dos comandos, [`REFERENCIA.md`](REFERENCIA.md).

## O que ele faz

O Companion roda no seu computador e envia ao relógio, a cada 60 segundos, quanto você já usou de Claude Code, Codex,
Antigravity, OpenCode e DeepSeek. Ele também avisa no letreiro quando o Claude Code termina ou espera por você, e traz
um editor para ajustar o Display pelo computador.

- O computador e o relógio precisam estar na mesma rede Wi-Fi. Nada passa pela internet.
- Só saem do computador percentuais, valores e o tempo até renovar. Conversas, código e senhas não são lidos.
- O relógio guarda os números só na memória. Depois de 15 minutos sem envio, o painel de IA sai da tela.
- Com 90% ou mais de uso em alguma janela, o letreiro avisa.

## Antes de começar

- O relógio já está no Wi-Fi da casa e mostrando a hora. Um relógio novo é colocado na rede pelo app DoguIA.
- O computador está na mesma rede do relógio, fora de VPN e de rede de convidados.
- Pelo menos uma das ferramentas de IA já foi usada neste computador.

## Passo 1: instalar

1. Baixe o [instalador universal](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest/download/doguia-instalar-universal.zip)
   e **extraia o ZIP inteiro**.
2. Abra o instalador da pasta extraída:

   | Sistema | O que abrir | Observação |
   |---|---|---|
   | Windows 10/11 | `Instalar-DoguIA.cmd` | Instala só para o seu usuário. O Windows pode pedir confirmação, porque o instalador não tem assinatura comercial |
   | macOS Intel e Apple Silicon | `Instalar-DoguIA.command` | Se o macOS bloquear, botão direito > Abrir. Pede a senha do Mac |
   | Linux x64 | `sh Instalar-DoguIA.command` | Instala só para o seu usuário, sem sudo |

3. No fim, o painel do Companion abre no navegador.

O instalador traz o Python dentro, escolhe o pacote do seu sistema e confere a integridade antes de executar. Não
precisa de internet durante a instalação.

### Links para baixar

O instalador universal serve para todos. Para baixar só o arquivo do seu sistema, estes são os da versão 1.2.0:

| Sistema | Arquivo | Tamanho | Como instalar |
|---|---|---|---|
| Windows, macOS e Linux | [doguia-instalar-universal.zip](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest/download/doguia-instalar-universal.zip) | 51 MB | Extraia e abra **Instalar-DoguIA** |
| Windows 10/11, 64 bits | [doguia-usage-1.2.0-windows-x64-setup.exe](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage-1.2.0-windows-x64-setup.exe) | 22,8 MB | Abra o arquivo |
| macOS Apple Silicon | [doguia-usage-1.2.0-macos-arm64.pkg](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage-1.2.0-macos-arm64.pkg) | 9,3 MB | Botão direito > Abrir |
| macOS Intel | [doguia-usage-1.2.0-macos-x64.pkg](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage-1.2.0-macos-x64.pkg) | 9,9 MB | Botão direito > Abrir |
| Debian, Ubuntu, Mint | [doguia-usage_1.2.0_amd64.deb](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage_1.2.0_amd64.deb) | 9,8 MB | `sudo apt install ./doguia-usage_1.2.0_amd64.deb`, depois `doguia-usage painel` |
| Outros Linux de 64 bits | [doguia-usage-1.2.0-linux-x64.tar.gz](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage-1.2.0-linux-x64.tar.gz) | 9,8 MB | Descompacte e rode `./install.sh` |
| Qualquer sistema com Python 3.9+ | [doguia-usage.pyz](https://github.com/marvinmvns/doguiadisplaycompanion/releases/download/usage-v1.2.0/doguia-usage.pyz) | 137 KB | `python3 doguia-usage.pyz painel`, com o arquivo em uma pasta fixa |

Versões mais novas e o `SHA256SUMS.txt` ficam na [página de downloads](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest).
Linux em ARM e Windows de 32 bits ou ARM não têm instalador: use o `.pyz`.

## Passo 2: configurar no painel

O painel abre no navegador, mas roda só no seu computador (`127.0.0.1`). **Salvar e continuar** leva de uma etapa para
a outra. Para abrir de novo: atalho **Configurar DoguIA Usage** ou `doguia-usage painel`.

| Etapa | O que fazer |
|---|---|
| 1. Conectar | Clique em **Procurar na rede**. Se o relógio não for achado, digite o endereço IP dele, que aparece no app do roteador. **Verificar ambiente** confere se o computador está pronto |
| 2. Ferramentas | Deixe marcadas as IAs que você usa e clique em **Verificar dados disponíveis** |
| 3. Preferências | Escolha o **Painel de consumo** (Barras, Cartões, Foco ou DoguIA animado), o **Indicador do Claude**, o intervalo de envio (10 a 3600 s, padrão 60) e o **Orçamento DeepSeek** |
| 4. Integrar | Clique em **Ativar início automático**. Se usa o Claude Code, escolha o estilo da status line e clique em **Aplicar integração Claude** |
| 5. Conferir | Clique em **Testar conexão e envio**. O letreiro mostra um aviso e o painel de IA aparece no relógio |

"Sem dados disponíveis" na etapa 2 quer dizer que a ferramenta ainda não gravou nada que o Companion consiga ler. Não
quer dizer consumo zero. Sem consumo para mostrar, o teste da etapa 5 envia só o aviso, e ele já confirma a conexão.

## Passo 3: ligar cada IA

| Ferramenta | O que fazer | Na tela |
|---|---|---|
| Claude Code | 1. Na etapa **Integrar**, clique em **Aplicar integração Claude**. 2. Feche e abra o Claude Code. 3. Mande uma mensagem: o rodapé passa a mostrar algo como `5h: 42% \| 7d: 18%` | Janelas de 5 horas e de 7 dias. Só em contas Pro e Max, e só mudam com o Claude Code aberto |
| Codex | Use o Codex neste computador e confira em **Verificar dados disponíveis** | Janelas de 5 horas e de 7 dias |
| Antigravity | Abra e use pelo menos uma vez | O modelo mais usado |
| OpenCode | Use hoje neste computador | Custo do dia, ou tokens se o modelo for gratuito |
| DeepSeek | Informe o **Orçamento DeepSeek** em dólares. Para o saldo oficial, deixe a chave em `DEEPSEEK_API_KEY` no ambiente | Saldo, ou consumo do dia pelo OpenCode |

A integração do Claude Code **substitui a status line existente** e guarda o arquivo anterior em
`settings.json.doguia-bak`, na pasta `.claude` do usuário. Para voltar atrás, feche o Claude Code e recoloque essa
cópia como `settings.json`.

## Passo 4: ver no relógio

O modo da tela é escolhido no app DoguIA, na página do relógio:

- **Automático** (de fábrica): o painel de IA entra na rotação, depois do pet e do relógio.
- **IA**: o painel fica fixo na tela, com a hora em cima.
- **Mostrar o uso de IA no relógio agora**: chama o painel na hora.

| Painel de consumo | O que mostra |
|---|---|
| Barras | Uma linha por ferramenta, com a barra, o percentual e o tempo até renovar |
| Cartões | Blocos em grade, com os números em destaque |
| Foco | A ferramenta de maior consumo em tamanho grande |
| DoguIA animado | O pet no quarto reagindo ao consumo, com o indicador do Claude na parede |

No DoguIA animado, o **Indicador do Claude** tem quatro animações: plasma, gamer, holograma que segue o pet e reator
orbital.

## Avisos do Claude Code no letreiro

| Quando | No relógio |
|---|---|
| O Claude terminou | "Claude terminou em <pasta>", e o pet comemora |
| O Claude espera você | "Claude esperando você em <pasta>" ou "Claude pede permissão em <pasta>", com o letreiro âmbar |
| Você respondeu ou fechou a sessão | O aviso some |

Estilos da status line no rodapé do Claude Code:

| Estilo | Exemplo |
|---|---|
| `compact` | `5h: 42% \| 7d: 18%` |
| `bars` | `Claude 5h [████░░░░░░] 42%` |
| `badge` | `⚡ Claude [5h: 42% · 7d: 18%]` |
| `full` | `Claude 5h: 42% (renova 1h30)` |

Para testar um aviso: `doguia-usage notify --kind info --text "Olá"`.

## Personalizar o Display pelo computador

No alto do painel, **Personalizar Display**:

- **Ajustes do produto**: nome, brilho, tema, local, fuso, alarme visual e letreiro.
- **Estúdio da tela**: a montagem da tela personalizada, com posição e estilo de cada item.
- **Ver estado do Display**: lê o que o relógio informa sobre si.

Edite e clique em **Aplicar alterações ao Display**. Só os campos alterados são enviados, e valores fora da faixa são
recusados antes de chegar ao relógio. O editor é um formulário, sem prévia da tela.

## De onde vem cada número

Nenhum arquivo de login é aberto. No OpenCode, as tabelas de conta e credencial ficam de fora. No Antigravity, o token
de acesso não é lido. A chave do DeepSeek nunca é gravada. Os detalhes de cada fonte estão em
[`REFERENCIA.md`](REFERENCIA.md).

## Terminal

| Comando | Para quê |
|---|---|
| `painel` | Abre o painel no navegador |
| `configurar` | O mesmo assistente em perguntas no terminal |
| `doctor` | Mostra o que foi detectado e se o relógio responde, sem enviar nada |
| `once` | Coleta e envia uma vez |
| `run` | Envia sem parar. É o que o início automático usa |
| `setup` | Acha o relógio e salva o endereço. Aceita `--host`, `--view`, `--claude-style` e `--deepseek-budget` |
| `install` / `uninstall` | Liga ou desliga o início automático |
| `notify` | Manda um aviso ao letreiro |

Se o roteador trocar o endereço do relógio, o programa procura de novo sozinho depois de três envios sem resposta.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| O painel de IA do relógio está vazio ou sumiu | Na etapa **Conferir**, clique em **Testar conexão e envio**. Confira na etapa **Integrar** se o início automático está ativado |
| O Companion não acha o relógio | Confira se os dois estão na mesma rede, sem VPN, rede de convidados ou isolamento no roteador. Depois digite o IP na etapa **Conectar** |
| Uma IA aparece como "sem dados disponíveis" | Use a ferramenta uma vez neste computador e verifique de novo |
| Os limites do Claude não aparecem | Só existem em contas Pro e Max, com o Claude Code aberto e a integração aplicada |
| O painel não abre no navegador | Rode `doguia-usage painel` e copie o endereço `127.0.0.1` que ele mostra |

## Atualizar e remover

Para atualizar, baixe o instalador novo e repita o passo 1. A configuração fica preservada.

Para remover:

1. Na etapa **Integrar**, clique em **Desativar início automático** (ou `doguia-usage uninstall`).
2. Se aplicou a integração do Claude Code, feche o Claude e recoloque `settings.json.doguia-bak` como `settings.json`.
3. Desinstale: atalho **Desinstalar** no menu Iniciar do Windows, desinstalador da pasta DoguIA Usage no macOS, ou
   `~/.local/share/doguia-usage/uninstall.sh` no Linux.
