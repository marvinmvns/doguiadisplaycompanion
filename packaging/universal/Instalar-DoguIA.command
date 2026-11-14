#!/bin/sh
# Entrada única macOS/Linux. Não depende de Python, pip, jq ou internet.
set -eu
fail() { printf '\n%s\n' "$*" >&2; exit 1; }
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in ''|--verificar|--sem-abrir) ;; *) fail 'Opção inválida. Use --verificar ou --sem-abrir.' ;; esac
case "$(uname -s)" in Linux) sistema=linux ;; Darwin) sistema=macos ;; *) fail 'Sistema não suportado. No Windows, abra Instalar-DoguIA.cmd.' ;; esac
case "$(uname -m)" in x86_64|amd64) arq=x64 ;; arm64|aarch64) arq=arm64 ;; *) fail 'Arquitetura não suportada por este pacote.' ;; esac
# Um terminal sob Rosetta pode informar x86_64 num Mac Apple Silicon.
if [ "$sistema" = macos ] && [ "$(sysctl -n hw.optional.arm64 2>/dev/null || true)" = 1 ]; then arq=arm64; fi
chave="$sistema-$arq"
[ -f "$base/pacotes.tsv" ] || fail 'Extraia o ZIP inteiro antes de instalar. Não foi encontrado pacotes.tsv.'
linha=$(awk -F '\t' -v k="$chave" '$1==k {print $2 " " $3}' "$base/pacotes.tsv")
[ -n "$linha" ] || fail "Este pacote não inclui $chave. Consulte LEIA-ME.html para as plataformas disponíveis."
arquivo=${linha%% *}; esperado=${linha#* }
case "$arquivo" in *[!a-zA-Z0-9._-]*|'') fail 'Nome de pacote inválido.' ;; esac
[ ${#esperado} -eq 64 ] || fail 'Manifesto de integridade inválido.'
alvo="$base/pacotes/$arquivo"
[ -f "$alvo" ] || fail "Pacote ausente: $arquivo. Extraia novamente o ZIP completo."
printf '\nDoguIA Companion\nSistema detectado: %s\nConferindo o instalador…\n' "$chave"
if command -v sha256sum >/dev/null 2>&1; then atual=$(sha256sum "$alvo" | awk '{print $1}');
elif command -v shasum >/dev/null 2>&1; then atual=$(shasum -a 256 "$alvo" | awk '{print $1}');
else fail 'Não foi possível conferir o pacote: instale sha256sum (coreutils) ou shasum.'; fi
[ "$atual" = "$esperado" ] || fail 'O pacote está incompleto ou alterado. Baixe e extraia novamente; nada foi instalado.'
[ "${1:-}" != --verificar ] || { printf '%s\n' "Pacote íntegro e compatível: $arquivo"; exit 0; }
if [ "$sistema" = macos ]; then
  printf '%s\n' 'Abrindo o instalador do macOS. Conclua as etapas para abrir o painel DoguIA.'
  if [ "${1:-}" = --sem-abrir ]; then
    sudo env COMMAND_LINE_INSTALL=1 installer -pkg "$alvo" -target /
  else
    open "$alvo"
  fi
  exit 0
fi
command -v tar >/dev/null 2>&1 || fail 'O comando tar não está disponível. Instale o pacote tar da sua distribuição.'
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
tar -xzf "$alvo" -C "$tmp"
set -- "$tmp"/doguia-usage-*/install.sh "${1:-}"
[ -f "$1" ] || fail 'O pacote não contém o instalador esperado.'
DOGUIA_SEM_ASSISTENTE=1 sh "$1"
if [ "$2" != --sem-abrir ]; then
  printf '%s\n' 'Instalação concluída. Abrindo o assistente DoguIA…'
  "${XDG_BIN_HOME:-$HOME/.local/bin}/doguia-usage" painel
fi
