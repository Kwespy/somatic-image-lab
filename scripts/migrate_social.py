#!/usr/bin/env python3
from pathlib import Path
import json, traceback
from tsil_social import apply_social_to_reading, selected_browser_label

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'readings.json'

def main():
    if not DATA.exists():
        print('ERROR: no encuentro data/readings.json', flush=True)
        return 1
    items = json.loads(DATA.read_text(encoding='utf-8'))
    print('Navegador disponible para generación individual:', selected_browser_label(), flush=True)
    print('Esta actualización solo prepara HTML y datos; no genera imágenes.\n', flush=True)
    ok = 0
    failed = []
    total = len(items)
    for pos, it in enumerate(sorted(items, key=lambda x: int(x['number'])), 1):
        n = int(it['number'])
        print(f'\n=== READING {pos}/{total} · {n:03d} — {it["author"]} ===', flush=True)
        try:
            if apply_social_to_reading(ROOT, it, generate=False):
                ok += 1
                print(f'✓ READING {n:03d} listo', flush=True)
        except KeyboardInterrupt:
            print('\nCancelado por el usuario. Puedes volver a ejecutar para actualizar los datos pendientes.', flush=True)
            return 130
        except Exception as e:
            failed.append((n, str(e)))
            print(f'ERROR en {n:03d}: {e}', flush=True)
            print('Continuando con el siguiente reading...', flush=True)
    print(f'\n{ok}/{total} readings actualizados.', flush=True)
    if failed:
        print('\nFallaron:', flush=True)
        for n, err in failed:
            print(f' - {n:03d}: {err}', flush=True)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
