#!/bin/bash
set -e

SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SITE" ]; then
  echo "ERROR: No encuentro TSIL_PUBLISH"
  exit 1
fi

python3 "$HERE/patch_arrastre.py" "$SITE"
cp "$HERE/add_post.py" "$SITE/scripts/add_post.py"
chmod +x "$SITE/scripts/add_post.py"

cd "$SITE"
git add -A
git commit -m "Make carry cumulative and contaminated" || true
git push

echo
echo "========================================"
echo "ARRASTRE ACTUALIZADO"
echo "========================================"
echo "✓ regla visible bajo ARRASTRE"
echo "✓ Barad: nueva pregunta"
echo "✓ futuros posts heredan esta lógica"
echo
