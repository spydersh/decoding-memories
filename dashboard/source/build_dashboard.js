// Builds the dashboard as one self-contained HTML file (no internet needed).
// Usage (after `npm install d3` in this folder): node dashboard/source/build_dashboard.js docs/index.html
// The data tables are read from scripts/phase5_location_crowding_anova.
const fs = require('fs');
const out = process.argv[2] || 'Decoding_Memories_Dashboard.html';
const path = require('path');
const d3src = fs.readFileSync(path.join(__dirname, 'node_modules', 'd3', 'dist', 'd3.min.js'), 'utf8');
const TABLES = path.join(__dirname, '..', '..', 'scripts', 'phase5_location_crowding_anova');
const esc = (s) => s.replace(/<\/script/gi, '<\\/script');
const must = (s, a, b) => { if (!s.includes(a)) throw new Error('missing: ' + a.slice(0, 60)); return s.replace(a, b); };

// ---------------------------------------------------------------- icons (simple line icons, drawn here)
const I = (d) => `<span class="dm-ico" aria-hidden="true"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${d}</svg></span>`;
const ICON = {
  ratings: I('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
  tests: I('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 4v16"/>'),
  aspects: I('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>'),
  perceptual: I('<path d="M3 21V3M3 21h18"/><circle cx="9" cy="14" r="1.6"/><circle cx="14" cy="8" r="1.6"/><circle cx="18" cy="13" r="1.6"/>'),
  vocabulary: I('<path d="M4 6h16M4 12h10M4 18h13"/>'),
  topics: I('<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>'),
  together: I('<circle cx="8" cy="12" r="5"/><circle cx="16" cy="12" r="5"/>'),
  rewards: I('<path d="M12 3v18M5 8h5M14 16h5M5 8l-2 2 2 2M19 16l2-2-2-2"/>'),
  ipa: I('<path d="M3 21V3M3 21h18M12 3v18M3 12h18" opacity=".55"/><circle cx="17" cy="7" r="1.8"/><circle cx="7" cy="16" r="1.8"/>'),
  complaints: I('<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18v.5"/>'),
  arc: I('<path d="M2 15c4-9 6-9 10-3s6 6 10-4"/>'),
  season: I('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
  trend: I('<path d="M3 17l6-6 4 4 8-9"/><path d="M15 6h6v6"/>'),
  map: I('<path d="M12 21s7-6.2 7-11.5A7 7 0 005 9.500C5 14.800 12 21 12 21z"/><circle cx="12" cy="9.500" r="2.500"/>'),
  distance: I('<circle cx="5" cy="18" r="2"/><circle cx="19" cy="6" r="2"/><path d="M7 16.500L17 7.500" stroke-dasharray="2 3"/>'),
  crowding: I('<circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.500"/><path d="M2 20c0-3.500 2.700-6 6-6s6 2.500 6 6M15 14.200c3.200-.6 7 1.400 7 5.800"/>'),
  notes: I('<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.500v.5"/>'),
  reviews: I('<path d="M4 5h16v11H9l-5 4V5z"/>'),
  star: I('<path d="M12 3l2.700 5.600 6.100.9-4.400 4.300 1 6.100L12 17l-5.400 2.900 1-6.100L3.200 9.500l6.100-.9L12 3z"/>'),
  low: I('<path d="M3 7l6 6 4-4 8 9"/><path d="M15 18h6v-6"/>'),
};

// ---------------------------------------------------------------- Kyoto skyline (original drawing)
function skyline() {
  const parts = [];
  parts.push('<path d="M0 150V112C80 96 150 104 230 92c90-14 150-40 250-34 80 5 130 32 220 30 110-2 170-44 280-40 90 3 150 30 220 44v48z" opacity=".35"/>');
  parts.push('<circle cx="890" cy="44" r="24" opacity=".28"/>');
  // five-story pagoda
  const cx = 1040, base = 150;
  for (let i = 0; i < 5; i++) {
    const w = 78 - i * 11, y = base - 24 - i * 21;
    parts.push(`<path d="M${cx - w / 2 - 9} ${y}q8-2 13-9h${w - 8}q5 7 13 9z"/>`);
    parts.push(`<rect x="${cx - w * 0.28}" y="${y}" width="${w * 0.56}" height="13"/>`);
  }
  parts.push(`<rect x="${cx - 26}" y="${base - 24 + 13}" width="52" height="12"/>`);
  parts.push(`<path d="M${cx - 1.500} ${base - 24 - 4 * 21 - 9}v-30h3v30z"/><path d="M${cx - 5} ${base - 24 - 4 * 21 - 16}h10M${cx - 4} ${base - 24 - 4 * 21 - 23}h8" stroke="currentColor" stroke-width="2"/>`);
  // torii gate
  const tx = 520, ty = 150;
  parts.push(`<path d="M${tx - 52} ${ty - 62}q52 9 104 0l3 8q-55 9-110 0z"/><rect x="${tx - 42}" y="${ty - 46}" width="84" height="6"/><path d="M${tx - 33} ${ty - 54}h8l-3 54h-8zM${tx + 25} ${ty - 54}h8l3 54h-8z"/>`);
  // machiya roofs
  let x = 610;
  [[70, 30], [54, 24], [84, 34], [60, 26], [76, 30]].forEach(([w, h], k) => {
    parts.push(`<path d="M${x - 6} ${150 - h * 0.55}q${w / 2 + 6}-${h * 0.75} ${w + 12} 0v4h-${w + 12}z"/><rect x="${x}" y="${150 - h * 0.55}" width="${w}" height="${h * 0.55}" opacity=".8"/>`);
    x += w + (k % 3 === 2 ? 22 : 8);
  });
  return `<svg class="dm-sky" viewBox="0 0 1200 150" preserveAspectRatio="xMidYMax slice" aria-hidden="true" fill="currentColor" stroke="currentColor" stroke-width="0">${parts.join('')}</svg>`;
}

// ---------------------------------------------------------------- page: restructure the original markup
let page = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8')
  .replace(/<script src="[^"]+"><\/script>\s*/g, '')
  .replace('<meta name="dash-one-writer">', '')
  .replace(/<style>[\s\S]*?<\/style>/, '');
page = must(page, 'Criticised together', 'Criticized together');
// type names capitalized as in the thesis (text only, never inside tags)
const capTypes = (t) => t.replace(/\bluxury hotels\b/g, 'Luxury Hotels').replace(/\b(ryokan|hotel|hybrid)(s?)\b/g, (m, w, p) => w[0].toUpperCase() + w.slice(1) + p);
page = page.replace(/>([^<>]+)</g, (m, t) => '>' + capTypes(t) + '<');

// header -> banner, number cards, tabs
const head = page.slice(page.indexOf('<header class="dm-head"'), page.indexOf('</nav>') + 6);
const legendRH = '<span><i class="dm-sw" data-type="Ryokan"></i>Ryokan</span><span><i class="dm-sw" data-type="Hotel"></i>Hotel</span>';
const kpi = (id, icon, label, body, foot) => `<div class="dm-kpi" id="kpi-${id}"><div class="dm-kpi-top">${icon}<span class="dm-kpi-label">${label}</span></div>${body}<p class="dm-kpi-foot">${foot}</p></div>`;
const pair = (k) => `<div class="dm-kpi-pair"><div><span class="dm-kpi-who"><i class="dm-sw" data-type="Ryokan"></i>Ryokan</span><b class="dm-kpi-num" data-draw="kpi" data-kpi="${k}-Ryokan" data-source="properties locations">—</b></div><div><span class="dm-kpi-who"><i class="dm-sw" data-type="Hotel"></i>Hotel</span><b class="dm-kpi-num" data-draw="kpi" data-kpi="${k}-Hotel" data-source="properties locations">—</b></div></div>`;
const newHead = `
  <header class="dm-banner" id="top">
    ${skyline()}
    <div class="dm-banner-in">
      <div>
        <p class="dm-eyebrow">Graduation thesis companion · Ritsumeikan Asia Pacific University</p>
        <h1 class="dm-title" id="title">Decoding Memories 1.0</h1>
        <p class="dm-sub">Traditional Ryokans and Modern Luxury Hotels in Kyoto, read through 6,042 guest reviews</p>
      </div>
      <button type="button" id="themeBtn" class="dm-theme" aria-label="Switch between light and dark appearance">Light / dark</button>
    </div>
  </header>

  <nav class="dm-tabs" role="tablist" aria-label="Views" id="tabs">
    <button class="dm-tab" type="button" role="tab" data-tab="overview" aria-selected="true">Overview</button>
    <button class="dm-tab" type="button" role="tab" data-tab="narrate" aria-selected="false">RQ1 · What guests narrate</button>
    <button class="dm-tab" type="button" role="tab" data-tab="satisfaction" aria-selected="false">RQ2 · Satisfaction</button>
    <button class="dm-tab" type="button" role="tab" data-tab="place" aria-selected="false">RQ3 · Season, time and place</button>
  </nav>

`;
page = must(page, head, newHead);
const kpis = `
  <section class="dm-kpis" aria-label="Headline numbers">
    ${kpi('reviews', ICON.reviews, 'Reviews analyzed',
      '<b class="dm-kpi-num dm-kpi-big" data-draw="kpi" data-kpi="reviews" data-source="properties">—</b><div class="dm-kpi-mix" data-draw="kpimix" data-source="properties"></div>',
      'Ten properties, April 2005 to February 2026')}
    ${kpi('rating', ICON.star, 'Mean star rating', pair('mean') + '<div class="dm-kpi-spark" data-draw="kpispark" data-source="trend"></div>',
      'Gap of <b data-draw="kpi" data-kpi="gap" data-source="properties">—</b> stars, not established at the property level (exact p = .171)')}
    ${kpi('low', ICON.low, 'Rated three stars or fewer', pair('low') + '<div class="dm-kpi-strip" data-draw="kpistrip" data-kpi="low" data-source="properties locations"></div>',
      'Each dot is one property: every Ryokan is below every Hotel')}
    ${kpi('crowd', ICON.crowding, 'Reviews describing crowding', pair('crowd') + '<div class="dm-kpi-strip" data-draw="kpistrip" data-kpi="crowd" data-source="properties locations"></div>',
      'Each dot is one property: the share follows the property more than the season')}
  </section>
`;
page = must(page, '<div class="dm-view" id="overview" data-view>', '<div class="dm-view" id="overview" data-view>' + kpis);

// overview: one section -> two cards (ratings chart, test table)
page = must(page, '<section class="dm-sec" id="anova">', '<section class="dm-sec" id="ratings">');
page = must(page, '<div class="dm-card" id="anova-table">',
  '</section>\n    <section class="dm-sec" id="tests">\n      <div class="dm-sec-head"><div><p class="dm-kicker">Analysis of variance</p><h2 class="dm-h2">The same gap under seven versions of the test</h2></div></div>\n      <div class="dm-card" id="anova-table">');
// icons in every section head
page = page.replace(/<section class="dm-sec" id="([a-z]+)">\s*<div class="dm-sec-head">\s*<div>/g, (all, id) => {
  if (!ICON[id]) throw new Error('no icon for ' + id);
  return `<section class="dm-sec" id="${id}">\n      <div class="dm-sec-head">\n        <div class="dm-sec-title">${ICON[id]}<div>`;
});
page = page.replace(/(<div class="dm-sec-title">[\s\S]*?<\/h2>)<\/div>/g, '$1</div></div>');
page = must(page, '<summary>How these figures were made</summary>', `<summary>${ICON.notes}<span>How these figures were made</span></summary>`);

const IDS = ['properties', 'anova', 'aspects', 'arc', 'complaints', 'locations', 'hotspots', 'location_tests', 'crowd',
  'perceptual', 'rewards', 'season', 'topics', 'trend', 'words', 'cooccurrence'];
const data = Object.fromEntries(IDS.map((k) => [k, fs.readFileSync(path.join(TABLES, k + '.csv'), 'utf8')]));
const scripts = ['core.js', 'rq1.js', 'rq2.js', 'rq3.js']
  .map((f) => fs.readFileSync(path.join(__dirname, f), 'utf8').replace('coloured by accommodation type', 'colored by accommodation type'))
  .map(capTypes)
  .map((s) => '<script>\n' + esc(s) + '\n</script>').join('\n');

const tokens = (m) => m === 'dark' ? `
  --color-fg:#ece7df; --color-fg-muted:#a9a196; --color-bg:#191817; --color-panel:#232120; --color-border-line:#37322e;
  --cds-chart-grid:#322e2a; --cds-chart-axis:#6b645b; --cds-chart-reference:#8a8278; --cds-text-secondary:#a9a196;
  --cds-surface-popover:#2c2925; --cds-shadow-popover:0 6px 24px rgba(0,0,0,.5); --cds-border:#3b3632;
  --color-ok:#6fbf73; --color-warn:#e0a03a; --dm-banner:#14263a; --dm-banner-ink:#f3efe8; --dm-sky:#2b4d6e;
  --dm-tabsel:#2f5d86; --dm-accent:#6aa9da; --dm-tint:rgba(106,169,218,.14); --dm-shadow:0 1px 2px rgba(0,0,0,.4);` : `
  --color-fg:#1f2328; --color-fg-muted:#667085; --color-bg:#f3f1ec; --color-panel:#ffffff; --color-border-line:#e4e0d8;
  --cds-chart-grid:#eeebe5; --cds-chart-axis:#a59d91; --cds-chart-reference:#8a8278; --cds-text-secondary:#667085;
  --cds-surface-popover:#ffffff; --cds-shadow-popover:0 6px 24px rgba(40,30,20,.16); --cds-border:#e4e0d8;
  --color-ok:#2e7d32; --color-warn:#9a5b00; --dm-banner:#1d3a57; --dm-banner-ink:#ffffff; --dm-sky:#3a6088;
  --dm-tabsel:#1d3a57; --dm-accent:#1f6fa8; --dm-tint:rgba(31,111,168,.09); --dm-shadow:0 1px 2px rgba(31,35,40,.05), 0 6px 18px rgba(31,35,40,.05);`;

const css = `
:root {
  --dm-font-sans: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  --dm-font-serif: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  --cds-font-size-caption:12px; --cds-font-size-body:14px; --cds-font-size-heading:16px; --cds-font-size-title:30px;
  --cds-font-weight-medium:600; --cds-radius:8px; --cds-pad-lg:16px;
  --cds-gap-sm:8px; --cds-gap-md:12px; --cds-gap-lg:20px; --cds-gap-xl:32px;
  color-scheme: light dark;${tokens('light')}
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {${tokens('dark')} } }
:root[data-theme="dark"] {${tokens('dark')} }
:root[data-theme="light"] {${tokens('light')} }
* { box-sizing: border-box; }
html, body { margin:0; background:var(--color-bg); color:var(--color-fg); }
body { font:14px/1.5 var(--dm-font-sans); -webkit-font-smoothing:antialiased; }
[hidden] { display:none !important; }
#dash-root { padding: 16px 16px 40px; }
.dm-page { max-width: 1280px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.dm-page > .dm-view { margin-bottom: -16px; }

/* banner */
.dm-banner { position: relative; overflow: hidden; border-radius: 16px; background: var(--dm-banner); color: var(--dm-banner-ink); min-height: 150px; display: flex; }
.dm-sky { position: absolute; inset: auto 0 0 0; width: 100%; height: 100%; color: var(--dm-sky); pointer-events: none; }
.dm-banner-in { position: relative; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; padding: 22px 26px 24px; width: 100%; }
.dm-eyebrow { margin: 0 0 6px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; opacity: .82; }
.dm-title { margin: 0; font-size: clamp(24px, 3.4vw, 34px); font-weight: 700; letter-spacing: -.01em; line-height: 1.15; }
.dm-sub { margin: 6px 0 0; font-size: 15px; opacity: .92; max-width: 60ch; text-wrap: balance; }
.dm-theme { flex: none; font: inherit; font-size: 12px; color: var(--dm-banner-ink); background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.28); border-radius: 999px; padding: 5px 12px; cursor: pointer; }
.dm-theme:hover { background: rgba(255,255,255,.2); }

/* tabs */
.dm-tabs { position: sticky; top: 0; z-index: 8; display: flex; flex-wrap: wrap; gap: 6px; padding: 8px; border-radius: 14px; background: var(--color-panel); border: 1px solid var(--color-border-line); box-shadow: var(--dm-shadow); }
.dm-tab { font: inherit; font-size: 14px; font-weight: 600; color: var(--color-fg-muted); background: transparent; border: 0; border-radius: 9px; padding: 8px 14px; cursor: pointer; }
.dm-tab:hover { color: var(--color-fg); background: var(--dm-tint); }
.dm-tab[aria-selected="true"] { color: #fff; background: var(--dm-tabsel); }
.dm-tab:focus-visible, .dm-controls select:focus-visible, .dm-theme:focus-visible { outline: 2px solid var(--dm-accent); outline-offset: 2px; }

/* number cards */
.dm-kpis { column-span: all; margin: 0 0 16px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.dm-kpi, .dm-sec, .dm-details { background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: 14px; box-shadow: var(--dm-shadow); }
.dm-kpi { padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.dm-kpi-top { display: flex; align-items: center; gap: 10px; }
.dm-kpi-label { font-size: 13px; font-weight: 600; color: var(--color-fg-muted); }
.dm-kpi-num { font-size: 26px; font-weight: 700; letter-spacing: -.01em; font-variant-numeric: tabular-nums; line-height: 1.1; display: block; }
.dm-kpi-big { font-size: 32px; }
.dm-kpi-pair { display: flex; gap: 22px; }
.dm-kpi-who { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-fg-muted); margin-bottom: 2px; }
.dm-kpi-foot { margin: auto 0 0; font-size: 12px; color: var(--color-fg-muted); line-height: 1.45; }
.dm-kpi-foot b { color: var(--color-fg); font-weight: 600; }
.dm-kpi-spark svg, .dm-kpi-mix svg, .dm-kpi-strip svg { display: block; width: 100%; }
.dm-kpi-mix text, .dm-kpi-spark text, .dm-kpi-strip text { font-size: 11px; fill: var(--color-fg-muted); font-family: var(--dm-font-sans); }
.dm-ico { flex: none; display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: var(--dm-tint); color: var(--dm-accent); }

/* views and cards */
.dm-view { columns: 2; column-gap: 16px; }
.dm-viewhead { column-span: all; margin: 0 0 14px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 20px; padding: 2px 4px; }
.dm-question { margin: 0; font-size: 17px; font-weight: 600; max-width: 70ch; text-wrap: balance; }
.dm-sec { padding: 16px 18px 16px; display: flex; flex-direction: column; gap: 12px; min-width: 0; break-inside: avoid; margin: 0 0 16px; }
#aspects, #perceptual, #vocabulary, #rewards, #ipa, #season { column-span: all; }
.dm-sec-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 8px 20px; }
.dm-sec-title { display: flex; align-items: flex-start; gap: 12px; min-width: 0; }
.dm-kicker { font-size: 11.500px; color: var(--color-fg-muted); margin: 0 0 1px; letter-spacing: .06em; text-transform: uppercase; }
.dm-h2 { font-size: 16px; font-weight: 600; margin: 0; line-height: 1.3; text-wrap: balance; }
.dm-card { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.dm-note { font-size: 12px; color: var(--color-fg-muted); margin: 0; max-width: 90ch; line-height: 1.5; }
.dm-note b, .dm-read b { font-weight: 600; font-variant-numeric: tabular-nums; }
.dm-read { font-size: 13px; line-height: 1.55; margin: 0; padding: 10px 12px; border-radius: 10px; background: var(--dm-tint); color: var(--color-fg); max-width: none; }
.dm-legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12px; color: var(--color-fg-muted); padding-top: 4px; }
.dm-legend span { display: inline-flex; align-items: center; gap: 6px; }
.dm-sw { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex: none; }
.dm-sw-sq { border-radius: 2px; background: var(--color-fg-muted); transform: rotate(45deg); width: 8px; height: 8px; }
.dm-chart { position: relative; width: 100%; min-width: 0; }
.dm-chart svg { display: block; width: 100%; overflow: visible; }
.dm-chart text { font-family: var(--dm-font-sans); font-size: 12px; fill: var(--cds-text-secondary); font-variant-numeric: tabular-nums; }
.dm-chart text.dm-strong { fill: var(--color-fg); }
.dm-chart text.dm-bold { fill: var(--color-fg); font-weight: 600; }
.dm-chart .dm-grid { stroke: var(--cds-chart-grid); stroke-width: 1; }
.dm-chart .dm-axis { stroke: var(--cds-chart-axis); stroke-width: 1; }
.dm-chart .dm-ref { stroke: var(--cds-chart-reference); stroke-width: 1; stroke-dasharray: 3 3; fill: none; }
.dm-chart .dm-band { fill: var(--color-fg-muted); opacity: .09; }
.dm-chart .dm-hit { fill: transparent; cursor: default; }
.dm-h-dots { min-height: 342px; } .dm-h-heat { min-height: 370px; } .dm-h-arc { min-height: 300px; } .dm-h-bars { min-height: 358px; }
.dm-h-md { min-height: 320px; } .dm-h-lg { min-height: 420px; } .dm-h-sm { min-height: 154px; } .dm-h-co { min-height: 268px; } .dm-h-cr { min-height: 240px; }
.dm-empty { font-size: 12px; color: var(--color-fg-muted); padding: 24px 0; }
.dm-tip { position: absolute; z-index: 5; pointer-events: none; background: var(--cds-surface-popover); border: 1px solid var(--cds-border); box-shadow: var(--cds-shadow-popover); border-radius: 8px; padding: 8px 10px; font-size: 12px; line-height: 1.45; color: var(--color-fg); max-width: 250px; font-variant-numeric: tabular-nums; }
.dm-tip-title { font-weight: 600; } .dm-tip-sub { color: var(--cds-text-secondary); }
.dm-tablewrap { overflow-x: auto; }
.dm-table { border-collapse: collapse; width: 100%; font-size: 12px; font-variant-numeric: tabular-nums; }
.dm-table th { text-align: left; font-weight: 600; color: var(--color-fg-muted); padding: 6px 10px 6px 0; border-bottom: 1px solid var(--color-border-line); }
.dm-table td { padding: 8px 10px 8px 0; border-bottom: 1px solid var(--color-border-line); vertical-align: top; }
.dm-table td.dm-num, .dm-table th.dm-num { text-align: right; white-space: nowrap; }
.dm-pill { display: inline-block; padding: 2px 8px; border-radius: 9px; border: 1px solid var(--color-border-line); line-height: 1.3; }
.dm-pill.dm-yes { border-color: var(--color-ok); } .dm-pill.dm-no { border-color: var(--color-warn); }
.dm-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; font-size: 12px; color: var(--color-fg-muted); }
.dm-controls label { display: inline-flex; align-items: center; gap: 6px; }
select { font: inherit; font-size: 12.500px; color: var(--color-fg); background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: 8px; padding: 5px 8px; max-width: 100%; }
.dm-details { padding: 14px 18px; font-size: 12.500px; color: var(--color-fg-muted); line-height: 1.55; }
.dm-details summary { cursor: pointer; color: var(--color-fg); font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 12px; list-style: none; }
.dm-details summary::-webkit-details-marker { display: none; }
.dm-details summary::after { content: "+"; margin-left: auto; font-size: 18px; color: var(--color-fg-muted); }
.dm-details[open] summary::after { content: "–"; }
.dm-details p { margin: 10px 0 0; max-width: 100ch; }
.off-foot { font-size: 12px; color: var(--color-fg-muted); line-height: 1.6; padding: 4px 4px 0; margin: 0; }
@media (max-width: 1040px) { .dm-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 860px) { .dm-view { columns: 1; } }
@media (max-width: 520px) { .dm-kpis { grid-template-columns: minmax(0, 1fr); } .dm-banner-in { padding: 18px 16px 20px; flex-direction: column; } .dm-tab { padding: 7px 10px; font-size: 13px; } #dash-root { padding: 10px 10px 32px; } }
@media print { .dm-theme { display: none; } .dm-tabs { position: static; } }
`;

const kpiJs = `
(function () {
  const meanBy = (rows, key, f) => { const o = {}; d3.rollup(rows, (v) => d3.mean(v, f), (r) => r[key]).forEach((v, k) => { o[k] = v; }); return o; };
  dash.draw('kpi', (el) => {
    const k = el.getAttribute('data-kpi'), P = dash.data('properties'), L = dash.data('locations');
    if (P.status !== 'ok' || L.status !== 'ok') { el.textContent = '—'; return; }
    const mean = meanBy(P.data, 'type', (r) => +r.mean), low = meanBy(P.data, 'type', (r) => +r.low_share), crowd = meanBy(L.data, 'type', (r) => +r.crowd_exposed);
    const [what, type] = k.split('-');
    el.textContent = what === 'reviews' ? DM.fi(d3.sum(P.data, (r) => +r.n))
      : what === 'gap' ? DM.signed(mean.Ryokan - mean.Hotel)
      : what === 'mean' ? DM.f2(mean[type]) : what === 'low' ? DM.f1(low[type]) + '%' : DM.f1(crowd[type]) + '%';
  });
  dash.draw('kpimix', (el) => {
    const P = dash.data('properties'); if (P.status !== 'ok') return;
    const tot = DM.TYPES.map((t) => ({t, n: d3.sum(P.data.filter((r) => r.type === t), (r) => +r.n), k: P.data.filter((r) => r.type === t).length}));
    const all = d3.sum(tot, (d) => d.n); el.replaceChildren();
    const W = Math.max(180, el.clientWidth), H = 34, svg = d3.select(el).append('svg').attr('viewBox', '0 0 ' + W + ' ' + H).attr('height', H).attr('role', 'img')
      .attr('aria-label', tot.map((d) => d.t + ' ' + DM.fi(d.n) + ' reviews').join(', '));
    let x = 0; tot.forEach((d) => { const w = (W - 4) * d.n / all; d.x = x; d.w = w; x += w + 2; });
    svg.selectAll('rect').data(tot).join('rect').attr('x', (d) => d.x).attr('y', 0).attr('width', (d) => Math.max(1, d.w)).attr('height', 8).attr('rx', 3).style('fill', (d) => DM.colorOf(d.t));
    let lx = 0; tot.forEach((d) => { const s = d.t + ' ' + DM.fi(d.n); const t = svg.append('text').attr('x', lx).attr('y', 26).text(s); lx += t.node().getComputedTextLength() + 12; });
    if (lx - 12 > W) svg.selectAll('text').remove(), svg.attr('height', 10).attr('viewBox', '0 0 ' + W + ' 10');
  });
  dash.draw('kpistrip', (el) => {
    const k = el.getAttribute('data-kpi'), g = dash.data(k === 'low' ? 'properties' : 'locations'); if (g.status !== 'ok') return;
    const rows = g.data.filter((r) => r.type !== 'Hybrid').map((r) => ({p: r.property, t: r.type, v: +(k === 'low' ? r.low_share : r.crowd_exposed)}));
    el.replaceChildren();
    const W = Math.max(180, el.clientWidth), H = 44, max = Math.ceil(d3.max(rows, (r) => r.v) / 4) * 4, x = d3.scaleLinear().domain([0, max]).range([6, W - 6]);
    const svg = d3.select(el).append('svg').attr('viewBox', '0 0 ' + W + ' ' + H).attr('height', H).attr('role', 'img').attr('aria-label', rows.map((r) => r.p + ' ' + DM.f1(r.v) + '%').join(', '));
    svg.append('line').attr('x1', x(0)).attr('x2', x(max)).attr('y1', 20).attr('y2', 20).style('stroke', 'var(--cds-chart-axis)');
    [0, max / 2, max].forEach((t) => { svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', 17).attr('y2', 23).style('stroke', 'var(--cds-chart-axis)');
      svg.append('text').attr('x', x(t)).attr('y', H - 2).attr('text-anchor', t === 0 ? 'start' : t === max ? 'end' : 'middle').text(DM.f0(t) + '%'); });
    svg.selectAll('circle').data(rows).join('circle').attr('cx', (r) => x(r.v)).attr('cy', (r) => (r.t === 'Ryokan' ? 13 : 27) - 7 + 7).attr('cy', 20).attr('r', 5.5)
      .style('fill', (r) => DM.colorOf(r.t)).style('stroke', 'var(--color-panel)').attr('stroke-width', 2).append('title').text((r) => r.p + ': ' + DM.f1(r.v) + '%');
  });
  dash.draw('kpispark', (el) => {
    const T = dash.data('trend'); if (T.status !== 'ok') return;
    const rows = T.data.filter((r) => r.level === 'type' && (r.type === 'Ryokan' || r.type === 'Hotel') && +r.n >= 10 && +r.year >= 2010 && ![2020, 2021, 2022].includes(+r.year)).map((r) => ({t: r.type, y: +r.year, v: +r.rating}));
    el.replaceChildren(); if (!rows.length) return;
    const W = Math.max(180, el.clientWidth), H = 44, x = d3.scaleLinear().domain(d3.extent(rows, (r) => r.y)).range([2, W - 2]), y = d3.scaleLinear().domain(d3.extent(rows, (r) => r.v)).range([H - 14, 4]);
    const svg = d3.select(el).append('svg').attr('viewBox', '0 0 ' + W + ' ' + H).attr('height', H).attr('role', 'img').attr('aria-label', 'Mean rating by year, Ryokans and Hotels, 2010 to 2026, without 2020 to 2022');
    const line = d3.line().x((r) => x(r.y)).y((r) => y(r.v));
    ['Hotel', 'Ryokan'].forEach((t) => { const s = rows.filter((r) => r.t === t).sort((a, b) => a.y - b.y);
      const pre = s.filter((r) => r.y < 2020), post = s.filter((r) => r.y > 2022);
      [pre, post].forEach((seg) => svg.append('path').attr('d', line(seg)).attr('fill', 'none').style('stroke', DM.colorOf(t)).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round'));
      const last = s[s.length - 1]; svg.append('circle').attr('cx', x(last.y)).attr('cy', y(last.v)).attr('r', 3).style('fill', DM.colorOf(t)); });
    const d = x.domain(); svg.append('text').attr('x', 2).attr('y', H - 1).text(d[0]); svg.append('text').attr('x', W - 2).attr('y', H - 1).attr('text-anchor', 'end').text(d[1]);
    svg.append('text').attr('x', W / 2).attr('y', H - 1).attr('text-anchor', 'middle').text('yearly mean');
  });
})();
`;

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decoding Memories Dashboard</title>
<meta name="description" content="Interactive dashboard accompanying the graduation thesis Decoding Memories 1.0 (Sai Htet Eain Lin, Ritsumeikan Asia Pacific University, 2027). Works without an internet connection.">
<style>${css}</style>
</head>
<body>
<div id="dash-root">
${page.replace(/<\/div>\s*$/, '')}
  <p class="off-foot">Sai Htet Eain Lin, <i>Decoding Memories 1.0: A Comparative Big Data Study of Traditional Ryokans and Modern Luxury Hotels in Kyoto by Analyzing TripAdvisor Reviews</i>, graduation thesis, College of Sustainability and Tourism, Ritsumeikan Asia Pacific University (supervisor: Professor DAHLAN Nariman). Data: 6,042 English-language TripAdvisor reviews of ten Kyoto properties, April 2005 to February 2026. Point at any mark to read its values. The figures, tests, and definitions are those of the thesis, and the thesis is the reference where the two differ. This file needs no internet connection and stores nothing.</p>
</div>
</div>
<script>${esc(d3src)}</script>
<script>
(function () {
  const RAW = ${JSON.stringify(data)};
  const parse = (t) => { const [h, ...r] = d3.csvParseRows(t); return r.map((x) => Object.fromEntries(h.map((k, i) => [k, x[i] === '' ? null : x[i]]))); };
  const D = Object.fromEntries(Object.entries(RAW).map(([k, v]) => [k, parse(v)]));
  const P = {}, draws = {}, onD = [];
  const PAL = { light: ['#1f6fa8', '#d9452b', '#c9a227'], dark: ['#4a93cc', '#c0412d', '#ad8d26'] };
  const mode = () => { const t = document.documentElement.getAttribute('data-theme');
    return t || (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); };
  const runOne = (n) => { const f = draws[n]; if (!f) return;
    document.querySelectorAll('[data-draw="' + n + '"]').forEach((el) => { if (el.closest('[hidden]')) return;
      try { f(el); } catch (e) { console.error('draw ' + n + ': ' + e.message); } }); };
  const run = () => { dash.colors = PAL[mode()].concat(['#999999']);
    document.querySelectorAll('.dm-sw[data-type]').forEach((el) => { el.style.background = DM.colorOf(el.getAttribute('data-type')); });
    onD.forEach((f) => f()); Object.keys(draws).forEach(runOne); };
  window.dash = {
    colors: PAL[mode()].concat(['#999999']),
    data: (id) => ({ status: D[id] ? 'ok' : 'missing', data: D[id] || [] }),
    draw: (n, f) => { if (f) draws[n] = f; else runOne(n); },
    onData: (f) => { onD.push(f); f(); },
    params: () => P,
    setParams: (o) => { Object.assign(P, o); run(); },
    setLink: (id) => { try { history.replaceState(null, '', '#' + id); } catch (e) {} },
    calc() {},
  };
  window.__dmRun = run; window.__dmMode = mode;
})();
</script>
${scripts}
<script>${kpiJs}</script>
<script>
(function () {
  let t; const rerun = () => { clearTimeout(t); t = setTimeout(window.__dmRun, 120); };
  window.addEventListener('resize', rerun);
  if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener('change', rerun);
  document.getElementById('themeBtn').addEventListener('click', () => {
    document.documentElement.setAttribute('data-theme', window.__dmMode() === 'dark' ? 'light' : 'dark'); window.__dmRun(); });
  window.__dmRun();
})();
</script>
</body>
</html>`;
fs.writeFileSync(out, html.replaceAll('--dm-font-', '--dm-font-'));
console.log('wrote', out, (html.length / 1024).toFixed(0) + ' KB');
