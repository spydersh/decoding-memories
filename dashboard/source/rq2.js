// Research question 2: satisfaction and dissatisfaction.
{
const DM = window.DM, {num, colorOf, textWidth, f0, f1, f2, f3, fi, TYPES, ASPECTS, SHORT} = DM;
const mname = (m) => (m === 'bert' ? 'transformer' : 'lexicon');
const rewardRows = () => {
  const m = DM.param('measure');
  return dash.data('rewards').data.filter((r) => r.measure === m && (r.group === 'Ryokan' || r.group === 'Hotel'))
    .map((r) => ({group: r.group, aspect: r.aspect, reward: num(r.reward), pr: num(r.p_reward), penalty: num(r.penalty), pp: num(r.p_penalty), npos: num(r.n_positive), nneg: num(r.n_negative), imp: num(r.importance), perf: num(r.performance)}));
};

// rewards and penalties: one panel per type, shared scale
dash.draw('rp', (el) => {
  if (!DM.ready(el, ['rewards'])) return;
  const rows = rewardRows();
  el.replaceChildren();
  const W = DM.width(el), two = W >= 640, gap = 26, panelW = two ? (W - gap) / 2 : W, rowH = 30, head = 24, foot = 34;
  const panelH = head + ASPECTS.length * rowH + foot, H = two ? panelH : panelH * 2 + 12;
  const svg = DM.svg(el, W, H, 'Diverging bar charts of the reward and penalty of each aspect on the star rating, for ryokans and for hotels');
  const lo = Math.min(-0.1, d3.min(rows, (r) => Math.min(r.penalty, r.reward))), hi = Math.max(0.1, d3.max(rows, (r) => Math.max(r.penalty, r.reward)));
  const order = ASPECTS.slice().sort((a, b) => d3.ascending(d3.sum(rows.filter((r) => r.aspect === a), (r) => r.penalty), d3.sum(rows.filter((r) => r.aspect === b), (r) => r.penalty)));
  const tip = DM.makeTip(el);
  ['Ryokan', 'Hotel'].forEach((grp, i) => {
    const g = svg.append('g').attr('transform', two ? `translate(${i * (panelW + gap)},0)` : `translate(0,${i * (panelH + 12)})`);
    const rs = order.map((a) => rows.find((r) => r.group === grp && r.aspect === a)).filter(Boolean);
    const narrow = panelW < 380, lab = (a) => (narrow ? SHORT[a] : a);
    const left = d3.max(order, (a) => textWidth(svg, lab(a), 'dm-strong')) + 10;
    const padL = textWidth(svg, '−0.00', 'dm-strong') + 8, padR = textWidth(svg, '+0.00', 'dm-strong') + 8;
    const x = d3.scaleLinear().domain([lo, hi]).range([left + padL, panelW - padR]);
    g.append('text').attr('class', 'dm-bold').attr('x', 0).attr('y', 12).text(grp === 'Ryokan' ? 'Ryokans' : 'Hotels');
    const ticks = x.ticks(4);
    g.append('g').selectAll('line').data(ticks).join('line').attr('class', 'dm-grid').attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', head).attr('y2', head + rs.length * rowH);
    g.append('g').selectAll('text').data(ticks).join('text').attr('x', (d) => x(d)).attr('y', head + rs.length * rowH + 15).attr('text-anchor', 'middle').text((d) => (d === 0 ? '0' : DM.signed(d, f1)));
    g.append('text').attr('x', x(0) - 8).attr('y', panelH - 3).attr('text-anchor', 'end').text('← penalty');
    g.append('text').attr('x', x(0) + 8).attr('y', panelH - 3).text('reward →');
    const row = g.selectAll('g.r').data(rs).join('g').attr('class', 'r').attr('transform', (r, j) => `translate(0,${head + j * rowH})`);
    row.append('text').attr('class', 'dm-strong').attr('x', left - 8).attr('y', rowH / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => lab(r.aspect));
    const bh = 9;
    row.append('path').attr('transform', `translate(0,${rowH / 2 - bh - 1})`).attr('d', (r) => DM.hbar(x(0), x(r.reward), bh)).style('fill', colorOf(grp)).attr('fill-opacity', (r) => (r.pr < 0.05 ? 1 : 0.3));
    row.append('path').attr('transform', `translate(0,${rowH / 2 + 1})`).attr('d', (r) => DM.hbar(x(0), x(r.penalty), bh)).style('fill', colorOf(grp)).attr('fill-opacity', (r) => (r.pp < 0.05 ? 1 : 0.3));
    row.append('text').attr('class', 'dm-strong').attr('x', (r) => x(Math.max(0, r.reward)) + 5).attr('y', rowH / 2 - bh / 2 - 1).attr('dy', '0.35em').text((r) => DM.signed(r.reward));
    row.append('text').attr('class', 'dm-strong').attr('x', (r) => x(Math.min(0, r.penalty, r.reward)) - 5).attr('y', rowH / 2 + bh / 2 + 1).attr('dy', '0.35em').attr('text-anchor', 'end').text((r) => (r.penalty < 0 ? DM.signed(r.penalty) : ''));
    g.append('line').attr('class', 'dm-axis').attr('x1', x(0)).attr('x2', x(0)).attr('y1', head).attr('y2', head + rs.length * rowH);
    row.append('rect').attr('class', 'dm-hit').attr('width', panelW).attr('height', rowH)
      .on('pointermove', (event, r) => tip.show(event, [`${r.aspect} · ${grp === 'Ryokan' ? 'ryokans' : 'hotels'}`, `Reward ${DM.signed(r.reward, f3)} stars (${DM.pval(r.pr)}; ${fi(r.npos)} positive mentions)`, `Penalty ${DM.signed(r.penalty, f3)} stars (${DM.pval(r.pp)}; ${fi(r.nneg)} negative mentions)`, `Scored with the ${mname(DM.param('measure'))} measure`]))
      .on('pointerleave', () => tip.hide());
  });
});

// importance-performance: one panel per type
dash.draw('ipa', (el) => {
  if (!DM.ready(el, ['rewards'])) return;
  const rows = rewardRows();
  el.replaceChildren();
  const W = DM.width(el), two = W >= 640, gap = 26, panelW = two ? (W - gap) / 2 : W, head = 24, plotH = 280, foot = 38;
  const panelH = head + plotH + foot, H = two ? panelH : panelH * 2 + 12;
  const svg = DM.svg(el, W, H, 'Scatter plots of importance against performance of seven aspects, for ryokans and for hotels');
  const xe = d3.extent(rows, (r) => r.perf), ye = [0, d3.max(rows, (r) => r.imp) * 1.12];
  const tip = DM.makeTip(el);
  ['Ryokan', 'Hotel'].forEach((grp, i) => {
    const ox = two ? i * (panelW + gap) : 0, oy = two ? 0 : i * (panelH + 12);
    const g = svg.append('g').attr('transform', `translate(${ox},${oy})`);
    const rs = rows.filter((r) => r.group === grp);
    const left = textWidth(svg, '0.00') + 10, right = 10;
    const x = d3.scaleLinear().domain([xe[0] - 3, xe[1] + 3]).range([left, panelW - right]);
    const y = d3.scaleLinear().domain(ye).range([head + plotH, head]);
    g.append('text').attr('class', 'dm-bold').attr('x', 0).attr('y', 12).text(grp === 'Ryokan' ? 'Ryokans' : 'Hotels');
    const yt = y.ticks(5), xt = x.ticks(panelW < 380 ? 4 : 6);
    g.append('g').selectAll('line').data(yt).join('line').attr('class', 'dm-grid').attr('x1', left).attr('x2', panelW - right).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
    g.append('g').selectAll('text').data(yt).join('text').attr('x', left - 6).attr('y', (d) => y(d)).attr('dy', '0.35em').attr('text-anchor', 'end').text((d) => f1(d));
    g.append('g').selectAll('text').data(xt).join('text').attr('x', (d) => x(d)).attr('y', head + plotH + 15).attr('text-anchor', 'middle').text((d) => d + '%');
    g.append('text').attr('x', (left + panelW - right) / 2).attr('y', panelH - 4).attr('text-anchor', 'middle').text('Performance (positive share of mentions)');
    const mi = d3.mean(rs, (r) => r.imp), mp = d3.mean(rs, (r) => r.perf);
    g.append('line').attr('class', 'dm-ref').attr('x1', left).attr('x2', panelW - right).attr('y1', y(mi)).attr('y2', y(mi));
    g.append('line').attr('class', 'dm-ref').attr('x1', x(mp)).attr('x2', x(mp)).attr('y1', head).attr('y2', head + plotH);
    g.append('text').attr('x', left + 6).attr('y', head + 12).text('Concentrate here');
    g.append('text').attr('x', panelW - right - 6).attr('y', head + 12).attr('text-anchor', 'end').text('Keep it up');
    const pts = rs.map((r) => ({...r, px: x(r.perf), py: y(r.imp)}));
    g.append('g').selectAll('circle').data(pts).join('circle').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 6).style('fill', colorOf(grp)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
    DM.labels(g, pts.map((p) => ({x: p.px, y: p.py, label: SHORT[p.aspect], cls: 'dm-strong', r: 6})), [left, head + 16, panelW - right, head + plotH]);
    g.append('g').selectAll('circle').data(pts).join('circle').attr('class', 'dm-hit').attr('cx', (p) => p.px).attr('cy', (p) => p.py).attr('r', 14)
      .on('pointermove', (event, p) => tip.show(event, [`${p.aspect} · ${grp === 'Ryokan' ? 'ryokans' : 'hotels'}`, `Importance ${f2(p.imp)} stars (reward ${DM.signed(p.reward)}, penalty ${DM.signed(p.penalty)})`, `Performance ${f1(p.perf)}% of mentions positive`, p.imp >= mi && p.perf < mp ? 'Above-average importance, below-average performance' : '']))
      .on('pointerleave', () => tip.hide());
  });
});

// complaint profile
dash.draw('complaints', (el) => {
  if (!DM.ready(el, ['complaints'])) return;
  const rows = dash.data('complaints').data.map((r) => ({type: r.type, aspect: r.aspect, low: num(r.low_rated_share), high: num(r.high_rated_share), n: num(r.n_low_rated)}));
  const byHotel = new Map(rows.filter((r) => r.type === 'Hotel').map((r) => [r.aspect, r.low]));
  const aspects = Array.from(new Set(rows.map((r) => r.aspect))).sort((a, b) => d3.descending(byHotel.get(a), byHotel.get(b)));
  const types = TYPES.filter((t) => rows.some((r) => r.type === t));
  el.replaceChildren();
  const W = DM.width(el), barH = 14, gap = 2, groupPad = 16, top = 6, bottom = 30;
  const groupH = types.length * barH + (types.length - 1) * gap + groupPad;
  const H = top + aspects.length * groupH + bottom;
  const svg = DM.svg(el, W, H, 'Grouped bar chart: share of low-rated reviews with a negative mention of each aspect, ryokans and hotels');
  const left = d3.max(aspects, (a) => textWidth(svg, a, 'dm-strong')) + 12, right = textWidth(svg, '00.0%', 'dm-strong') + 10;
  const x = d3.scaleLinear().domain([0, d3.max(rows, (r) => r.low) || 1]).nice(4).range([left, W - right]);
  const ticks = x.ticks(W < 460 ? 3 : 5);
  svg.append('g').selectAll('line').data(ticks).join('line').attr('class', 'dm-grid').attr('x1', (d) => x(d)).attr('x2', (d) => x(d)).attr('y1', top).attr('y2', H - bottom);
  svg.append('g').selectAll('text').data(ticks).join('text').attr('x', (d) => x(d)).attr('y', H - bottom + 16).attr('text-anchor', 'middle').text((d) => d + '%');
  const tip = DM.makeTip(el);
  const grp = svg.append('g').selectAll('g').data(aspects).join('g').attr('transform', (a, i) => `translate(0,${top + i * groupH + groupPad / 2})`);
  grp.append('text').attr('class', 'dm-strong').attr('x', left - 10).attr('y', (types.length * barH + (types.length - 1) * gap) / 2).attr('dy', '0.35em').attr('text-anchor', 'end').text((a) => a);
  const bar = grp.selectAll('g').data((a) => types.map((t) => rows.find((r) => r.aspect === a && r.type === t)).filter(Boolean)).join('g').attr('transform', (r) => `translate(0,${types.indexOf(r.type) * (barH + gap)})`);
  bar.append('path').attr('d', (r) => DM.hbar(left, x(r.low), barH)).style('fill', (r) => colorOf(r.type));
  bar.append('text').attr('class', 'dm-strong').attr('x', (r) => x(r.low) + 6).attr('y', barH / 2).attr('dy', '0.35em').text((r) => f1(r.low) + '%');
  bar.append('rect').attr('class', 'dm-hit').attr('x', 0).attr('y', -gap / 2).attr('width', W).attr('height', barH + gap)
    .on('pointermove', (event, r) => tip.show(event, [`${r.aspect} · ${r.type}`, `Negative mention in ${f1(r.low)}% of ${fi(r.n)} reviews rated three stars or fewer`, `In reviews rated four or five stars: ${f1(r.high)}%`]))
    .on('pointerleave', () => tip.hide());
  svg.append('line').attr('class', 'dm-axis').attr('x1', left).attr('x2', left).attr('y1', top).attr('y2', H - bottom);
});

// narrative arc
dash.draw('arc', (el) => {
  if (!DM.ready(el, ['arc'])) return;
  const measure = DM.param('measure');
  const rows = dash.data('arc').data.filter((r) => r.measure === measure).map((r) => ({type: r.type, pos: num(r.pos), part: r.part, v: num(r.sentiment), n: num(r.n_reviews)}));
  const parts = Array.from(d3.group(rows, (r) => r.pos), ([pos, rs]) => ({pos, part: rs[0].part})).sort((a, b) => a.pos - b.pos);
  const series = TYPES.map((t) => ({type: t, pts: rows.filter((r) => r.type === t).sort((a, b) => a.pos - b.pos)})).filter((s) => s.pts.length);
  el.replaceChildren();
  const W = DM.width(el), H = 300, top = 14, bottom = 30;
  const svg = DM.svg(el, W, H, 'Line chart of mean sentence sentiment across five parts of a review, one line for each accommodation type');
  const ext = d3.extent(rows, (r) => r.v), pad = Math.max(0.02, (ext[1] - ext[0]) * 0.15);
  const yS = d3.scaleLinear().domain([ext[0] - pad, ext[1] + pad]).nice(5).range([H - bottom, top]);
  const yTicks = yS.ticks(5);
  const left = d3.max(yTicks, (t) => textWidth(svg, f2(t))) + 10;
  const right = d3.max(series, (s) => textWidth(svg, s.type + ' 0.00', 'dm-strong')) + 12;
  const x = d3.scalePoint().domain(parts.map((p) => p.pos)).range([left + 16, W - right - 4]);
  svg.append('g').selectAll('line').data(yTicks).join('line').attr('class', 'dm-grid').attr('x1', left).attr('x2', W - right + 4).attr('y1', (d) => yS(d)).attr('y2', (d) => yS(d));
  svg.append('g').selectAll('text').data(yTicks).join('text').attr('x', left - 8).attr('y', (d) => yS(d)).attr('dy', '0.35em').attr('text-anchor', 'end').text((d) => f2(d));
  svg.append('g').selectAll('text').data(parts).join('text').attr('x', (d) => x(d.pos)).attr('y', H - 8).attr('text-anchor', 'middle').text((d) => d.part);
  const line = d3.line().x((d) => x(d.pos)).y((d) => yS(d.v));
  const sg = svg.append('g').selectAll('g').data(series).join('g');
  sg.append('path').attr('d', (s) => line(s.pts)).attr('fill', 'none').style('stroke', (s) => colorOf(s.type)).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
  sg.selectAll('circle').data((s) => s.pts).join('circle').attr('cx', (d) => x(d.pos)).attr('cy', (d) => yS(d.v)).attr('r', 4.5).style('fill', (d) => colorOf(d.type)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2);
  const ends = series.map((s) => ({type: s.type, v: s.pts[s.pts.length - 1].v, y: yS(s.pts[s.pts.length - 1].v)})).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
  const over = ends.length ? ends[ends.length - 1].y - (H - bottom - 4) : 0;
  if (over > 0) ends.forEach((e) => { e.y -= over; });
  svg.append('g').selectAll('text').data(ends).join('text').attr('class', 'dm-strong').attr('x', W - right + 8).attr('y', (d) => d.y).attr('dy', '0.35em').text((d) => `${d.type} ${f2(d.v)}`);
  const tip = DM.makeTip(el);
  const cross = svg.append('line').attr('class', 'dm-ref').attr('y1', top).attr('y2', H - bottom).style('display', 'none');
  const step = parts.length > 1 ? x(parts[1].pos) - x(parts[0].pos) : W;
  svg.append('g').selectAll('rect').data(parts).join('rect').attr('class', 'dm-hit').attr('x', (d) => x(d.pos) - step / 2).attr('y', top).attr('width', step).attr('height', H - bottom - top)
    .on('pointermove', (event, d) => {
      cross.style('display', null).attr('x1', x(d.pos)).attr('x2', x(d.pos));
      const at = series.map((s) => s.pts.find((p) => p.pos === d.pos)).filter(Boolean).sort((a, b) => b.v - a.v);
      tip.show(event, [`${d.part} part of the review`].concat(at.map((p) => `${p.type}: ${f3(p.v)} (${fi(p.n)} reviews)`)));
    })
    .on('pointerleave', () => { cross.style('display', 'none'); tip.hide(); });
});
}
