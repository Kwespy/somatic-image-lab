#!/usr/bin/env python3
from pathlib import Path
import json
from tsil_social import apply_social_to_reading
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'readings.json'
def main():
    if not DATA.exists():
        print('ERROR: no encuentro data/readings.json')
        return 1
    items=json.loads(DATA.read_text(encoding='utf-8'))
    ok=0
    for it in sorted(items,key=lambda x:int(x['number'])):
        print(f'GENERANDO {int(it["number"]):03d} — {it["author"]} ...')
        if apply_social_to_reading(ROOT,it,generate=True):
            ok+=1
    print(f'\n{ok} readings actualizados con metadata + Story ES/EN + imágenes sociales.')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
