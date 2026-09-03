#!/usr/bin/env python3
from pathlib import Path
import sys,re

ROOT=Path(sys.argv[1])
READINGS=ROOT/"readings"

NOTE_ES='Esta pregunta comprime las tensiones del texto y de su Máquina de Error. Hereda las contaminaciones anteriores para que el error se acumule y abra nuevas posibilidades.'
NOTE_EN='This question compresses the tensions of the text and its Error Machine. It inherits previous contaminations so error can accumulate and open new possibilities.'
CSS='\n.carry-rule{\n  margin:10px 0 18px;\n  max-width:720px;\n  font-size:11px;\n  line-height:1.45;\n  letter-spacing:.02em;\n  color:var(--muted);\n}\n'

def patch_page(p):
    s=p.read_text(encoding="utf-8")
    s=s.replace("arrastrar al próximo texto","arrastre").replace("carry into the next text","carry")

    if ".carry-rule{" not in s:
        s=s.replace("</style>",CSS+"\n</style>",1)

    s=re.sub(
        r'\s*<div class="carry-rule"[^>]*>.*?</div>\s*'
        r'<div class="carry-rule"[^>]*>.*?</div>\s*',
        "\n",s,flags=re.S
    )

    pair=re.search(
        r'(<div class="section-title" data-copy="es">arrastre</div>\s*'
        r'<div class="section-title" data-copy="en">carry</div>)',
        s,re.I|re.S
    )
    if pair:
        note=(pair.group(1)
              +f'\n<div class="carry-rule" data-copy="es">{NOTE_ES}</div>'
              +f'\n<div class="carry-rule" data-copy="en">{NOTE_EN}</div>')
        s=s[:pair.start()]+note+s[pair.end():]

    p.write_text(s,encoding="utf-8")

for p in sorted(READINGS.glob("*/index.html")):
    patch_page(p)
    print("✓",p.parent.name,"— nota de ARRASTRE")

# Update Barad's current carry question to the agreed version.
for d in sorted(READINGS.glob("*karen-barad*")):
    p=d/"index.html"
    if not p.exists(): continue
    s=p.read_text(encoding="utf-8")
    s=re.sub(
        r'<div class="carry" data-copy="es">.*?</div>',
        '<div class="carry" data-copy="es">¿Cuándo una imagen sigue siendo la misma si cada sistema que atraviesa también participa en transformarla?</div>',
        s,count=1,flags=re.S
    )
    s=re.sub(
        r'<div class="carry" data-copy="en">.*?</div>',
        '<div class="carry" data-copy="en">When does an image remain the same if every system it passes through also participates in transforming it?</div>',
        s,count=1,flags=re.S
    )
    p.write_text(s,encoding="utf-8")
    print("✓",d.name,"— pregunta de ARRASTRE actualizada")
