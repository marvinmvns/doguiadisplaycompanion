#!/bin/bash
# Desliga o início automático e remove o programa. A configuração fica em ~/Library/Application Support/doguia-usage.
/usr/local/bin/doguia-usage uninstall
echo "Para remover os arquivos, digite a senha de administrador:"
sudo rm -rf /usr/local/bin/doguia-usage "/Applications/DoguIA Usage" && sudo pkgutil --forget br.com.doguia.usage >/dev/null
echo "doguia-usage removido."
read -r -p "Pressione Enter para fechar."
