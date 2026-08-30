/* stroke.js — dependency-free hanja stroke-order animation for study pages.
 *
 * Loads ordered per-stroke SVG path + median data at runtime from the
 * CORS-enabled jsDelivr CDN of the MIT-licensed `hanzi-writer-data`
 * package (derived from the Make Me a Hanzi project). The data files are
 * named by character (e.g. `%E5%B1%B1.json` for 山) and carry an ordered
 * list of filled SVG paths plus a "median" polyline skeleton per stroke.
 *
 * This is consistent with the rest of this static site: no build step, no
 * vendored dependency, no framework. The animation is our own: future
 * strokes show as faint median guides, the current stroke gets a glowing
 * dot that travels along its median (revealing writing direction), and
 * completed strokes fill in as solid ink. If the data can't be fetched
 * (offline) the modal reports it and the study page keeps its glyph.
 *
 * Exposes window.openStrokeOrder(char).
 */
(function (w) {
  'use strict';
  var DATA_BASE = 'https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/';
  var SVG = 'http://www.w3.org/2000/svg';
  var SPEED = 720;      // median units travelled per second
  var DWELL = 240;      // ms pause between strokes
  var FETCH_TIMEOUT = 12000;

  var INK = 'rgba(242,239,230,0.92)';
  var GHOST = 'rgba(242,239,230,0.18)';
  var GHOST_CUR = 'rgba(242,239,230,0.45)';
  var ACCENT = '#ffcf6b';

  var cache = {};        // char -> data | null (null = missing/failed)
  var modal = null;      // current modal element
  var UI = null;         // map of modal controls
  var ctx = null;        // animation state
  var svgEl = null;      // <svg> for the current modal
  var rafId = null;
  var playing = false;
  var last = 0;

  /* ---------- tiny DOM helpers ---------- */
  function vEl(tag, attrs, parent) {
    var e = document.createElementNS(SVG, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function dEl(tag, attrs, parent) {
    var e = document.createElement(tag);
    for (var k in attrs) {
      if (k === 'text') continue;
      e.setAttribute(k === 'className' ? 'class' : k, attrs[k]);
    }
    if (attrs.text !== undefined) e.textContent = attrs.text;
    if (parent) parent.appendChild(e);
    return e;
  }

  /* ---------- geometry ---------- */
  function medianPath(p) {
    var d = 'M ' + p[0][0] + ' ' + p[0][1];
    for (var i = 1; i < p.length; i++) d += ' L ' + p[i][0] + ' ' + p[i][1];
    return d;
  }
  function totalLen(p) {
    var s = 0;
    for (var i = 1; i < p.length; i++) s += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
    return s;
  }
  function pointAt(p, dist) {
    var i = 1, acc = 0;
    while (i < p.length) {
      var seg = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
      if (acc + seg >= dist) {
        var t = (dist - acc) / (seg || 1);
        return [p[i - 1][0] + (p[i][0] - p[i - 1][0]) * t, p[i - 1][1] + (p[i][1] - p[i - 1][1]) * t];
      }
      acc += seg; i++;
    }
    var e = p[p.length - 1];
    return [e[0], e[1]];
  }

  /* ---------- data loading ---------- */
  function withTimeout(p) {
    return new Promise(function (res, rej) {
      var t = setTimeout(function () { rej(new Error('timeout')); }, FETCH_TIMEOUT);
      p.then(function (v) { clearTimeout(t); res(v); }, function (e) { clearTimeout(t); rej(e); });
    });
  }
  function getData(char) {
    if (cache[char] !== undefined) return Promise.resolve(cache[char]);
    return withTimeout(fetch(DATA_BASE + encodeURIComponent(char) + '.json', { mode: 'cors' }))
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (d) {
        if (!d || !Array.isArray(d.strokes) || !d.strokes.length || !Array.isArray(d.medians)) throw new Error('bad data');
        cache[char] = d;
        return d;
      })
      .catch(function () { cache[char] = null; return null; });
  }

  /* ---------- animation ---------- */
  function stopLoop() {
    if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
    playing = false;
  }
  function loop() {
    var now = performance.now();
    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    var d = ctx.data, N = d.strokes.length;
    if (ctx.dwell > 0) {
      ctx.dwell -= dt * 1000;
    } else {
      ctx.curDist += dt * SPEED;
      if (ctx.curDist >= ctx.strokeLen) {
        ctx.done += 1;
        if (ctx.done >= N) { finish(); return; }
        ctx.curDist = 0;
        ctx.strokeLen = totalLen(d.medians[ctx.done]) || 1;
        ctx.dwell = DWELL;
      }
    }
    render();
    rafId = requestAnimationFrame(loop);
  }
  function start() {
    last = performance.now();
    playing = true;
    if (rafId === null) rafId = requestAnimationFrame(loop);
  }
  function pause() {
    stopLoop();
    render();
  }
  function reset() {
    ctx.done = -1;
    ctx.curDist = 0;
    ctx.dwell = 0;
    ctx.strokeLen = totalLen(ctx.data.medians[0]) || 1;
    UI.pauseBtn.textContent = '⏸';
    if (UI.counter) UI.counter.textContent = '0 / ' + ctx.data.strokes.length;
    start();
  }
  function finish() {
    stopLoop();
    render();
    if (UI.pauseBtn) UI.pauseBtn.textContent = '▶';
    if (UI.counter) UI.counter.textContent = '완료 · ' + ctx.data.strokes.length + ' strokes';
  }
  function inked(j) {
    vEl('path', { d: ctx.data.strokes[j], fill: INK }, svgEl);
  }
  function render() {
    while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
    var d = ctx.data, N = d.strokes.length;
    var finished = ctx.done >= N;

    // frame + faint crosshair guide
    vEl('rect', { x: 40, y: 40, width: 944, height: 944, rx: 16, fill: 'none', stroke: 'rgba(242,239,230,0.14)', 'stroke-width': 3 }, svgEl);
    vEl('line', { x1: 60, y1: 512, x2: 964, y2: 512, stroke: 'rgba(242,239,230,0.06)', 'stroke-width': 2 }, svgEl);
    vEl('line', { x1: 512, y1: 60, x2: 512, y2: 964, stroke: 'rgba(242,239,230,0.06)', 'stroke-width': 2 }, svgEl);

    for (var i = 0; i < N; i++) {
      if (finished || i < ctx.done) { inked(i); continue; }
      vEl('path', {
        d: medianPath(d.medians[i]),
        fill: 'none',
        stroke: i === ctx.done ? GHOST_CUR : GHOST,
        'stroke-width': 24, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'
      }, svgEl);
      if (i === ctx.done) {
        var pt = pointAt(d.medians[i], Math.min(ctx.curDist, ctx.strokeLen));
        var g = vEl('g', {}, svgEl);
        vEl('circle', { cx: pt[0], cy: pt[1], r: 32, fill: 'none', stroke: 'rgba(255,207,107,0.35)', 'stroke-width': 6 }, g);
        vEl('circle', { cx: pt[0], cy: pt[1], r: 21, fill: ACCENT }, g);
      }
    }
    if (!finished && UI.counter) UI.counter.textContent = Math.min(ctx.done + 1, N) + ' / ' + N;
  }

  /* ---------- modal chrome ---------- */
  function ensureStyle() {
    if (document.getElementById('strokeo-style')) return;
    var st = document.createElement('style');
    st.id = 'strokeo-style';
    st.textContent =
      '.strokeo-mask{position:fixed;inset:0;background:rgba(0,0,0,0.62);display:flex;align-items:center;justify-content:center;z-index:9999}' +
      '.strokeo-card{background:#171717;border:1px solid rgba(242,239,230,0.22);border-radius:12px;box-shadow:0 18px 60px rgba(0,0,0,0.5);width:min(380px,92vw);padding:18px 20px 16px;color:#f2efe6;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif}' +
      '.strokeo-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}' +
      '.strokeo-char{font-family:Georgia,"Times New Roman",serif;font-size:18px;color:rgba(242,239,230,0.9)}' +
      '.strokeo-counter{margin-left:auto;font-size:12px;letter-spacing:.12em;color:rgba(242,239,230,0.6)}' +
      '.strokeo-close{border:none;background:transparent;color:rgba(242,239,230,0.6);font-size:16px;cursor:pointer;padding:4px 6px;line-height:1}' +
      '.strokeo-close:hover{color:#fff}' +
      '.strokeo-stage{background:rgba(0,0,0,0.35);border-radius:8px;overflow:hidden}' +
      '.strokeo-svg{width:100%;display:block}' +
      '.strokeo-foot{display:flex;align-items:center;gap:10px;margin-top:12px}' +
      '.strokeo-btn{border:1px solid rgba(242,239,230,0.3);background:transparent;color:#f2efe6;font-size:13px;padding:6px 12px;border-radius:6px;cursor:pointer;font-family:inherit}' +
      '.strokeo-btn:hover{border-color:#fff;color:#fff}' +
      '.strokeo-btn:disabled{opacity:.4;cursor:default}' +
      '.strokeo-tip{font-size:11px;color:rgba(242,239,230,0.42);letter-spacing:.04em}' +
      '.strokeo-err{text-align:center;color:rgba(242,239,230,0.6);font-size:13px;padding:34px 8px;line-height:1.7}' +
      '.strokeo-err small{font-size:11px;color:rgba(242,239,230,0.4)}';
    document.head.appendChild(st);
  }
  function showError(stage) {
    while (stage.firstChild) stage.removeChild(stage.firstChild);
    var w = dEl('div', { className: 'strokeo-err' }, stage);
    var b = document.createElement('div');
    b.innerHTML = '이 글자의 획순 데이터를 불러오지 못했어요.<br>' +
      '<small>Stroke-order data unavailable — offline, or this character is outside the dataset.<br>' +
      'You can still study the reading, meaning, and example words above.</small>';
    w.appendChild(b);
    UI.pauseBtn.disabled = true;
    UI.restartBtn.disabled = true;
    UI.counter.textContent = 'unavailable';
  }
  function closeModal() {
    stopLoop();
    if (modal) {
      if (modal._keys) document.removeEventListener('keydown', modal._keys);
      if (modal.parentNode) modal.parentNode.removeChild(modal);
    }
    modal = null; UI = null; ctx = null; svgEl = null;
  }
  function openModal(char) {
    ensureStyle();
    closeModal();

    var mask = dEl('div', { className: 'strokeo-mask' }, document.body);
    var card = dEl('div', { className: 'strokeo-card' }, mask);

    var head = dEl('div', { className: 'strokeo-head' }, card);
    dEl('span', { className: 'strokeo-char', text: char + ' · 손글씨 순서' }, head);
    var counter = dEl('span', { className: 'strokeo-counter', text: 'loading…' }, head);
    var close = dEl('button', { className: 'strokeo-close', type: 'button', text: '✕' }, head);

    var stage = dEl('div', { className: 'strokeo-stage' }, card);
    var svg = vEl('svg', { viewBox: '0 0 1024 1024', preserveAspectRatio: 'xMidYMid meet', 'class': 'strokeo-svg' }, stage);

    var foot = dEl('div', { className: 'strokeo-foot' }, card);
    var pauseBtn = dEl('button', { className: 'strokeo-btn', type: 'button', text: '⏸' }, foot);
    var restartBtn = dEl('button', { className: 'strokeo-btn', type: 'button', text: '↻' }, foot);
    var tip = dEl('span', { className: 'strokeo-tip', text: 'hanzi-writer-data (MIT)' }, foot);

    modal = mask; UI = { counter: counter, pauseBtn: pauseBtn, restartBtn: restartBtn };
    svgEl = svg;

    close.onclick = closeModal;
    mask.addEventListener('click', function (e) { if (e.target === mask) closeModal(); });
    restartBtn.onclick = reset;

    getData(char).then(function (data) {
      if (!data) { showError(stage); return; }
      ctx = { data: data, done: -1, curDist: 0, strokeLen: totalLen(data.medians[0]) || 1, dwell: 0 };
      pauseBtn.onclick = function () {
        if (playing) { pause(); pauseBtn.textContent = '▶'; }
        else if (ctx.done < data.strokes.length) { pauseBtn.textContent = '⏸'; start(); }
        else reset();
      };
      counter.textContent = '0 / ' + data.strokes.length;
      render();
      start();
    });

    var keys = function (e) { if (e.key === 'Escape') closeModal(); };
    document.addEventListener('keydown', keys);
    modal._keys = keys;
  }

  w.openStrokeOrder = openModal;
  w.strokeOrderDataBase = DATA_BASE;
})(window);