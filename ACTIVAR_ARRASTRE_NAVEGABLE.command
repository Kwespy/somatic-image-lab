#!/bin/bash
SITE="/Users/kwy/Library/Mobile Documents/com~apple~CloudDocs/TSIL_PUBLISH"
TARGET="$SITE/scripts/add_post.py"

if [ ! -d "$SITE" ]; then
  echo "ERROR: No encuentro TSIL_PUBLISH en iCloud."
  exit 1
fi

mkdir -p "$SITE/scripts"

cat > "$TARGET" <<'PY'
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
    print("\nERROR:", msg)
    raise SystemExit(1)

def slugify(s):
    trans = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    s = s.translate(trans).lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def unpack(source):
    p = Path(source).expanduser().resolve()
    if not p.exists():
        die("No encuentro: " + str(p))
    if p.is_dir():
        return p, None
    if p.suffix.lower() != ".zip":
        die("Arrastra un ZIP o una carpeta.")
    temp = Path(tempfile.mkdtemp(prefix="tsil_post_"))
    with zipfile.ZipFile(p) as z:
        z.extractall(temp)
    manifests = list(temp.rglob("manifest.json"))
    if not manifests:
        die("El ZIP no contiene manifest.json")
    return manifests[0].parent, temp

def render_card(it):
    n = f'{it["number"]:03d}'
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
    text = HOME.read_text(encoding="utf-8")
    cards = "\n".join(render_card(it) for it in sorted(items, key=lambda x: x["number"], reverse=True))
    text = re.sub(
        r'<!-- POSTS_START -->.*?<!-- POSTS_END -->',
        '<!-- POSTS_START -->\n' + cards + '\n<!-- POSTS_END -->',
        text, flags=re.S
    )
    HOME.write_text(text, encoding="utf-8")

def update_sitemap(items):
    urls = [DOMAIN + "/"] + [DOMAIN + "/readings/" + it["slug"] + "/" for it in items]
    body = "\n".join("  <url><loc>" + u + "</loc></url>" for u in urls)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '\n</urlset>\n'
    SITEMAP.write_text(xml, encoding="utf-8")

def link_previous_carry(previous_slug, new_slug, new_number, new_author):
    """Turn the previous post's ARRASTRE into navigation to the newly published post."""
    p = READINGS / previous_slug / "index.html"
    if not p.exists():
        return

    s = p.read_text(encoding="utf-8")

    # Standardize the section label.
    s = s.replace("arrastrar al próximo texto", "arrastre")
    s = s.replace("carry into the next text", "carry")

    # Remove an older navigation wrapper if this function is run again.
    s = re.sub(
        r'<a class="carry-link"[^>]*>\s*(<div class="carry" data-copy="es">.*?</div>\s*<div class="carry" data-copy="en">.*?</div>)\s*<div class="carry-next".*?</div>\s*</a>',
        r'\1',
        s,
        flags=re.S
    )

    pair = re.search(
        r'(<div class="carry" data-copy="es">.*?</div>\s*<div class="carry" data-copy="en">.*?</div>)',
        s,
        flags=re.S
    )
    if not pair:
        return

    rel = f"../{new_slug}/index.html"
    nav = (
        f'<a class="carry-link" href="{html.escape(rel)}" '
        'style="display:block;color:inherit;text-decoration:none;cursor:pointer" '
        f'aria-label="Ir a la lectura {new_number:03d}">\n'
        + pair.group(1)
        + '\n<div class="carry-next" style="margin-top:8px;text-align:right;font-size:11px;'
          'letter-spacing:.08em;text-transform:uppercase;color:var(--muted)">'
        + f'<span data-inline="es">seguir → {new_number:03d} · {html.escape(new_author)}</span>'
        + f'<span data-inline="en">continue → {new_number:03d} · {html.escape(new_author)}</span>'
        + '</div>\n</a>'
    )
    s = s[:pair.start()] + nav + s[pair.end():]
    p.write_text(s, encoding="utf-8")

def git_push(title):
    if not (ROOT / ".git").exists():
        print("\nPOST AGREGADO LOCALMENTE. Falta inicializar Git.")
        return
    subprocess.run(["git","add","-A"], cwd=ROOT)
    subprocess.run(["git","commit","-m","Add reading: " + title], cwd=ROOT)
    r = subprocess.run(["git","push"], cwd=ROOT)
    if r.returncode == 0:
        print("\n✓ GITHUB ACTUALIZADO")
    else:
        print("\nEl post quedó instalado, pero git push falló.")

def main():
    source = sys.argv[1] if len(sys.argv) > 1 else input("Arrastra el ZIP del post:\n> ").strip().strip("'\"")
    pkg, temp = unpack(source)
    try:
        mf = pkg / "manifest.json"
        hp = pkg / "index.html"
        if not mf.exists() or not hp.exists():
            die("El paquete necesita manifest.json e index.html")

        m = json.loads(mf.read_text(encoding="utf-8"))
        required = ["author","title_es","title_en","date","slug","error_es","error_en"]
        for key in required:
            if not m.get(key):
                die("Falta " + key + " en manifest.json")

        items = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []
        previous = max(items, key=lambda x: x["number"]) if items else None

        num = max([x["number"] for x in items], default=0) + 1
        slug = f"{num:03d}-{slugify(m['slug'])}"
        dest = READINGS / slug
        if dest.exists():
            die("Ya existe " + slug)

        dest.mkdir(parents=True)
        shutil.copy2(hp, dest/"index.html")

        rec = {
            "number": num,
            "slug": slug,
            "author": m["author"],
            "title_es": m["title_es"],
            "title_en": m["title_en"],
            "date": m["date"],
            "error_es": m["error_es"],
            "error_en": m["error_en"]
        }
        items.append(rec)

        # The key behavior: only when the new post exists,
        # the previous post's ARRASTRE becomes a link to it.
        if previous:
            link_previous_carry(
                previous["slug"],
                slug,
                num,
                m["author"]
            )

        DATA.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        update_home(items)
        update_sitemap(items)
        git_push(m["title_en"])

        print("\nPOST %03d ✓" % num)
        print(m["author"] + " — " + m["title_es"])
        print("ARRASTRE ANTERIOR → POST %03d ✓" % num)
        print("HOME ✓")
        print("SITEMAP ✓")
    finally:
        if temp:
            shutil.rmtree(temp, ignore_errors=True)

if __name__ == "__main__":
    main()
PY

chmod +x "$TARGET"

# If 002 is already installed, make 001 navigable immediately.
python3 - "$SITE" <<'PY'
from pathlib import Path
import re, html, sys, json

root=Path(sys.argv[1])
data=root/"data"/"readings.json"
if not data.exists():
    raise SystemExit

items=json.loads(data.read_text(encoding="utf-8"))
items=sorted(items,key=lambda x:x["number"])
if len(items) < 2:
    raise SystemExit

prev, nxt = items[-2], items[-1]
p=root/"readings"/prev["slug"]/"index.html"
if not p.exists():
    raise SystemExit

s=p.read_text(encoding="utf-8")
s=s.replace("arrastrar al próximo texto","arrastre")
s=s.replace("carry into the next text","carry")

if 'class="carry-link"' not in s:
    pair=re.search(r'(<div class="carry" data-copy="es">.*?</div>\s*<div class="carry" data-copy="en">.*?</div>)',s,re.S)
    if pair:
        rel=f'../{nxt["slug"]}/index.html'
        nav=(
            f'<a class="carry-link" href="{html.escape(rel)}" '
            'style="display:block;color:inherit;text-decoration:none;cursor:pointer">\n'
            + pair.group(1)
            + '\n<div class="carry-next" style="margin-top:8px;text-align:right;font-size:11px;'
              'letter-spacing:.08em;text-transform:uppercase;color:var(--muted)">'
            + f'<span data-inline="es">seguir → {nxt["number"]:03d} · {html.escape(nxt["author"])}</span>'
            + f'<span data-inline="en">continue → {nxt["number"]:03d} · {html.escape(nxt["author"])}</span>'
            + '</div>\n</a>'
        )
        s=s[:pair.start()]+nav+s[pair.end():]
        p.write_text(s,encoding="utf-8")
PY

cd "$SITE" || exit 1
git add scripts/add_post.py readings/ data/readings.json index.html sitemap.xml 2>/dev/null
git commit -m "Make carry navigate to next reading" 2>/dev/null || true
git push

echo
echo "✓ FLUJO ACTUALIZADO"
echo "Desde ahora:"
echo "001 ARRASTRE → 002"
echo "002 ARRASTRE → 003 cuando publiques 003"
echo "003 ARRASTRE → 004 cuando publiques 004"
