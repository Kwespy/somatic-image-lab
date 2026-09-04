#!/usr/bin/env python3
from pathlib import Path
import re, json, html as htmllib, subprocess, tempfile, shutil, zipfile

DOMAIN = "https://thesomaticimagelab.kurtwespyianatos.com"
AUTHOR_SITE = "https://www.kurtwespyianatos.com/"
SITE_AUTHOR = "Kurt Wesp Yianatos"
META_START = "<!-- TSIL_SOCIAL_META_START -->"
META_END = "<!-- TSIL_SOCIAL_META_END -->"
STYLE_START = "<!-- TSIL_SOCIAL_STYLE_START -->"
STYLE_END = "<!-- TSIL_SOCIAL_STYLE_END -->"
SCRIPT_START = "<!-- TSIL_SOCIAL_SCRIPT_START -->"
SCRIPT_END = "<!-- TSIL_SOCIAL_SCRIPT_END -->"
ASCII_STYLES = ["dense", "dotted", "glitch", "textmatrix", "gradient", "lines", "erasure", "outline"]
STOP_ES = {"de","la","el","los","las","un","una","y","o","en","a","por","para","del","al"}
STOP_EN = {"the","of","and","or","in","to","for","an","a","on","with"}


def strip_tags(s):
    s = re.sub(r'<br\s*/?>', ' ', s or '', flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    return htmllib.unescape(re.sub(r'\s+', ' ', s)).strip()


def extract_class_lang(page, cls, lang):
    pat = re.compile(
        rf'<(?P<tag>[a-z0-9]+)(?=[^>]*\bclass=["\'][^"\']*\b{re.escape(cls)}\b[^"\']*["\'])(?=[^>]*\bdata-copy=["\']{lang}["\'])[^>]*>(?P<body>.*?)</(?P=tag)>',
        re.I | re.S,
    )
    m = pat.search(page)
    return strip_tags(m.group('body')) if m else ''


def split_title(title):
    title = (title or '').strip()
    if ':' in title:
        a, b = title.split(':', 1)
        return a.strip(), b.strip()
    return title, ''


def short_description(text, max_chars=260):
    text = strip_tags(text)
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out = ''
    for s in sentences:
        trial = (out + ' ' + s).strip()
        if len(trial) > max_chars and out:
            break
        out = trial
        if len(out) >= 150:
            break
    if len(out) > max_chars:
        out = out[:max_chars-1].rstrip() + '…'
    return out


def concepts_for(band, error_word, lang):
    stop = STOP_ES if lang == 'es' else STOP_EN
    vals = []
    for pri, raw in [(0, band), (1, error_word)]:
        parts = raw.split('→') if pri == 0 else [raw]
        for p in parts:
            p = re.sub(r'[^\w\-À-ÿ ]+', ' ', p, flags=re.U)
            p = re.sub(r'\s+', ' ', p).strip()
            if not p:
                continue
            toks = [x.casefold() for x in p.split()]
            if all(t in stop for t in toks):
                continue
            compact = re.sub(r'\s+', '', p)
            if len(compact) < 3:
                continue
            vals.append((len(compact), pri, p.upper()))
    vals.sort(key=lambda x: (x[0], x[1], x[2]))
    out = []
    for _, _, v in vals:
        if v not in out:
            out.append(v)
    if not out:
        out = ['IMAGEN' if lang == 'es' else 'IMAGE']
    while len(out) < 4:
        out.append(out[len(out) % len(out)])
    return out[:4]


def reading_data(item, page):
    band = {lang: extract_class_lang(page, 'text', lang) for lang in ('es', 'en')}
    err_ctx = {lang: extract_class_lang(page, 'error-context', lang) for lang in ('es', 'en')}
    err_word = {
        'es': extract_class_lang(page, 'error-word', 'es') or item.get('error_es', ''),
        'en': extract_class_lang(page, 'error-word', 'en') or item.get('error_en', ''),
    }
    lead = {lang: extract_class_lang(page, 'article-lead', lang) for lang in ('es', 'en')}
    desc = {lang: short_description(lead[lang]) for lang in ('es', 'en')}
    titles = {'es': item['title_es'], 'en': item['title_en']}
    parts, concepts = {}, {}
    for lang in ('es', 'en'):
        a, b = split_title(titles[lang])
        parts[lang] = {'title': a, 'subtitle': b}
        concepts[lang] = concepts_for(band[lang], err_word[lang], lang)
    return {
        'number': int(item['number']),
        'slug': item['slug'],
        'author': item['author'],
        'date': item.get('date', ''),
        'canonical': f"{DOMAIN}/readings/{item['slug']}/",
        'title': titles,
        'parts': parts,
        'lead': lead,
        'description': desc,
        'band': band,
        'error_context': err_ctx,
        'error_word': err_word,
        'concepts': concepts,
    }


def esc(s):
    return htmllib.escape(str(s or ''), quote=True)


def meta_block(d):
    n = d['number']
    title = d['title']['en']
    author = d['author']
    canonical = d['canonical']
    desc = d['description']['en'] or f"TSIL Reading {n:03d}: {title} by {author}. Bilingual ES / EN."
    og = canonical + 'share-og.png'
    keywords = []
    for x in [author, title, d['band']['en'], d['error_context']['en'], d['error_word']['en'], 'The Somatic Image Lab', SITE_AUTHOR]:
        if x:
            keywords.append(x)
    schema = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'mainEntityOfPage': {'@type': 'WebPage', '@id': canonical},
        'headline': f"{title} — {author}",
        'description': desc,
        'datePublished': d.get('date') or None,
        'inLanguage': ['en', 'es'],
        'author': {'@type': 'Person', 'name': SITE_AUTHOR, 'url': AUTHOR_SITE, 'alternateName': ['KWY', 'KWY-A⁰¹RTBORG']},
        'publisher': {'@type': 'Organization', 'name': 'The Somatic Image Lab', 'url': DOMAIN + '/'},
        'isBasedOn': {'@type': 'Book', 'name': title, 'author': {'@type': 'Person', 'name': author}},
        'image': [
            {'@type': 'ImageObject', 'url': og, 'width': 1200, 'height': 630},
            {'@type': 'ImageObject', 'url': canonical + 'share-post-en.png', 'width': 1080, 'height': 1350},
            {'@type': 'ImageObject', 'url': canonical + 'share-post-es.png', 'width': 1080, 'height': 1350},
        ],
        'about': [x for x in [d['band']['en'], d['error_context']['en'], d['error_word']['en']] if x],
    }
    schema = {k: v for k, v in schema.items() if v is not None}
    schema_text = json.dumps(schema, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    data_text = json.dumps(d, ensure_ascii=False).replace('</', '<\\/')
    return f'''{META_START}
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{SITE_AUTHOR}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="keywords" content="{esc(', '.join(keywords))}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Somatic Image Lab">
<meta property="og:title" content="{esc(title + ' — ' + author)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og)}">
<meta property="og:image:secure_url" content="{esc(og)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc('The Somatic Image Lab — Reading ' + f'{n:03d}' + ' — ' + title + ' — ' + author)}">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="es_ES">
<meta property="article:published_time" content="{esc(d.get('date', ''))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title + ' — ' + author)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(og)}">
<meta name="theme-color" content="#f2efe7">
<script type="application/ld+json">{schema_text}</script>
<script id="tsil-social-data" type="application/json">{data_text}</script>
{META_END}'''


SOCIAL_CSS = '''<!-- TSIL_SOCIAL_STYLE_START -->
<style id="tsil-social-secret-style">
.tsil-secret-story{cursor:default!important}
.tsil-secret-story:focus{outline:none!important}
#tsil-secret-export{position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.72);display:none;align-items:center;justify-content:center;padding:20px}
#tsil-secret-export.open{display:flex}
#tsil-secret-export .tsil-export-box{width:min(420px,92vw);background:#f2efe7;color:#0a0a0a;border:1px solid #0a0a0a;padding:18px;font-family:Arial,Helvetica,sans-serif}
#tsil-secret-export .tsil-export-head{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;border-bottom:1px solid #bbb4aa;font-size:10px;letter-spacing:.14em;text-transform:uppercase}
#tsil-secret-export .tsil-export-close{border:0;background:none;color:inherit;font:inherit;padding:0;cursor:pointer}
#tsil-secret-export .tsil-export-grid{display:grid;grid-template-columns:1fr;gap:8px;margin-top:14px}
#tsil-secret-export .tsil-export-btn{border:1px solid #bbb4aa;background:transparent;color:inherit;padding:11px 12px;text-align:left;font:11px/1.15 Arial,Helvetica,sans-serif;letter-spacing:.08em;text-transform:uppercase;cursor:pointer}
#tsil-secret-export .tsil-export-btn:hover{border-color:#ff4b17;color:#ff4b17}
#tsil-secret-export .tsil-export-note{margin-top:12px;font-size:9px;line-height:1.4;color:#706b63}
</style>
<!-- TSIL_SOCIAL_STYLE_END -->'''


SOCIAL_JS = '''<!-- TSIL_SOCIAL_SCRIPT_START -->
<script id="tsil-social-secret-runtime">
(()=>{
  const dataEl=document.getElementById('tsil-social-data');
  if(!dataEl)return;
  const D=JSON.parse(dataEl.textContent);
  const pad=n=>String(n).padStart(2,'0');
  const currentLang=()=>document.documentElement.getAttribute('data-lang')==='en'?'en':'es';
  const randomStoryName=()=>`share-story-${currentLang()}-${pad(1+Math.floor(Math.random()*8))}.png`;
  const postName=()=>`share-post-${currentLang()}.png`;
  const abs=name=>new URL(name,location.href).href;

  async function getFile(name){
    const r=await fetch(abs(name),{cache:'no-store'});
    if(!r.ok)throw new Error('asset unavailable: '+name);
    const blob=await r.blob();
    return new File([blob],name,{type:blob.type||'image/png'});
  }
  async function download(name){
    try{
      const file=await getFile(name);
      const u=URL.createObjectURL(file);
      const a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(u),2500);
    }catch(e){window.open(abs(name),'_blank','noopener')}
  }
  async function shareAsset(name){
    try{
      const file=await getFile(name);
      const lang=currentLang();
      const title=(D.title?.[lang]||D.title?.en||'TSIL Reading');
      const txt=`${title} — ${D.author} · The Somatic Image Lab`;
      try{await navigator.clipboard?.writeText(D.canonical)}catch(e){}
      if(navigator.share && (!navigator.canShare || navigator.canShare({files:[file]}))){
        await navigator.share({files:[file],title:title,text:txt,url:D.canonical});
      }else{
        await download(name);
      }
    }catch(e){await download(name)}
  }
  async function copyLink(){try{await navigator.clipboard.writeText(D.canonical)}catch(e){}}

  function ensurePanel(){
    let panel=document.getElementById('tsil-secret-export');
    if(panel)return panel;
    panel=document.createElement('div');
    panel.id='tsil-secret-export';
    panel.innerHTML=`<div class="tsil-export-box" role="dialog" aria-modal="true" aria-label="TSIL export">
      <div class="tsil-export-head"><span>TSIL / EXPORT</span><button class="tsil-export-close" type="button">×</button></div>
      <div class="tsil-export-grid">
        <button class="tsil-export-btn" data-action="story-download" type="button">DOWNLOAD STORY 9:16 · RANDOM ASCII</button>
        <button class="tsil-export-btn" data-action="story-share" type="button">SHARE STORY 9:16 · RANDOM ASCII</button>
        <button class="tsil-export-btn" data-action="post-download" type="button">DOWNLOAD INSTAGRAM POST 4:5</button>
        <button class="tsil-export-btn" data-action="post-share" type="button">SHARE INSTAGRAM POST 4:5</button>
        <button class="tsil-export-btn" data-action="og-download" type="button">DOWNLOAD LINK PREVIEW 1200×630</button>
        <button class="tsil-export-btn" data-action="copy" type="button">COPY READING LINK</button>
        <button class="tsil-export-btn" data-action="all" type="button">DOWNLOAD ALL SOCIAL ASSETS · ZIP</button>
      </div>
      <div class="tsil-export-note">Story uses the active ES / EN language and chooses one of eight ASCII variants at random.</div>
    </div>`;
    document.body.appendChild(panel);
    const close=()=>panel.classList.remove('open');
    panel.querySelector('.tsil-export-close').addEventListener('click',close);
    panel.addEventListener('click',e=>{if(e.target===panel)close()});
    panel.querySelector('[data-action="story-download"]').addEventListener('click',()=>download(randomStoryName()));
    panel.querySelector('[data-action="story-share"]').addEventListener('click',()=>shareAsset(randomStoryName()));
    panel.querySelector('[data-action="post-download"]').addEventListener('click',()=>download(postName()));
    panel.querySelector('[data-action="post-share"]').addEventListener('click',()=>shareAsset(postName()));
    panel.querySelector('[data-action="og-download"]').addEventListener('click',()=>download('share-og.png'));
    panel.querySelector('[data-action="copy"]').addEventListener('click',copyLink);
    panel.querySelector('[data-action="all"]').addEventListener('click',()=>download('tsil-social-assets.zip'));
    return panel;
  }
  function openPanel(){ensurePanel().classList.add('open')}
  document.querySelectorAll('.tsil-secret-story').forEach(el=>{
    el.setAttribute('role','button');
    el.setAttribute('tabindex','0');
    el.addEventListener('click',openPanel);
    el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openPanel()}});
  });
})();
</script>
<!-- TSIL_SOCIAL_SCRIPT_END -->'''


def remove_old(page):
    for a, b in [(META_START, META_END), (STYLE_START, STYLE_END), (SCRIPT_START, SCRIPT_END)]:
        page = re.sub(re.escape(a) + r'.*?' + re.escape(b) + r'\s*', '', page, flags=re.S)
    page = re.sub(r'<!-- TSIL_SHARE_STYLE_START -->.*?<!-- TSIL_SHARE_STYLE_END -->\s*', '', page, flags=re.S)
    page = re.sub(r'<!-- TSIL_SHARE_SCRIPT_START -->.*?<!-- TSIL_SHARE_SCRIPT_END -->\s*', '', page, flags=re.S)
    page = re.sub(r'<button[^>]*(?:story-share-btn|tsil-story-btn)[^>]*>.*?</button>\s*', '', page, flags=re.I | re.S)
    page = re.sub(r'<meta\s+name=["\'](?:description|author|robots|keywords|twitter:[^"\']+)["\'][^>]*>\s*', '', page, flags=re.I)
    page = re.sub(r'<meta\s+property=["\'](?:og:[^"\']+|article:published_time)["\'][^>]*>\s*', '', page, flags=re.I)
    page = re.sub(r'<link\s+rel=["\']canonical["\'][^>]*>\s*', '', page, flags=re.I)
    page = re.sub(r'<script\s+type=["\']application/ld\+json["\'][^>]*>.*?</script>\s*', '', page, flags=re.I | re.S)
    page = re.sub(r'\s+class=["\']tsil-secret-story["\']', '', page)
    return page


def patch_html(page, d):
    page = remove_old(page)
    page = page.replace('<span>KWY-A⁰¹RTBORG</span>', '<span class="tsil-secret-story">KWY-A⁰¹RTBORG</span>')
    if '</head>' in page:
        page = page.replace('</head>', meta_block(d) + '\n' + SOCIAL_CSS + '\n</head>', 1)
    else:
        page = meta_block(d) + '\n' + SOCIAL_CSS + '\n' + page
    if '</body>' in page:
        page = page.replace('</body>', SOCIAL_JS + '\n</body>', 1)
    else:
        page += SOCIAL_JS
    return page


# EXACT approved Story master. Internal proportions are not altered.
STORY_STYLE = r'''
:root{--paper:#f2efe7;--ink:#0a0a0a;--muted:#787168;--line:#c5beb3;--orange:#ff5a1f}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;background:#ddd8cf;color:var(--ink);font-family:Arial,Helvetica,sans-serif;display:flex;align-items:flex-start;justify-content:center;padding:24px}
.poster{width:min(100%,720px);aspect-ratio:1080/1920;background:var(--paper);border:1px solid #d8d1c6;box-shadow:0 2px 20px rgba(0,0,0,.06);padding:3.4% 5.3% 3.2%;display:flex;flex-direction:column;container-type:inline-size;overflow:hidden}
.header{display:flex;justify-content:space-between;align-items:flex-start;font-size:1.72cqw;letter-spacing:.17em;text-transform:uppercase;padding-top:.4%}.lang{display:flex;gap:.45em;align-items:center}.lang .slash{color:var(--orange)}.topline,.bottomline{border:0;border-top:2px solid var(--line)}.topline{margin:2.45% 0 0}.reading{margin-top:5.6%;font-size:2.15cqw;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.ascii-wrap{--ascii-gap:12.6cqw;margin-top:var(--ascii-gap);margin-bottom:16cqw;width:100%;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;flex:1 1 auto;min-height:0}.ascii-band{width:100%;overflow:hidden;flex:0 0 auto;min-height:0;display:block}.ascii-band+.ascii-band{margin-top:0}.ascii{margin:0;font-family:"Courier New",Courier,monospace;font-size:4.8cqw;line-height:.54;letter-spacing:-.09em;font-weight:900;white-space:pre;color:var(--ink);transform:scaleX(1.11);transform-origin:left top}.ascii-band:nth-child(2) .ascii{transform:scaleX(1.11) translateX(-1.6%);opacity:.97}.ascii-band:nth-child(3) .ascii{transform:scaleX(1.11) translateX(.8%);opacity:.95}.ascii-band:nth-child(4) .ascii{transform:scaleX(1.11) translateX(-.7%);opacity:.96}
.bottom-content{flex:0 0 auto;width:62%;max-width:62%}.title-block{margin-top:0}.title{margin:0;font-size:11.2cqw;line-height:.84;font-weight:800;letter-spacing:-.06em}.subtitle{margin:1.8% 0 0;font-size:3.95cqw;line-height:.98;letter-spacing:-.03em;font-weight:400}.author{margin:1.5% 0 0;font-size:3.8cqw;line-height:1;letter-spacing:-.02em;font-weight:400}.error{margin-top:6.4%}.error-label{margin:0;font-size:2.2cqw;line-height:1;font-weight:300;letter-spacing:.15em;text-transform:uppercase;color:var(--muted)}.error-context{margin:2.4% 0 0;font-size:2.45cqw;line-height:1;font-weight:300;letter-spacing:.10em;text-transform:uppercase;color:#5b5650}.error-context .slash{color:var(--orange);padding:0 .38em}.error-word-row{margin-top:1.65%;display:flex;align-items:center;gap:1.6%}.error-arrow{font-size:4cqw;line-height:1;font-weight:300;color:var(--orange)}.error-word{display:inline-block;background:var(--orange);padding:.52% 1.75% .6%;font-family:"Courier New",Courier,monospace;font-size:2.95cqw;line-height:1;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.footer{margin-top:6.2%}.bottomline{margin:0 0 3.2%}.footer-row{display:flex;justify-content:space-between;align-items:flex-end}.brand{font-size:1.95cqw;line-height:1;letter-spacing:.15em;text-transform:uppercase}.footer-arrow{font-size:4.65cqw;line-height:.9}
html.render body{padding:0;background:var(--paper)}html.render .poster{width:1080px;height:1920px;aspect-ratio:auto;border:0;box-shadow:none}
'''

ASCII_JS = r'''
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function rng(seed){let x=seed>>>0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return((x>>>0)%100000)/100000}}
function asciiWord(word,style,band){
 const cols=44,rows=4,W=1100,H=260;const cv=document.createElement('canvas');cv.width=W;cv.height=H;const c=cv.getContext('2d');c.fillStyle='#000';c.fillRect(0,0,W,H);c.fillStyle='#fff';c.textAlign='center';c.textBaseline='middle';let fs=230;c.font='900 '+fs+'px Arial';while(c.measureText(word).width>1030&&fs>60){fs-=5;c.font='900 '+fs+'px Arial'}c.fillText(word,W/2,H/2+8);const im=c.getImageData(0,0,W,H).data;const R=rng(hash(word+style+band));let out=[];
 for(let gy=0;gy<rows;gy++){let line='';for(let gx=0;gx<cols;gx++){const x0=Math.floor(gx*W/cols),x1=Math.floor((gx+1)*W/cols),y0=Math.floor(gy*H/rows),y1=Math.floor((gy+1)*H/rows);let s=0,n=0;for(let y=y0;y<y1;y+=6){for(let x=x0;x<x1;x+=6){s+=im[(y*W+x)*4];n++}}const v=n?s/(255*n):0,r=R();let ch=' ';if(style==='dense')ch=v>.18?'■':' ';else if(style==='dotted')ch=v>.18?(r>.5?'•':'·'):' ';else if(style==='glitch')ch=v>.15&&r>.08?['#','@','=','-','/','\\','■'][Math.floor(r*7)%7]:' ';else if(style==='textmatrix'){const w=word.replace(/\s+/g,'')||'IMAGE';ch=v>.18?w[(gx+gy)%w.length]:' '}else if(style==='gradient'){const q=' .·:*#■';ch=q[Math.min(q.length-1,Math.floor(v*(q.length-1)))]}else if(style==='lines')ch=v>.18?'━':' ';else if(style==='erasure')ch=v>.18&&r>.22?(r>.55?'▓':'█'):' ';else if(style==='outline')ch=(v>.07&&v<.82)?'■':' ';line+=ch}out.push(line)}return out.join('\n')
}
document.querySelectorAll('.ascii[data-word]').forEach((el,i)=>el.textContent=asciiWord(el.dataset.word,document.body.dataset.style||'dense',i));
'''


def story_html(d, lang, style, render=False):
    p = d['parts'][lang]
    reading = ('LECTURA' if lang == 'es' else 'READING') + f" / {d['number']:03d}"
    errlabel = 'MÁQUINA DE ERROR' if lang == 'es' else 'ERROR MACHINE'
    concepts = d['concepts'][lang]
    bands = '\n'.join(f'<div class="ascii-band"><pre class="ascii" data-word="{esc(w)}"></pre></div>' for w in concepts)
    cls = 'render' if render else ''
    subtitle = f'<p class="subtitle">{esc(p["subtitle"])}</p>' if p['subtitle'] else ''
    return f'''<!doctype html><html class="{cls}" lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TSIL Story {d['number']:03d}</title><style>{STORY_STYLE}</style></head><body data-style="{style}"><article class="poster"><header class="header"><div>THE SOMATIC IMAGE LAB</div><div class="lang"><span>ES</span><span class="slash">/</span><span>EN</span></div></header><hr class="topline"><div class="reading">{esc(reading)}</div><div class="ascii-wrap">{bands}</div><div class="bottom-content"><section class="title-block"><h1 class="title">{esc(p['title'])}</h1>{subtitle}<p class="author">{esc(d['author'])}</p></section><section class="error"><p class="error-label">{esc(errlabel)}</p><p class="error-context">{esc(d['error_context'][lang])}</p><div class="error-word-row"><div class="error-arrow">→</div><div class="error-word">{esc(d['error_word'][lang])}</div></div></section></div><footer class="footer"><hr class="bottomline"><div class="footer-row"><div class="brand">THE SOMATIC IMAGE LAB</div><div class="footer-arrow">→</div></div></footer></article><script>{ASCII_JS}</script></body></html>'''


POST_STYLE = r'''
:root{--paper:#f2efe7;--ink:#0a0a0a;--muted:#787168;--line:#c5beb3;--orange:#ff5a1f}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;background:#ddd8cf;color:var(--ink);font-family:Arial,Helvetica,sans-serif;display:flex;align-items:flex-start;justify-content:center;padding:20px}
.poster{width:min(100%,720px);aspect-ratio:1080/1350;background:var(--paper);border:1px solid #d8d1c6;padding:3.8% 5.4% 3.6%;display:flex;flex-direction:column;container-type:inline-size;overflow:hidden}
.header{display:flex;justify-content:space-between;align-items:center;font-size:1.7cqw;letter-spacing:.17em;text-transform:uppercase}.lang .slash{color:var(--orange)}.topline,.bottomline{border:0;border-top:2px solid var(--line)}.topline{margin:2.3% 0 0}.reading{margin-top:5%;font-size:1.75cqw;letter-spacing:.17em;text-transform:uppercase;color:var(--muted)}
.ascii-wrap{flex:1;min-height:0;margin:6.5% 0 5.8%;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}.ascii-band{overflow:hidden;flex:0 0 auto}.ascii{margin:0;font-family:"Courier New",Courier,monospace;font-size:3.55cqw;line-height:.58;letter-spacing:-.09em;font-weight:900;white-space:pre;color:var(--ink);transform:scaleX(1.10);transform-origin:left top}.ascii-band:nth-child(2) .ascii{transform:scaleX(1.10) translateX(-1%);opacity:.96}.ascii-band:nth-child(3) .ascii{transform:scaleX(1.10) translateX(.6%);opacity:.94}
.bottom-content{width:72%;max-width:72%;flex:0 0 auto}.title{margin:0;font-size:9.2cqw;line-height:.86;letter-spacing:-.06em;font-weight:800}.subtitle{margin:1.8% 0 0;font-size:3.4cqw;line-height:.98;letter-spacing:-.03em}.author{margin:1.4% 0 0;font-size:3.0cqw;line-height:1}.error{margin-top:5.8%}.error-label{font-size:1.8cqw;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);font-weight:300}.error-context{margin-top:2.3%;font-size:2.1cqw;letter-spacing:.10em;text-transform:uppercase;color:#5b5650}.error-word-row{margin-top:1.6%;display:flex;align-items:center;gap:1.5%}.error-arrow{font-size:3.4cqw;color:var(--orange)}.error-word{display:inline-block;background:var(--orange);padding:.5% 1.5% .58%;font:700 2.45cqw/1 "Courier New",Courier,monospace;letter-spacing:.07em;text-transform:uppercase}.footer{margin-top:4.8%}.bottomline{margin:0 0 3%}.footer-row{display:flex;justify-content:space-between;align-items:flex-end}.brand{font-size:1.65cqw;letter-spacing:.15em;text-transform:uppercase}.footer-arrow{font-size:3.8cqw;line-height:.9}
html.render body{padding:0;background:var(--paper)}html.render .poster{width:1080px;height:1350px;aspect-ratio:auto;border:0}
'''


def post_html(d, lang, style='dense', render=False):
    p = d['parts'][lang]
    reading = ('LECTURA' if lang == 'es' else 'READING') + f" / {d['number']:03d}"
    errlabel = 'MÁQUINA DE ERROR' if lang == 'es' else 'ERROR MACHINE'
    concepts = (d['concepts'][lang] or ['IMAGEN' if lang == 'es' else 'IMAGE'])[:3]
    while len(concepts) < 3:
        concepts.append(concepts[-1])
    bands = '\n'.join(f'<div class="ascii-band"><pre class="ascii" data-word="{esc(w)}"></pre></div>' for w in concepts)
    cls = 'render' if render else ''
    subtitle = f'<p class="subtitle">{esc(p["subtitle"])}</p>' if p['subtitle'] else ''
    return f'''<!doctype html><html class="{cls}" lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TSIL Instagram Post {d['number']:03d}</title><style>{POST_STYLE}</style></head><body data-style="{style}"><article class="poster"><header class="header"><div>THE SOMATIC IMAGE LAB</div><div class="lang"><span>ES</span><span class="slash"> / </span><span>EN</span></div></header><hr class="topline"><div class="reading">{esc(reading)}</div><div class="ascii-wrap">{bands}</div><div class="bottom-content"><section><h1 class="title">{esc(p['title'])}</h1>{subtitle}<p class="author">{esc(d['author'])}</p></section><section class="error"><div class="error-label">{esc(errlabel)}</div><div class="error-context">{esc(d['error_context'][lang])}</div><div class="error-word-row"><div class="error-arrow">→</div><div class="error-word">{esc(d['error_word'][lang])}</div></div></section></div><footer class="footer"><hr class="bottomline"><div class="footer-row"><div class="brand">THE SOMATIC IMAGE LAB</div><div class="footer-arrow">→</div></div></footer></article><script>{ASCII_JS}</script></body></html>'''


def og_ascii_js():
    # Two centered ASCII bands for the approved 1200x630 link layout.
    # Each band uses a short concept extracted from the reading itself.
    return r"""
function tsilHash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function tsilRng(seed){let x=seed>>>0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return((x>>>0)%100000)/100000}}
function tsilAsciiBand(word,band){
  const cols=44,rows=7,W=1100,H=360;
  const cv=document.createElement('canvas');cv.width=W;cv.height=H;
  const c=cv.getContext('2d');c.fillStyle='#000';c.fillRect(0,0,W,H);
  c.fillStyle='#fff';c.textAlign='center';c.textBaseline='middle';
  let fs=250;c.font='900 '+fs+'px Arial,Helvetica,sans-serif';
  while(c.measureText(word).width>1030&&fs>55){fs-=5;c.font='900 '+fs+'px Arial,Helvetica,sans-serif'}
  c.fillText(word,W/2,H/2+10);
  const im=c.getImageData(0,0,W,H).data;const R=tsilRng(tsilHash(word+band));
  let out=[];
  for(let gy=0;gy<rows;gy++){
    let line='';
    for(let gx=0;gx<cols;gx++){
      const x0=Math.floor(gx*W/cols),x1=Math.floor((gx+1)*W/cols),y0=Math.floor(gy*H/rows),y1=Math.floor((gy+1)*H/rows);
      let sum=0,n=0;
      for(let y=y0;y<y1;y+=6){for(let x=x0;x<x1;x+=6){sum+=im[(y*W+x)*4];n++}}
      const v=n?sum/(255*n):0;
      line+=v>.17?'■':' ';
    }
    out.push(line);
  }
  return out.join('\n');
}
document.querySelectorAll('.ascii[data-word]').forEach((el,i)=>{el.textContent=tsilAsciiBand(el.dataset.word,i)});
"""


def approved_og_html(d):
    p = d['parts']['en']
    title = esc(p['title'])
    subtitle = esc(p['subtitle'])
    author = esc(d['author'])
    reading = f"READING / {d['number']:03d}"
    errctx = esc(d['error_context']['en'])
    err = esc(d['error_word']['en'])
    concepts = d['concepts']['en'] or ['IMAGE']
    word1 = esc(concepts[0])
    word2 = esc(concepts[1] if len(concepts) > 1 else concepts[0])
    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ''
    js = og_ascii_js()
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1200, initial-scale=1">
<title>TSIL — Reading {d['number']:03d} — Link Preview HTML</title>
<style>
:root{{--paper:#f2efe7;--ink:#0a0a0a;--muted:#787168;--line:#c5beb3;--orange:#ff5a1f}}
*{{box-sizing:border-box}}
html,body{{margin:0;width:1200px;height:630px;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif}}
.card{{width:1200px;height:630px;padding:30px 46px 24px;display:flex;flex-direction:column;overflow:hidden}}
.header{{display:flex;justify-content:space-between;align-items:center;font-size:14px;letter-spacing:.18em;text-transform:uppercase}}
.rule{{height:2px;background:var(--line);flex:0 0 auto}}
.top-rule{{margin-top:22px}}
.main{{flex:1;min-height:0;display:grid;grid-template-columns:56% 44%}}
.left{{min-width:0;padding:36px 34px 18px 0;display:flex;flex-direction:column;overflow:hidden}}
.right{{min-width:0;padding:36px 0 18px 38px;border-left:1px solid var(--line);display:flex;flex-direction:column}}
.reading{{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);flex:0 0 auto}}
.ascii-wrap{{flex:1;min-height:0;margin-top:28px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;overflow:hidden}}
.ascii{{margin:0;width:100%;font-family:"Courier New",Courier,monospace;font-size:25px;line-height:.60;letter-spacing:-.10em;font-weight:900;white-space:pre;color:var(--ink);transform:scaleX(1.12);transform-origin:center center}}
.title{{margin:0;font-size:70px;line-height:.86;letter-spacing:-.06em;font-weight:800}}
.subtitle{{margin:18px 0 0;font-size:30px;line-height:1;letter-spacing:-.03em;font-weight:400}}
.author{{margin:14px 0 0;font-size:25px;line-height:1;letter-spacing:-.02em;font-weight:400}}
.error{{margin-top:auto;padding-bottom:8px}}
.error-label{{font-size:16px;line-height:1;letter-spacing:.17em;text-transform:uppercase;color:var(--muted);font-weight:300}}
.context{{margin-top:20px;font-size:20px;line-height:1;letter-spacing:.11em;text-transform:uppercase;font-weight:300}}
.context .slash{{color:var(--orange)}}
.error-row{{margin-top:18px;display:flex;align-items:center;gap:16px}}
.arrow{{color:var(--orange);font-size:38px;line-height:1;font-weight:300}}
.badge{{background:var(--orange);padding:9px 15px 10px;font-family:"Courier New",Courier,monospace;font-size:24px;line-height:1;font-weight:800;letter-spacing:.05em}}
.footer{{flex:0 0 auto}}
.bottom-rule{{margin-top:0}}
.footer-row{{display:flex;justify-content:space-between;align-items:center;padding-top:20px;font-size:14px;letter-spacing:.18em;text-transform:uppercase}}
.footer-arrow{{font-size:24px;line-height:1}}
</style>
</head>
<body>
<div class="card">
<header class="header"><div>THE SOMATIC IMAGE LAB</div><div>ES / EN</div></header>
<div class="rule top-rule"></div>
<main class="main">
<section class="left">
<div class="reading">{reading}</div>
<div class="ascii-wrap">
<pre class="ascii" data-word="{word1}" aria-label="{word1} — ASCII row one"></pre>
<pre class="ascii" data-word="{word2}" aria-label="{word2} — ASCII row two"></pre>
</div>
</section>
<section class="right">
<div><h1 class="title">{title}</h1>{subtitle_html}<p class="author">{author}</p></div>
<div class="error"><div class="error-label">ERROR MACHINE</div><div class="context">{errctx}</div><div class="error-row"><div class="arrow">→</div><div class="badge">{err}</div></div></div>
</section>
</main>
<footer class="footer"><div class="rule bottom-rule"></div><div class="footer-row"><div>THE SOMATIC IMAGE LAB</div><div class="footer-arrow">→</div></div></footer>
</div>
<script>{js}</script>
</body>
</html>'''


def generic_social_html(d, kind='og'):
    if kind == 'og':
        return approved_og_html(d)

    # Square and portrait are secondary derivatives. The approved 1200x630
    # layout above is the canonical image used when a reading URL is shared.
    lang = 'en'
    p = d['parts'][lang]
    desc = d['description'][lang] or d['lead'][lang]
    if kind == 'square':
        w, h = 1080, 1080
    else:
        w, h = 1080, 1350
    title = esc(p['title']); subtitle = esc(p['subtitle']); author = esc(d['author'])
    reading = f"READING / {d['number']:03d}"
    concept = esc(d['concepts']['en'][0]); errctx = esc(d['error_context']['en']); err = esc(d['error_word']['en']); desc = esc(desc)
    sub_html = f'<h2>{subtitle}</h2>' if subtitle else ''
    layout = 'grid-template-columns:1fr;grid-template-rows:auto 1fr auto;'
    body = f'<div class="head"><span>THE SOMATIC IMAGE LAB</span><span>ES / EN</span></div><div class="left"><div class="reading">{reading}</div><div class="ascii-word">{concept}</div><h1>{title}</h1>{sub_html}<div class="author">{author}</div><div class="idea">{desc}</div><div class="error-label">ERROR MACHINE</div><div class="ctx">{errctx}</div><div class="err"><span>→</span><b>{err}</b></div></div><div class="foot"><span>THE SOMATIC IMAGE LAB</span><span>→</span></div>'
    extra = '.left{grid-column:1;grid-row:2;padding:42px 58px 24px}.idea{margin-top:36px;max-width:850px}'
    fs_ascii = '82px'; margin_ascii = '42px 0 30px'; fs_h1 = '86px'; fs_h2 = '40px'; fs_author = '32px'; fs_idea = '29px'; err_margin = '34px'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>:root{{--paper:#f2efe7;--ink:#0a0a0a;--muted:#787168;--line:#c5beb3;--orange:#ff5a1f}}*{{box-sizing:border-box}}html,body{{margin:0;width:{w}px;height:{h}px;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif}}.card{{width:100%;height:100%;display:grid;{layout}}}.head{{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;margin:0 58px;padding:32px 0 20px;border-bottom:2px solid var(--line);font-size:16px;letter-spacing:.16em}}{extra}.reading{{font-size:18px;letter-spacing:.15em;color:var(--muted)}}.ascii-word{{font-family:Courier New,monospace;font-weight:900;font-size:{fs_ascii};letter-spacing:-.08em;margin:{margin_ascii};overflow:hidden;white-space:nowrap}}h1{{margin:0;font-size:{fs_h1};line-height:.86;letter-spacing:-.055em}}h2{{margin:12px 0 0;font-size:{fs_h2};font-weight:400;line-height:1}}.author{{margin-top:12px;font-size:{fs_author}}}.idea{{font-size:{fs_idea};line-height:1.22;letter-spacing:-.02em}}.error-label{{margin-top:{err_margin};font-size:16px;letter-spacing:.15em;color:var(--muted)}}.ctx{{margin-top:16px;font-size:20px;letter-spacing:.08em}}.err{{margin-top:14px;display:flex;gap:16px;align-items:center;color:var(--orange);font-size:36px}}.err b{{background:var(--orange);color:var(--ink);font:700 24px Courier New,monospace;padding:8px 13px}}.foot{{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;margin:0 58px;padding:18px 0 24px;border-top:2px solid var(--line);font-size:16px;letter-spacing:.14em}}</style></head><body><div class="card">{body}</div></body></html>'''

def chrome_bin():
    candidates = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def screenshot(html_text, out, size):
    chrome = chrome_bin()
    w, h = size
    last_error = ''
    if chrome:
        td = Path(tempfile.mkdtemp(prefix='tsil_social_'))
        try:
            hp = td / 'render.html'
            hp.write_text(html_text, encoding='utf-8')
            profile = td / 'profile'
            cmd = [
                chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
                f'--user-data-dir={profile}', '--force-device-scale-factor=1', f'--window-size={w},{h}', '--virtual-time-budget=1200',
                f'--screenshot={Path(out).resolve()}', hp.resolve().as_uri(),
            ]
            try:
                r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                if r.returncode == 0 and Path(out).exists():
                    return
                last_error = r.stderr[-1000:]
            except subprocess.TimeoutExpired:
                last_error = 'Chrome headless superó 30 segundos.'
        finally:
            shutil.rmtree(td, ignore_errors=True)

    # Fallback: Python Playwright, if available.
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            kwargs = {'headless': True, 'args': ['--no-sandbox']}
            if chrome:
                kwargs['executable_path'] = chrome
            browser = pw.chromium.launch(**kwargs)
            page = browser.new_page(viewport={'width': w, 'height': h})
            page.set_content(html_text, wait_until='load')
            page.wait_for_timeout(80)
            page.screenshot(path=str(Path(out).resolve()), full_page=False)
            browser.close()
        if Path(out).exists():
            return
    except Exception as e:
        last_error = (last_error + '\n' + str(e)).strip()

    raise RuntimeError('No pude generar ' + str(out) + '. Necesito Google Chrome/Chromium funcional. ' + last_error)


def generate_assets(reading_dir, d):
    reading_dir = Path(reading_dir)
    generated = []
    for lang in ('es', 'en'):
        for i, style in enumerate(ASCII_STYLES, 1):
            out = reading_dir / f'share-story-{lang}-{i:02d}.png'
            screenshot(story_html(d, lang, style, render=True), out, (1080, 1920))
            generated.append(out)
    for lang in ('es', 'en'):
        out = reading_dir / f'share-post-{lang}.png'
        screenshot(post_html(d, lang, 'dense', render=True), out, (1080, 1350))
        generated.append(out)
    og = reading_dir / 'share-og.png'
    screenshot(generic_social_html(d, 'og'), og, (1200, 630))
    generated.append(og)

    manifest = {
        'reading': d['number'],
        'title': d['title'],
        'book_author': d['author'],
        'publication_author': SITE_AUTHOR,
        'canonical': d['canonical'],
        'description': d['description'],
        'assets': [x.name for x in generated],
    }
    manifest_path = reading_dir / 'social-manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    zip_path = reading_dir / 'tsil-social-assets.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in generated:
            z.write(f, f.name)
        z.write(manifest_path, manifest_path.name)

def apply_social_to_reading(root, item, generate=True):
    root = Path(root)
    rd = root / 'readings' / item['slug']
    p = rd / 'index.html'
    if not p.exists():
        print('AVISO social: no existe', p)
        return False
    page = p.read_text(encoding='utf-8')
    d = reading_data(item, page)
    p.write_text(patch_html(page, d), encoding='utf-8')
    if generate:
        generate_assets(rd, d)
    return True
