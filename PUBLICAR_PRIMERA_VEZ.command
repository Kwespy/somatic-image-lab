#!/bin/bash
cd "$(dirname "$0")"
clear
echo "THE SOMATIC IMAGE LAB"
echo "PRIMERA PUBLICACIÓN"
echo "----------------------"
echo

if [ ! -d ".git" ]; then
  git init
fi
git branch -M main

CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)

if [ -z "$CURRENT_REMOTE" ]; then
  echo "Pega la URL HTTPS del repositorio GitHub vacío:"
  echo "ej: https://github.com/Kwespy/somatic-image-lab.git"
  read -r REPO
  if [ -z "$REPO" ]; then
    echo "No ingresaste URL."
    read -n 1 -s -r -p "Presiona una tecla para cerrar..."
    exit 1
  fi
  git remote add origin "$REPO"
fi

git add -A
git commit -m "Launch The Somatic Image Lab" 2>/dev/null || true
git push -u origin main

echo
if [ $? -eq 0 ]; then
  echo "✓ SITIO SUBIDO A GITHUB"
  echo
  echo "Ahora: GitHub > Settings > Pages"
  echo "Deploy from a branch > main / root"
  echo "Custom domain: somatic.kurtwespyianatos.com"
else
  echo "ERROR: git push falló."
fi
echo
read -n 1 -s -r -p "Presiona una tecla para cerrar..."
