# Downloads do DoguIA Companion

## Instalação recomendada

**[Baixar o ZIP universal da versão atual](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest/download/doguia-instalar-universal.zip)**

Extraia o ZIP inteiro e abra **Instalar DoguIA**: `.cmd` no Windows; `.command` no macOS; `sh Instalar-DoguIA.command` no Linux. O sistema escolhe e confere o instalador. Python e assets estão incluídos.

[Todos os arquivos e notas da versão](https://github.com/marvinmvns/doguiadisplaycompanion/releases/latest) · [Histórico de versões](https://github.com/marvinmvns/doguiadisplaycompanion/releases)

| Sistema | Arquivo individual na release |
|---|---|
| Windows 10/11 x64 | `doguia-usage-<versão>-windows-x64-setup.exe` |
| macOS Apple Silicon | `doguia-usage-<versão>-macos-arm64.pkg` |
| macOS Intel | `doguia-usage-<versão>-macos-x64.pkg` |
| Debian/Ubuntu x64 | `doguia-usage_<versão>_amd64.deb` |
| Linux x64/glibc | `doguia-usage-<versão>-linux-x64.tar.gz` |
| Qualquer sistema com Python 3.9+ | `doguia-usage.pyz` |

Os instaladores não têm assinatura comercial Microsoft/Apple e podem exigir confirmação do sistema ao abrir. Linux ARM/musl e Windows ARM/32 bits não fazem parte do ZIP. Consulte [INSTALACAO.md](INSTALACAO.md) para instalação, atualização e remoção.

## Integridade

Cada release contém `SHA256SUMS.txt`. Linux: `sha256sum -c SHA256SUMS.txt --ignore-missing`; macOS: `shasum -a 256 <arquivo>`; Windows: `Get-FileHash <arquivo> -Algorithm SHA256`. Compare com a linha do arquivo no manifesto. O iniciador universal faz a conferência do instalador selecionado automaticamente.

Os checksums detectam corrupção; obtenha os arquivos deste repositório oficial. Builds em andamento podem ser acompanhados em [Actions](https://github.com/marvinmvns/doguiadisplaycompanion/actions/workflows/companion.yml). Os artefatos de teste de `main` não substituem a release estável.
