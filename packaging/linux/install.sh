#!/bin/sh
# Instala o doguia-usage só para este usuário, sem sudo, em ~/.local/bin, e abre o assistente de configuração.
set -e
here=$(cd "$(dirname "$0")" && pwd)
bin="${XDG_BIN_HOME:-$HOME/.local/bin}"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
docs="${XDG_DATA_HOME:-$HOME/.local/share}/doguia-usage"
mkdir -p "$bin" "$apps" "$docs"
# Copie para um arquivo temporário: atualizações funcionam mesmo com o binário aberto.
stage=$(mktemp "$bin/.doguia-usage.XXXXXX")
trap 'rm -f "$stage"' EXIT HUP INT TERM
install -m 755 "$here/doguia-usage" "$stage"
mv -f "$stage" "$bin/doguia-usage"
install -m 755 "$here/uninstall.sh" "$docs/uninstall.sh"
for doc in README.md INSTALACAO.md; do
  [ ! -f "$here/$doc" ] || install -m 644 "$here/$doc" "$docs/$doc"
done
# Exec do Desktop Entry tem escape próprio, diferente de um comando de shell.
exec_path=$(printf '%s' "$bin/doguia-usage" | sed 's/\\/\\\\/g; s/"/\\"/g; s/`/\\`/g; s/\$/\\$/g; s/%/%%/g')
printf '[Desktop Entry]\nType=Application\nName=Configurar DoguIA Usage\nExec="%s" painel\nTerminal=true\nIcon=utilities-terminal\nCategories=Utility;\n' "$exec_path" > "$apps/doguia-usage.desktop"
echo "Instalado em $bin/doguia-usage"
case ":$PATH:" in
  *":$bin:"*) ;;
  *) echo "Aviso: $bin não está no PATH. Acrescente ao ~/.profile: export PATH=\"$bin:\$PATH\"" ;;
esac
# atualização: o envio em segundo plano passa a usar a versão nova
if systemctl --user is-active --quiet doguia-usage.service 2>/dev/null; then
  systemctl --user restart doguia-usage.service || true
fi
if [ -t 0 ] && [ "${DOGUIA_SEM_ASSISTENTE:-}" = "" ]; then
  "$bin/doguia-usage" painel
else
  echo "Para configurar: $bin/doguia-usage painel"
fi
