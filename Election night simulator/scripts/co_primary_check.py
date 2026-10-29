"""The Colorado Republican governor primary, June 30, 2026: how badly did the markets misread the count?

Downloads NYT's results file (count timeline) and Kalshi's / Polymarket's minute prices for Marx and
Kirkmeyer, lines them up, and prints:
  - the count, the visible margin and Marx's price through the night;
  - a within-night trend: the margin of the votes added over the last 15% of the count, and the
    final margin you get if the rest of the vote breaks like that;
  - how cheap the eventual winner got, for how long, and how wide Kalshi's book was then.
NYT published no live model estimate for this primary (nyt_model_estimates is empty), and v0 has no
primary history, so the trend is the only projection here. It is a simple rule picked after the fact:
see MARKET_CHECK.md before reading it as a strategy.

    py "Election night simulator/scripts/co_primary_check.py"

Raw files: data/raw/primaries/ (not committed). Output: data/processed/co_gov_rep_2026_trend.csv
"""
import json
import os
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, ".."))
from utils.http_headers import DEFAULT_HEADERS  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "primaries")
PROC = os.path.join(ROOT, "data", "processed")
NYT = "https://static01.nyt.com/elections-assets/pages/data/2026-06-30/results-colorado-governor-primary.json"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2/historical/markets/{t}/candlesticks"
CANDS = {"Marx": ("marx-v", "KXGOVCONOMR-26-VMAR"), "Kirkmeyer": ("kirkmeyer-b", "KXGOVCONOMR-26-BKIR")}
POLY_EVENT = "colorado-governor-republican-primary-winner"
START, END = pd.Timestamp("2026-06-30T22:00Z"), pd.Timestamp("2026-07-03T00:00Z")
TREND_WINDOW = 15      # points of the count


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=DEFAULT_HEADERS), timeout=60) as r:
        b = r.read()
    return b if raw else json.loads(b)


def download():
    os.makedirs(RAW, exist_ok=True)
    nyt = os.path.join(RAW, "nyt-colorado-governor-primary.json")
    if not os.path.exists(nyt):
        open(nyt, "wb").write(get(NYT, raw=True))
    s, e = int(START.timestamp()), int(END.timestamp())
    ev = None
    for name, (_, ticker) in CANDS.items():
        kp = os.path.join(RAW, f"co_gov_rep_kalshi_{name}.csv")
        if not os.path.exists(kp):
            rows, a = [], s
            while a < e:
                b = min(a + 12 * 3600, e)
                c = get(f"{KALSHI.format(t=ticker)}?start_ts={a}&end_ts={b}&period_interval=1")
                rows += [dict(ts=k["end_period_ts"], bid=k["yes_bid"]["close"], ask=k["yes_ask"]["close"])
                         for k in c.get("candlesticks", [])]
                a = b
                time.sleep(0.2)
            pd.DataFrame(rows).to_csv(kp, index=False)
        pp = os.path.join(RAW, f"co_gov_rep_poly_{name}.csv")
        if not os.path.exists(pp):
            ev = ev or get(f"https://gamma-api.polymarket.com/events?slug={POLY_EVENT}")[0]
            m = next(m for m in ev["markets"] if name in m["question"])
            tok = json.loads(m["clobTokenIds"])[0]
            rows, a = [], s
            while a < e:
                b = min(a + 12 * 3600, e)
                rows += get(f"https://clob.polymarket.com/prices-history?market={tok}&startTs={a}&endTs={b}"
                            f"&fidelity=1")["history"]
                a = b
            pd.DataFrame(rows).to_csv(pp, index=False)


def timeline():
    d = json.load(open(os.path.join(RAW, "nyt-colorado-governor-primary.json"), encoding="utf-8"))
    rows = []
    for x in d["timeseries"]["CO-R-G-2026-06-30"]:            # newest first; ends with zeroed points
        v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in x["candidates"]}
        if x.get("total_votes"):
            rows.append(dict(t=x.get("greatest_updated_at") or x.get("provider_updated_at"),
                             votes=x["total_votes"], marx=v.get("marx-v", 0), kirk=v.get("kirkmeyer-b", 0)))
    n = pd.DataFrame(rows)
    n["t"] = pd.to_datetime(n.t, utc=True, format="ISO8601")
    n = n.sort_values("t").drop_duplicates("t").reset_index(drop=True)
    n["pct"] = 100 * n.votes / n.votes.max()
    n["margin"] = 100 * (n.marx - n.kirk) / n.votes
    return n


def prices():
    idx = pd.date_range(START, END, freq="1min")
    out = pd.DataFrame(index=idx)
    for name in CANDS:
        k = pd.read_csv(os.path.join(RAW, f"co_gov_rep_kalshi_{name}.csv"))
        k.index = pd.to_datetime(k.ts, unit="s", utc=True)
        k = k[~k.index.duplicated()]
        out[f"k_{name}"] = ((k.bid + k.ask) / 2).reindex(idx, method="ffill")
        out[f"k_{name}_spread"] = (k.ask - k.bid).reindex(idx, method="ffill")
        p = pd.read_csv(os.path.join(RAW, f"co_gov_rep_poly_{name}.csv"))
        p.index = pd.DatetimeIndex(pd.to_datetime(p.t, unit="s", utc=True)).floor("min")
        out[f"p_{name}"] = p[~p.index.duplicated(keep="last")].p.reindex(idx, method="ffill")
    return out


def main():
    download()
    n, px = timeline(), prices()
    final = n.margin.iloc[-1]
    rows = []
    for _, r in n.iterrows():
        base = n[n.pct <= r.pct - TREND_WINDOW]
        if base.empty or r.pct >= 99:
            continue
        b = base.iloc[-1]
        trend = 100 * ((r.marx - b.marx) - (r.kirk - b.kirk)) / (r.votes - b.votes)
        t = r.t.floor("min") + pd.Timedelta(minutes=2)
        rows.append(dict(t_mt=r.t.tz_convert("America/Denver").strftime("%a %H:%M"), counted=round(r.pct, 1),
                         visible=round(r.margin, 2), last15_breaking=round(trend, 1),
                         trend_final=round(r.margin + (1 - r.pct / 100) * (trend - r.margin), 2),
                         kalshi_marx=px.k_Marx.get(t), kalshi_spread=px.k_Marx_spread.get(t),
                         poly_marx=px.p_Marx.get(t)))
    o = pd.DataFrame(rows).drop_duplicates("counted")
    os.makedirs(PROC, exist_ok=True)
    o.to_csv(os.path.join(PROC, "co_gov_rep_2026_trend.csv"), index=False)
    print(f"Final: Marx {final:+.2f} over Kirkmeyer. Marx at poll close (7 pm MT): Kalshi "
          f"{px.k_Marx.asof(pd.Timestamp('2026-07-01T00:59Z')):.3f}\n")
    print(o[o.counted >= 40].iloc[::3].to_string(index=False))
    w = px.loc[n.loc[n.pct >= 50, "t"].min():n.loc[n.pct >= 99, "t"].min()]
    low = w.k_Marx.idxmin()
    print(f"\nAfter half the vote was counted: Marx's Kalshi low {w.k_Marx.min():.3f} at "
          f"{low.tz_convert('America/Denver'):%a %H:%M} MT; minutes under 15c {int((w.k_Marx < 0.15).sum())}, "
          f"under 30c {int((w.k_Marx < 0.30).sum())}, under 50c {int((w.k_Marx < 0.5).sum())}; "
          f"median Kalshi spread while under 15c {w.k_Marx_spread[w.k_Marx < 0.15].median():.3f}")


if __name__ == "__main__":
    main()
