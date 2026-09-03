#!/usr/bin/env python3
from pathlib import Path
import sys,re,json,html,shutil

ROOT=Path(sys.argv[1])
READINGS=ROOT/"readings"
DATA=ROOT/"data"/"readings.json"
FLOW_CSS='\n.carry-rule{\n  margin:10px 0 18px;\n  max-width:760px;\n  font-size:11px;\n  line-height:1.45;\n  letter-spacing:.02em;\n  color:var(--muted);\n}\n.carry-source{display:none!important}\n.carry-flow{\n  display:grid;\n  grid-template-columns:1fr 1fr;\n  gap:14px;\n  grid-column:1 / -1;\n}\n.carry-card{\n  min-height:220px;\n  padding:22px;\n  border:1px solid var(--line);\n  display:flex;\n  flex-direction:column;\n  justify-content:space-between;\n  color:inherit;\n  text-decoration:none;\n  transition:border-color .15s ease;\n}\na.carry-card:hover{border-color:var(--orange)}\n.carry-card.current{border-color:var(--ink)}\n.carry-direction{\n  font-size:11px;\n  line-height:1.35;\n  letter-spacing:.09em;\n  text-transform:uppercase;\n  color:var(--muted);\n  margin-bottom:36px;\n}\n.carry-question{\n  font-size:clamp(22px,2.5vw,38px);\n  line-height:1.08;\n  letter-spacing:-.035em;\n}\n.carry-card.start .carry-question{\n  font-size:14px;\n  line-height:1.4;\n  letter-spacing:0;\n  color:var(--muted);\n}\n.carry-card.waiting .carry-direction::after{\n  content:"";\n}\n@media(max-width:760px){\n  .carry-flow{grid-template-columns:1fr}\n  .carry-card{min-height:180px}\n}\n'
NOTE_ES='Cada pregunta comprime las tensiones de su texto y de su Máquina de Error. Hereda contaminaciones anteriores para que el error se acumule y abra nuevas posibilidades.'
NOTE_EN='Each question compresses the tensions of its text and its Error Machine. It inherits previous contaminations so error can accumulate and open new possibilities.'

items=json.loads(DATA.read_text(encoding="utf-8"))
items=sorted(items,key=lambda x:int(x["number"]))

# Remove accidental duplicate books, keeping the earliest.
seen=set();clean=[]
for it in items:
    key=(it["author"].strip().casefold(),it["title_en"].strip().casefold())
    if key in seen:
        d=READINGS/it["slug"]
        if d.exists(): shutil.rmtree(d)
        print("✓ duplicado eliminado:",f'{int(it["number"]):03d}',it["author"])
    else:
        seen.add(key);clean.append(it)
items=clean
DATA.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")

def strip_tags(s): return re.sub(r'<[^>]+>','',s).strip()

def own_carry(page):
    for cls in ("carry-source","carry"):
        es=re.search(rf'<div class="{cls}" data-copy="es">(.*?)</div>',page,re.S)
        en=re.search(rf'<div class="{cls}" data-copy="en">(.*?)</div>',page,re.S)
        if es and en:return strip_tags(es.group(1)),strip_tags(en.group(1))
    return None,None

questions={}
for it in items:
    p=READINGS/it["slug"]/"index.html"
    if p.exists():
        es,en=own_carry(p.read_text(encoding="utf-8"))
        if es and en:questions[it["slug"]]=(es,en)

def section(own_es,own_en,prev,nxt,prev_es,prev_en):
    if prev:
        left=f"""<a class="carry-card incoming" href="../{html.escape(prev["slug"])}/index.html">
  <div class="carry-direction"><span data-inline="es">← viene de {int(prev["number"]):03d} · {html.escape(prev["author"])}</span><span data-inline="en">← comes from {int(prev["number"]):03d} · {html.escape(prev["author"])}</span></div>
  <div class="carry-question" data-copy="es">{html.escape(prev_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(prev_en)}</div>
</a>"""
    else:
        left="""<div class="carry-card start">
  <div class="carry-direction"><span data-inline="es">inicio de la cadena</span><span data-inline="en">start of the chain</span></div>
  <div class="carry-question" data-copy="es">Esta lectura produce la primera pregunta de arrastre.</div>
  <div class="carry-question" data-copy="en">This reading produces the first carry question.</div>
</div>"""
    if nxt:
        right=f"""<a class="carry-card current" href="../{html.escape(nxt["slug"])}/index.html">
  <div class="carry-direction"><span data-inline="es">va hacia {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span><span data-inline="en">goes to {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span></div>
  <div class="carry-question" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(own_en)}</div>
</a>"""
    else:
        right=f"""<div class="carry-card current waiting">
  <div class="carry-direction"><span data-inline="es">hacia el próximo texto →</span><span data-inline="en">toward the next text →</span></div>
  <div class="carry-question" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(own_en)}</div>
</div>"""
    return f"""<section class="grid">
  <div class="section-title" data-copy="es">arrastre</div>
  <div class="section-title" data-copy="en">carry</div>
  <div class="carry-rule" data-copy="es">{NOTE_ES}</div>
  <div class="carry-rule" data-copy="en">{NOTE_EN}</div>
  <div class="carry-source" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-source" data-copy="en">{html.escape(own_en)}</div>
  <div class="carry-flow">{left}{right}</div>
</section>"""

for i,it in enumerate(items):
    p=READINGS/it["slug"]/"index.html"
    if not p.exists():continue
    page=p.read_text(encoding="utf-8")
    if ".carry-flow{" not in page:
        page=page.replace("</style>",FLOW_CSS+"\n</style>",1)
    own_es,own_en=questions.get(it["slug"],("",""))
    if not own_es:continue
    prev=items[i-1] if i>0 else None
    nxt=items[i+1] if i+1<len(items) else None
    prev_es,prev_en=questions.get(prev["slug"],("","")) if prev else ("","")
    new=section(own_es,own_en,prev,nxt,prev_es,prev_en)
    pattern=(r'<section class="grid">\s*'
             r'<div class="section-title" data-copy="es">(?:arrastre|arrastrar al próximo texto)</div>\s*'
             r'<div class="section-title" data-copy="en">(?:carry|carry into the next text)</div>'
             r'.*?</section>')
    if re.search(pattern,page,re.I|re.S):
        page=re.sub(pattern,new,page,count=1,flags=re.I|re.S)
        p.write_text(page,encoding="utf-8")
        print("✓",it["slug"],"— doble arrastre")

print("✓ flujo reconstruido")
