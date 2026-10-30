"""Is the count misread more in primaries than in general elections? Every 2026 Senate/Governor primary
with a market, against the 2024 generals.

For each 2026 primary in the primary model's list (data/processed/model_primary_predictions_2026.csv,
plus the March 3 states it doesn't cover) this downloads NYT's results file and the candidates' minute
prices (Kalshi KXGOV{ST}NOM{R|D}-26, governors only; Polymarket {state}-governor-{party}-primary-winner
and {state}-{party}-senate-primary-winner), then measures, the same way for the 2024 generals
(market_check.py's data):
  - how cheap the eventual winner got after half the vote was counted (until 99%), and for how long;
  - between 50% and 95% counted, how often each of these named the eventual winner (each race weighted
    equally): the market's favorite, the visible leader, and a within-night trend (the visible margin
    plus the rest of the vote breaking like the last 15% of the count did).
Races decided later (a runoff, or a market that settled on someone other than the count's leader) are
left out. Margins are the eventual winner minus the runner-up, in points of all votes.

    py "Election night simulator/scripts/primary_check.py"

Raw files: data/raw/primaries/2026/ (not committed). Output: data/processed/primary_check_2026.csv
(per race) and primary_check_compare.csv (the 2026 primaries next to the 2024 generals).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)
from utils.http_headers import DEFAULT_HEADERS  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "primaries", "2026")
PROC = os.path.join(ROOT, "data", "processed")
NYT = "https://static01.nyt.com/elections-assets/pages/data/{date}/results-{slug}.json"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
TREND_WINDOW = 15
STATE = {"AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas", "CA": "california", "CO": "colorado",
         "CT": "connecticut", "DE": "delaware", "FL": "florida", "GA": "georgia", "HI": "hawaii", "ID": "idaho",
         "IL": "illinois", "IN": "indiana", "IA": "iowa", "KS": "kansas", "KY": "kentucky", "LA": "louisiana",
         "ME": "maine", "MD": "maryland", "MA": "massachusetts", "MI": "michigan", "MN": "minnesota",
         "MS": "mississippi", "MO": "missouri", "MT": "montana", "NE": "nebraska", "NV": "nevada",
         "NH": "new-hampshire", "NJ": "new-jersey", "NM": "new-mexico", "NY": "new-york", "NC": "north-carolina",
         "ND": "north-dakota", "OH": "ohio", "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania",
         "RI": "rhode-island", "SC": "south-carolina", "SD": "south-dakota", "TN": "tennessee", "TX": "texas",
         "UT": "utah", "VT": "vermont", "VA": "virginia", "WA": "washington", "WV": "west-virginia",
         "WI": "wisconsin", "WY": "wyoming"}
PARTY = {"REP": ("R", "republican", "GOP"), "DEM": ("D", "democratic", "DEM")}
# March 3 primaries the primary model's list doesn't cover
EXTRA = [("TX", "Senate", "REP", "2026-03-03"), ("TX", "Senate", "DEM", "2026-03-03"),
         ("TX", "Governor", "REP", "2026-03-03"), ("TX", "Governor", "DEM", "2026-03-03"),
         ("NC", "Senate", "REP", "2026-03-03"), ("NC", "Senate", "DEM", "2026-03-03"),
         ("AR", "Senate", "REP", "2026-03-03"), ("AR", "Governor", "REP", "2026-03-03")]


def get(url, raw=False, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=DEFAULT_HEADERS), timeout=60) as r:
                b = r.read()
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if e.code == 429 and i + 1 < tries:
                time.sleep(3 * (i + 1))
                continue
            raise


def races():
    p = pd.read_csv(os.path.join(REPO, "data", "processed", "model_primary_predictions_2026.csv"))
    r = p[p.office.isin(["Senate", "Governor"])]
    out = {(x.state, x.office, x.party, x.election_date) for x in r.itertuples()}
    return sorted(out | set(EXTRA))


# 2026 primary nights. The primary model's list carries the RUNOFF date for some states (TX May 26,
# GA/AL June 16, SC June 23, SD July 28) and other dates that aren't the primary night (ME, AZ, RI),
# so a race with no file on its listed date tries these, earliest first.
PRIMARY_NIGHTS = ["2026-03-03", "2026-03-10", "2026-03-17", "2026-05-05", "2026-05-12", "2026-05-19",
                  "2026-06-02", "2026-06-09", "2026-06-16", "2026-06-23", "2026-06-30", "2026-07-21",
                  "2026-07-28", "2026-08-04", "2026-08-06", "2026-08-11", "2026-08-18", "2026-09-01",
                  "2026-09-08", "2026-09-09", "2026-09-15"]


def nyt_file(st, office, date):
    """(NYT results file for the state's primary, both parties' races; its date), cached. Tries the
    listed date, then every 2026 primary night."""
    os.makedirs(RAW, exist_ok=True)
    slugs = (["governor-primary"] if office == "Governor"
             else ["us-senate-primary", "us-senate-special-primary"])
    miss = os.path.join(RAW, "_missing.json")
    missing = set(json.load(open(miss))) if os.path.exists(miss) else set()
    for day in [date] + [x for x in PRIMARY_NIGHTS if x != date]:
        for s in slugs:
            slug = f"{STATE[st]}-{s}"
            path = os.path.join(RAW, f"{day}_{slug}.json")
            if os.path.exists(path):
                return json.load(open(path, encoding="utf-8")), day
            if f"{day}_{slug}" in missing:
                continue
            b = get(NYT.format(date=day, slug=slug), raw=True)
            if b:
                open(path, "wb").write(b)
                return json.loads(b), day
            missing.add(f"{day}_{slug}")
            time.sleep(0.05)
    json.dump(sorted(missing), open(miss, "w"))
    return None, None


def nyt_race(d, party):
    """-> (timeline DataFrame t/votes/{cand: votes}, {cand: last name}, final order) or None."""
    nyt_party = PARTY[party][2]
    for r in d.get("races", []):
        meta = r.get("candidate_metadata") or {}
        parties = {str((m.get("party") or {}).get("nyt_id")) for m in meta.values()}
        if parties != {nyt_party} and str((r.get("party") or {}).get("nyt_id")) != nyt_party:
            continue
        if (r.get("outcome") or {}).get("advanced_to_runoff"):
            return None                                        # decided in a runoff (TX, GA, NC, ...)
        rows = []
        for x in (d.get("timeseries") or {}).get(r["nyt_id"], []):
            if x.get("total_votes"):
                v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in x["candidates"]}
                rows.append(dict(t=x.get("greatest_updated_at") or x.get("provider_updated_at"),
                                 votes=x["total_votes"], **v))
        if len(rows) < 5:
            return None
        n = pd.DataFrame(rows)
        n["t"] = pd.to_datetime(n.t, utc=True, format="ISO8601")
        n = n.sort_values("t").drop_duplicates("t").reset_index(drop=True)
        names = {k: m.get("last_name", k) for k, m in meta.items()}
        firsts = {m.get("last_name", k): str(m.get("first_name") or "") for k, m in meta.items()}
        order = sorted(names, key=lambda k: -n[k].iloc[-1] if k in n else 0)
        # ranked-choice (Maine): primary night only decides it if someone has a first-round majority;
        # otherwise the tabulation days later does. The timeline ends on the final round, where the
        # winner always has a majority, so read the initial round (as swing_analysis.py does).
        if "ranked" in str(r.get("tabulation_method") or "").lower():
            initial = [rd for rd in (r.get("rounds") or []) if rd.get("round_type") == "initial"]
            tot1 = [c.get("total", 0) for c in (initial[0]["candidates"] if initial else [])]
            if not tot1 or max(tot1) <= 0.5 * sum(tot1):
                return "ranked-choice with no first-round majority: decided by tabulation days later"
        return n, names, order, firsts
    return None


def _candles(ticker, s, e):
    rows, a = [], s
    while a < e:
        b = min(a + 12 * 3600, e)
        c = get(f"{KALSHI}/historical/markets/{ticker}/candlesticks?start_ts={a}&end_ts={b}&period_interval=1") \
            or get(f"{KALSHI}/series/{ticker.split('-')[0]}/markets/{ticker}/candlesticks"
                   f"?start_ts={a}&end_ts={b}&period_interval=1")
        rows += [dict(ts=k["end_period_ts"], bid=(k.get("yes_bid") or {}).get("close"),
                      ask=(k.get("yes_ask") or {}).get("close")) for k in (c or {}).get("candlesticks", [])]
        a = b
        time.sleep(0.15)
    return rows


def _words(s):
    return " " + "".join(ch if ch.isalpha() else " " for ch in str(s).lower()) + " "


def match(title, firsts):
    """-> (last name, matched on the full name?) for a contract title, or (None, False). Full name
    first: Kalshi lists Hannah AND Chellie Pingree for Maine, and a last-name match let the dead
    Chellie contract stand in for the winner."""
    t = _words(title)
    full = [ln for ln, fn in firsts.items() if fn and _words(fn).strip() and
            _words(fn).strip().split()[0] in t.split() and _words(ln) in t]
    if full:
        return max(full, key=len), True
    last = [ln for ln in firsts if _words(ln).strip() and _words(ln) in t]
    return (last[0], False) if len(last) == 1 else (None, False)


def markets(st, office, party, date, names, firsts):
    """{venue: {last name: (DataFrame ts/bid/ask or ts/p, settled yes?)}} for the race's candidates.
    When two contracts match one candidate, the full-name match wins, then the most traded."""
    key = f"{date}_{st}_{office}_{party}"
    cache = os.path.join(RAW, f"{key}_markets.json")
    if os.path.exists(cache):
        js = json.load(open(cache, encoding="utf-8"))
        return {v: {n: (pd.DataFrame(x["rows"]), x["won"]) for n, x in c.items()} for v, c in js.items()}
    s = int(pd.Timestamp(f"{date}T22:00Z").timestamp())
    e = s + 3 * 86400
    out = {"kalshi": {}, "polymarket": {}}

    def pick(contracts):
        """[(last name, full match?, volume, contract)] -> {last name: contract}"""
        best = {}
        for nm, full, vol, c in contracts:
            if nm and vol > 1000 and (nm not in best or (full, vol) > best[nm][:2]):
                best[nm] = (full, vol, c)
        return {nm: c for nm, (_, _, c) in best.items()}

    if office == "Governor":
        ev = f"KXGOV{st}NOM{PARTY[party][0]}-26"
        ms = ((get(f"{KALSHI}/historical/markets?event_ticker={ev}") or {}).get("markets")
              or (get(f"{KALSHI}/markets?event_ticker={ev}") or {}).get("markets") or [])
        for nm, m in pick([(*match(m.get("yes_sub_title", ""), firsts), float(m.get("volume_fp") or 0), m)
                           for m in ms]).items():
            out["kalshi"][nm] = (_candles(m["ticker"], s, e), m.get("result") == "yes")
    pw = PARTY[party][1]
    slug = (f"{STATE[st]}-governor-{pw}-primary-winner" if office == "Governor"
            else f"{STATE[st]}-{pw}-senate-primary-winner")
    evs = get(f"{GAMMA}/events?slug={slug}") or []
    chosen = pick([(*match(m["question"], firsts), float(m.get("volumeNum") or 0), m)
                   for m in (evs[0]["markets"] if evs else [])])
    for nm, m in chosen.items():
        tok = json.loads(m["clobTokenIds"])[0]
        rows, a = [], s
        while a < e:
            b = min(a + 12 * 3600, e)
            rows += [dict(ts=x["t"], p=x["p"]) for x in (get(f"{CLOB}/prices-history?market={tok}&startTs={a}"
                                                             f"&endTs={b}&fidelity=1") or {}).get("history", [])]
            a = b
        won = json.loads(m.get("outcomePrices") or "[]")
        out["polymarket"][nm] = (rows, bool(won) and won[0] == "1")
    json.dump({v: {n: dict(rows=r, won=w) for n, (r, w) in c.items()} for v, c in out.items()},
              open(cache, "w", encoding="utf-8"))
    return {v: {n: (pd.DataFrame(r), w) for n, (r, w) in c.items()} for v, c in out.items()}


def mid_series(mk, name, idx):
    """Per-minute mid for one candidate: Kalshi where its spread is 10c or less, else Polymarket."""
    m = pd.Series(np.nan, index=idx)
    k = mk.get("kalshi", {}).get(name)
    if k is not None and len(k[0]):
        x = k[0].copy()
        x.index = pd.to_datetime(x.ts, unit="s", utc=True)
        x = x[~x.index.duplicated()].astype(float)
        bid, ask = x.bid.reindex(idx, method="ffill"), x.ask.reindex(idx, method="ffill")
        ok = (ask - bid) <= 0.10
        m[ok] = ((bid + ask) / 2)[ok]
    p = mk.get("polymarket", {}).get(name)
    if p is not None and len(p[0]):
        x = p[0].copy()
        x.index = pd.DatetimeIndex(pd.to_datetime(x.ts, unit="s", utc=True)).floor("min")
        m = m.fillna(x[~x.index.duplicated(keep="last")].p.astype(float).reindex(idx, method="ffill"))
    return m


def directional(pct, margin, cum_w, cum_r, votes, winner_price, runner_price):
    """Share of updates (50-95% counted) on which each signal named the eventual winner."""
    hits = {"market": [], "visible": [], "trend": []}
    for i in range(len(pct)):
        if not 50 <= pct[i] <= 95:
            continue
        j = np.searchsorted(pct, pct[i] - TREND_WINDOW, side="right") - 1
        if j < 0:
            continue
        dv = votes[i] - votes[j]
        if dv <= 0:
            continue
        trend = 100 * ((cum_w[i] - cum_w[j]) - (cum_r[i] - cum_r[j])) / dv
        proj = margin[i] + (1 - pct[i] / 100) * (trend - margin[i])
        hits["visible"].append(margin[i] > 0)
        hits["trend"].append(proj > 0)
        if winner_price[i] == winner_price[i] and runner_price[i] == runner_price[i]:
            hits["market"].append(winner_price[i] > runner_price[i])
    return {k: (float(np.mean(v)) if v else None) for k, v in hits.items()}


def winner_low(idx, w_price, pct_at_min):
    after = (pct_at_min >= 50) & (pct_at_min < 99)
    w = w_price[after].dropna()
    if w.empty:
        return None
    return dict(low=round(float(w.min()), 3), when=w.idxmin(),
                min_under_15=int((w < 0.15).sum()), min_under_30=int((w < 0.30).sum()))


_snap_cache = {}


def model_snapshot(st, office, party, date):
    """{last name: (model, market)} from the primary model's page as published before polls closed
    (docs/primary_model_data.js in git; history starts 2026-07-15), or {}."""
    key = (date,)
    if key not in _snap_cache:
        import subprocess
        c = subprocess.run(["git", "log", "-1", "--format=%h", f"--before={date}T22:00Z", "--",
                            "docs/primary_model_data.js"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        races_ = {}
        if c:
            s = subprocess.run(["git", "show", f"{c}:docs/primary_model_data.js"], cwd=REPO,
                               capture_output=True, text=True, encoding="utf-8").stdout
            try:
                j = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
                races_ = {r["race_id"]: r for r in j.get("races", [])}
            except ValueError:
                pass
        _snap_cache[key] = races_
    r = _snap_cache[key].get(f"2026_{st}_{office}_{party}")
    if not r or r.get("election_date") != date:
        return {}
    return {str(c["candidate"]).split()[-1].lower(): (c.get("model"), c.get("market"))
            for c in r.get("candidates", [])}


def primaries():
    rows, skipped, series, seen = [], [], [], set()
    for st, office, party, date in races():
        race = f"{st}-{office}-{party}"
        d, found = nyt_file(st, office, date)
        date = found or date
        if race in seen:                    # listed twice (TX: March 3 here, its May 26 runoff in the list)
            continue
        seen.add(race)
        if not d:
            skipped.append(dict(race=race, date=date, reason="no NYT results file"))
            continue
        x = nyt_race(d, party)
        if not x or isinstance(x, str):
            skipped.append(dict(race=race, date=date, reason=x or "no usable NYT timeline, or went to a runoff"))
            continue
        n, names, order, firsts = x
        if len(order) < 2:
            skipped.append(dict(race=race, date=date, reason="uncontested"))
            continue
        mk = markets(st, office, party, date, names, firsts)
        if not (mk["kalshi"] or mk["polymarket"]):
            skipped.append(dict(race=race, date=date, reason="no market with $1,000+ traded"))
            continue
        wk, rk = order[0], order[1]
        wn, rn = names[wk], names[rk]
        winners = [nm for v in mk.values() for nm, (_, won) in v.items() if won]
        if winners and wn not in winners:
            print(f"{st} {office} {party}: market settled on {winners}, the count's leader is {wn} - left out")
            skipped.append(dict(race=race, date=date,
                                reason=f"market settled on {winners[0]} (runoff), not the count's leader {wn}"))
            continue
        idx = pd.date_range(pd.Timestamp(f"{date}T22:00Z"), periods=3 * 1440, freq="1min")
        wp, rp = mid_series(mk, wn, idx), mid_series(mk, rn, idx)
        final = n.votes.iloc[-1]
        pct = (100 * n.votes / final).to_numpy()
        margin = (100 * (n[wk] - n[rk]) / n.votes).to_numpy()
        t2 = n.t.dt.floor("min") + pd.Timedelta(minutes=2)
        wpi, rpi = wp.reindex(t2).to_numpy(), rp.reindex(t2).to_numpy()
        hit = directional(pct, margin, n[wk].to_numpy(), n[rk].to_numpy(), n.votes.to_numpy(), wpi, rpi)
        pct_min = pd.Series(pct, index=n.t).reindex(idx.union(n.t)).sort_index().ffill().reindex(idx).fillna(0)
        low = winner_low(idx, wp, pct_min.to_numpy())
        first = n.t.iloc[0].floor("min") - pd.Timedelta(minutes=5)
        pre = wp.asof(first) if first >= idx[0] else np.nan
        snap = model_snapshot(st, office, party, date)
        model_w = snap.get(wn.split()[-1].lower(), (None, None))[0]
        if abs(margin[-1]) < 3:                         # the page charts every close race
            for i in range(len(pct)):
                series.append(dict(race=race, t=n.t.iloc[i].isoformat(), pct=round(pct[i], 2),
                                   margin=round(margin[i], 3),
                                   winner_price=None if wpi[i] != wpi[i] else round(float(wpi[i]), 4)))
        rows.append(dict(race=race, date=date, winner=wn, runner_up=rn,
                         final_margin=round(margin[-1], 2), winner_at_close=round(pre, 3) if pre == pre else None,
                         model_winner=None if model_w is None else round(model_w, 3),
                         winner_low=low["low"] if low else None,
                         low_when_et=low["when"].tz_convert("America/New_York").strftime("%m-%d %H:%M") if low else "",
                         min_under_15=low["min_under_15"] if low else None,
                         min_under_30=low["min_under_30"] if low else None,
                         venues="+".join(v for v in ("kalshi", "polymarket") if mk[v]),
                         **{f"right_{k}": None if v is None else round(v, 3) for k, v in hit.items()}))
        print(f"{st} {office} {party} {date}: {wn} over {rn} by {margin[-1]:.1f}; winner low "
              f"{low['low'] if low else '-'}")
    return pd.DataFrame(rows), pd.DataFrame(skipped), pd.DataFrame(series)


def generals_2024():
    """The same measures for the 2024 generals, from market_check.py's downloads."""
    import market_check as mc
    tl = mc.timelines()
    settled = mc.contract_results()
    rows = []
    for race in sorted(os.listdir(mc.HIST)):
        if not os.path.isdir(os.path.join(mc.HIST, race)):
            continue
        st, office = race.split("-", 1)
        if (2024, st, office) not in tl:
            continue
        pct, mar, final, ts = tl[(2024, st, office)]
        won = final > 0
        if any(settled.get((race, v), won) != won for v in ("kalshi", "polymarket")):
            continue
        df = mc.minute_frame(race)
        m = pd.Series(np.nan, index=df.index)
        if "k_bid" in df:
            ok = (df.k_ask - df.k_bid) <= 0.10
            m[ok] = ((df.k_bid + df.k_ask) / 2)[ok]
        if "poly" in df:
            m = m.fillna(df.poly)
        wp = m if won else 1 - m
        t = pd.DatetimeIndex(ts).floor("min") + pd.Timedelta(minutes=2)
        pre = wp.asof(pd.Timestamp(ts[0]).floor("min") - pd.Timedelta(minutes=5))
        if not (pre == pre and 0.03 <= pre <= 0.97):
            continue
        sign = 1 if won else -1                       # margins as winner minus loser
        wm = sign * np.asarray(mar)
        # cumulative winner-minus-loser votes are not stored; rebuild the trend from margins and shares
        votes = np.asarray(pct)
        diff = wm * votes / 100
        hit = directional(np.asarray(pct), wm, diff, np.zeros_like(diff), votes,
                          wp.reindex(t).to_numpy(), (1 - wp).reindex(t).to_numpy())
        pct_min = pd.Series(pct, index=pd.DatetimeIndex(ts)).reindex(df.index.union(pd.DatetimeIndex(ts))) \
            .sort_index().ffill().reindex(df.index).fillna(0)
        low = winner_low(df.index, wp, pct_min.to_numpy())
        rows.append(dict(race=race, final_margin=round(abs(final), 2),
                         winner_at_close=round(float(pre), 3), winner_low=low["low"] if low else None,
                         min_under_15=low["min_under_15"] if low else None,
                         **{f"right_{k}": v for k, v in hit.items()}))
    return pd.DataFrame(rows)


def summary(df, label):
    d = df.dropna(subset=["winner_low"])
    return dict(set=label, races=len(df),
                winner_under_50c=f"{(d.winner_low < 0.5).sum()} ({(d.winner_low < 0.5).mean():.0%})",
                winner_under_20c=f"{(d.winner_low < 0.2).sum()} ({(d.winner_low < 0.2).mean():.0%})",
                winner_under_10c=f"{(d.winner_low < 0.1).sum()} ({(d.winner_low < 0.1).mean():.0%})",
                right_market=round(df.right_market.mean(), 3), right_visible=round(df.right_visible.mean(), 3),
                right_trend=round(df.right_trend.mean(), 3))


def main():
    p, skipped, series = primaries()
    g = generals_2024()
    os.makedirs(PROC, exist_ok=True)
    p.to_csv(os.path.join(PROC, "primary_check_2026.csv"), index=False)
    skipped.to_csv(os.path.join(PROC, "primary_check_2026_skipped.csv"), index=False)
    series.to_csv(os.path.join(PROC, "primary_check_close_series.csv"), index=False)
    g.to_csv(os.path.join(PROC, "primary_check_2024_generals.csv"), index=False)
    cmp_ = pd.DataFrame([summary(p, "2026 primaries"), summary(g, "2024 generals")])
    cmp_.to_csv(os.path.join(PROC, "primary_check_compare.csv"), index=False)
    pd.set_option("display.width", 250)
    print("\nPer race (2026 primaries):\n")
    print(p.drop(columns=["date"]).sort_values("winner_low").to_string(index=False))
    print("\nPrimaries vs generals. right_* = share of updates at 50-95% counted on which the signal named "
          "the eventual winner (races weighted equally):\n")
    print(cmp_.to_string(index=False))


if __name__ == "__main__":
    main()
