# DoguIA Display no computador

[Baixar o instalador universal](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest/download/doguia-instalar-universal.zip) · [Todos os downloads](DOWNLOAD.md)

O companion reúne consumo de IA, configuração guiada e edição do Display. Funciona em Windows, macOS e Linux, com Python 3.9 ou superior ou com os instaladores que incluem Python. O painel abre no navegador padrão e funciona localmente; o computador e o Display precisam estar na mesma rede Wi-Fi.

## Instalação universal recomendada

O ZIP `doguia-instalar-universal.zip` reúne os instaladores nativos e escolhe automaticamente o correto. Não precisa de Python instalado nem de internet durante a instalação.

1. Baixe o ZIP universal da release `usage-v*` e **extraia tudo**.
2. Windows: abra `Instalar-DoguIA.cmd`. macOS: abra `Instalar-DoguIA.command`. Linux: execute `sh Instalar-DoguIA.command` na pasta extraída.
3. Conclua o instalador e siga o assistente no navegador para conectar seu Display.

Cobertura: Windows 10/11 x64, macOS Intel e Apple Silicon, Linux x64 com glibc compatível. Linux ARM/musl e Windows ARM/32 bits não estão incluídos: o iniciador informa quando não houver pacote compatível, sem tentar executar outro binário. O macOS pede autorização administrativa pelo instalador nativo; Windows e Linux instalam por usuário.

Os instaladores levam o Python e os assets. O iniciador confere SHA-256 antes de executar, detectando corrupção do arquivo. Baixe sempre dos canais oficiais: checksum incluído no mesmo ZIP não substitui a autenticidade da origem.

Atualizar é repetir o mesmo processo com o ZIP novo. A configuração fica preservada. O Linux mantém o desinstalador em `$XDG_DATA_HOME/doguia-usage/uninstall.sh` ou `~/.local/share/doguia-usage/uninstall.sh`.

Para conferir o pacote sem instalar: `sh Instalar-DoguIA.command --verificar`, ou `powershell -File Instalar-DoguIA.ps1 -Verificar` no Windows. `--sem-abrir` (Windows: `-SemAbrir`) instala sem abrir o painel, para testes automatizados.

### Gerar o ZIP universal

O workflow `companion` constrói e testa cada instalador em seu sistema, inclui macOS Intel e Apple Silicon e monta o ZIP no job `universal`. A montagem falha se faltar qualquer plataforma. Na execução manual, o ZIP aparece como artefato `doguia-universal`; nas tags `usage-v*`, vai para a release.

Também é possível juntar os quatro instaladores em uma pasta e executar:

```sh
python3 packaging/universal.py --input /pasta/dos/instaladores
```

Para testar apenas a plataforma local: `python3 packaging/universal.py --target linux-x64`. Esse arquivo recebe o sufixo **teste-linux-x64** e não deve ser distribuído como universal. A versão completa só existe após a construção dos quatro pacotes nativos. Nenhuma release nova é publicada automaticamente pela edição do código.

## Abrir sem instalar bibliotecas

Com Python 3.9 ou mais novo, abra `Iniciar-DoguIA.cmd` no Windows ou execute `./Iniciar-DoguIA.command` no macOS/Linux. Também funciona `python3 iniciar.py` (Windows: `py -3 iniciar.py`). O iniciador prepara um `.pyz` com tudo incluído e abre o navegador. Não usa pip, setuptools, venv, Node ou downloads de dependências.

A cópia portátil fica em `%LOCALAPPDATA%\DoguIA Companion` no Windows, `~/Library/Application Support/DoguIA Companion` no macOS e `$XDG_DATA_HOME/doguia-companion` (ou `~/.local/share/doguia-companion`) no Linux. As integrações passam a usar esse caminho estável. Rodar o iniciador novamente atualiza a cópia e preserva a configuração do usuário.

Se Python não estiver instalado, use o instalador nativo com Python incluído. Para executar a partir do código, o iniciador informa o endereço oficial de instalação do Python. Ele não pede bibliotecas adicionais.

Na etapa Conectar, **Verificar ambiente** confere a versão do Python, acesso à configuração e disponibilidade do início automático. Uma sessão Linux sem systemd permite usar o painel e enviar com `doguia-usage run`; a verificação explica a pendência do serviço.

O logo, a foto do Display e as fontes da marca estão no pacote. A interface abre sem internet; só os links de ajuda e do site dependem de internet. A comunicação com o Display exige a rede local.

## Instalar a partir do código

Na raiz deste repositório, execute:

| Sistema | Instalar | Abrir o painel |
|---|---|---|
| Windows 10/11 | `py -m pip install .` | `doguia-usage painel` |
| macOS | `python3 -m venv .venv` e `.venv/bin/python -m pip install .` | `.venv/bin/doguia-usage painel` |
| Linux | `python3 -m venv .venv` e `.venv/bin/python -m pip install .` | `.venv/bin/doguia-usage painel` |

No Windows, se a pasta Scripts do Python não estiver no PATH, use `py -m doguia_usage painel`. No macOS ou Linux, use `.venv/bin/python -m doguia_usage painel`. No Linux, o pacote `python3-venv` pode ser necessário.

## Arquivo portátil

Gere com `python3 packaging/build.py`. O resultado é `dist/doguia-usage.pyz`, com a interface, schemas e imagem incluídos. Guarde-o em uma pasta fixa antes de ativar integrações e início automático.

- Windows: `py C:\DoguIA\doguia-usage.pyz painel`
- macOS e Linux: `python3 ~/doguia/doguia-usage.pyz painel`

O arquivo usa somente a biblioteca padrão do Python. Não precisa de Node, Electron nem conexão com serviços externos para abrir a interface. O navegador deve ser uma versão atual do Chrome, Edge, Firefox ou Safari.

## Instaladores com Python incluído

`python3 packaging/build.py --installer` gera o instalador do sistema em que o comando roda. Instale PyInstaller no ambiente de construção. Windows também exige Inno Setup 6; macOS usa `pkgbuild`; Linux usa `dpkg-deb` para o pacote Debian. O workflow `.github/workflows/companion.yml` contém a matriz de construção por sistema. Executáveis de outros sistemas precisam ser construídos nos respectivos sistemas.

Os atalhos “Configurar DoguIA Usage” abrem o painel visual. A instalação pelo terminal e o assistente `doguia-usage configurar` continuam disponíveis. No pacote Linux portátil, o script `install.sh` também abre o painel quando executado em um terminal. Para instalar sem abrir o assistente, defina `DOGUIA_SEM_ASSISTENTE=1`.

## Configuração em cinco passos

1. **Conectar:** informe o IP do Display ou clique em Procurar na rede. Para um aparelho novo, configure primeiro a Wi-Fi pelo portal do próprio Display.
2. **Ferramentas:** selecione Claude Code, Codex, Antigravity, OpenCode e DeepSeek e verifique os dados disponíveis. “Sem dados” significa que a ferramenta ainda não produziu dados locais compatíveis; não é uma confirmação de consumo zero.
3. **Preferências:** escolha painel, animação, intervalo de 10 a 3600 segundos, orçamento DeepSeek e, se usar, endereço da ponte ai-dev-meter.
4. **Integrar:** ative o início automático. Opcionalmente, aplique status line e hooks do Claude. A operação substitui a status line existente e cria uma cópia `.doguia-bak` do settings.json anterior. Para restaurar, feche o Claude e recoloque o backup como settings.json.
5. **Conferir:** clique em Testar conexão e envio. Confira o aviso no letreiro e os dados no Display. Sem consumo disponível, apenas o aviso é enviado.

Fechar o painel encerra apenas a interface quando seu processo é encerrado. O serviço configurado para início automático é independente. Para enviar imediatamente em primeiro plano, use `doguia-usage run`; Ctrl+C encerra esse processo. Para desligar o serviço, use o botão do painel ou `doguia-usage uninstall`.

## Editar o Display como produto

Abra **Personalizar Display**. Salve o endereço no assistente antes de ler o aparelho.

- **Ajustes do produto:** nome, responsável, brilho, tema, localização, fuso, alarme e opções do letreiro, com os limites e descrições da API.
- **Estúdio da tela:** posições, visibilidade, estilos, pet, relógio, clima, tokens, notícias, texto e objetos da composição 240 × 240.
- **Ver estado:** lê o estado atual do aparelho para diagnóstico.

Busque um ajuste pelo nome ou descrição, edite e clique em **Aplicar alterações ao Display**. Campos de leitura aparecem desativados. O painel recusa valores fora das faixas, opções inválidas e textos longos antes de acessar o aparelho. Só os campos alterados são enviados; os ajustes são relidos após a gravação. A API aplica a montagem Custom imediatamente, conforme a versão do firmware. Os campos usam os nomes da API para permitir acesso a todas as opções documentadas. O editor é um formulário; não representa uma prévia exata da tela.

O painel não grava firmware nem apaga o LittleFS. A transformação de um relógio de fábrica em Display fica no aplicativo separado no [repositório do firmware](https://github.com/marvinmvns/doguiadisplay/tree/main/installer).

## Onde ficam os ajustes

| Sistema | Pasta |
|---|---|
| Windows | `%APPDATA%\doguia-usage` |
| macOS | `~/Library/Application Support/doguia-usage` |
| Linux | `$XDG_CONFIG_HOME/doguia-usage` ou `~/.config/doguia-usage` |

O painel escuta apenas em `127.0.0.1`, em uma porta livre, e protege operações com um token de sessão. Para escolher porta: `doguia-usage painel --port 8765`. Para abrir o navegador manualmente: acrescente `--sem-navegador`. Encerre o painel com Ctrl+C no terminal.

## Resolver problemas

- **Display sem resposta:** confirme IP, Wi-Fi e ausência de isolamento de clientes no roteador. VPN pode impedir acesso à rede local. A descoberta usa mDNS e a sub-rede /24; informe o IP quando necessário.
- **Consumo ausente:** execute `doguia-usage doctor`. Use a ferramenta de IA e verifique novamente. As fontes e limitações estão no README. Coletores não leem arquivos de login ou credenciais.
- **Página não abre:** copie o endereço impresso no terminal. Mantenha o processo do painel aberto e use o mesmo endereço `127.0.0.1`.
- **Erro ao salvar no Display:** confira a faixa do campo e a versão do firmware. Releia o aparelho antes de tentar de novo.

## Validar e empacotar

Na raiz deste repositório:

```sh
python3 -m unittest discover -s tests
python3 packaging/build.py
python3 dist/doguia-usage.pyz painel --sem-navegador
```

Os testes cobrem coletores, terminal, wizard, persistência do painel, proteção da sessão HTTP, arquivos visuais e contratos de envio. A validação com aparelho real deve confirmar aviso, consumo, mudanças de brilho e composição; os testes simulados não substituem essa conferência física. O CI também executa `python packaging/smoke.py <executável instalado>` em cada sistema para conferir HTML, CSS, JavaScript, imagem, schemas e sessão HTTP. Localmente, o pacote portátil e o binário Linux passaram nessa conferência. Os instaladores Windows/macOS exigem execução da matriz nos respectivos sistemas.

A imagem do pet é derivada do atlas existente `assets/sprites/body-age-17.jmd` pelo leitor `tools/jmd.py`. Os schemas vêm de `docs/openapi.json`; atualize `doguia_usage/web/schemas.json` quando esses contratos mudarem. A identidade usa azul e ciano e oferece acesso ao site e à ajuda oficiais em https://www.doguia.com.br/ajuda/display/.
