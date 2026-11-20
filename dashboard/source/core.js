// Shared helpers, tabs, controls and the overview charts.
const DM = (window.DM = {});
DM.TYPES = ['Ryokan', 'Hotel', 'Hybrid'];
DM.ASPECTS = ['Staff & service', 'Room', 'Dining', 'Location', 'Culture', 'Bath', 'Value & price'];
DM.SHORT = {'Staff & service': 'Staff', 'Room': 'Room', 'Dining': 'Dining', 'Location': 'Location', 'Culture': 'Culture', 'Bath': 'Bath', 'Value & price': 'Value'};
DM.DEFAULTS = {metric: 'mention_share', measure: 'vader', tperiod: 'All years', ctype: 'Hotel', cpol: 'neg', smetric: 'rating', tmetric: 'rating', tprop: '', lx: 'dist_gion_kiyomizu_m', ly: 'mean', csplit: 'season'};
DM.param = (k) => { const v = dash.params()[k]; return v === undefined || v === null ? DM.DEFAULTS[k] : v; };
DM.colorOf = (t) => dash.colors[Math.max(0, DM.TYPES.indexOf(t))];
DM.num = (v) => (v === null || v === undefined || v === '' ? NaN : +v);
DM.f0 = d3.format('.0f'); DM.f1 = d3.format('.1f'); DM.f2 = d3.format('.2f'); DM.f3 = d3.format('.3f'); DM.fi = d3.format(',');
DM.signed = (v, f) => (v > 0 ? '+' : v < 0 ? '−' : '') + (f || DM.f2)(Math.abs(v));
DM.pval = (p) => (p < 0.001 ? 'p < 0.001' : 'p = ' + DM.f3(p));

DM.textWidth = (svg, str, cls) => {
  const t = svg.append('text').attr('class', cls || null).text(str);
  const w = t.node().getComputedTextLength(); t.remove(); return w;
};
DM.placeholder = (el, status) => {
  el.replaceChildren();
  const p = document.createElement('p'); p.className = 'dm-empty';
  p.textContent = status === 'error' ? 'Failed to load' : '—';
  el.appendChild(p);
};
// returns true when every named source is loaded; otherwise draws the placeholder
DM.ready = (el, ids) => {
  for (const id of ids) { const g = dash.data(id); if (g.status !== 'ok') { DM.placeholder(el, g.status); return false; } }
  return true;
};
DM.svg = (el, W, H, label) => d3.select(el).append('svg').attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).attr('role', 'img').attr('aria-label', label);
DM.width = (el) => Math.max(280, el.clientWidth);
DM.makeTip = (el) => {
  const tip = document.createElement('div'); tip.className = 'dm-tip'; tip.hidden = true; el.appendChild(tip);
  return {
    show(event, lines) {
      tip.replaceChildren();
      lines.filter(Boolean).forEach((l, i) => { const d = document.createElement('div'); d.className = i === 0 ? 'dm-tip-title' : 'dm-tip-sub'; d.textContent = l; tip.appendChild(d); });
      tip.hidden = false;
      const box = el.getBoundingClientRect();
      let x = event.clientX - box.left + 12, y = event.clientY - box.top + 12;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      if (x + w > box.width) x = Math.max(0, event.clientX - box.left - w - 12);
      if (y + h > box.height) y = Math.max(0, event.clientY - box.top - h - 12);
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    },
    hide() { tip.hidden = true; }
  };
};
// horizontal bar from x0 to x1 with a rounded data end
DM.hbar = (x0, x1, h) => {
  const w = Math.max(1, Math.abs(x1 - x0)), r = Math.min(4, w, h / 2), s = x1 >= x0 ? 1 : -1;
  return `M${x0},0h${s * (w - r)}a${r},${r} 0 0 ${s > 0 ? 1 : 0} ${s * r},${r}v${h - 2 * r}a${r},${r} 0 0 ${s > 0 ? 1 : 0} ${-s * r},${r}h${-s * (w - r)}z`;
};
// greedy label placement around points; pts: [{x, y, label, cls, r}]
DM.labels = (svg, pts, bounds) => {
  const boxes = pts.map((p) => [p.x - (p.r || 5), p.y - (p.r || 5), p.x + (p.r || 5), p.y + (p.r || 5)]);
  const hit = (b) => boxes.some((o) => !(b[2] < o[0] || b[0] > o[2] || b[3] < o[1] || b[1] > o[3]));
  const out = [];
  pts.forEach((p) => {
    const w = DM.textWidth(svg, p.label, p.cls), h = 14, r = (p.r || 5) + 4;
    const cands = [
      {x: p.x + r, y: p.y, a: 'start', b: [p.x + r, p.y - h / 2, p.x + r + w, p.y + h / 2]},
      {x: p.x - r, y: p.y, a: 'end', b: [p.x - r - w, p.y - h / 2, p.x - r, p.y + h / 2]},
      {x: p.x, y: p.y - r - 5, a: 'middle', b: [p.x - w / 2, p.y - r - 5 - h / 2, p.x + w / 2, p.y - r - 5 + h / 2]},
      {x: p.x, y: p.y + r + 5, a: 'middle', b: [p.x - w / 2, p.y + r + 5 - h / 2, p.x + w / 2, p.y + r + 5 + h / 2]},
      {x: p.x + r, y: p.y - 12, a: 'start', b: [p.x + r, p.y - 12 - h / 2, p.x + r + w, p.y - 12 + h / 2]},
      {x: p.x + r, y: p.y + 12, a: 'start', b: [p.x + r, p.y + 12 - h / 2, p.x + r + w, p.y + 12 + h / 2]},
      {x: p.x - r, y: p.y - 12, a: 'end', b: [p.x - r - w, p.y - 12 - h / 2, p.x - r, p.y - 12 + h / 2]},
      {x: p.x - r, y: p.y + 12, a: 'end', b: [p.x - r - w, p.y + 12 - h / 2, p.x - r, p.y + 12 + h / 2]}
    ];
    [[0, -24], [0, 24], [0, -38], [0, 38]].forEach(([ox, oy]) => cands.push({x: p.x, y: p.y + oy, a: 'middle', b: [p.x - w / 2, p.y + oy - h / 2, p.x + w / 2, p.y + oy + h / 2]}));
    [[1, -24], [1, 24], [-1, -24], [-1, 24]].forEach(([sx, oy]) => cands.push({x: p.x + sx * r, y: p.y + oy, a: sx > 0 ? 'start' : 'end', b: sx > 0 ? [p.x + r, p.y + oy - h / 2, p.x + r + w, p.y + oy + h / 2] : [p.x - r - w, p.y + oy - h / 2, p.x - r, p.y + oy + h / 2]}));
    const inside = (b) => b[0] >= bounds[0] && b[2] <= bounds[2] && b[1] >= bounds[1] && b[3] <= bounds[3];
    const c = cands.find((k) => inside(k.b) && !hit(k.b)) || cands.find((k) => inside(k.b)) || cands[0];
    boxes.push(c.b); out.push({p, c});
  });
  svg.append('g').selectAll('text').data(out).join('text').attr('class', (d) => d.p.cls || 'dm-strong').attr('x', (d) => d.c.x).attr('y', (d) => d.c.y).attr('dy', '0.35em').attr('text-anchor', (d) => d.c.a).text((d) => d.p.label);
};

// legend swatches: style only
document.querySelectorAll('.dm-sw[data-type]').forEach((el) => { el.style.background = DM.colorOf(el.getAttribute('data-type')); });

// controls: static options, choices never reach a query
document.querySelectorAll('select[data-param]').forEach((sel) => {
  const k = sel.getAttribute('data-param');
  sel.value = DM.param(k);
  sel.addEventListener('change', () => dash.setParams({[k]: sel.value}));
});
dash.onData(() => {
  document.querySelectorAll('select[data-param]').forEach((sel) => {
    if (document.activeElement !== sel) sel.value = DM.param(sel.getAttribute('data-param'));
  });
});

// tabs
DM.show = (id, link) => {
  const views = Array.from(document.querySelectorAll('[data-view]'));
  if (!views.some((v) => v.id === id)) id = views.length ? views[0].id : id;
  views.forEach((v) => { v.hidden = v.id !== id; });
  document.querySelectorAll('.dm-tab[data-tab]').forEach((b) => b.setAttribute('aria-selected', b.getAttribute('data-tab') === id ? 'true' : 'false'));
  if (link) dash.setLink(id);
  const shown = document.getElementById(id);
  if (link && shown) new Set(Array.from(shown.querySelectorAll('[data-draw]')).map((e) => e.getAttribute('data-draw'))).forEach((n) => dash.draw(n));
};
document.querySelectorAll('.dm-tab[data-tab]').forEach((b) => b.addEventListener('click', () => DM.show(b.getAttribute('data-tab'), true)));
{
  const h = (location.hash || '').replace('#', '');
  const target = h && document.getElementById(h);
  const view = target && (target.hasAttribute('data-view') ? target : target.closest('[data-view]'));
  if (view) DM.show(view.id, false);
}

// single cells inside sentences
dash.draw('cell', (el) => {
  const src = el.getAttribute('data-source'), field = el.getAttribute('data-field');
  const where = (el.getAttribute('data-where') || '').split('&').filter(Boolean).map((kv) => kv.split('=').map(decodeURIComponent));
  const g = dash.data(src);
  if (g.status !== 'ok') { el.textContent = '—'; return; }
  const row = g.data.find((r) => where.every(([k, v]) => String(r[k]) === v));
  el.textContent = row && row[field] !== null && row[field] !== '' ? String(row[field]) : '—';
});

// ANOVA table
dash.draw('anovarows', (tbody) => {
  const g = dash.data('anova');
  tbody.replaceChildren();
  if (g.status !== 'ok') return;
  const cols = ['label', 'groups', 'F', 'df', 'p', 'eta2', 'verdict'];
  g.data.forEach((r) => {
    const tr = document.createElement('tr'); tr.setAttribute('data-key', encodeURIComponent(r.test));
    cols.forEach((c) => {
      const td = document.createElement('td');
      const v = r[c] === null || r[c] === undefined ? '' : String(r[c]);
      if (c === 'verdict') {
        const s = document.createElement('span'); s.className = 'dm-pill ' + (v.startsWith('Not') ? 'dm-no' : 'dm-yes'); s.textContent = v; td.appendChild(s);
      } else { td.textContent = v; }
      if (c === 'F' || c === 'df' || c === 'p' || c === 'eta2') td.className = 'dm-num';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
});

// property means with confidence intervals
dash.draw('propdots', (el) => {
  if (!DM.ready(el, ['properties'])) return;
  const {num, colorOf, textWidth, f1, f2, f3, fi} = DM;
  const rows = dash.data('properties').data.map((r) => ({property: r.property, type: r.type, n: num(r.n), mean: num(r.mean), lo: num(r.ci_lo), hi: num(r.ci_hi), sd: num(r.sd), low: num(r.low_share)}))
    .sort((a, b) => d3.descending(a.mean, b.mean));
  el.replaceChildren();
  const W = DM.width(el), rowH = 30, top = 8, bottom = 34;
  const H = top + rows.length * rowH + bottom;
  const svg = DM.svg(el, W, H, 'Mean star rating of each of ten properties with 95% confidence intervals, coloured by accommodation type');
  const left = Math.min(W * 0.42, d3.max(rows, (r) => textWidth(svg, r.property, 'dm-strong')) + 14);
  const right = textWidth(svg, '4.99', 'dm-strong') + 14;
  const x = d3.scaleLinear().domain([4.4, 5]).range([left, W - right]);
  const y = d3.scaleBand().domain(rows.map((r) => r.property)).range([top, top + rows.length * rowH]);
  const ticks = W < 460 ? [4.4, 4.6, 4.8, 5] : [4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5];
  svg.append('g').selectAll('line').data(ticks).join('line').attr('class', 'dm-grid').attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', top).attr('y2', top + rows.length * rowH);
  svg.append('g').selectAll('text').data(ticks).join('text').attr('x', (d) => x(d)).attr('y', top + rows.length * rowH + 16).attr('text-anchor', 'middle').text((d) => f1(d));
  svg.append('text').attr('x', (left + W - right) / 2).attr('y', H - 2).attr('text-anchor', 'middle').text('Mean rating (stars)');
  const row = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', (r) => `translate(0,${y(r.property) + rowH / 2})`);
  row.append('text').attr('class', 'dm-strong').attr('x', left - 12).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => r.property);
  row.append('line').attr('x1', (r) => x(Math.max(4.4, r.lo))).attr('x2', (r) => x(Math.min(5, r.hi))).style('stroke', (r) => colorOf(r.type)).attr('stroke-width', 2).attr('stroke-linecap', 'round');
  row.append('circle').attr('cx', (r) => x(r.mean)).attr('r', 5.5).style('fill', (r) => colorOf(r.type)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
  row.append('text').attr('class', 'dm-strong').attr('x', W - right + 12).attr('dy', '0.35em').text((r) => f2(r.mean));
  const tip = DM.makeTip(el);
  row.append('rect').attr('class', 'dm-hit').attr('x', 0).attr('y', -rowH / 2).attr('width', W).attr('height', rowH)
    .on('pointermove', (event, r) => tip.show(event, [r.property, `${r.type} · ${fi(r.n)} reviews`, `Mean ${f3(r.mean)} stars (95% CI ${f2(r.lo)} to ${f2(r.hi)})`, `Standard deviation ${f2(r.sd)}`, `Rated three stars or fewer: ${f1(r.low)}%`]))
    .on('pointerleave', () => tip.hide());
});
