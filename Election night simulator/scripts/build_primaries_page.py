"""Build the dashboard page "Primaries vs the markets" (docs/primaries-vs-markets.html).

Reads primary_check.py's outputs (data/processed/primary_check_*.csv) and writes
    docs/primaries_vs_markets_data.js   the numbers (const PVM = {...})
    docs/primaries-vs-markets.html      the page; tables and charts are drawn from the data file
Every number in the page text comes from the data. Rebuild after primary_check.py:

    py "Election night simulator/scripts/primary_check.py"
    py "Election night simulator/scripts/build_primaries_page.py"
    node tests/dash_smoke.js docs/primaries-vs-markets.html
"""
import datetime as dt
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
PROC = os.path.join(ROOT, "data", "processed")
DOCS = os.path.join(REPO, "docs")
CLOSE = 3.0                     # a "close" race: final margin under 3 points
OFFICE = {"Governor": "Gov", "Senate": "Sen"}
PARTY = {"REP": "R", "DEM": "D"}


def label(race):
    st, office, party = race.split("-")
    return f"{st} {PARTY.get(party, party)} {OFFICE.get(office, office)}"


def num(x, nd=3):
    return None if x is None or (isinstance(x, float) and x != x) else round(float(x), nd)


def main():
    p = pd.read_csv(os.path.join(PROC, "primary_check_2026.csv"))
    s = pd.read_csv(os.path.join(PROC, "primary_check_2026_skipped.csv"))
    g = pd.read_csv(os.path.join(PROC, "primary_check_2024_generals.csv"))
    ser = pd.read_csv(os.path.join(PROC, "primary_check_close_series.csv"))

    races = []
    for r in p.itertuples():
        races.append(dict(race=r.race, label=label(r.race), date=r.date, winner=r.winner, runner_up=r.runner_up,
                          margin=num(r.final_margin, 2), at_close=num(r.winner_at_close),
                          model=num(r.model_winner), low=num(r.winner_low), low_when=r.low_when_et or "",
                          under15=num(r.min_under_15, 0), under30=num(r.min_under_30, 0), venues=r.venues,
                          right_market=num(r.right_market), right_visible=num(r.right_visible),
                          right_trend=num(r.right_trend)))
    skipped = [dict(label=label(r.race), date=r.date, reason=r.reason) for r in s.itertuples()]

    # before the count
    q = p.dropna(subset=["winner_at_close"])
    buckets = []
    for lo, hi in [(0.5, 0.7), (0.7, 0.9), (0.9, 0.97), (0.97, 1.01)]:
        fav = np.maximum(q.winner_at_close, 1 - q.winner_at_close)       # the favorite's price
        won = q.winner_at_close > 0.5
        m = (fav >= lo) & (fav < hi)
        buckets.append(dict(range=f"{lo * 100:.0f}-{min(hi, 1) * 100:.0f}c", races=int(m.sum()),
                            fav_won=int((won & m).sum()), avg_price=num(fav[m].mean()) if m.any() else None))
    mm = p.dropna(subset=["winner_at_close", "model_winner"])
    model_cmp = dict(races=len(mm),
                     brier_market=num(((1 - mm.winner_at_close) ** 2).mean(), 4),
                     brier_model=num(((1 - mm.model_winner) ** 2).mean(), 4),
                     fav_market=int((mm.winner_at_close > 0.5).sum()),
                     fav_model=int((mm.model_winner > 0.5).sum()),
                     first=str(mm.date.min()) if len(mm) else "")

    # during the count, primaries vs 2024 generals
    def summary(df):
        d = df.dropna(subset=["winner_low"])
        close = d[d.final_margin.abs() < CLOSE]
        return dict(races=len(df), under50=int((d.winner_low < 0.5).sum()), under20=int((d.winner_low < 0.2).sum()),
                    under10=int((d.winner_low < 0.1).sum()),
                    right_market=num(df.right_market.mean()), right_visible=num(df.right_visible.mean()),
                    right_trend=num(df.right_trend.mean()),
                    close=len(close), close_under50=int((close.winner_low < 0.5).sum()),
                    close_under20=int((close.winner_low < 0.2).sum()),
                    close_right_market=num(close.right_market.mean()),
                    close_right_visible=num(close.right_visible.mean()),
                    close_right_trend=num(close.right_trend.mean()))
    lows = ([dict(label=label(r.race), set="2026 primary", low=num(r.winner_low), margin=num(r.final_margin, 2))
             for r in p.itertuples() if abs(r.final_margin) < CLOSE and r.winner_low == r.winner_low] +
            [dict(label=f"{r.race.replace('-', ' ')} 2024", set="2024 general", low=num(r.winner_low),
                  margin=num(r.final_margin, 2))
             for r in g.itertuples() if abs(r.final_margin) < CLOSE and r.winner_low == r.winner_low])
    lows.sort(key=lambda x: x["low"])

    charts = []
    for race, d in ser.groupby("race", sort=False):
        r = p[p.race == race].iloc[0]
        # stop at 99.5% counted: after that the market settles and its quotes go blank (Vermont's
        # winner dropped to a 50c mid at 100%)
        d = d.sort_values("t")
        d = d[d.pct < 99.5]
        charts.append(dict(race=race, label=label(race), winner=r.winner, runner_up=r.runner_up,
                           margin=num(r.final_margin, 2), low=num(r.winner_low),
                           pts=[[pd.Timestamp(t).tz_convert("America/New_York").strftime("%a %H:%M"),
                                 num(pc, 1), num(m, 2), num(w)] for t, pc, m, w in
                                zip(d.t, d.pct, d.margin, d.winner_price)]))
    charts.sort(key=lambda c: c["low"] if c["low"] is not None else 2)

    data = dict(generated_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                close_pts=CLOSE, races=races, skipped=skipped, buckets=buckets, model_cmp=model_cmp,
                primaries=summary(p), generals=summary(g), lows=lows, charts=charts,
                considered=len(p) + len(s),
                fav_won=int((q.winner_at_close > 0.5).sum()), with_close_price=len(q))
    with open(os.path.join(DOCS, "primaries_vs_markets_data.js"), "w", encoding="utf-8") as f:
        f.write("const PVM = " + json.dumps(data, separators=(",", ":")) + ";\n")
    with open(os.path.join(DOCS, "primaries-vs-markets.html"), "w", encoding="utf-8") as f:
        f.write(PAGE)
    print(f"{len(races)} primaries, {len(skipped)} left out, {len(charts)} close-race charts -> "
          f"docs/primaries-vs-markets.html")


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Primaries vs Markets</title>
<!-- Generated by "Election night simulator/scripts/build_primaries_page.py" from primary_check.py's output.
     Edit the builder, not this file. -->
<script src="primaries_vs_markets_data.js"></script>
<style>
:root {
  --bg: #0b0e14; --panel: #121722; --panel2: #171d2b; --line: #222a3b; --line2: #2c3549;
  --text: #e6ebf4; --muted: #8a96ad; --faint: #5b667d; --accent: #6d8bff;
  --s1: #9085e9; --s2: #199e70; --price: #9085e9; --mline: #c3cbe0; --bad: #f87171;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.5; -webkit-font-smoothing: antialiased; }
a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 20px; }
@media (max-width: 600px) { .wrap { padding: 0 16px; } }
.top { border-bottom: 1px solid var(--line); background: linear-gradient(180deg, #10151f, var(--bg)); }
.top .wrap { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding-top: 14px; padding-bottom: 14px; }
.brand h1 { font-size: 1.15rem; font-weight: 750; }
.top nav { display: flex; gap: 18px; font-size: 0.82rem; flex-wrap: wrap; }
.hero { padding: 26px 0 6px; }
.hero h2 { font-size: clamp(1.5rem, 3.4vw, 2.2rem); font-weight: 800; letter-spacing: -0.02em; }
.hero p { color: var(--muted); max-width: 860px; margin-top: 8px; font-size: 0.95rem; }
.asof { margin-top: 10px; font-size: 0.76rem; color: var(--faint); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 18px 0 6px; }
.tile { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; }
.tile .v { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; }
.tile .k { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
section { margin: 34px 0; }
h3 { font-size: 1.2rem; font-weight: 750; margin-bottom: 8px; }
h4 { font-size: 0.95rem; font-weight: 700; margin: 18px 0 6px; }
p, li { font-size: 0.92rem; }
.prose { max-width: 880px; } .prose p { margin: 8px 0; } .prose ul { padding-left: 20px; } .prose li { margin: 4px 0; }
.muted { color: var(--muted); } .small { font-size: 0.78rem; }
.tw { overflow-x: auto; margin: 10px 0 14px; border: 1px solid var(--line); border-radius: 10px; }
table { border-collapse: collapse; width: 100%; font-size: 0.8rem; }
th, td { text-align: left; padding: 6px 9px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th { color: var(--muted); font-weight: 650; font-size: 0.72rem; background: var(--panel); cursor: default; }
th.sort { cursor: pointer; } th.sort:hover { color: var(--text); }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
tbody tr:nth-child(even) td { background: #0f131c; }
.flag { color: var(--bad); font-weight: 650; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; }
.chart { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 12px 12px 8px; position: relative; }
.chart .t { font-size: 0.86rem; font-weight: 700; } .chart .st { font-size: 0.74rem; color: var(--muted); margin-bottom: 4px; }
.chart svg { width: 100%; height: auto; display: block; }
.tip { position: absolute; pointer-events: none; background: #0b0e14ee; border: 1px solid var(--line2); border-radius: 8px;
       padding: 6px 8px; font-size: 0.74rem; color: var(--text); display: none; white-space: nowrap; z-index: 2; }
.legend { display: flex; gap: 16px; font-size: 0.78rem; color: var(--muted); margin: 6px 0; flex-wrap: wrap; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.bars .row { display: grid; grid-template-columns: 150px 1fr 54px; align-items: center; gap: 10px; font-size: 0.8rem; padding: 3px 0; }
.bars .track { height: 12px; position: relative; border-left: 1px solid var(--line2); }
.bars .bar { height: 12px; border-radius: 0 4px 4px 0; position: absolute; left: 0; top: 0; }
.bars .half { position: absolute; top: -4px; bottom: -4px; border-left: 1px dashed var(--line2); }
@media (max-width: 600px) { .bars .row { grid-template-columns: 110px 1fr 46px; } }
footer { border-top: 1px solid var(--line); padding: 20px 0 40px; color: var(--faint); font-size: 0.78rem; }
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="brand"><h1>Primaries vs the markets</h1></div>
  <nav><a href="index.html">Dashboard</a><a href="predictions.html">Forecast</a><a href="map.html">Map</a><a href="election-night.html">Election night</a></nav>
</div></header>
<main class="wrap">
  <div class="hero">
    <h2>Did the prediction markets read the 2026 primaries right?</h2>
    <p id="lede"></p>
    <div class="asof" id="asof"></div>
  </div>
  <div class="tiles" id="tiles"></div>

  <section>
    <h3>1. Before the count: did the market's favorite win?</h3>
    <div class="prose" id="pre_text"></div>
    <div class="tw" id="buckets"></div>
    <h4>Upsets: winners priced under 70c when polls closed</h4>
    <div class="tw" id="upsets"></div>
    <h4>Our primary model vs the markets</h4>
    <div class="prose" id="model_text"></div>
    <div class="tw" id="model_table"></div>
  </section>

  <section>
    <h3>2. During the count: how cheap did the eventual winner get?</h3>
    <div class="prose" id="count_text"></div>
    <div class="tw" id="lowtable"></div>
    <h4>Every close race, through the night</h4>
    <p class="muted small" id="chart_note"></p>
    <div class="grid2" id="charts"></div>
  </section>

  <section>
    <h3>3. Primaries vs the 2024 general elections</h3>
    <div class="prose" id="cmp_text"></div>
    <div class="tw" id="cmp_table"></div>
    <h4>Lowest price of the eventual winner after half the vote was counted, close races</h4>
    <div class="legend"><span><i style="background:var(--s1)"></i>2026 primary</span><span><i style="background:var(--s2)"></i>2024 general</span><span class="muted">dashed line: 50c</span></div>
    <div class="bars" id="lows"></div>
  </section>

  <section>
    <h3>4. Every primary</h3>
    <p class="muted small">Click a column to sort. "Winner low" is the lowest mid price of the eventual winner between 50% and 99% counted (Kalshi where its spread was 10c or less, otherwise Polymarket). "Market right" is the share of NYT updates at 50-95% counted on which the market's favorite was the eventual winner.</p>
    <div class="tw" id="all"></div>
    <h4>Left out</h4>
    <div class="tw" id="skipped"></div>
  </section>

  <section class="prose">
    <h3>5. How this was measured</h3>
    <ul>
      <li><b>Races:</b> every 2026 Senate and Governor primary in our primary model's list, plus the March 3 primaries it doesn't cover. Kept if NYT published a count timeline, a market traded $1,000+, and the race was decided on primary night (no runoff, no ranked-choice tabulation, market settled on the count's leader).</li>
      <li><b>Prices:</b> Kalshi 1-minute candles (governor nominee markets, <code>KXGOV{ST}NOM{R|D}-26</code>) and Polymarket 1-minute prices (governor and Senate primary-winner markets). Contracts are matched to candidates by full name: Kalshi listed both Hannah and Chellie Pingree for Maine.</li>
      <li><b>Count:</b> NYT's results files, every update. Margins are the eventual winner minus the runner-up, in points of all votes. Market prices are read 2 minutes after each NYT update.</li>
      <li><b>Trend:</b> the visible margin plus the rest of the vote breaking like the last 15% of the count did. A rule picked after looking at Colorado, tested here on everything else.</li>
      <li><b>Model:</b> our primary model's odds as published before polls closed (the page's git history, which starts July 15).</li>
      <li><b>2024 generals:</b> the same measures on the 2024 President, Senate and Governor races priced 3-97% at poll close (<code>market_check.py</code>).</li>
      <li>Full write-up, traps and code: <a href="https://github.com/pjmerica/polling-agg-2026/blob/master/Election%20night%20simulator/MARKET_CHECK.md">MARKET_CHECK.md</a> in the repo.</li>
    </ul>
  </section>
</main>
<footer><div class="wrap">Not financial advice. Built from NYT results and Kalshi / Polymarket price histories.</div></footer>
<script>
(function () {
  const D = PVM;
  const $ = id => document.getElementById(id);
  const pct = x => x == null ? '-' : Math.round(x * 100) + '%';
  const c = x => x == null ? '-' : (x * 100 < 1 ? (x * 100).toFixed(1) : Math.round(x * 100)) + 'c';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const P = D.primaries, G = D.generals;

  $('asof').textContent = 'Built ' + D.generated_at + ' from ' + D.races.length + ' primaries decided on primary night (' + D.considered + ' considered).';
  const closeP = D.races.filter(r => Math.abs(r.margin) < D.close_pts);
  $('lede').innerHTML = 'The markets picked the winner of ' + D.fav_won + ' of ' + D.with_close_price + ' primaries when polls closed. ' +
    'During the count they mostly followed whoever was visibly ahead, which went badly in close races: the eventual winner traded under 50c ' +
    'after half the vote was counted in ' + P.close_under50 + ' of ' + P.close + ' close primaries, about the same rate as the 2024 general elections (' +
    G.close_under50 + ' of ' + G.close + '). Primaries aren\'t misread more; close races are.';

  $('tiles').innerHTML = [
    [D.fav_won + ' / ' + D.with_close_price, 'primaries won by the market favorite at poll close'],
    [P.under50 + ' / ' + P.races, 'eventual winners priced under 50c after half the vote was counted'],
    [P.close_under50 + ' / ' + P.close, 'close primaries (final margin under ' + D.close_pts + ' pts) with the winner under 50c'],
    [G.close_under50 + ' / ' + G.close, 'close 2024 general races with the winner under 50c'],
  ].map(t => '<div class="tile"><div class="v">' + t[0] + '</div><div class="k">' + t[1] + '</div></div>').join('');

  function table(el, cols, rows, sortable) {
    let state = { k: null, dir: 1 };
    function draw() {
      let rs = rows.slice();
      if (state.k != null) rs.sort((a, b) => { const x = a[state.k], y = b[state.k];
        if (x == null) return 1; if (y == null) return -1; return (x > y ? 1 : x < y ? -1 : 0) * state.dir; });
      $(el).innerHTML = '<table><thead><tr>' + cols.map((cl, i) => '<th class="' + (cl.n ? 'n ' : '') + (sortable ? 'sort' : '') +
        '" data-i="' + i + '">' + cl.h + '</th>').join('') + '</tr></thead><tbody>' +
        rs.map(r => '<tr>' + cols.map(cl => '<td class="' + (cl.n ? 'n' : '') + '">' + (cl.f ? cl.f(r) : esc(r[cl.k])) + '</td>').join('') + '</tr>').join('') +
        '</tbody></table>';
      if (sortable) document.querySelectorAll('#' + el + ' th').forEach(th => th.addEventListener('click', () => {
        const k = cols[+th.dataset.i].k; state = { k, dir: state.k === k ? -state.dir : 1 }; draw(); }));
    }
    draw();
  }

  // 1. before the count
  $('pre_text').innerHTML = '<p>The price of the favorite in the last minute before the first votes posted, against how often that favorite won. ' +
    'A well-calibrated market\'s 70-90c favorites win 70-90% of the time.</p>';
  table('buckets', [{h: 'Favorite\'s price at poll close', k: 'range'}, {h: 'Primaries', k: 'races', n: 1},
    {h: 'Favorite won', k: 'fav_won', n: 1}, {h: 'Avg price', k: 'avg_price', n: 1, f: r => c(r.avg_price)},
    {h: 'Win rate', k: 'races', n: 1, f: r => r.races ? pct(r.fav_won / r.races) : '-'}], D.buckets);
  table('upsets', [{h: 'Race', k: 'label'}, {h: 'Date', k: 'date'}, {h: 'Winner', k: 'winner'}, {h: 'Runner-up', k: 'runner_up'},
    {h: 'Winner at poll close', k: 'at_close', n: 1, f: r => c(r.at_close)}, {h: 'Our model', k: 'model', n: 1, f: r => r.model == null ? '-' : pct(r.model)},
    {h: 'Final margin', k: 'margin', n: 1, f: r => r.margin.toFixed(1)}],
    D.races.filter(r => r.at_close != null && r.at_close < 0.7).sort((a, b) => a.at_close - b.at_close));
  const M = D.model_cmp;
  $('model_text').innerHTML = '<p>On the ' + M.races + ' primaries since ' + M.first + ' where both are available, the market at poll close beat our primary model: ' +
    'Brier score ' + M.brier_market + ' vs ' + M.brier_model + ' (lower is better), and its favorite won ' + M.fav_market + ' times to the model\'s ' + M.fav_model +
    '. The model rests on polls, which are sparse and old in primaries.</p>';
  table('model_table', [{h: 'Race', k: 'label'}, {h: 'Winner', k: 'winner'}, {h: 'Market at close', k: 'at_close', n: 1, f: r => pct(r.at_close)},
    {h: 'Our model', k: 'model', n: 1, f: r => pct(r.model)}, {h: 'Final margin', k: 'margin', n: 1, f: r => r.margin.toFixed(1)}],
    D.races.filter(r => r.model != null && r.at_close != null && Math.abs(r.model - r.at_close) >= 0.1).sort((a, b) => a.model - b.model));

  // 2. during the count
  $('count_text').innerHTML = '<p>After half the vote was counted, the eventual winner traded under 50c in ' + P.under50 + ' of ' + P.races +
    ' primaries, under 20c in ' + P.under20 + '. Almost all were close races: the market\'s favorite was right on ' + pct(P.right_market) +
    ' of updates overall but ' + pct(P.close_right_market) + ' in close races, where the visible leader was right ' + pct(P.close_right_visible) + '.</p>';
  table('lowtable', [{h: 'Race', k: 'label'}, {h: 'Winner', k: 'winner'}, {h: 'Final margin', k: 'margin', n: 1, f: r => r.margin.toFixed(2)},
    {h: 'At poll close', k: 'at_close', n: 1, f: r => c(r.at_close)}, {h: 'Low after 50% counted', k: 'low', n: 1, f: r => '<span class="flag">' + c(r.low) + '</span>'},
    {h: 'When (ET)', k: 'low_when'}, {h: 'Minutes under 15c', k: 'under15', n: 1}, {h: 'Under 30c', k: 'under30', n: 1},
    {h: 'Market right', k: 'right_market', n: 1, f: r => pct(r.right_market)}, {h: 'Visible leader right', k: 'right_visible', n: 1, f: r => pct(r.right_visible)}],
    D.races.filter(r => r.low != null && r.low < 0.5).sort((a, b) => a.low - b.low));
  $('chart_note').textContent = 'Top: the visible margin, winner minus runner-up (points). Bottom: the eventual winner\'s price. Hover for the moment.';

  // small multiples, one per close race: margin on top, price below, shared time axis (by update)
  const W = 520, H1 = 120, H2 = 110, GAP = 22, L = 40, R = 10, T = 8;
  $('charts').innerHTML = D.charts.map((ch, i) => {
    const pts = ch.pts.filter(p => p[2] != null);
    if (!pts.length) return '';
    const n = pts.length, x = j => L + (W - L - R) * j / Math.max(1, n - 1);
    const ms = pts.map(p => p[2]); let mlo = Math.min(0, ...ms), mhi = Math.max(0, ...ms); const pad = (mhi - mlo) * 0.08 || 1; mlo -= pad; mhi += pad;
    const y1 = v => T + H1 * (1 - (v - mlo) / (mhi - mlo));
    const y2 = v => T + H1 + GAP + H2 * (1 - v);
    const line1 = pts.map((p, j) => (j ? 'L' : 'M') + x(j).toFixed(1) + ' ' + y1(p[2]).toFixed(1)).join('');
    let line2 = '', pen = false;
    pts.forEach((p, j) => { if (p[3] == null) { pen = false; return; } line2 += (pen ? 'L' : 'M') + x(j).toFixed(1) + ' ' + y2(p[3]).toFixed(1); pen = true; });
    const ticks = [0, Math.floor(n / 2), n - 1].map(j => '<text x="' + x(j) + '" y="' + (T + H1 + GAP + H2 + 14) + '" fill="#8a96ad" font-size="10" text-anchor="' +
      (j === 0 ? 'start' : j === n - 1 ? 'end' : 'middle') + '">' + esc(pts[j][0]) + ' · ' + pts[j][1] + '%</text>').join('');
    const svg = '<svg viewBox="0 0 ' + W + ' ' + (T + H1 + GAP + H2 + 20) + '" data-i="' + i + '">' +
      '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y1(0) + '" y2="' + y1(0) + '" stroke="#2c3549"/>' +
      '<text x="' + (L - 6) + '" y="' + (y1(0) + 3) + '" fill="#8a96ad" font-size="10" text-anchor="end">0</text>' +
      // range labels only where they clear the zero label (RI and MI had them on top of each other)
      (y1(0) - y1(mhi) > 16 ? '<text x="' + (L - 6) + '" y="' + (y1(mhi) + 10) + '" fill="#8a96ad" font-size="10" text-anchor="end">+' + mhi.toFixed(0) + '</text>' : '') +
      (y1(mlo) - y1(0) > 16 ? '<text x="' + (L - 6) + '" y="' + (y1(mlo) - 2) + '" fill="#8a96ad" font-size="10" text-anchor="end">' + mlo.toFixed(0) + '</text>' : '') +
      [0, 0.5, 1].map(v => '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y2(v) + '" y2="' + y2(v) + '" stroke="' + (v === 0.5 ? '#2c3549' : '#1b2232') + '"' + (v === 0.5 ? ' stroke-dasharray="3 3"' : '') + '/>' +
        '<text x="' + (L - 6) + '" y="' + (y2(v) + 3) + '" fill="#8a96ad" font-size="10" text-anchor="end">' + Math.round(v * 100) + 'c</text>').join('') +
      '<path d="' + line1 + '" fill="none" stroke="var(--mline)" stroke-width="2"/>' +
      '<path d="' + line2 + '" fill="none" stroke="var(--price)" stroke-width="2"/>' + ticks +
      '<line class="xh" x1="0" x2="0" y1="' + T + '" y2="' + (T + H1 + GAP + H2) + '" stroke="#5b667d" visibility="hidden"/>' +
      '<rect x="' + L + '" y="0" width="' + (W - L - R) + '" height="' + (T + H1 + GAP + H2) + '" fill="transparent" class="hit"/></svg>';
    return '<div class="chart"><div class="t">' + esc(ch.label) + ': ' + esc(ch.winner) + ' over ' + esc(ch.runner_up) + ' by ' + ch.margin.toFixed(2) +
      '</div><div class="st">Winner\'s low after half counted: ' + c(ch.low) + '</div>' + svg + '<div class="tip"></div></div>';
  }).join('');
  document.querySelectorAll('#charts svg').forEach(svg => {
    const ch = D.charts[+svg.dataset.i], pts = ch.pts.filter(p => p[2] != null), n = pts.length;
    const hit = svg.querySelector('.hit'), xh = svg.querySelector('.xh'), tip = svg.parentNode.querySelector('.tip');
    hit.addEventListener('mousemove', ev => {
      const b = svg.getBoundingClientRect(), sx = (ev.clientX - b.left) * W / b.width;
      const j = Math.max(0, Math.min(n - 1, Math.round((sx - L) / (W - L - R) * (n - 1)))), p = pts[j];
      const xx = L + (W - L - R) * j / Math.max(1, n - 1);
      xh.setAttribute('x1', xx); xh.setAttribute('x2', xx); xh.setAttribute('visibility', 'visible');
      tip.innerHTML = esc(p[0]) + ' ET · ' + p[1] + '% counted<br>' + esc(ch.winner) + ' ' + (p[2] >= 0 ? '+' : '') + p[2].toFixed(2) + ' visible<br>' +
        esc(ch.winner) + ' price ' + c(p[3]);
      tip.style.display = 'block';
      const left = (ev.clientX - svg.parentNode.getBoundingClientRect().left);
      tip.style.left = Math.min(left + 12, svg.parentNode.clientWidth - 170) + 'px'; tip.style.top = '40px';
    });
    hit.addEventListener('mouseleave', () => { xh.setAttribute('visibility', 'hidden'); tip.style.display = 'none'; });
  });

  // 3. primaries vs generals
  $('cmp_text').innerHTML = '<p>The same measures on the 2024 President, Senate and Governor races. "Right" columns are the share of NYT updates at 50-95% counted on which each signal named the eventual winner, each race weighted equally.</p>' +
    '<p>The within-night trend does no better than the visible margin: batches come in lumpy, county by county, so the last stretch of the count says little about the next. ' +
    'What separates a misread from a correct read is which counties are still out, which is what the county-level projector (v1) is for.</p>';
  const rowsCmp = [['2026 primaries, all', P.races, P.under50, P.under20, P.right_market, P.right_visible, P.right_trend],
    ['2024 generals, all', G.races, G.under50, G.under20, G.right_market, G.right_visible, G.right_trend],
    ['2026 primaries, close', P.close, P.close_under50, P.close_under20, P.close_right_market, P.close_right_visible, P.close_right_trend],
    ['2024 generals, close', G.close, G.close_under50, G.close_under20, G.close_right_market, G.close_right_visible, G.close_right_trend]]
    .map(r => ({set: r[0], races: r[1], u50: r[2], u20: r[3], m: r[4], v: r[5], t: r[6]}));
  table('cmp_table', [{h: 'Set', k: 'set'}, {h: 'Races', k: 'races', n: 1}, {h: 'Winner under 50c', k: 'u50', n: 1}, {h: 'Under 20c', k: 'u20', n: 1},
    {h: 'Market right', k: 'm', n: 1, f: r => pct(r.m)}, {h: 'Visible leader right', k: 'v', n: 1, f: r => pct(r.v)}, {h: 'Trend right', k: 't', n: 1, f: r => pct(r.t)}], rowsCmp);
  $('lows').innerHTML = D.lows.map(r => '<div class="row" title="' + esc(r.label) + ': lowest ' + c(r.low) + ', final margin ' + r.margin.toFixed(2) + '"><span>' + esc(r.label) +
    '</span><div class="track"><div class="half" style="left:50%"></div><div class="bar" style="width:' + Math.max(0.6, r.low * 100) + '%;background:' +
    (r.set === '2026 primary' ? 'var(--s1)' : 'var(--s2)') + '"></div></div><span class="n" style="text-align:right">' + c(r.low) + '</span></div>').join('');

  // 4. every race
  table('all', [{h: 'Race', k: 'label'}, {h: 'Date', k: 'date'}, {h: 'Winner', k: 'winner'}, {h: 'Runner-up', k: 'runner_up'},
    {h: 'Margin', k: 'margin', n: 1, f: r => r.margin.toFixed(1)}, {h: 'At close', k: 'at_close', n: 1, f: r => c(r.at_close)},
    {h: 'Our model', k: 'model', n: 1, f: r => r.model == null ? '-' : pct(r.model)}, {h: 'Winner low', k: 'low', n: 1, f: r => c(r.low)},
    {h: 'Market right', k: 'right_market', n: 1, f: r => pct(r.right_market)}, {h: 'Visible right', k: 'right_visible', n: 1, f: r => pct(r.right_visible)},
    {h: 'Trend right', k: 'right_trend', n: 1, f: r => pct(r.right_trend)}, {h: 'Venues', k: 'venues'}],
    D.races.slice().sort((a, b) => (a.low == null) - (b.low == null) || a.low - b.low), true);
  table('skipped', [{h: 'Race', k: 'label'}, {h: 'Date', k: 'date'}, {h: 'Why', k: 'reason'}], D.skipped);
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
