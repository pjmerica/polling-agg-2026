// Exercise script for tests/dash_smoke.js on docs/map.html (2026-10-23):
//   node tests/dash_smoke.js docs/map.html tests/map_exercise.js
// Startup only draws the Senate map, so this renders every source x office, the House district map
// (whole country, zoomed to a state with a district selected, zoom in / out) and the squares view,
// and checks the district map really drew all 435 districts with their profiles.
const T = window.MAP_TEST;
if (!T) throw new Error('map.html did not expose MAP_TEST');
const html = id => document.getElementById(id).innerHTML;
const count = (s, re) => (s.match(re) || []).length;
// 2026-10-30: the Margin and Model-vs-markets views, every office, every race card
for (const [metric, cmp] of [['margin', 'kalshi'], ['cmp', 'kalshi'], ['cmp', 'polymarket'], ['cmp', 'silver']]) {
  for (const office of ['Senate', 'House', 'Governor']) {
    Object.assign(T.st, { metric, cmp, src: 'model', office, hv: 'map', vb: null, sel: null, all: true, polledOnly: false });
    T.render();
    const n = count(html('rows'), /<tr/g);
    if (!n && (metric === 'margin' || cmp === 'kalshi')) throw new Error(`${metric}/${cmp} ${office}: empty race table`);
    if (metric === 'margin' && !/ \+\d+\.\d<\/span>/.test(html('rows'))) throw new Error(`margin ${office}: no margin pills`);
    for (const k of T.keys(office)) T.card(office, k);
  }
}
Object.assign(T.st, { metric: 'win', sel: null });
for (const src of ['model', 'kalshi', 'polymarket', 'silver']) {
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
