#!/bin/bash
cd "$(dirname "$0")"
clear
python3 scripts/add_post.py "$1"
echo
read -n 1 -s -r -p "Presiona una tecla para cerrar..."
