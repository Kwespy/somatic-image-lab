#!/usr/bin/env python3
from pathlib import Path
import zipfile,tempfile,shutil,json,sys,re,subprocess,html

ROOT=Path(__file__).resolve().parents[1]
READINGS=ROOT/"readings"
DATA=ROOT/"data"/"readings.json"
HOME=ROOT/"index.html"
SITEMAP=ROOT/"sitemap.xml"
DOMAIN="https://thesomaticimagelab.kurtwespyianatos.com"
CARRY_NOTE_ES='Esta pregunta comprime las tensiones del texto y de su Máquina de Error. Hereda las contaminaciones anteriores para que el error se acumule y abra nuevas posibilidades.'
CARRY_NOTE_EN='This question compresses the tensions of the text and its Error Machine. It inherits previous contaminations so error can accumulate and open new possibilities.'
CARRY_RULE_CSS='\n.carry-rule{\n  margin:10px 0 18px;\n  max-width:720px;\n  font-size:11px;\n  line-height:1.45;\n  letter-spacing:.02em;\n  color:var(--muted);\n}\n'

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
.reading-nav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.reading-nav a,.reading-nav .empty{
  min-height:48px;padding:12px 14px;border:1px solid var(--line);color:inherit;
  text-decoration:none;font-size:11px;line-height:1.35;letter-spacing:.07em;text-transform:uppercase
}
.reading-nav a:hover{border-color:var(--orange)}
.reading-nav .next{text-align:right}
.reading-nav .empty{border-color:transparent}
@media(max-width:600px){
  .random-start{align-items:flex-start}
  .reading-nav{grid-template-columns:1fr}
  .reading-nav .next{text-align:left}
}
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
    if p.suffix.lower()!=".zip": die("ERROR: arrastra un ZIP.")
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
    s=re.sub(r'<!-- POSTS_START -->.*?<!-- POSTS_END -->',
             '<!-- POSTS_START -->\n'+cards+'\n<!-- POSTS_END -->',s,flags=re.S)
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


def ensure_carry_rule(s):
    s=s.replace("arrastrar al próximo texto","arrastre").replace("carry into the next text","carry")
    if ".carry-rule{" not in s:
        s=s.replace("</style>",CARRY_RULE_CSS+"\n</style>",1)
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
              +f'\n<div class="carry-rule" data-copy="es">{CARRY_NOTE_ES}</div>'
              +f'\n<div class="carry-rule" data-copy="en">{CARRY_NOTE_EN}</div>')
        s=s[:pair.start()]+note+s[pair.end():]
    return s

def strip_nav(s):
    s=re.sub(r'\s*<div class="reading-nav">.*?</div>\s*(?=</section>)','\n',s,flags=re.S)
    s=re.sub(
        r'<a class="carry-link"[^>]*>\s*'
        r'(<div class="carry" data-copy="es">.*?</div>\s*'
        r'<div class="carry" data-copy="en">.*?</div>)'
        r'.*?</a>',
        r'\1',s,flags=re.S
    )
    return s

def rebuild_nav(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    for i,cur in enumerate(seq):
        p=READINGS/cur["slug"]/"index.html"
        if not p.exists(): continue
        s=strip_nav(p.read_text(encoding="utf-8"))
        s=s.replace("arrastrar al próximo texto","arrastre").replace("carry into the next text","carry")
        s=ensure_carry_rule(s)
        if ".reading-nav{" not in s:
            s=s.replace("</style>",RANDOM_CSS+"\n</style>",1)
        pair=re.search(
            r'(<div class="carry" data-copy="es">.*?</div>\s*'
            r'<div class="carry" data-copy="en">.*?</div>)',
            s,re.S
        )
        if not pair: continue
        prev=seq[i-1] if i>0 else None
        nxt=seq[i+1] if i+1<len(seq) else None

        if prev:
            left=(f'<a class="prev" href="../{html.escape(prev["slug"])}/index.html">'
                  f'<span data-inline="es">← anterior · {int(prev["number"]):03d} · {html.escape(prev["author"])}</span>'
                  f'<span data-inline="en">← previous · {int(prev["number"]):03d} · {html.escape(prev["author"])}</span></a>')
        else:
            left='<div class="empty"></div>'

        if nxt:
            right=(f'<a class="next" href="../{html.escape(nxt["slug"])}/index.html">'
                   f'<span data-inline="es">siguiente · {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span>'
                   f'<span data-inline="en">next · {int(nxt["number"]):03d} · {html.escape(nxt["author"])} →</span></a>')
        else:
            right='<div class="empty"></div>'

        nav='<div class="reading-nav">\n'+left+'\n'+right+'\n</div>'
        s=s[:pair.start()]+pair.group(1)+'\n'+nav+s[pair.end():]
        p.write_text(s,encoding="utf-8")

def update_sitemap(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    urls=[DOMAIN+"/"]+[DOMAIN+"/readings/"+x["slug"]+"/" for x in seq]
    SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        +"\n".join("  <url><loc>"+u+"</loc></url>" for u in urls)
        +'\n</urlset>\n',
        encoding="utf-8"
    )

def gitpush(title):
    subprocess.run(["git","add","-A"],cwd=ROOT)
    subprocess.run(["git","commit","-m","Add reading: "+title],cwd=ROOT)
    subprocess.run(["git","push"],cwd=ROOT)

def main():
    src=sys.argv[1] if len(sys.argv)>1 else input("Arrastra el ZIP del post:\n> ").strip().strip("'\"")
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
        rebuild_nav(items)
        update_sitemap(items)
        gitpush(m["title_en"])
        print(f"\nPOST {num:03d} ✓")
    finally:
        if tmp: shutil.rmtree(tmp,ignore_errors=True)

if __name__=="__main__":
    main()
