// Runtime mínimo do painel: carrega os dados, calcula e desenha.
(() => {
  const FONTES = { catalogo: 'data/catalogo.json', historico: 'data/historico.json', rede_2023: 'data/rede_2023.json' };
  const RAW = {};
  const calcs = {}, draws = {}, onFns = [];
  let cache = {};
  let estado = 'loading';
  const data = (id) => {
    if (id in FONTES) return estado === 'ok' ? { status: 'ok', data: RAW[id] } : { status: estado };
    if (cache[id]) return cache[id];
    const c = calcs[id];
    if (!c) return { status: 'error' };
    const ins = c.inputs.map(data);
    const pend = ins.find((r) => r.status !== 'ok');
    if (pend) return { status: pend.status };
    try { cache[id] = { status: 'ok', data: c.fn(...ins.map((r) => r.data)) }; }
    catch (e) { console.error('cálculo', id, e); cache[id] = { status: 'error' }; }
    return cache[id];
  };
  const visivel = (el) => !el.closest('[hidden]');
  const largura = new WeakMap();
  const desenhar = (n, el) => {
    if (!visivel(el)) return;
    try { draws[n](el); } catch (e) { console.error('desenho', n, e); }
    if (estado !== 'loading') el.classList.remove('dash-skeleton');
    largura.set(el, el.clientWidth);
  };
  const elementos = (n) => document.querySelectorAll('[data-draw="' + n + '"]');
  const todos = () => {
    onFns.forEach((f) => { try { f(); } catch (e) { console.error(e); } });
    Object.keys(draws).forEach((n) => elementos(n).forEach((el) => desenhar(n, el)));
  };
  const revisar = () => Object.keys(draws).forEach((n) => elementos(n).forEach((el) => {
    if (visivel(el) && (!largura.has(el) || largura.get(el) !== el.clientWidth)) desenhar(n, el);
  }));
  window.dash = {
    calc: (id, o) => { calcs[id] = o; },
    draw: (n, fn) => { if (fn) draws[n] = fn; else elementos(n).forEach((el) => desenhar(n, el)); },
    data,
    onData: (f) => onFns.push(f),
    colors: [getComputedStyle(document.documentElement).getPropertyValue('--ls-accent').trim() || '#1f5fa8'],
    setLink: (h) => { try { history.replaceState(null, '', '#' + h); } catch (e) { /* sem histórico */ } },
    params: () => ({}),
  };
  new MutationObserver((ms) => {
    if (ms.some((m) => m.attributeName === 'hidden' && !m.target.hidden)) requestAnimationFrame(revisar);
  }).observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['hidden'] });
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(revisar, 150); });
  window.addEventListener('DOMContentLoaded', () => {
    todos();
    Promise.all(Object.entries(FONTES).map(([k, u]) => fetch(u, { cache: 'no-cache' })
      .then((r) => { if (!r.ok) throw new Error(u + ': ' + r.status); return r.json(); })
      .then((j) => { RAW[k] = j.rows || j; })))
      .then(() => { estado = 'ok'; }, (e) => { estado = 'error'; console.error(e); })
      .then(() => { cache = {}; todos(); });
  });
})();
