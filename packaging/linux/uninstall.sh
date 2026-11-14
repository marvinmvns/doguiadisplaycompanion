#!/bin/sh
# Desliga o início automático e remove o que o install.sh copiou. A configuração fica em ~/.config/doguia-usage.
bin="${XDG_BIN_HOME:-$HOME/.local/bin}"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
[ -x "$bin/doguia-usage" ] && "$bin/doguia-usage" uninstall || true
rm -f "$bin/doguia-usage" "$apps/doguia-usage.desktop"
echo "doguia-usage removido. Para apagar também a configuração: rm -r ~/.config/doguia-usage"
