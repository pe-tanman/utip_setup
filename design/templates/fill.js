// Shared helper: shows the requested slide and fills [data-k="club.links.form"] style bindings.
(function () {
  const D = window.UTIP || { club: {}, officers: [], slide: null };
  const get = (path) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), D);
  window.UTIP_GET = get;
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-k]').forEach((el) => { const v = get(el.dataset.k); if (v != null) el.textContent = v; });
    document.querySelectorAll('[data-href]').forEach((el) => { el.textContent = String(get(el.dataset.href) || '').replace(/^https?:\/\//, ''); });
    const want = D.slide;
    const slides = document.querySelectorAll('.slide');
    slides.forEach((s, i) => { if ((want == null && i === 0) || s.dataset.slide === want) s.classList.add('on'); });
    if (window.UTIP_AFTER) window.UTIP_AFTER(D);
  });
})();
