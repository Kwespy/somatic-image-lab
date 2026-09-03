#!/bin/bash
set -e
SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SITE" ]; then
  /usr/bin/osascript -e 'display dialog "No encuentro la carpeta TSIL_PUBLISH en iCloud." buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi

python3 "$HERE/patch_double_carry.py" "$SITE"
cp "$HERE/add_post.py" "$SITE/scripts/add_post.py"
cp "$HERE/AGREGAR_POST.command" "$SITE/AGREGAR_POST.command"
chmod +x "$SITE/AGREGAR_POST.command" "$SITE/scripts/add_post.py"

cd "$SITE"
git add -A
git commit -m "Add bidirectional carry questions and Finder post picker" || true
git push

/usr/bin/osascript -e 'display dialog "Actualización lista. Desde ahora abre AGREGAR_POST.command con doble clic y elige el ZIP en Finder." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"'
