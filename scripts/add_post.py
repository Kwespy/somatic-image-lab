#!/usr/bin/env python3
from pathlib import Path
import zipfile, tempfile, shutil, json, sys, re, subprocess, html

ROOT = Path(__file__).resolve().parents[1]
READINGS = ROOT / "readings"
DATA = ROOT / "data" / "readings.json"
HOME = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
DOMAIN = "https://thesomaticimagelab.kurtwespyianatos.com"

def die(msg):
    print("\n" + msg + "\n")
    raise SystemExit(1)

def slugify(s):
    trans = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    s = s.translate(trans).lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def unpack(source):
    p = Path(source).expanduser().resolve()
    if not p.exists():
        die("ERROR: no encuentro " + str(p))
    if p.is_dir():
        return p, None
    if p.suffix.lower() != ".zip":
        die("ERROR: arrastra un ZIP de post.")
    temp = Path(tempfile.mkdtemp(prefix="tsil_post_"))
    with zipfile.ZipFile(p) as z:
        z.extractall(temp)
    manifests = list(temp.rglob("manifest.json"))
    if not manifests:
        die("ERROR: el ZIP no contiene manifest.json")
    return manifests[0].parent, temp

def render_card(it):
    n=f'{int(it["number"]):03d}'
    return (
        '<a class="post-card" href="readings/{slug}/index.html">\n'
        '  <div class="post-number">{n}</div>\n'
        '  <div>\n'
        '    <h2 class="post-title" data-copy="es">{tes}</h2>\n'
        '    <h2 class="post-title" data-copy="en">{ten}</h2>\n'
        '    <div class="post-author">{author}</div>\n'
        '    <div class="post-meta">\n'
        '      <span data-inline="es">lectura / umbral /</span>\n'
        '      <span data-inline="en">reading / threshold /</span>\n'
        '      <span class="error-pill" data-inline="es">error forzado: {ees}</span>\n'
        '      <span class="error-pill" data-inline="en">forced error: {een}</span>\n'
        '    </div>\n'
        '  </div>\n'
        '  <div class="post-arrow">→</div>\n'
        '</a>'
    ).format(
        slug=html.escape(it["slug"]), n=n,
        tes=html.escape(it["title_es"]), ten=html.escape(it["title_en"]),
        author=html.escape(it["author"]),
        ees=html.escape(it["error_es"]), een=html.escape(it["error_en"])
    )

def update_home(items):
    s=HOME.read_text(encoding="utf-8")
    cards="\n".join(render_card(x) for x in sorted(items,key=lambda x:int(x["number"]),reverse=True))
    s=re.sub(r'<!-- POSTS_START -->.*?<!-- POSTS_END -->',
             '<!-- POSTS_START -->\n'+cards+'\n<!-- POSTS_END -->',s,flags=re.S)
    HOME.write_text(s,encoding="utf-8")

def unwrap_carry(s):
    return re.sub(
        r'<a class="carry-link"[^>]*>\s*'
        r'(<div class="carry" data-copy="es">.*?</div>\s*'
        r'<div class="carry" data-copy="en">.*?</div>)'
        r'.*?</a>',
        r'\1', s, flags=re.S
    )

def set_carry(post,nxt=None):
    p=READINGS/post["slug"]/"index.html"
    if not p.exists(): return
    s=unwrap_carry(p.read_text(encoding="utf-8"))
    s=s.replace("arrastrar al próximo texto","arrastre")
    s=s.replace("carry into the next text","carry")
    pair=re.search(
        r'(<div class="carry" data-copy="es">.*?</div>\s*'
        r'<div class="carry" data-copy="en">.*?</div>)',s,re.S)
    if pair and nxt:
        href=f'../{nxt["slug"]}/index.html'
        num=f'{int(nxt["number"]):03d}'
        nav=(
          f'<a class="carry-link" href="{html.escape(href)}" '
          'style="display:block;color:inherit;text-decoration:none;cursor:pointer">'
          +pair.group(1)+
          '<div class="carry-next" style="margin-top:10px;text-align:right;'
          'font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)">'
          f'<span data-inline="es">seguir → {num} · {html.escape(nxt["author"])}</span>'
          f'<span data-inline="en">continue → {num} · {html.escape(nxt["author"])}</span>'
          '</div></a>'
        )
        s=s[:pair.start()]+nav+s[pair.end():]
    p.write_text(s,encoding="utf-8")

def rebuild_chain(items):
    seq=sorted(items,key=lambda x:int(x["number"]))
    for i,it in enumerate(seq):
        set_carry(it,seq[i+1] if i+1<len(seq) else None)

def update_sitemap(items):
    urls=[DOMAIN+"/"]+[DOMAIN+"/readings/"+x["slug"]+"/" for x in sorted(items,key=lambda x:int(x["number"]))]
    body="\n".join("  <url><loc>"+u+"</loc></url>" for u in urls)
    SITEMAP.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                       +body+'\n</urlset>\n',encoding="utf-8")

def git_push(title):
    subprocess.run(["git","add","-A"],cwd=ROOT)
    subprocess.run(["git","commit","-m","Add reading: "+title],cwd=ROOT)
    r=subprocess.run(["git","push"],cwd=ROOT)
    if r.returncode==0: print("\n✓ GITHUB ACTUALIZADO")

def main():
    source=sys.argv[1] if len(sys.argv)>1 else input("Arrastra el ZIP del post:\n> ").strip().strip("'\"")
    pkg,temp=unpack(source)
    try:
        mf=pkg/"manifest.json"
        hp=pkg/"index.html"
        if not mf.exists() or not hp.exists():
            die("ERROR: el paquete necesita manifest.json e index.html")

        m=json.loads(mf.read_text(encoding="utf-8"))
        items=json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []

        key=(m["author"].strip().casefold(),m["title_en"].strip().casefold())
        for old in items:
            oldkey=(old["author"].strip().casefold(),old["title_en"].strip().casefold())
            if oldkey==key:
                die(f'YA EXISTE COMO {int(old["number"]):03d}. No se volvió a publicar.')

        num=max([int(x["number"]) for x in items],default=0)+1
        slug=f'{num:03d}-{slugify(m["slug"])}'
        dest=READINGS/slug
        dest.mkdir(parents=True)

        page=hp.read_text(encoding="utf-8")
        page=re.sub(r'(lectura / )\d+',r'\g<1>'+f'{num:03d}',page)
        page=re.sub(r'(reading / )\d+',r'\g<1>'+f'{num:03d}',page)
        (dest/"index.html").write_text(page,encoding="utf-8")

        rec={"number":num,"slug":slug,"author":m["author"],
             "title_es":m["title_es"],"title_en":m["title_en"],
             "date":m["date"],"error_es":m["error_es"],"error_en":m["error_en"]}
        items.append(rec)

        DATA.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
        update_home(items)
        rebuild_chain(items)
        update_sitemap(items)
        git_push(m["title_en"])

        print(f'\nPOST {num:03d} ✓')
        print('ARRASTRE ANTERIOR → ESTE POST ✓')
    finally:
        if temp: shutil.rmtree(temp,ignore_errors=True)

if __name__=="__main__":
    main()
