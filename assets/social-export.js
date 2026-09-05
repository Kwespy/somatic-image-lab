(() => {
  const source = document.getElementById('tsil-social-data');
  if (!source) return;
  const data = JSON.parse(source.textContent);
  const words = {
    es: { title: 'TSIL / EXPORTAR', format: 'Formato', language: 'Idioma', story: 'Story 9:16 · ASCII aleatorio', post: 'Post Instagram 4:5', link: 'Vista previa de enlace 1200×630', generate: 'Generar vista previa', download: 'Descargar imagen', waiting: 'Generando imagen…', ready: 'Imagen lista. Puedes descargarla o generar otra.', failed: 'No se pudo generar. Comprueba el servicio local y vuelve a intentarlo.', busy: 'Se está generando otra imagen. Inténtalo en unos segundos.', local: 'Para generar imágenes, abre este sitio con el servicio Python local en tu computador.', note: 'Solo se genera la imagen que pides. No se guarda en la carpeta de la lectura. La vista de enlace usa la plantilla fija en inglés.', close: 'Cerrar', preview: 'Vista previa de la imagen', copy: 'Copiar enlace de la lectura', copied: 'Enlace copiado.', copyFailed: 'No se pudo copiar el enlace.' },
    en: { title: 'TSIL / EXPORT', format: 'Format', language: 'Language', story: 'Story 9:16 · Random ASCII', post: 'Instagram post 4:5', link: 'Link preview 1200×630', generate: 'Generate preview', download: 'Download image', waiting: 'Generating image…', ready: 'Image ready. Download it or generate another.', failed: 'Could not generate. Check the local service and try again.', busy: 'Another image is being generated. Try again in a few seconds.', local: 'To generate images, open this site with the local Python service on your computer.', note: 'Only the requested image is generated. It is not saved in the reading folder. Link previews use the fixed English template.', close: 'Close', preview: 'Image preview', copy: 'Copy reading link', copied: 'Link copied.', copyFailed: 'Could not copy the link.' }
  };
  let panel, url, opener, generating = false;
  function open() {
    if (panel) { if (!generating) panel.remove(); else { panel.classList.add('open'); return; } }
    if (url) { URL.revokeObjectURL(url); url = null; }
    const lang = document.documentElement.dataset.lang === 'en' ? 'en' : 'es';
    const t = words[lang];
    opener = document.activeElement;
    panel = document.createElement('div');
    panel.id = 'tsil-secret-export';
    panel.className = 'open';
    panel.innerHTML = `<div class="tsil-export-box" role="dialog" aria-modal="true" aria-label="${t.title}" style="max-height:90vh;overflow:auto">
      <div class="tsil-export-head"><span>${t.title}</span><button class="tsil-export-close" aria-label="${t.close}">×</button></div>
      <div class="tsil-export-grid">
        <label>${t.format}<select data-format style="display:block;width:100%;padding:8px"><option value="story">${t.story}</option><option value="post">${t.post}</option><option value="link">${t.link}</option></select></label>
        <label>${t.language}<select data-lang style="display:block;width:100%;padding:8px"><option value="es">Español</option><option value="en">English</option></select></label>
        <button class="tsil-export-btn" data-generate>${t.generate}</button>
        <img data-preview alt="${t.preview}" hidden style="max-width:100%;max-height:40vh;object-fit:contain;margin:auto">
        <a class="tsil-export-btn" data-download hidden>${t.download}</a>
        <button class="tsil-export-btn" data-copy-link>${t.copy}</button>
      </div><p data-status role="status" class="tsil-export-note"></p><p class="tsil-export-note">${t.note}</p></div>`;
    document.body.appendChild(panel);
    const current = panel;
    const q = s => current.querySelector(s);
    q('[data-lang]').value = lang;
    const close = () => { current.classList.remove('open'); opener?.focus(); };
    q('.tsil-export-close').onclick = close;
    current.onclick = e => { if (e.target === current) close(); };
    current.onkeydown = e => {
      if (e.key === 'Escape') close();
      if (e.key === 'Tab') {
        const focusable = [...current.querySelectorAll('button, select, a[href]')].filter(el => !el.disabled && !el.hidden);
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    q('[data-format]').onchange = () => { q('[data-lang]').disabled = q('[data-format]').value === 'link'; };
    q('[data-copy-link]').onclick = async () => {
      try { await navigator.clipboard.writeText(data.canonical); q('[data-status]').textContent = t.copied; }
      catch { q('[data-status]').textContent = t.copyFailed; }
    };
    q('[data-generate]').onclick = async () => {
      if (generating) return;
      q('[data-status]').textContent = t.waiting;
      q('[data-generate]').disabled = true;
      generating = true;
      try {
        let token;
        try {
          const probe = await fetch('/api/local', { cache: 'no-store' });
          if (!probe.ok) throw Error();
          token = (await probe.json()).token;
          if (!token) throw Error();
        } catch { throw Error(t.local); }
        const format = q('[data-format]').value, language = q('[data-lang]').value;
        const response = await fetch('/api/render', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TSIL-Token': token }, body: JSON.stringify({ slug: data.slug, format, lang: language, variant: Math.floor(Math.random() * 8) }) });
        if (!response.ok) throw Error(response.status === 409 ? t.busy : t.failed);
        const blob = await response.blob();
        if (url) URL.revokeObjectURL(url);
        url = URL.createObjectURL(blob);
        q('[data-preview]').src = url;
        q('[data-preview]').hidden = false;
        q('[data-download]').href = url;
        q('[data-download]').download = `tsil-${String(data.number).padStart(3, '0')}-${format}-${format === 'link' ? 'en' : language}.png`;
        q('[data-download]').hidden = false;
        q('[data-status]').textContent = t.ready;
      } catch (e) { q('[data-status]').textContent = e.message || t.failed; }
      finally { generating = false; q('[data-generate]').disabled = false; }
    };
    q('.tsil-export-close').focus();
  }
  document.querySelectorAll('.tsil-secret-story').forEach(el => {
    el.setAttribute('role', 'button'); el.tabIndex = 0;
    el.addEventListener('click', open);
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  });
})();
