// Research question 1: what guests narrate.
{
const DM = window.DM, {num, colorOf, textWidth, f0, f1, f2, fi, TYPES, ASPECTS, SHORT} = DM;

// property x aspect heat map
dash.draw('heat', (el) => {
  if (!DM.ready(el, ['aspects', 'properties'])) return;
  const metric = DM.param('metric');
  const order = dash.data('properties').data.map((r) => ({property: r.property, type: r.type, mean: num(r.mean)}))
    .sort((a, b) => d3.ascending(TYPES.indexOf(a.type), TYPES.indexOf(b.type)) || d3.descending(a.mean, b.mean));
  const cells = dash.data('aspects').data.map((r) => ({property: r.property, type: r.type, aspect: r.aspect, v: num(r[metric]), n: num(r.n_mentions), mention: num(r.mention_share), pos: num(r.positive_share), neg: num(r.negative_share)}));
  el.replaceChildren();
  const W = DM.width(el), rowH = 34;
  const svg = d3.select(el).append('svg').attr('role', 'img').attr('aria-label', 'Heat map of ten properties by seven aspects of the stay');
  const narrow = W < 520;
  const label = (p) => (narrow ? p.replace(' Kyoto', '').replace(' Ryokan', '').replace('The ', '') : p);
  const left = d3.max(order, (r) => textWidth(svg, label(r.property), 'dm-strong')) + 26;
  const x = d3.scaleBand().domain(ASPECTS).range([left, W]).paddingInner(0.04);
  const fits = (map) => ASPECTS.every((a) => textWidth(svg, map ? map[a] : a) + 6 <= x.bandwidth());
  const full = fits(null), tilt = !full && !fits(SHORT);
  const top = tilt ? 12 + d3.max(ASPECTS, (a) => textWidth(svg, SHORT[a])) * 0.72 : 26;
  const H = top + order.length * rowH + 4;
  svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
  const y = d3.scaleBand().domain(order.map((r) => r.property)).range([top, top + order.length * rowH]).paddingInner(0.08);
  const op = d3.scaleLinear().domain([0, d3.max(cells, (c) => c.v) || 1]).range([0.05, 0.62]);
  svg.append('g').selectAll('text').data(ASPECTS).join('text')
    .attr('transform', (d) => `translate(${x(d) + x.bandwidth() / 2},${top - 9})` + (tilt ? ' rotate(-45)' : ''))
    .attr('text-anchor', tilt ? 'start' : 'middle').text((d) => (full ? d : SHORT[d]));
  const lab = svg.append('g').selectAll('g').data(order).join('g').attr('transform', (r) => `translate(0,${y(r.property) + y.bandwidth() / 2})`);
  lab.append('circle').attr('cx', 5).attr('r', 4.5).style('fill', (r) => colorOf(r.type));
  lab.append('text').attr('class', 'dm-strong').attr('x', 16).attr('dy', '0.35em').text((r) => label(r.property));
  const tip = DM.makeTip(el);
  const cell = svg.append('g').selectAll('g').data(cells).join('g').attr('transform', (c) => `translate(${x(c.aspect)},${y(c.property)})`);
  cell.append('rect').attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 4).style('fill', dash.colors[0]).attr('fill-opacity', (c) => (isNaN(c.v) ? 0 : op(c.v)));
  cell.append('text').attr('class', 'dm-strong').attr('x', x.bandwidth() / 2).attr('y', y.bandwidth() / 2).attr('dy', '0.35em').attr('text-anchor', 'middle').text((c) => (isNaN(c.v) ? '' : f0(c.v)));
  cell.append('rect').attr('class', 'dm-hit').attr('width', x.bandwidth()).attr('height', y.bandwidth())
    .on('pointermove', (event, c) => tip.show(event, [`${c.property} · ${c.aspect}`, `Mentioned in ${f1(c.mention)}% of reviews (${fi(c.n)})`, `Positive mentions: ${f1(c.pos)}%`, `Negative mentions: ${f1(c.neg)}%`]))
    .on('pointerleave', () => tip.hide());
});

// perceptual map (correspondence analysis); on a narrow page the main dimension runs top to bottom
dash.draw('pmap', (el) => {
  if (!DM.ready(el, ['perceptual'])) return;
  const W = DM.width(el), tall = W < 600;
  const rows = dash.data('perceptual').data.map((r) => ({kind: r.kind, label: r.label, type: r.type, d1: num(r.dim1), d2: num(r.dim2), i1: num(r.inertia1), i2: num(r.inertia2)}))
    .map((r) => ({...r, x: tall ? r.d2 : r.d1, y: tall ? -r.d1 : r.d2}));
  el.replaceChildren();
  const left = 14, right = 14, top = 14, bottom = 40;
  const ex = d3.extent(rows, (r) => r.x), ey = d3.extent(rows, (r) => r.y);
  const px = (ex[1] - ex[0]) * (tall ? 0.45 : 0.16), py = (ey[1] - ey[0]) * (tall ? 0.08 : 0.3);
  const dx = [ex[0] - px, ex[1] + px], dy = [ey[0] - py, ey[1] + py];
  const k = (W - left - right) / (dx[1] - dx[0]);                       // same scale on both axes
  const plotH = Math.max(230, Math.min(tall ? 640 : 460, k * (dy[1] - dy[0])));
  const H = top + plotH + bottom;
  const svg = DM.svg(el, W, H, 'Perceptual map placing ten properties and seven aspects on the first two dimensions of a correspondence analysis');
  const x = d3.scaleLinear().domain(dx).range([left, W - right]);
  const mid = (dy[0] + dy[1]) / 2, half = plotH / 2 / k;
  const y = d3.scaleLinear().domain([mid - half, mid + half]).range([top + plotH, top]);
  svg.append('line').attr('class', 'dm-axis').attr('x1', left).attr('x2', W - right).attr('y1', y(0)).attr('y2', y(0));
  svg.append('line').attr('class', 'dm-axis').attr('x1', x(0)).attr('x2', x(0)).attr('y1', top).attr('y2', top + plotH);
  const l1 = `dimension 1 (${f1(rows[0].i1)}% of the variation)`, l2 = `dimension 2 (${f1(rows[0].i2)}%)`;
  svg.append('text').attr('x', left).attr('y', H - 20).text(tall ? `Top to bottom: ${l1}` : `Left to right: ${l1}`);
  svg.append('text').attr('x', left).attr('y', H - 4).text(tall ? `Left to right: ${l2}` : `Bottom to top: ${l2}`);
  const pts = rows.map((r) => ({...r, px: x(r.x), py: y(r.y)}));
  const asp = pts.filter((p) => p.kind === 'aspect'), prop = pts.filter((p) => p.kind === 'property');
  svg.append('g').selectAll('rect').data(asp).join('rect').attr('x', (p) => p.px - 4.5).attr('y', (p) => p.py - 4.5).attr('width', 9).attr('height', 9)
    .attr('transform', (p) => `rotate(45 ${p.px} ${p.py})`).style('fill', 'var(--color-fg-muted)').style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
  svg.append('g').selectAll('circle').data(prop).join('circle').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 6).style('fill', (p) => colorOf(p.type)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
  const short = (s) => (W < 600 ? s.replace(' Kyoto', '').replace(' Ryokan', '').replace('The ', '') : s);
  DM.labels(svg, asp.map((p) => ({x: p.px, y: p.py, label: tall ? SHORT[p.label] : p.label, cls: 'dm-bold', r: 6})).concat(prop.map((p) => ({x: p.px, y: p.py, label: short(p.label), cls: 'dm-strong', r: 6}))), [0, 0, W, top + plotH]);
  const tip = DM.makeTip(el);
  svg.append('g').selectAll('circle').data(pts).join('circle').attr('class', 'dm-hit').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 14)
    .on('pointermove', (event, p) => tip.show(event, [p.label, p.kind === 'property' ? p.type : 'Aspect of the stay', `Dimension 1: ${DM.signed(p.d1)}`, `Dimension 2: ${DM.signed(p.d2)}`]))
    .on('pointerleave', () => tip.hide());
});

// distinctive vocabulary
dash.draw('words', (el) => {
  if (!DM.ready(el, ['words'])) return;
  const all = dash.data('words').data.map((r) => ({term: r.term, side: r.side, ry: num(r.ryokan_rate), ho: num(r.hotel_rate), times: num(r.times)}));
  el.replaceChildren();
  const W = DM.width(el), two = W >= 620, gap = 28, panelW = two ? (W - gap) / 2 : W, rowH = 22, head = 22, n = 14;
  const panels = ['Ryokan', 'Hotel'].map((side) => ({side, rows: all.filter((r) => r.side === side).slice(0, n)}));
  const H = two ? head + n * rowH + 4 : 2 * (head + n * rowH) + 20;
  const svg = DM.svg(el, W, H, 'Bar charts of the most distinctive terms in ryokan reviews and in hotel reviews');
  const tip = DM.makeTip(el);
  const max = d3.max(all, (r) => Math.max(r.ry, r.ho));
  panels.forEach((p, i) => {
    const g = svg.append('g').attr('transform', two ? `translate(${i * (panelW + gap)},0)` : `translate(0,${i * (head + n * rowH + 20)})`);
    const own = (r) => (p.side === 'Ryokan' ? r.ry : r.ho), other = (r) => (p.side === 'Ryokan' ? r.ho : r.ry);
    const left = d3.max(p.rows, (r) => textWidth(svg, r.term, 'dm-strong')) + 10, right = textWidth(svg, '00.0%', 'dm-strong') + 8;
    const x = d3.scaleLinear().domain([0, max]).range([left, panelW - right]);
    g.append('text').attr('class', 'dm-bold').attr('x', 0).attr('y', 12).text(p.side === 'Ryokan' ? 'More in ryokan reviews' : 'More in hotel reviews');
    const row = g.selectAll('g.r').data(p.rows).join('g').attr('class', 'r').attr('transform', (r, j) => `translate(0,${head + j * rowH})`);
    row.append('text').attr('class', 'dm-strong').attr('x', left - 8).attr('y', rowH / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => r.term);
    row.append('path').attr('transform', 'translate(0,4)').attr('d', (r) => DM.hbar(left, x(own(r)), rowH - 8)).style('fill', colorOf(p.side));
    row.append('line').attr('x1', (r) => x(other(r))).attr('x2', (r) => x(other(r))).attr('y1', 2).attr('y2', rowH - 2).style('stroke', colorOf(p.side === 'Ryokan' ? 'Hotel' : 'Ryokan')).attr('stroke-width', 2);
    row.append('text').attr('class', 'dm-strong').attr('x', (r) => x(own(r)) + 6).attr('y', rowH / 2).attr('dy', '0.35em').text((r) => f1(own(r)) + '%');
    row.append('rect').attr('class', 'dm-hit').attr('width', panelW).attr('height', rowH)
      .on('pointermove', (event, r) => tip.show(event, [`“${r.term}”`, `Ryokan reviews: ${f1(r.ry)}%`, `Hotel reviews: ${f1(r.ho)}%`, `About ${f0(r.times)} times more frequent in ${p.side.toLowerCase()} reviews`]))
      .on('pointerleave', () => tip.hide());
  });
});

// topics
dash.draw('topics', (el) => {
  if (!DM.ready(el, ['topics'])) return;
  const period = DM.param('tperiod');
  const rows = dash.data('topics').data.filter((r) => r.period === period).map((r) => ({topic: num(r.topic), label: r.label, words: r.top_words, type: r.type, n: num(r.n), v: num(r.share)}));
  const topics = Array.from(d3.group(rows, (r) => r.topic), ([t, rs]) => ({t, label: rs[0].label, words: rs[0].words, rs}))
    .sort((a, b) => d3.descending(d3.max(a.rs, (r) => (r.type === 'Ryokan' ? r.v : 0)), d3.max(b.rs, (r) => (r.type === 'Ryokan' ? r.v : 0))));
  el.replaceChildren();
  if (!topics.length) { DM.placeholder(el, 'ok'); return; }
  const W = DM.width(el), barH = 13, gap = 2, head = 34, groupPad = 14, top = 4, bottom = 26;
  const groupH = head + TYPES.length * (barH + gap) + groupPad;
  const H = top + topics.length * groupH + bottom;
  const svg = DM.svg(el, W, H, 'Grouped bar chart of the share of review content in five topics, for ryokans, hotels and hybrids');
  const left = 4, right = textWidth(svg, '00.0%', 'dm-strong') + 10;
  const x = d3.scaleLinear().domain([0, Math.max(35, d3.max(rows, (r) => r.v))]).range([left, W - right]);
  const ticks = x.ticks(W < 460 ? 4 : 7);
  svg.append('g').selectAll('text').data(ticks).join('text').attr('x', (d) => x(d)).attr('y', H - 6).attr('text-anchor', (d) => (d === 0 ? 'start' : 'middle')).text((d) => d + '%');
  const tip = DM.makeTip(el);
  const maxChars = Math.max(20, Math.floor((W - 8) / 6.2));
  const grp = svg.append('g').selectAll('g').data(topics).join('g').attr('transform', (t, i) => `translate(0,${top + i * groupH})`);
  grp.append('text').attr('class', 'dm-bold').attr('x', left).attr('y', 12).text((t) => t.label);
  grp.append('text').attr('x', left).attr('y', 27).text((t) => (t.words.length > maxChars ? t.words.slice(0, t.words.lastIndexOf(',', maxChars)) + ' …' : t.words));
  const bar = grp.selectAll('g.b').data((t) => TYPES.map((ty) => t.rs.find((r) => r.type === ty)).filter(Boolean)).join('g').attr('class', 'b').attr('transform', (r) => `translate(0,${head + TYPES.indexOf(r.type) * (barH + gap)})`);
  bar.append('path').attr('d', (r) => DM.hbar(left, x(r.v), barH)).style('fill', (r) => colorOf(r.type));
  bar.append('text').attr('class', 'dm-strong').attr('x', (r) => x(r.v) + 6).attr('y', barH / 2).attr('dy', '0.35em').text((r) => f1(r.v) + '%');
  bar.append('rect').attr('class', 'dm-hit').attr('y', -gap / 2).attr('width', W).attr('height', barH + gap)
    .on('pointermove', (event, r) => tip.show(event, [`${r.label} · ${r.type}`, `${f1(r.v)}% of review content`, `${fi(r.n)} reviews, ${period === 'All years' ? 'all years' : period.replace('-', ' to ')}`]))
    .on('pointerleave', () => tip.hide());
});

// aspects praised or criticised together
dash.draw('cooc', (el) => {
  if (!DM.ready(el, ['cooccurrence'])) return;
  const type = DM.param('ctype'), pol = DM.param('cpol');
  const cells = dash.data('cooccurrence').data.filter((r) => r.type === type && r.polarity === pol)
    .map((r) => ({a: r.aspect_a, b: r.aspect_b, lift: num(r.lift), n: num(r.n_both), share: num(r.share_of_a)}));
  el.replaceChildren();
  const W = DM.width(el), rowH = 34;
  const svg = d3.select(el).append('svg').attr('role', 'img').attr('aria-label', 'Matrix of how often pairs of aspects are mentioned together, as lift over chance');
  const narrow = W < 560, lab = (a) => (narrow ? SHORT[a] : a);
  const left = d3.max(ASPECTS, (a) => textWidth(svg, lab(a), 'dm-strong')) + 12;
  const x = d3.scaleBand().domain(ASPECTS).range([left, W]).paddingInner(0.04);
  const fit = ASPECTS.every((a) => textWidth(svg, lab(a)) + 6 <= x.bandwidth());
  const fitShort = ASPECTS.every((a) => textWidth(svg, SHORT[a]) + 6 <= x.bandwidth());
  const tilt = !fit && !fitShort, top = tilt ? 12 + d3.max(ASPECTS, (a) => textWidth(svg, SHORT[a])) * 0.72 : 26;
  const H = top + ASPECTS.length * rowH + 4;
  svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H);
  const y = d3.scaleBand().domain(ASPECTS).range([top, top + ASPECTS.length * rowH]).paddingInner(0.08);
  const ok = (c) => !isNaN(c.lift) && c.n >= 5;
  const max = Math.max(1.6, d3.max(cells.filter(ok), (c) => c.lift) || 1.6);
  const op = d3.scaleLinear().domain([1, max]).range([0.06, 0.62]).clamp(true);
  svg.append('g').selectAll('text').data(ASPECTS).join('text')
    .attr('transform', (d) => `translate(${x(d) + x.bandwidth() / 2},${top - 9})` + (tilt ? ' rotate(-45)' : ''))
    .attr('text-anchor', tilt ? 'start' : 'middle').text((d) => (fit ? lab(d) : SHORT[d]));
  svg.append('g').selectAll('text').data(ASPECTS).join('text').attr('class', 'dm-strong').attr('x', left - 10).attr('y', (d) => y(d) + y.bandwidth() / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((d) => lab(d));
  const tip = DM.makeTip(el), word = pol === 'neg' ? 'criticize' : 'praise';
  const cell = svg.append('g').selectAll('g').data(cells.filter((c) => c.a !== c.b)).join('g').attr('transform', (c) => `translate(${x(c.b)},${y(c.a)})`);
  cell.append('rect').attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 4).style('fill', colorOf(type)).attr('fill-opacity', (c) => (ok(c) ? op(c.lift) : 0.03));
  cell.append('text').attr('class', 'dm-strong').attr('x', x.bandwidth() / 2).attr('y', y.bandwidth() / 2).attr('dy', '0.35em').attr('text-anchor', 'middle').text((c) => (ok(c) ? f1(c.lift) : '·'));
  cell.append('rect').attr('class', 'dm-hit').attr('width', x.bandwidth()).attr('height', y.bandwidth())
    .on('pointermove', (event, c) => tip.show(event, [`${c.a} with ${c.b}`, ok(c) ? `Lift ${f2(c.lift)}` : 'Too few reviews to judge', `${fi(c.n)} ${type.toLowerCase()} reviews ${word} both`, isNaN(c.share) ? '' : `${f1(c.share)}% of reviews that ${word} ${c.a.toLowerCase()} also ${word} ${c.b.toLowerCase()}`]))
    .on('pointerleave', () => tip.hide());
});
}
