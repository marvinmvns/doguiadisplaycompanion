# DoguIA Display Companion

Aplicativo para conectar o computador ao DoguIA Display, acompanhar consumo de IA e personalizar o aparelho. Este é o repositório oficial do **companion**, dos instaladores e dos downloads. O firmware continua em [doguiadisplay](https://github.com/marvinmvns/doguiadisplay).

[![Build e instaladores](https://github.com/marvinmvns/doguiadisplaycompanion/actions/workflows/companion.yml/badge.svg)](https://github.com/marvinmvns/doguiadisplaycompanion/actions/workflows/companion.yml)

## Baixar e instalar

**[Baixar instalador universal](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest/download/doguia-instalar-universal.zip)** · [Todos os downloads](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest) · [Guia de download](DOWNLOAD.md)

1. Baixe e extraia o ZIP completo.
2. Windows: abra `Instalar-DoguIA.cmd`. macOS: abra `Instalar-DoguIA.command`. Linux: execute `sh Instalar-DoguIA.command`.
3. Siga o assistente para conectar o Display à mesma rede do computador.

Python já está incluído nos instaladores. Não precisa instalar bibliotecas, Node ou Electron. O ZIP funciona offline durante a instalação. Cobertura: Windows x64, macOS Intel/Apple Silicon e Linux x64/glibc.

[Manual de instalação](INSTALACAO.md) · [Manual de uso](MANUAL.md) · [Referência técnica](REFERENCIA.md) · [Builds e publicação](BUILD.md)

## Desenvolver

```sh
git clone https://github.com/marvinmvns/doguiadisplaycompanion.git
cd doguiadisplaycompanion
python3 iniciar.py
```

No Windows: `py -3 iniciar.py`. A partir do código é necessário Python 3.9+. O iniciador prepara uma cópia portátil estável e abre o painel, sem pip nem bibliotecas externas.

```sh
python3 -m unittest discover -s tests
python3 packaging/build.py
python3 -m doguia_usage painel
```

O código e a documentação são em português. Os coletores não abrem arquivos de login nem credenciais. Nenhum build deste repositório grava firmware no Display.
