#!/usr/bin/env python3
"""Check that a reading is complete locally or in the staged Git commit."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_file(relative, staged):
    path = ROOT / relative
    if not staged:
        if not path.exists():
            raise RuntimeError(f"Falta {relative}.")
        return path.read_text(encoding="utf-8")
    result = subprocess.run(
        ["git", "show", f":{relative}"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        raise RuntimeError(f"{relative} no está incluido en el commit.")
    return result.stdout


def check(number, staged):
    items = json.loads(read_file("data/readings.json", staged))
    item = next((x for x in items if int(x["number"]) == number), None)
    if not item:
        raise RuntimeError(f"El reading {number:03d} no está en data/readings.json.")

    slug = item["slug"]
    reading = f"readings/{slug}/index.html"
    page = read_file(reading, staged)
    if f"lectura / {number:03d}" not in page or f"reading / {number:03d}" not in page:
        raise RuntimeError(f"La página {number:03d} no tiene sus dos etiquetas de idioma.")

    card = read_file("maquina-del-error/index.html", staged)
    card_link = f'../readings/{slug}/index.html'
    if card_link not in card:
        raise RuntimeError(f"Falta la tarjeta {number:03d} en Máquina de Error.")

    sitemap = read_file("sitemap.xml", staged)
    if f"/readings/{slug}/" not in sitemap:
        raise RuntimeError(f"Falta el reading {number:03d} en sitemap.xml.")

    previous = next((x for x in items if int(x["number"]) == number - 1), None)
    if previous:
        prior = read_file(f'readings/{previous["slug"]}/index.html', staged)
        if f'../{slug}/index.html' not in prior:
            raise RuntimeError(
                f"Falta el enlace desde el reading {number - 1:03d} hacia {number:03d}."
            )


def main():
    parser = argparse.ArgumentParser(
        description="Comprueba que un reading está completo antes de publicar."
    )
    parser.add_argument("number", type=int, nargs="*", help="Número de reading")
    parser.add_argument(
        "--all", action="store_true", help="Comprueba todos los readings registrados."
    )
    parser.add_argument(
        "--staged", action="store_true",
        help="Comprueba los archivos seleccionados para el próximo commit.",
    )
    args = parser.parse_args()

    try:
        items = json.loads(read_file("data/readings.json", args.staged))
        numbers = [int(x["number"]) for x in items] if args.all else args.number
        if not numbers:
            raise RuntimeError("Indica un número de reading o usa --all.")
        for number in numbers:
            check(number, args.staged)
    except (RuntimeError, json.JSONDecodeError) as error:
        print(f"PUBLICACIÓN INCOMPLETA: {error}", file=sys.stderr)
        raise SystemExit(1)

    scope = "seleccionado para publicar" if args.staged else "local"
    labels = ", ".join(f"{number:03d}" for number in numbers)
    print(f"READING {labels} — paquete {scope} completo ✓")


if __name__ == "__main__":
    main()
