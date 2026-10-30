// Exercise script for tests/dash_smoke.js on docs/map.html (2026-10-23):
//   node tests/dash_smoke.js docs/map.html tests/map_exercise.js
// Startup only draws the Senate map, so this renders every source x office, the House district map
// (whole country, zoomed to a state with a district selected, zoom in / out) and the squares view,
// and checks the district map really drew all 435 districts with their profiles.
const T = window.MAP_TEST;
if (!T) throw new Error('map.html did not expose MAP_TEST');
const html = id => document.getElementById(id).innerHTML;
const count = (s, re) => (s.match(re) || []).length;
// 2026-10-30: the Margin, Model-vs-markets and Margin-vs-markets views (Kalshi and Polymarket ladders), every office, every race card
let mcmpSenate = 0;
for (const [metric, cmp, msrc] of [['margin', 'kalshi', 'model'], ['margin', 'kalshi', 'polymarket'], ['cmp', 'kalshi'], ['cmp', 'polymarket'], ['margin', 'kalshi', 'kalshi'], ['mcmp', 'kalshi', 'kalshi'], ['mcmp', 'kalshi', 'polymarket']]) {
  for (const office of ['Senate', 'House', 'Governor']) {
    Object.assign(T.st, { metric, cmp, msrc: metric === 'mcmp' ? 'model' : msrc || 'model', mcmp: msrc || 'kalshi', src: 'model', office, hv: 'map', vb: null, sel: null, all: true, polledOnly: false });
    T.render();
    const n = count(html('rows'), /<tr/g);
    if (!n && ((metric === 'margin' && msrc === 'model') || (metric === 'cmp' && cmp === 'kalshi'))) throw new Error(`${metric}/${cmp} ${office}: empty race table`);
    if (metric === 'margin' && n && !/ \+\d+\.\d<\/span>/.test(html('rows'))) throw new Error(`margin ${office}: no margin pills`);
    // 2026-10-30: Margin vs markets (model margin minus Polymarket's ladder median); Senate always has ladders
    if (metric === 'mcmp' && office === 'Senate') mcmpSenate += n;
    if (metric === 'mcmp' && n && !/[DR] \+\d+\.\d<\/td>/.test(html('rows'))) throw new Error(`mcmp ${office}: no signed margins in the table`);
    for (const k of T.keys(office)) T.card(office, k);
  }
}
if (!mcmpSenate) throw new Error('Margin vs markets: no Senate race has a model margin and a Kalshi or Polymarket ladder');
Object.assign(T.st, { metric: 'win', sel: null });
for (const src of ['model', 'kalshi', 'polymarket']) {
  for (const office of ['Senate', 'House', 'Governor']) {
    Object.assign(T.st, { src, office, hv: 'map', vb: null, sel: null, all: true });
    T.render();
    if (!count(html('rows'), /<tr/g) && src === 'model') throw new Error(`${src} ${office}: empty race table`);
    for (const k of T.keys(office)) T.card(office, k);
  }
  T.st.office = 'House';
  T.render();
  const n = count(html('map'), /class="ds/g);
  if (n !== 435) throw new Error(`${src}: district map drew ${n} districts, not 435`);
  Object.assign(T.st, { vb: T.boxFor('TX'), sel: 'TX-28' });
  T.render();
  if (!/Redrawn for 2026/.test(html('detail'))) throw new Error(`${src}: TX-28's card has no redraw note`);
  if (!/College grads/.test(html('detail'))) throw new Error(`${src}: TX-28's card has no district profile`);
  if (!/class="dn"/.test(html('map'))) throw new Error(`${src}: no district numbers when zoomed in`);
  T.zoomBy(1.8); T.zoomBy(1 / 1.8); T.zoomBy(1 / 50);
  if (T.st.vb !== null) throw new Error('zooming all the way out should return to the whole country');
  Object.assign(T.st, { hv: 'tiles', sel: 'CA-1' });
  T.render();
  if (count(html('map'), /class="sq/g) !== 435) throw new Error(`${src}: squares view lost districts`);
}
// 2026-10-30: the explainer drawer opens for every race the model scores, factors carry their definitions,
// and the page prints the full glossary
let nWhy = 0;
for (const office of ['Senate', 'House', 'Governor']) for (const k of T.keys(office)) {
  T.explain(office, k);
  const h = html('d-body');
  if (!h) continue;
  nWhy++;
  if (/class="factor"/.test(h) && !/class="f-desc">[^<]{12,}/.test(h)) throw new Error(`${office} ${k}: a factor has no definition`);
  if (/>[a-z]+(_[a-z0-9]+)+</.test(h)) throw new Error(`${office} ${k}: a raw column name reached the explainer`);
}
if (nWhy < 400) throw new Error(`explainer opened for only ${nWhy} races`);
if (count(html('glossary'), /<dt>/g) < 20) throw new Error('glossary missing from the page');
