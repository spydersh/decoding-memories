// Research question 3: season, time and place.
{
const DM = window.DM, {num, colorOf, textWidth, f0, f1, f2, f3, fi, TYPES} = DM;
const short = (s) => s.replace(' Kyoto', '').replace(' Ryokan', '').replace('The ', '');

// month x type heat map
dash.draw('season', (el) => {
  if (!DM.ready(el, ['season'])) return;
  const metric = DM.param('smetric'), isRating = metric === 'rating';
  const rows = dash.data('season').data.map((r) => ({type: r.type, m: num(r.month), name: r.month_name, peak: num(r.peak) === 1, n: num(r.n), rating: num(r.rating), low: num(r.low_share), v: num(r[metric])}));
  const months = Array.from(d3.group(rows, (r) => r.m), ([m, rs]) => ({m, name: rs[0].name, peak: rs[0].peak})).sort((a, b) => a.m - b.m);
  el.replaceChildren();
  const W = DM.width(el), tall = W < 600;           // narrow: months down, types across
  const svg = d3.select(el).append('svg').attr('role', 'img').attr('aria-label', 'Heat map of ratings by month of the year for ryokans, hotels and hybrids');
  const fmt = isRating ? f2 : (v) => f1(v);
  const ext = d3.extent(rows, (r) => r.v);
  const op = d3.scaleLinear().domain(ext).range([0.06, 0.62]);
  const tip = DM.makeTip(el);
  const over = (sel) => sel.on('pointermove', (event, c) => tip.show(event, [`${c.type} · ${c.name}${c.peak ? ' (peak month)' : ''}`, `Mean rating ${f2(c.rating)} stars`, `Rated three stars or fewer: ${f1(c.low)}%`, `${fi(c.n)} reviews`])).on('pointerleave', () => tip.hide());
  if (!tall) {
    const left = d3.max(TYPES, (t) => textWidth(svg, t, 'dm-strong')) + 26, top = 30, rowH = 40, H = top + TYPES.length * rowH + 4;
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
    const x = d3.scaleBand().domain(months.map((m) => m.m)).range([left, W]).paddingInner(0.05);
    const y = d3.scaleBand().domain(TYPES).range([top, top + TYPES.length * rowH]).paddingInner(0.1);
    const mh = svg.append('g').selectAll('g').data(months).join('g').attr('transform', (m) => `translate(${x(m.m) + x.bandwidth() / 2},0)`);
    mh.append('text').attr('class', (m) => (m.peak ? 'dm-bold' : null)).attr('y', 14).attr('text-anchor', 'middle').text((m) => m.name);
    mh.filter((m) => m.peak).append('circle').attr('cy', 22).attr('r', 2.5).style('fill', 'var(--color-fg)');
    const lab = svg.append('g').selectAll('g').data(TYPES).join('g').attr('transform', (t) => `translate(0,${y(t) + y.bandwidth() / 2})`);
    lab.append('circle').attr('cx', 5).attr('r', 4.5).style('fill', (t) => colorOf(t));
    lab.append('text').attr('class', 'dm-strong').attr('x', 16).attr('dy', '0.35em').text((t) => t);
    const cell = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', (c) => `translate(${x(c.m)},${y(c.type)})`);
    cell.append('rect').attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 4).style('fill', (c) => colorOf(c.type)).attr('fill-opacity', (c) => op(c.v));
    cell.append('text').attr('class', 'dm-strong').attr('x', x.bandwidth() / 2).attr('y', y.bandwidth() / 2).attr('dy', '0.35em').attr('text-anchor', 'middle').text((c) => (x.bandwidth() > 34 ? fmt(c.v) : isRating ? f1(c.v) : f0(c.v)));
    over(cell.append('rect').attr('class', 'dm-hit').attr('width', x.bandwidth()).attr('height', y.bandwidth()));
  } else {
    const left = textWidth(svg, 'Sep', 'dm-bold') + 22, top = 24, rowH = 28, H = top + months.length * rowH + 4;
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
    const x = d3.scaleBand().domain(TYPES).range([left, W]).paddingInner(0.05);
    const y = d3.scaleBand().domain(months.map((m) => m.m)).range([top, top + months.length * rowH]).paddingInner(0.1);
    svg.append('g').selectAll('text').data(TYPES).join('text').attr('class', 'dm-strong').attr('x', (t) => x(t) + x.bandwidth() / 2).attr('y', 14).attr('text-anchor', 'middle').text((t) => t);
    const mh = svg.append('g').selectAll('g').data(months).join('g').attr('transform', (m) => `translate(0,${y(m.m) + y.bandwidth() / 2})`);
    mh.filter((m) => m.peak).append('circle').attr('cx', 4).attr('r', 2.5).style('fill', 'var(--color-fg)');
    mh.append('text').attr('class', (m) => (m.peak ? 'dm-bold' : null)).attr('x', 12).attr('dy', '0.35em').text((m) => m.name);
    const cell = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', (c) => `translate(${x(c.type)},${y(c.m)})`);
    cell.append('rect').attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 4).style('fill', (c) => colorOf(c.type)).attr('fill-opacity', (c) => op(c.v));
    cell.append('text').attr('class', 'dm-strong').attr('x', x.bandwidth() / 2).attr('y', y.bandwidth() / 2).attr('dy', '0.35em').attr('text-anchor', 'middle').text((c) => fmt(c.v) + (isRating ? '' : '%'));
    over(cell.append('rect').attr('class', 'dm-hit').attr('width', x.bandwidth()).attr('height', y.bandwidth()));
  }
});

// yearly trend
dash.draw('trend', (el) => {
  if (!DM.ready(el, ['trend'])) return;
  const metric = DM.param('tmetric'), hl = DM.param('tprop'), isRating = metric === 'rating';
  const all = dash.data('trend').data.map((r) => ({level: r.level, name: r.name, type: r.type, year: num(r.year), n: num(r.n), rating: num(r.rating), low: num(r.low_share), v: num(r[metric])}))
    .filter((r) => r.year >= 2010 && r.n >= 10);
  const series = TYPES.map((t) => ({key: t, type: t, dashed: false, pts: all.filter((r) => r.level === 'type' && r.name === t).sort((a, b) => a.year - b.year)})).filter((s) => s.pts.length);
  const hp = hl ? all.filter((r) => r.level === 'property' && r.name === hl).sort((a, b) => a.year - b.year) : [];
  if (hp.length) series.push({key: hl, type: hp[0].type, dashed: true, pts: hp});
  el.replaceChildren();
  const W = DM.width(el), H = 320, top = 16, bottom = 30;
  const svg = DM.svg(el, W, H, 'Line chart of ratings by year of review for ryokans, hotels and hybrids');
  const pts = series.flatMap((s) => s.pts), ext = d3.extent(pts, (r) => r.v);
  const pad = Math.max(isRating ? 0.03 : 1, (ext[1] - ext[0]) * 0.12);
  const y = d3.scaleLinear().domain([isRating ? ext[0] - pad : 0, isRating ? Math.min(5, ext[1] + pad) : ext[1] + pad]).nice(5).range([H - bottom, top]);
  const yt = y.ticks(5), yf = isRating ? f1 : (v) => v + '%';
  const left = d3.max(yt, (t) => textWidth(svg, yf(t))) + 10;
  const right = d3.max(series, (s) => textWidth(svg, short(s.key), 'dm-strong')) + 14;
  const years = d3.range(2010, 2027), x = d3.scaleLinear().domain([2010, 2026]).range([left + 8, W - right]);
  svg.append('rect').attr('class', 'dm-band').attr('x', x(2019.5)).attr('width', x(2022.5) - x(2019.5)).attr('y', top).attr('height', H - bottom - top);
  svg.append('g').selectAll('line').data(yt).join('line').attr('class', 'dm-grid').attr('x1', left).attr('x2', W - right).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
  svg.append('g').selectAll('text').data(yt).join('text').attr('x', left - 8).attr('y', (d) => y(d)).attr('dy', '0.35em').attr('text-anchor', 'end').text((d) => yf(d));
  const xt = years.filter((yr) => (W < 520 ? yr % 4 === 2 : yr % 2 === 0));
  svg.append('g').selectAll('text').data(xt).join('text').attr('x', (d) => x(d)).attr('y', H - 8).attr('text-anchor', 'middle').text((d) => d);
  const line = d3.line().x((d) => x(d.year)).y((d) => y(d.v));
  const sg = svg.append('g').selectAll('g').data(series).join('g');
  sg.append('path').attr('d', (s) => line(s.pts)).attr('fill', 'none').style('stroke', (s) => colorOf(s.type)).attr('stroke-width', 2).attr('stroke-dasharray', (s) => (s.dashed ? '5 4' : null)).attr('stroke-linejoin', 'round').attr('opacity', (s) => (hp.length && !s.dashed ? 0.45 : 1));
  sg.selectAll('circle').data((s) => s.pts.map((p) => ({...p, dashed: s.dashed}))).join('circle').attr('cx', (d) => x(d.year)).attr('cy', (d) => y(d.v)).attr('r', 3.5).style('fill', (d) => colorOf(d.type)).style('stroke', 'var(--color-panel)').attr('stroke-width', 1.5).attr('opacity', (d) => (hp.length && !d.dashed ? 0.45 : 1));
  const ends = series.map((s) => { const p = s.pts[s.pts.length - 1]; return {key: s.key, x: x(p.year), y: y(p.v)}; }).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
  svg.append('g').selectAll('text').data(ends).join('text').attr('class', 'dm-strong').attr('x', W - right + 8).attr('y', (d) => d.y).attr('dy', '0.35em').text((d) => short(d.key));
  const tip = DM.makeTip(el);
  const cross = svg.append('line').attr('class', 'dm-ref').attr('y1', top).attr('y2', H - bottom).style('display', 'none');
  const step = x(2011) - x(2010);
  svg.append('g').selectAll('rect').data(years).join('rect').attr('class', 'dm-hit').attr('x', (d) => x(d) - step / 2).attr('y', top).attr('width', step).attr('height', H - bottom - top)
    .on('pointermove', (event, yr) => {
      cross.style('display', null).attr('x1', x(yr)).attr('x2', x(yr));
      const at = series.map((s) => ({s, p: s.pts.find((p) => p.year === yr)})).filter((d) => d.p);
      tip.show(event, [String(yr)].concat(at.length ? at.map((d) => `${d.s.key}: ${isRating ? f2(d.p.v) + ' stars' : f1(d.p.v) + '%'} (${fi(d.p.n)} reviews)`) : ['Fewer than ten reviews']));
    })
    .on('pointerleave', () => { cross.style('display', 'none'); tip.hide(); });
});

// schematic map of central Kyoto
dash.draw('kmap', (el) => {
  if (!DM.ready(el, ['locations', 'hotspots'])) return;
  const props = dash.data('locations').data.map((r) => ({name: r.property, type: r.type, lat: num(r.lat), lon: num(r.lon), mean: num(r.mean), near: r.nearest_hotspot, dn: num(r.dist_nearest_m), dg: num(r.dist_gion_kiyomizu_m), ds: num(r.dist_station_m), crowd: num(r.crowd_exposed)}));
  const hots = dash.data('hotspots').data.map((r) => ({name: r.name, area: r.area, lat: num(r.lat), lon: num(r.lon)}));
  el.replaceChildren();
  const B = {w: 135.7435, e: 135.7905, s: 34.9815, n: 35.0265}, kx = Math.cos(35 * Math.PI / 180);
  const W = DM.width(el), mapW = Math.min(W, 620), ox = (W - mapW) / 2, pad = 18;
  const scale = (mapW - 2 * pad) / ((B.e - B.w) * kx), mapH = (B.n - B.s) * scale + 2 * pad;
  const H = mapH + 6;
  const svg = DM.svg(el, W, H, 'Schematic map of central Kyoto showing the ten properties and nearby busy sights');
  const X = (lon) => ox + pad + (lon - B.w) * kx * scale, Y = (lat) => pad + (B.n - lat) * scale;
  const mPerDeg = 110950, pxPerM = scale / mPerDeg;
  svg.append('rect').attr('x', ox).attr('y', 0).attr('width', mapW).attr('height', mapH).attr('rx', 8).style('fill', 'var(--color-bg)').style('stroke', 'var(--color-border-line)');
  const river = [[35.0265, 135.7712], [35.017, 135.7712], [35.010, 135.7712], [35.0037, 135.7716], [34.996, 135.769], [34.989, 135.7672], [34.9815, 135.766]];
  svg.append('path').attr('d', d3.line().x((d) => X(d[1])).y((d) => Y(d[0])).curve(d3.curveMonotoneY)(river)).attr('fill', 'none').style('stroke', 'var(--color-fg-muted)').attr('stroke-width', 5).attr('opacity', 0.16).attr('stroke-linecap', 'round');
  svg.append('text').attr('x', X(135.7712) - 8).attr('y', Y(35.0245)).attr('text-anchor', 'end').text('Kamo River');
  const inside = (p) => p.lon >= B.w && p.lon <= B.e && p.lat >= B.s && p.lat <= B.n;
  const hin = hots.filter(inside), hout = hots.filter((h) => !inside(h));
  svg.append('clipPath').attr('id', 'dm-mapclip').append('rect').attr('x', ox).attr('y', 0).attr('width', mapW).attr('height', mapH).attr('rx', 8);
  svg.append('g').attr('clip-path', 'url(#dm-mapclip)').selectAll('circle').data(hin.filter((h) => h.area === 'Gion / Kiyomizu')).join('circle').attr('class', 'dm-ref').attr('cx', (h) => X(h.lon)).attr('cy', (h) => Y(h.lat)).attr('r', 1000 * pxPerM);
  svg.append('g').selectAll('rect').data(hin).join('rect').attr('x', (h) => X(h.lon) - 4.5).attr('y', (h) => Y(h.lat) - 4.5).attr('width', 9).attr('height', 9).attr('transform', (h) => `rotate(45 ${X(h.lon)} ${Y(h.lat)})`).style('fill', 'var(--color-fg-muted)').style('stroke', 'var(--color-bg)').attr('stroke-width', 2);
  svg.append('g').selectAll('circle').data(props).join('circle').attr('cx', (p) => X(p.lon)).attr('cy', (p) => Y(p.lat)).attr('r', 6.5).style('fill', (p) => colorOf(p.type)).style('stroke', 'var(--color-bg)').attr('stroke-width', 2);
  const narrow = mapW < 480;
  DM.labels(svg, props.map((p) => ({x: X(p.lon), y: Y(p.lat), label: short(p.name), cls: 'dm-bold', r: 7}))
    .concat(hin.map((h) => ({x: X(h.lon), y: Y(h.lat), label: narrow ? h.name.replace(' (Gion)', '').replace(' Shrine', '').replace(' Market', '').replace(' Castle', '') : h.name.replace(' (Gion)', ''), cls: null, r: 6}))), [ox + 4, 4, ox + mapW - 4, mapH - 26]);
  // sights beyond the frame
  const cLat = (B.n + B.s) / 2, cLon = (B.e + B.w) / 2;
  hout.forEach((h) => {
    const dxm = (h.lon - cLon) * kx * mPerDeg, dym = (h.lat - cLat) * mPerDeg, km = Math.sqrt(dxm * dxm + dym * dym) / 1000;
    const ang = Math.atan2(-dym, dxm), ex = Math.cos(ang), ey = Math.sin(ang);
    const t = Math.min((mapW / 2 - 12) / Math.abs(ex || 1e-9), (mapH / 2 - 14) / Math.abs(ey || 1e-9));
    const px = ox + mapW / 2 + ex * t, py = mapH / 2 + ey * t;
    const arrow = ey > 0.7 ? '↓' : ey < -0.7 ? (ex > 0.3 ? '↗' : ex < -0.3 ? '↖' : '↑') : ex > 0 ? '→' : '←';
    const anchor = ex > 0.5 ? 'end' : ex < -0.5 ? 'start' : 'middle';
    const nm = h.name.replace(' (Arashiyama)', '').replace(' Taisha', '').replace('Togetsukyo Bridge', 'Arashiyama');
    svg.append('text').attr('x', px).attr('y', py).attr('dy', '0.35em').attr('text-anchor', anchor).text(anchor === 'start' ? `${arrow} ${nm} ${f1(km)} km` : `${nm} ${f1(km)} km ${arrow}`);
  });
  // scale bar
  const sbx = ox + 14, sby = mapH - 12;
  svg.append('line').attr('x1', sbx).attr('x2', sbx + 1000 * pxPerM).attr('y1', sby).attr('y2', sby).style('stroke', 'var(--color-fg)').attr('stroke-width', 2);
  svg.append('text').attr('class', 'dm-strong').attr('x', sbx + 1000 * pxPerM + 6).attr('y', sby).attr('dy', '0.35em').text('1 km');
  svg.append('text').attr('class', 'dm-strong').attr('x', ox + mapW - 14).attr('y', 16).attr('text-anchor', 'end').text('N ↑');
  const tip = DM.makeTip(el), km = (m) => f1(m / 1000) + ' km';
  svg.append('g').selectAll('circle').data(props).join('circle').attr('class', 'dm-hit').attr('cx', (p) => X(p.lon)).attr('cy', (p) => Y(p.lat)).attr('r', 14)
    .on('pointermove', (event, p) => tip.show(event, [p.name, `${p.type} · mean rating ${f2(p.mean)}`, `Nearest busy sight: ${p.near.replace(' (Gion)', '')}, ${km(p.dn)}`, `Gion / Kiyomizu: ${km(p.dg)} · Kyoto Station: ${km(p.ds)}`, `Reviews describing crowds: ${f1(p.crowd)}%`]))
    .on('pointerleave', () => tip.hide());
  svg.append('g').selectAll('circle').data(hin).join('circle').attr('class', 'dm-hit').attr('cx', (h) => X(h.lon)).attr('cy', (h) => Y(h.lat)).attr('r', 12)
    .on('pointermove', (event, h) => tip.show(event, [h.name, `Congestion-forecast area: ${h.area}`]))
    .on('pointerleave', () => tip.hide());
});

// distance against outcome, ten properties
dash.draw('locscatter', (el) => {
  if (!DM.ready(el, ['locations', 'location_tests'])) return;
  const lx = DM.param('lx'), ly = DM.param('ly');
  const rows = dash.data('locations').data.map((r) => ({name: r.property, type: r.type, x: num(r[lx]) / 1000, y: num(r[ly]), n: num(r.n)}));
  const test = dash.data('location_tests').data.find((t) => t.predictor === lx && t.outcome === ly);
  const YL = {mean: ['Mean rating (stars)', f2, ''], low_share: ['Rated three stars or fewer', f1, '%'], location_positive: ['Positive share of location mentions', f1, '%'], location_negative: ['Negative share of location mentions', f1, '%'], crowd_exposed: ['Reviews describing crowds', f1, '%'], peak_effect: ['Peak-season change in rating (stars)', (v) => DM.signed(v), '']};
  const XL = {dist_gion_kiyomizu_m: 'Distance to Gion / Kiyomizu (km)', dist_nearest_m: 'Distance to nearest busy sight (km)', dist_station_m: 'Distance to Kyoto Station (km)'};
  const [ylab, yfmt, yunit] = YL[ly] || [ly, f2, ''];
  el.replaceChildren();
  const W = DM.width(el), H = 340, top = 34, bottom = 40, right = 14;
  const svg = DM.svg(el, W, H, 'Scatter plot of ten properties: distance against the chosen outcome');
  const ye = d3.extent(rows, (r) => r.y), yp = (ye[1] - ye[0]) * 0.14 || 0.1;
  const y = d3.scaleLinear().domain([ye[0] - yp, ye[1] + yp]).nice(5).range([H - bottom, top]);
  const yt = y.ticks(5), left = d3.max(yt, (t) => textWidth(svg, yfmt(t) + yunit)) + 10;
  const x = d3.scaleLinear().domain([0, d3.max(rows, (r) => r.x) * 1.08]).nice(5).range([left, W - right]);
  const xt = x.ticks(W < 460 ? 4 : 6);
  svg.append('g').selectAll('line').data(yt).join('line').attr('class', 'dm-grid').attr('x1', left).attr('x2', W - right).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
  svg.append('g').selectAll('text').data(yt).join('text').attr('x', left - 6).attr('y', (d) => y(d)).attr('dy', '0.35em').attr('text-anchor', 'end').text((d) => yfmt(d) + yunit);
  svg.append('g').selectAll('text').data(xt).join('text').attr('x', (d) => x(d)).attr('y', H - bottom + 15).attr('text-anchor', 'middle').text((d) => f1(d));
  svg.append('text').attr('x', (left + W - right) / 2).attr('y', H - 5).attr('text-anchor', 'middle').text(XL[lx] || lx);
  svg.append('text').attr('x', 0).attr('y', 12).text(ylab);
  if (ly === 'peak_effect' && y.domain()[0] < 0 && y.domain()[1] > 0) svg.append('line').attr('class', 'dm-ref').attr('x1', left).attr('x2', W - right).attr('y1', y(0)).attr('y2', y(0));
  if (test) svg.append('text').attr('class', 'dm-bold').attr('x', W - right).attr('y', 12).attr('text-anchor', 'end').text(`Rank correlation ${DM.signed(num(test.spearman))}, ${DM.pval(num(test.p))}`);
  const pts = rows.map((r) => ({...r, px: x(r.x), py: y(r.y)}));
  svg.append('g').selectAll('circle').data(pts).join('circle').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 6.5).style('fill', (p) => colorOf(p.type)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
  DM.labels(svg, pts.map((p) => ({x: p.px, y: p.py, label: short(p.name), cls: 'dm-strong', r: 7})), [left, top - 6, W, H - bottom]);
  const tip = DM.makeTip(el);
  svg.append('g').selectAll('circle').data(pts).join('circle').attr('class', 'dm-hit').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 14)
    .on('pointermove', (event, p) => tip.show(event, [p.name, `${p.type} · ${fi(p.n)} reviews`, `${(XL[lx] || lx).replace(' (km)', '')}: ${f2(p.x)} km`, `${ylab.replace(' (stars)', '')}: ${yfmt(p.y)}${yunit}`]))
    .on('pointerleave', () => tip.hide());
});

// crowding language by type
dash.draw('crowd', (el) => {
  if (!DM.ready(el, ['crowd'])) return;
  const split = DM.param('csplit');
  const rows = dash.data('crowd').data.filter((r) => r.split === split && r.group !== 'All months').map((r) => ({type: r.type, group: r.group, n: num(r.n), v: num(r.exposed_share), refuge: num(r.refuge_share), rc: num(r.rating_if_crowds), rn: num(r.rating_if_none)}));
  const groups = Array.from(new Set(rows.map((r) => r.group)));
  if (split === 'season') groups.sort((a, b) => d3.descending(a, b)); else groups.sort();
  el.replaceChildren();
  const W = DM.width(el), barH = 15, gap = 3, head = 20, groupPad = 14, top = 2, bottom = 28;
  const groupH = head + groups.length * (barH + gap) + groupPad;
  const H = top + TYPES.length * groupH + bottom;
  const svg = DM.svg(el, W, H, 'Bar chart of the share of reviews describing crowding, by accommodation type');
  const glab = (g) => (split === 'period' ? g.replace('-', ' to ') : g);
  const left = d3.max(groups, (g) => textWidth(svg, glab(g))) + 12, right = textWidth(svg, '00.0%', 'dm-strong') + 10;
  const x = d3.scaleLinear().domain([0, d3.max(rows, (r) => r.v) || 1]).nice(4).range([left, W - right]);
  const ticks = x.ticks(W < 460 ? 3 : 5);
  svg.append('g').selectAll('line').data(ticks).join('line').attr('class', 'dm-grid').attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', top).attr('y2', H - bottom);
  svg.append('g').selectAll('text').data(ticks).join('text').attr('x', (d) => x(d)).attr('y', H - bottom + 16).attr('text-anchor', 'middle').text((d) => d + '%');
  const tip = DM.makeTip(el);
  const grp = svg.append('g').selectAll('g').data(TYPES).join('g').attr('transform', (t, i) => `translate(0,${top + i * groupH})`);
  grp.append('text').attr('class', 'dm-bold').attr('x', 0).attr('y', 13).text((t) => (t === 'Hybrid' ? 'Hybrids' : t + 's'));
  const bar = grp.selectAll('g.b').data((t) => groups.map((g) => rows.find((r) => r.type === t && r.group === g)).filter(Boolean)).join('g').attr('class', 'b').attr('transform', (r) => `translate(0,${head + groups.indexOf(r.group) * (barH + gap)})`);
  bar.append('text').attr('x', left - 8).attr('y', barH / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => glab(r.group));
  bar.append('path').attr('d', (r) => DM.hbar(left, x(r.v), barH)).style('fill', (r) => colorOf(r.type));
  bar.append('text').attr('class', 'dm-strong').attr('x', (r) => x(r.v) + 6).attr('y', barH / 2).attr('dy', '0.35em').text((r) => f1(r.v) + '%');
  bar.append('rect').attr('class', 'dm-hit').attr('y', -gap / 2).attr('width', W).attr('height', barH + gap)
    .on('pointermove', (event, r) => tip.show(event, [`${r.type} · ${glab(r.group)}`, `${f1(r.v)}% of ${fi(r.n)} reviews describe crowding`, `${f1(r.refuge)}% describe an escape from crowds`, isNaN(r.rc) ? '' : `Mean rating ${f2(r.rc)} when crowding is described, ${f2(r.rn)} otherwise`]))
    .on('pointerleave', () => tip.hide());
  svg.append('line').attr('class', 'dm-axis').attr('x1', left).attr('x2', left).attr('y1', top).attr('y2', H - bottom);
});
}
