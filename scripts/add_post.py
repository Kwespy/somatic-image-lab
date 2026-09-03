#!/usr/bin/env python3
from pathlib import Path
import zipfile,tempfile,shutil,json,sys,re,subprocess,html

ROOT=Path(__file__).resolve().parents[1]
READINGS=ROOT/"readings"
DATA=ROOT/"data"/"readings.json"
HOME=ROOT/"index.html"
SITEMAP=ROOT/"sitemap.xml"
DOMAIN="https://thesomaticimagelab.kurtwespyianatos.com"
CARRY_NOTE_ES='Estas preguntas condensan las tensiones entre el texto leído y su Máquina de Error. Dialogan entre sí, avanzan o retroceden hacia readings de distintos autores y heredan contaminaciones previas para abrir preguntas que sin el error no aparecerían.'
CARRY_NOTE_EN='These questions condense the tensions between the reading and its Error Machine. They speak to one another, move forward or backward across readings by different authors, and inherit previous contaminations to open questions that would not appear without error.'
FLOW_STYLE_ID="tsil-carry-flow-v4"
FLOW_CSS=r"""
<style id="tsil-carry-flow-v4">
.carry-rule{
  margin:10px 0 18px;
  max-width:760px;
  font-size:11px;
  line-height:1.45;
  letter-spacing:.02em;
  color:var(--muted);
}
.reading-nav{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
  margin-top:16px;
}
.reading-nav a,
.reading-nav .nav-block{
  min-height:126px;
  padding:14px;
  border:1px solid var(--line);
  color:inherit;
  text-decoration:none;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}
.reading-nav a:hover{border-color:var(--orange)}
.reading-nav .next{text-align:right}
.nav-label{
  font-size:10px;
  line-height:1.35;
  letter-spacing:.08em;
  text-transform:uppercase;
  color:var(--muted);
}
.nav-q{
  margin-top:20px;
  font-size:15px;
  line-height:1.28;
  letter-spacing:-.01em;
  text-transform:none;
}
.nav-block.pending{border-style:dashed}
.nav-block.start .nav-q{
  color:var(--muted);
  font-size:13px;
}
.carry-source{display:none!important}
@media(max-width:600px){
  .reading-nav{grid-template-columns:1fr}
  .reading-nav .next{text-align:left}
}
</style>
"""


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
    # Canonical design: the last visible nav-q is the outgoing question.
    es_all=re.findall(r'<div class="nav-q" data-copy="es">(.*?)</div>',page,re.S)
    en_all=re.findall(r'<div class="nav-q" data-copy="en">(.*?)</div>',page,re.S)
    if es_all and en_all:
        return strip_tags(es_all[-1]),strip_tags(en_all[-1])

    # Compatibility with older versions.
    for cls in ("carry-source","carry"):
        es=re.search(rf'<div class="{cls}" data-copy="es">(.*?)</div>',page,re.S)
        en=re.search(rf'<div class="{cls}" data-copy="en">(.*?)</div>',page,re.S)
        if es and en:
            return strip_tags(es.group(1)),strip_tags(en.group(1))

    es_all=re.findall(r'<div class="carry-question" data-copy="es">(.*?)</div>',page,re.S)
    en_all=re.findall(r'<div class="carry-question" data-copy="en">(.*?)</div>',page,re.S)
    if es_all and en_all:
        return strip_tags(es_all[-1]),strip_tags(en_all[-1])

    return None,None

def ensure_css(page):
    # Always install the canonical carry CSS last in <head>.
    page=re.sub(
        r'<style id="tsil-carry-flow-v4">.*?</style>\\s*',
        '',
        page,
        flags=re.S
    )
    if "</head>" in page:
        page=page.replace("</head>",FLOW_CSS+"\\n</head>",1)
    else:
        page=page.replace("</style>",FLOW_CSS+"\\n",1)
    return page

def carry_section(own_es,own_en,prev,nxt,prev_es,prev_en):
    if prev:
        left=f"""<a class="prev" href="../{html.escape(prev["slug"])}/index.html">
  <div>
    <div class="nav-label" data-copy="es">← viene de {int(prev["number"]):03d} · {html.escape(prev["author"])}</div>
    <div class="nav-label" data-copy="en">← comes from {int(prev["number"]):03d} · {html.escape(prev["author"])}</div>
    <div class="nav-q" data-copy="es">{html.escape(prev_es)}</div>
    <div class="nav-q" data-copy="en">{html.escape(prev_en)}</div>
  </div>
</a>"""
    else:
        left="""<div class="nav-block start">
  <div>
    <div class="nav-label" data-copy="es">inicio de la cadena</div>
    <div class="nav-label" data-copy="en">start of the chain</div>
    <div class="nav-q" data-copy="es">Esta lectura produce la primera pregunta de arrastre.</div>
    <div class="nav-q" data-copy="en">This reading produces the first carry question.</div>
  </div>
</div>"""

    if nxt:
        right=f"""<a class="next" href="../{html.escape(nxt["slug"])}/index.html">
  <div>
    <div class="nav-label" data-copy="es">va hacia {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</div>
    <div class="nav-label" data-copy="en">goes to {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</div>
    <div class="nav-q" data-copy="es">{html.escape(own_es)}</div>
    <div class="nav-q" data-copy="en">{html.escape(own_en)}</div>
  </div>
</a>"""
    else:
        right=f"""<div class="nav-block next pending">
  <div>
    <div class="nav-label" data-copy="es">hacia el próximo texto →</div>
    <div class="nav-label" data-copy="en">toward the next text →</div>
    <div class="nav-q" data-copy="es">{html.escape(own_es)}</div>
    <div class="nav-q" data-copy="en">{html.escape(own_en)}</div>
  </div>
</div>"""

    return f"""<section class="grid">
  <div class="section-title" data-copy="es">arrastre</div>
  <div class="section-title" data-copy="en">carry</div>

  <div>
    <div class="carry-rule" data-copy="es">{CARRY_NOTE_ES}</div>
    <div class="carry-rule" data-copy="en">{CARRY_NOTE_EN}</div>

    <div class="reading-nav">
      {left}
      {right}
    </div>
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

def _applescript_escape(s):
    return str(s).replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")

def confirm_update(old,m):
    num=f'{int(old["number"]):03d}'
    msg=(
        f'{num} ya existe.\\n\\n'
        f'{m["author"]}\\n{m["title_en"]}\\n\\n'
        '¿Quieres actualizar este post manteniendo su número y su URL?'
    )
    script=(
        'display dialog "'+_applescript_escape(msg)+'" '
        'buttons {"Cancelar","Actualizar"} '
        'default button "Actualizar" cancel button "Cancelar" '
        'with title "The Somatic Image Lab"'
    )
    r=subprocess.run(
        ["/usr/bin/osascript","-e",script],
        capture_output=True,text=True
    )
    return r.returncode==0 and "Actualizar" in r.stdout

def update_sitemap(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    urls=[DOMAIN+"/"]+[DOMAIN+"/readings/"+x["slug"]+"/" for x in seq]
    SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        +"\n".join("  <url><loc>"+u+"</loc></url>" for u in urls)
        +'\n</urlset>\n',encoding="utf-8")

def gitpush(title,num,mode):
    subprocess.run(["git","add","-A"],cwd=ROOT,check=False)

    # Nothing changed: not an error.
    staged=subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT)
    if staged.returncode==0:
        print("SIN CAMBIOS NUEVOS PARA GIT.")
        return

    verb="Update" if mode=="update" else "Add"
    r=subprocess.run(
        ["git","commit","-m",f"{verb} reading {num:03d}: {title}"],
        cwd=ROOT
    )
    if r.returncode!=0:
        die("Los archivos se prepararon, pero git commit falló.")

    r=subprocess.run(["git","push"],cwd=ROOT)
    if r.returncode!=0:
        die("El post quedó preparado y guardado en git, pero git push falló.")

def main():
    src=sys.argv[1] if len(sys.argv)>1 else input("Ruta del ZIP:\n> ").strip().strip("'\"")
    pkg,tmp=unpack(src)
    try:
        mf=pkg/"manifest.json"; hp=pkg/"index.html"
        if not mf.exists() or not hp.exists(): die("ERROR: paquete incompleto.")
        m=json.loads(mf.read_text(encoding="utf-8"))
        items=json.loads(DATA.read_text(encoding="utf-8"))

        key=(m["author"].strip().casefold(),m["title_en"].strip().casefold())
        existing=None
        for old in items:
            if (old["author"].strip().casefold(),old["title_en"].strip().casefold())==key:
                existing=old
                break

        # ──────────────────────────────────────────────────────────────
        # UPDATE EXISTING POST
        # Same author + title keeps number, slug and URL.
        # ──────────────────────────────────────────────────────────────
        if existing:
            num=int(existing["number"])
            slug=existing["slug"]

            if not confirm_update(existing,m):
                print(f"\nACTUALIZACIÓN {num:03d} CANCELADA. No se hicieron cambios.\n")
                raise SystemExit(2)

            dest=READINGS/slug
            dest.mkdir(parents=True,exist_ok=True)

            page=hp.read_text(encoding="utf-8")
            page=re.sub(r'(lectura / )\d+',r'\g<1>'+f'{num:03d}',page)
            page=re.sub(r'(reading / )\d+',r'\g<1>'+f'{num:03d}',page)
            (dest/"index.html").write_text(page,encoding="utf-8")

            # Preserve number, slug and original publication date.
            existing.update({
                "author":m["author"],
                "title_es":m["title_es"],
                "title_en":m["title_en"],
                "error_es":m["error_es"],
                "error_en":m["error_en"]
            })
            if not existing.get("date"):
                existing["date"]=m["date"]

            DATA.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
            update_home(items)
            rebuild_carry_flow(items)
            update_sitemap(items)
            gitpush(m["title_en"],num,"update")

            print(f"\nPOST {num:03d} ACTUALIZADO ✓")
            print("MISMO NÚMERO Y URL ✓")
            print("ARRASTRE DOBLE ✓")
            print("HOME ✓")
            print("SITEMAP ✓")
            return

        # ──────────────────────────────────────────────────────────────
        # ADD NEW POST
        # ──────────────────────────────────────────────────────────────
        num=max(int(x["number"]) for x in items)+1
        slug=f'{num:03d}-{slugify(m["slug"])}'
        dest=READINGS/slug
        dest.mkdir(parents=True,exist_ok=True)

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
        gitpush(m["title_en"],num,"add")

        print(f"\nPOST {num:03d} CREADO ✓")
        print("ARRASTRE DOBLE ✓")
        print("HOME ✓")
        print("SITEMAP ✓")
    finally:
        if tmp: shutil.rmtree(tmp,ignore_errors=True)

if __name__=="__main__":
    main()
