# Validação do painel do companion

Conferência local em 13/11/2026. Esta entrega adiciona o comando `doguia-usage painel` e mantém os comandos de terminal existentes.

| Requisito | Evidência atual | Resultado |
|---|---|---|
| Wizard de configuração | `tests/browser_smoke.py`: cinco etapas, preenchimento e persistência em perfil temporário | Passou em Chrome desktop e viewport móvel |
| Visual da marca e assets existentes | Interface azul/ciano, pet derivado do atlas do projeto, links para site e ajuda oficiais | Conferido visualmente em desktop; viewport móvel sem rolagem horizontal |
| Configuração das ferramentas | Coletores e wizard cobertos por `python3 -m unittest discover -s tests` | 50 testes passaram no conjunto |
| Envio ao Display | Testes de linhas de consumo, aviso, parser de formulário e intervalos do loop | Passou com simulação; aparelho físico pendente |
| Editor do produto e estúdio | Leitura, alteração parcial, aplicação e releitura; fluxo no navegador e servidor HTTP simulado | Passou; readonly, faixas, enums e textos inválidos bloqueados |
| Busca de ajustes | Browser smoke verifica visibilidade dos campos após busca | Passou |
| Pacote portátil | `packaging/build.py` e `packaging/smoke.py dist/doguia-usage.pyz` | Interface e sessão HTTP passaram no pacote |
| Executável Linux | `packaging/build.py --installer` e `packaging/smoke.py build/bin/doguia-usage` | Binário iniciou e serviu HTML, CSS, JS, pet, schemas e sessão |
| Instaladores | Construídos `.deb` e `.tar.gz`; scripts e inclusão do guia revisados | Linux gerado; instalação nativa Windows/macOS pendente |
| Documentação | `INSTALACAO.md`, link no README e inclusão no empacotamento | Entregue |
| CI multiplataforma | Matriz existente Linux/Windows/macOS ampliada para conferir o painel do executável instalado | Alteração local; execução remota ainda não comprovada |

Os testes usam perfis temporários e não ativam serviços na conta real. O teste de editor no navegador intercepta operações do Display. O teste HTTP do editor usa um servidor local simulado e verifica que os campos não alterados são preservados.

## Limites da conferência

O Display conhecido em `192.168.31.15` não respondeu em tentativas HTTP, e a descoberta de rede retornou `None`. Sem ele, não foi possível confirmar fisicamente o aviso no letreiro, o painel de consumo e a aplicação da montagem. É necessário informar o IP atual ou disponibilizar o aparelho na mesma rede do computador.

Este ambiente é Linux. Não foi executada uma instalação em Windows ou macOS. O workflow já possui os comandos para instalar e conferir os pacotes nesses sistemas; é necessário executá-lo com estas alterações ou fornecer ambientes nativos para fechar essa validação. O binário Linux local foi construído com glibc 2.39; a matriz de CI mantém Ubuntu 22.04 para produzir a distribuição com glibc mais antiga.

Não houve publicação de release nem gravação de firmware durante esta entrega.

## Otimização visual e de instalação

- Identidade alinhada aos CSS atuais do site: navy, ciano, logo oficial, foto do Display, Funnel Display e Inter. Assets e licenças das fontes incluídos no pacote, sem requisições externas da interface.
- Iniciadores Windows e macOS/Linux e `iniciar.py`: cópia portátil por usuário, sem pip/venv, com testes de geração e execução em caminho com espaços.
- Verificação do ambiente: Python, escrita na configuração e disponibilidade de início automático, com orientações para itens indisponíveis.
- Controles enumerados usam seletores; campos binários mostram Ativado/Desativado. Campos somente leitura permanecem bloqueados.
- Conferência no Chrome em desktop e 390 px, incluindo diagnóstico do ambiente, cinco etapas, editor, busca e ausência de overflow horizontal.
- Smoke do executável Linux e do .pyz inclui logo, foto e ambas as fontes, além dos recursos anteriores. A instalação nativa em Windows/macOS continua sem execução neste ambiente Linux.

## Instalação universal

- 54 testes passaram, incluindo seleção dos quatro destinos, manifesto SHA-256, rejeição de bundle incompleto, bloqueio de arquivo adulterado e atualização em pasta com espaços.
- O ZIP local `doguia-instalar-1.1.1-teste-linux-x64.zip` foi extraído, instalado e atualizado em diretórios isolados. O executável instalado passou na conferência HTTP do painel com todos os assets; atalho e desinstalador foram encontrados nas pastas esperadas.
- O CI agora constrói Windows x64, Linux x64 e macOS ARM64/Intel. Cada runner confere seu iniciador universal contra o instalador nativo produzido. O job agregado exige todos os pacotes e disponibiliza `doguia-instalar-universal.zip`.
- O ZIP completo não foi gerado localmente: faltam as compilações nativas Windows/macOS destas alterações. A implementação está pronta para a execução do workflow; não houve publicação de release.
