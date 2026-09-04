#!/bin/bash
set -u

SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"

if [ ! -d "$SITE" ]; then
  echo "ERROR: no encuentro $SITE"
  exit 1
fi

echo ""
echo "TSIL SOCIAL — FIX BRAVE"
echo "Brave Browser será el motor preferido para renderizar HTML → PNG."
echo "No necesita abrirse visualmente."
echo ""

mkdir -p "$SITE/BACKUP_FIX_BRAVE_$STAMP/scripts"
[ -f "$SITE/scripts/tsil_social.py" ] && cp "$SITE/scripts/tsil_social.py" "$SITE/BACKUP_FIX_BRAVE_$STAMP/scripts/"
[ -f "$SITE/scripts/migrate_social.py" ] && cp "$SITE/scripts/migrate_social.py" "$SITE/BACKUP_FIX_BRAVE_$STAMP/scripts/"

cp "$HERE/scripts/tsil_social.py" "$SITE/scripts/tsil_social.py"
cp "$HERE/scripts/migrate_social.py" "$SITE/scripts/migrate_social.py"

chmod +x "$SITE/scripts/tsil_social.py" "$SITE/scripts/migrate_social.py"

echo "FIX BRAVE instalado ✓"
echo "Los PNG ya generados se saltarán automáticamente."
echo "Puedes retomar desde Reading 001 sin perder lo ya hecho."
echo ""

cd "$SITE"
/usr/bin/python3 "$SITE/scripts/migrate_social.py"
STATUS=$?

if [ "$STATUS" -eq 130 ]; then
  echo ""
  echo "Cancelado. Puedes ejecutar este mismo FIX otra vez y continuará."
  exit 130
fi

if [ "$STATUS" -ne 0 ]; then
  echo ""
  echo "La migración terminó con errores. NO haré git push."
  echo "Mándame una captura de las últimas líneas."
  exit "$STATUS"
fi

echo ""
echo "Git..."
git add -A
if ! git diff --cached --quiet; then
  git commit -m "Add TSIL social export assets"
  git push
else
  echo "No hay cambios nuevos para subir."
fi

echo ""
echo "LISTO ✓"
