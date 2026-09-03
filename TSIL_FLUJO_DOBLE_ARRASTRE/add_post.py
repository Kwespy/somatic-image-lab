#!/usr/bin/env python3
from pathlib import Path
import zipfile,tempfile,shutil,json,sys,re,subprocess,html

ROOT=Path(__file__).resolve().parents[1]
READINGS=ROOT/"readings"
DATA=ROOT/"data"/"readings.json"
HOME=ROOT/"index.html"
SITEMAP=ROOT/"sitemap.xml"
DOMAIN="https://thesomaticimagelab.kurtwespyianatos.com"
CARRY_NOTE_ES='Cada pregunta comprime las tensiones de su texto y de su Máquina de Error. Hereda contaminaciones anteriores para que el error se acumule y abra nuevas posibilidades.'
CARRY_NOTE_EN='Each question compresses the tensions of its text and its Error Machine. It inherits previous contaminations so error can accumulate and open new possibilities.'
FLOW_CSS='\n.carry-rule{\n  margin:10px 0 18px;\n  max-width:760px;\n  font-size:11px;\n  line-height:1.45;\n  letter-spacing:.02em;\n  color:var(--muted);\n}\n.carry-source{display:none!important}\n.carry-flow{\n  display:grid;\n  grid-template-columns:1fr 1fr;\n  gap:14px;\n  grid-column:1 / -1;\n}\n.carry-card{\n  min-height:220px;\n  padding:22px;\n  border:1px solid var(--line);\n  display:flex;\n  flex-direction:column;\n  justify-content:space-between;\n  color:inherit;\n  text-decoration:none;\n  transition:border-color .15s ease;\n}\na.carry-card:hover{border-color:var(--orange)}\n.carry-card.current{border-color:var(--ink)}\n.carry-direction{\n  font-size:11px;\n  line-height:1.35;\n  letter-spacing:.09em;\n  text-transform:uppercase;\n  color:var(--muted);\n  margin-bottom:36px;\n}\n.carry-question{\n  font-size:clamp(22px,2.5vw,38px);\n  line-height:1.08;\n  letter-spacing:-.035em;\n}\n.carry-card.start .carry-question{\n  font-size:14px;\n  line-height:1.4;\n  letter-spacing:0;\n  color:var(--muted);\n}\n.carry-card.waiting .carry-direction::after{\n  content:"";\n}\n@media(max-width:760px){\n  .carry-flow{grid-template-columns:1fr}\n  .carry-card{min-height:180px}\n}\n'

RANDOM_CSS="""
.random-start{
  margin:0 0 18px;display:flex;align-items:center;justify-content:space-between;
  gap:20px;padding:15px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--line)
}
.random-start button{
  border:0;background:none;padding:0;color:var(--ink);font:inherit;
  font-size:clamp(20px,2.2vw,29px);line-height:1.15;letter-spacing:-.025em;
  cursor:pointer;text-align:left
}
.random-start button:hover{color:var(--orange)}
.random-start .random-arrow{font-size:28px;transform:rotate(-7deg)}
"""
RANDOM_JS="""<script id="tsil-random-start">
window.tsilRandomReading=function(){
  const cards=Array.from(document.querySelectorAll('a.post-card'));
  if(!cards.length)return;
  const card=cards[Math.floor(Math.random()*cards.length)];
  window.location.href=card.getAttribute('href');
};
</script>"""

def die(msg):
    print("\n"+msg+"\n")
    raise SystemExit(1)

def slugify(s):
    s=s.translate(str.maketrans("áéíóúüñÁÉÍÓÚÜÑ","aeiouunAEIOUUN")).lower().strip()
    return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",s)).strip("-")

def unpack(src):
    p=Path(src).expanduser().resolve()
    if not p.exists(): die("ERROR: no encuentro "+str(p))
    if p.is_dir(): return p,None
    if p.suffix.lower()!=".zip": die("ERROR: selecciona un ZIP de post.")
    t=Path(tempfile.mkdtemp(prefix="tsil_post_"))
    with zipfile.ZipFile(p) as z: z.extractall(t)
    manifests=list(t.rglob("manifest.json"))
    if not manifests: die("ERROR: falta manifest.json")
    return manifests[0].parent,t

def render_card(it):
    n=f'{int(it["number"]):03d}'
    return f"""<a class="post-card" href="readings/{html.escape(it["slug"])}/index.html">
  <div class="post-number">{n}</div>
  <div>
    <h2 class="post-title" data-copy="es">{html.escape(it["title_es"])}</h2>
    <h2 class="post-title" data-copy="en">{html.escape(it["title_en"])}</h2>
    <div class="post-author">{html.escape(it["author"])}</div>
    <div class="post-meta">
      <span data-inline="es">lectura / umbral /</span>
      <span data-inline="en">reading / threshold /</span>
      <span class="error-pill" data-inline="es">error forzado: {html.escape(it["error_es"])}</span>
      <span class="error-pill" data-inline="en">forced error: {html.escape(it["error_en"])}</span>
    </div>
  </div>
  <div class="post-arrow">→</div>
</a>"""

def update_home(items):
    s=HOME.read_text(encoding="utf-8")
    if ".random-start{" not in s:
        s=s.replace("</style>",RANDOM_CSS+"\n</style>",1)
    if 'id="tsil-random-start"' not in s:
        s=s.replace("</body>",RANDOM_JS+"\n</body>",1)
    cards="\n".join(render_card(x) for x in sorted(items,key=lambda x:int(x["number"]),reverse=True))
    if "<!-- POSTS_START -->" in s:
        s=re.sub(r'<!-- POSTS_START -->.*?<!-- POSTS_END -->','<!-- POSTS_START -->\n'+cards+'\n<!-- POSTS_END -->',s,flags=re.S)
    else:
        ms=list(re.finditer(r'<a class="post-card".*?</a>',s,re.S))
        if not ms: die("ERROR: no encuentro la lista de posts en home.")
        s=s[:ms[0].start()]+"<!-- POSTS_START -->\n"+cards+"\n<!-- POSTS_END -->"+s[ms[-1].end():]
    s=re.sub(r'\s*<div class="random-start".*?</div>\s*(?=<!-- POSTS_START -->)','\n',s,flags=re.S)
    rb="""<div class="random-start">
  <button type="button" onclick="tsilRandomReading()">
    <span data-inline="es">empezar en cualquier parte</span>
    <span data-inline="en">start anywhere</span>
  </button>
  <div class="random-arrow">↝</div>
</div>
"""
    s=s.replace("<!-- POSTS_START -->",rb+"\n<!-- POSTS_START -->",1)
    HOME.write_text(s,encoding="utf-8")

def strip_tags(s):
    return re.sub(r'<[^>]+>','',s).strip()

def own_carry(page):
    for cls in ("carry-source","carry"):
        es=re.search(rf'<div class="{cls}" data-copy="es">(.*?)</div>',page,re.S)
        en=re.search(rf'<div class="{cls}" data-copy="en">(.*?)</div>',page,re.S)
        if es and en:
            return strip_tags(es.group(1)),strip_tags(en.group(1))
    return None,None

def ensure_css(page):
    if ".carry-flow{" not in page:
        page=page.replace("</style>",FLOW_CSS+"\n</style>",1)
    return page

def carry_section(own_es,own_en,prev,nxt,prev_es,prev_en):
    if prev:
        left=f"""<a class="carry-card incoming" href="../{html.escape(prev["slug"])}/index.html">
  <div class="carry-direction">
    <span data-inline="es">← viene de {int(prev["number"]):03d} · {html.escape(prev["author"])}</span>
    <span data-inline="en">← comes from {int(prev["number"]):03d} · {html.escape(prev["author"])}</span>
  </div>
  <div class="carry-question" data-copy="es">{html.escape(prev_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(prev_en)}</div>
</a>"""
    else:
        left="""<div class="carry-card start">
  <div class="carry-direction">
    <span data-inline="es">inicio de la cadena</span>
    <span data-inline="en">start of the chain</span>
  </div>
  <div class="carry-question" data-copy="es">Esta lectura produce la primera pregunta de arrastre.</div>
  <div class="carry-question" data-copy="en">This reading produces the first carry question.</div>
</div>"""

    if nxt:
        right=f"""<a class="carry-card current" href="../{html.escape(nxt["slug"])}/index.html">
  <div class="carry-direction">
    <span data-inline="es">va hacia {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span>
    <span data-inline="en">goes to {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span>
  </div>
  <div class="carry-question" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(own_en)}</div>
</a>"""
    else:
        right=f"""<div class="carry-card current waiting">
  <div class="carry-direction">
    <span data-inline="es">hacia el próximo texto →</span>
    <span data-inline="en">toward the next text →</span>
  </div>
  <div class="carry-question" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-question" data-copy="en">{html.escape(own_en)}</div>
</div>"""

    return f"""<section class="grid">
  <div class="section-title" data-copy="es">arrastre</div>
  <div class="section-title" data-copy="en">carry</div>
  <div class="carry-rule" data-copy="es">{CARRY_NOTE_ES}</div>
  <div class="carry-rule" data-copy="en">{CARRY_NOTE_EN}</div>
  <div class="carry-source" data-copy="es">{html.escape(own_es)}</div>
  <div class="carry-source" data-copy="en">{html.escape(own_en)}</div>
  <div class="carry-flow">
    {left}
    {right}
  </div>
</section>"""

def rebuild_carry_flow(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    questions={}
    # First collect each post's own outgoing question before replacing markup.
    for it in seq:
        p=READINGS/it["slug"]/"index.html"
        if not p.exists(): continue
        page=p.read_text(encoding="utf-8")
        es,en=own_carry(page)
        if es and en: questions[it["slug"]]=(es,en)
    # Then rebuild every carry section.
    for i,it in enumerate(seq):
        p=READINGS/it["slug"]/"index.html"
        if not p.exists(): continue
        page=ensure_css(p.read_text(encoding="utf-8"))
        own_es,own_en=questions.get(it["slug"],("",""))
        if not own_es: continue
        prev=seq[i-1] if i>0 else None
        nxt=seq[i+1] if i+1<len(seq) else None
        if prev:
            prev_es,prev_en=questions.get(prev["slug"],("",""))
        else:
            prev_es,prev_en="",""
        new=carry_section(own_es,own_en,prev,nxt,prev_es,prev_en)
        pattern=(r'<section class="grid">\s*'
                 r'<div class="section-title" data-copy="es">(?:arrastre|arrastrar al próximo texto)</div>\s*'
                 r'<div class="section-title" data-copy="en">(?:carry|carry into the next text)</div>'
                 r'.*?</section>')
        if re.search(pattern,page,re.I|re.S):
            page=re.sub(pattern,new,page,count=1,flags=re.I|re.S)
        else:
            print("AVISO: no encontré sección ARRASTRE en",it["slug"])
        p.write_text(page,encoding="utf-8")

def update_sitemap(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    urls=[DOMAIN+"/"]+[DOMAIN+"/readings/"+x["slug"]+"/" for x in seq]
    SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        +"\n".join("  <url><loc>"+u+"</loc></url>" for u in urls)
        +'\n</urlset>\n',encoding="utf-8")

def gitpush(title):
    subprocess.run(["git","add","-A"],cwd=ROOT)
    subprocess.run(["git","commit","-m","Add reading: "+title],cwd=ROOT)
    r=subprocess.run(["git","push"],cwd=ROOT)
    if r.returncode!=0:
        die("El post quedó creado, pero git push falló.")

def main():
    src=sys.argv[1] if len(sys.argv)>1 else input("Ruta del ZIP:\n> ").strip().strip("'\"")
    pkg,tmp=unpack(src)
    try:
        mf=pkg/"manifest.json"; hp=pkg/"index.html"
        if not mf.exists() or not hp.exists(): die("ERROR: paquete incompleto.")
        m=json.loads(mf.read_text(encoding="utf-8"))
        items=json.loads(DATA.read_text(encoding="utf-8"))

        key=(m["author"].strip().casefold(),m["title_en"].strip().casefold())
        for old in items:
            if (old["author"].strip().casefold(),old["title_en"].strip().casefold())==key:
                die(f'YA EXISTE COMO {int(old["number"]):03d}. No se volvió a publicar.')

        num=max(int(x["number"]) for x in items)+1
        slug=f'{num:03d}-{slugify(m["slug"])}'
        dest=READINGS/slug
        dest.mkdir(parents=True)

        page=hp.read_text(encoding="utf-8")
        page=re.sub(r'(lectura / )\d+',r'\g<1>'+f'{num:03d}',page)
        page=re.sub(r'(reading / )\d+',r'\g<1>'+f'{num:03d}',page)
        (dest/"index.html").write_text(page,encoding="utf-8")

        items.append({
            "number":num,"slug":slug,"author":m["author"],
            "title_es":m["title_es"],"title_en":m["title_en"],
            "date":m["date"],"error_es":m["error_es"],"error_en":m["error_en"]
        })
        DATA.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
        update_home(items)
        rebuild_carry_flow(items)
        update_sitemap(items)
        gitpush(m["title_en"])
        print(f"\nPOST {num:03d} ✓")
        print("ARRASTRE DOBLE ✓")
        print("HOME ✓")
    finally:
        if tmp: shutil.rmtree(tmp,ignore_errors=True)

if __name__=="__main__":
    main()
