#!/bin/bash
# publicar-nuevo.command
# Empaqueta el reading preparado en _proximo_reading/, lo importa con add_post.py
# y publica en GitHub solo cuando el paquete completo pasa las verificaciones.
#
# Requisito previo: Claude/Codex debe haber dejado manifest.json + index.html
# (y recursos si los hay) dentro de la carpeta _proximo_reading/.

set -e
SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
STAGING="$SITE/_proximo_reading"
cd "$SITE" || exit 1

echo ""
echo "THE SOMATIC IMAGE LAB — Publicar nuevo reading"
echo ""

# Las ediciones previas no se mezclan con una publicación nueva. Los archivos
# no rastreados (incluida _proximo_reading/) no cuentan en esta comprobación.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  /usr/bin/osascript -e 'display dialog "Hay cambios pendientes en el sitio. Revisalos o guardalos antes de publicar: este lanzador no los mezcla con el nuevo reading." buttons {"OK"} default button "OK" with icon caution with title "The Somatic Image Lab"' >/dev/null
  exit 1
fi

if [ ! -f "$STAGING/manifest.json" ] || [ ! -f "$STAGING/index.html" ]; then
  /usr/bin/osascript -e 'display dialog "No encontré manifest.json e index.html en _proximo_reading/. Pedile a Claude que prepare el próximo reading primero." buttons {"OK"} default button "OK" with icon stop with title "The Somatic Image Lab"' >/dev/null
  exit 1
fi

# 1) Nombre del ZIP a partir de la fecha/hora para no pisar lotes anteriores
ZIP_NAME="proximo_reading_$(date +%Y%m%d_%H%M%S).zip"
ZIP_PATH="$SITE/$ZIP_NAME"

echo "1/4 · Empaquetando $STAGING → $ZIP_NAME"
(cd "$STAGING" && zip -r "$ZIP_PATH" . -x ".*") >/dev/null

# 2) Importar con el pipeline existente
echo "2/4 · Importando con scripts/add_post.py"
/usr/bin/python3 "$SITE/scripts/add_post.py" "$ZIP_PATH"
IMPORT_STATUS=$?

if [ "$IMPORT_STATUS" -ne 0 ]; then
  /usr/bin/osascript -e 'display dialog "add_post.py falló al importar el reading. Revisá la Terminal para el detalle." buttons {"OK"} default button "OK" with icon stop with title "The Somatic Image Lab"' >/dev/null
  exit "$IMPORT_STATUS"
fi

# 3) Verificar y seleccionar solo los archivos que actualiza el importador.
echo "3/5 · Verificando el paquete"
/usr/bin/python3 "$SITE/scripts/verify_reading_publish.py" --all
git add data/readings.json maquina-del-error/index.html sitemap.xml readings/
/usr/bin/python3 "$SITE/scripts/verify_reading_publish.py" --all --staged

echo "4/5 · Registrando la publicación"
git commit -m "Agregar nuevo reading"

# 4) Push directo: requiere una cuenta de GitHub autenticada en este Mac.
echo "5/5 · git push origin main"
git push origin main
PUSH_STATUS=$?

# Limpieza: sacar el zip temporal y vaciar la carpeta de staging
rm -f "$ZIP_PATH"
rm -rf "${STAGING:?}"/*

if [ "$PUSH_STATUS" -eq 0 ]; then
  /usr/bin/osascript -e 'display dialog "Reading publicado y subido a GitHub correctamente." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"' >/dev/null
else
  /usr/bin/osascript -e 'display dialog "El commit se hizo pero el push falló. Revisá la conexión y corré git push manualmente." buttons {"OK"} default button "OK" with icon caution with title "The Somatic Image Lab"' >/dev/null
fi

exit "$PUSH_STATUS"
