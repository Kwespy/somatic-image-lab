#!/bin/bash
SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
cd "$SITE" || exit 1

if [ "$#" -ge 1 ] && [ -f "$1" ]; then
  ZIP="$1"
else
  ZIP=$(/usr/bin/osascript <<'APPLESCRIPT'
try
  set theFile to choose file with prompt "Selecciona el ZIP del post nuevo o actualizado de The Somatic Image Lab" of type {"zip"}
  return POSIX path of theFile
on error number -128
  return ""
end try
APPLESCRIPT
)
fi

if [ -z "$ZIP" ]; then
  exit 0
fi

/usr/bin/python3 "$SITE/scripts/add_post.py" "$ZIP"
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  /usr/bin/osascript -e 'display dialog "Post agregado o actualizado correctamente." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"' >/dev/null
elif [ "$STATUS" -eq 2 ]; then
  /usr/bin/osascript -e 'display dialog "Actualización cancelada. No se hicieron cambios." buttons {"OK"} default button "OK" with title "The Somatic Image Lab"' >/dev/null
else
  /usr/bin/osascript -e 'display dialog "No se pudo procesar el post. La ventana de Terminal muestra el error." buttons {"OK"} default button "OK" with icon stop with title "The Somatic Image Lab"' >/dev/null
fi

exit "$STATUS"
