#!/bin/bash
SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
cd "$SITE" || exit 1

ZIPS=()

# Also supports dropping one or several ZIPs onto the .command file.
if [ "$#" -ge 1 ]; then
  for ARG in "$@"; do
    if [ -f "$ARG" ]; then
      ZIPS+=("$ARG")
    fi
  done
else
  ZIP_LIST=$(/usr/bin/osascript <<'APPLESCRIPT'
try
  set theFiles to choose file with prompt "Selecciona uno o varios ZIPs de The Somatic Image Lab" of type {"zip"} with multiple selections allowed
  set outputText to ""
  repeat with theFile in theFiles
    set outputText to outputText & POSIX path of theFile & linefeed
  end repeat
  return outputText
on error number -128
  return ""
end try
APPLESCRIPT
)

  while IFS= read -r ZIP; do
    if [ -n "$ZIP" ]; then
      ZIPS+=("$ZIP")
    fi
  done <<< "$ZIP_LIST"
fi

if [ "${#ZIPS[@]}" -eq 0 ]; then
  exit 0
fi

echo ""
echo "THE SOMATIC IMAGE LAB"
echo "ZIPs seleccionados: ${#ZIPS[@]}"
for ZIP in "${ZIPS[@]}"; do
  echo "  • $(basename "$ZIP")"
done
echo ""

/usr/bin/python3 "$SITE/scripts/add_post.py" "${ZIPS[@]}"
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  /usr/bin/osascript -e 'display dialog "Lote de posts agregado/actualizado correctamente." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"' >/dev/null
elif [ "$STATUS" -eq 2 ]; then
  /usr/bin/osascript -e 'display dialog "No hubo posts para publicar o las actualizaciones fueron canceladas." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"' >/dev/null
else
  /usr/bin/osascript -e 'display dialog "No se pudo procesar el lote. La ventana de Terminal muestra el error." buttons {"OK"} default button "OK" with icon stop with title "The Somatic Image Lab"' >/dev/null
fi

exit "$STATUS"
