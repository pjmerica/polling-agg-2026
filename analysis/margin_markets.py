"""Polymarket's margin-of-victory ladders -> each race's market-implied margin (2026-10-30).

Polymarket lists, under most 2026 races, a ladder of bracket markets: "Will the Democratic Party
candidate win the 2026 AZ-06 House election by 3%-6%?", ..., "... by 18% or more?", and the same
for the Republican. Normalized, the brackets are the market's distribution of the final margin.
The map page's Margin view shows its median beside our margin model's projection.

Kalshi lists the same thing as thresholds (series KXMIDTERMMOV): per race, an event for each
side with markets "margin of victory for Democrats ... at least N percentage points" - see
kalshi_margins() below. (An earlier note here said Kalshi had none; it was wrong, 2026-10-30.)
These markets never enter the arb scanner or the party-winner book: utils/election_shapes keeps
margin brackets out of every party leg on purpose (they were the fake "guaranteed" arbs of
2026-09-24).

Margins are signed toward the Democrat (D +4 = Democrat wins by 4 points). First-round ladders
(Maine's ranked-choice first round) are skipped: the model projects the final round.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

LADDER = re.compile(r"^Will the (Democratic|Republican) Party candidate win the 2026 (.+?) by "
                    r"(\d+(?:\.\d+)?)%(?:\s*-\s*(\d+(?:\.\d+)?)%| or more)\?$")
MIN_BRACKETS = 5          # fewer than this is not a ladder (a stray "within 5%" style question)
SUM_RANGE = (0.6, 1.8)    # raw prices should add up to about 1; far off means a broken book


def parse_ladders(df):
    """{race_id: [(lo, hi, p, volume), ...]} signed toward the Democrat, hi None = open-ended."""
    out = {}
    for q, rid, p, vol in zip(df["question"].fillna(""), df["race_id"], df["implied_prob"], df["volume"]):
        m = LADDER.match(q.strip())
        if not m or not isinstance(rid, str) or not rid.startswith("2026") or "first round" in m.group(2):
            continue
        if p != p or p is None:
            continue
        lo, hi = float(m.group(3)), (float(m.group(4)) if m.group(4) else None)
        if m.group(1) == "Republican":   # mirror; an open-ended one runs from -inf to -lo
            lo, hi = (-hi if hi is not None else None), -lo
        out.setdefault(rid, []).append((lo, hi, float(p), float(vol or 0)))
    return out


def summarize(brackets, book=None):
    """Median margin, P(Democrat wins), the most likely bracket and the normalized ladder, or None
    if the ladder is too short, its prices don't add up, or the median can't be placed.

    Most ladders (281 of 394 on 2026-10-10) list brackets for the favored party only ("R by 0-5%",
    ... with no Democratic brackets). Normalizing those alone would read as a 100% Republican win,
    which is wrong in races like KS-Sen (Polymarket's own winner market: Democrat 54%). So the
    unlisted side gets its chance from `book` (the venue's normalized winner book, {'D','R','I'}),
    the listed brackets share the rest, and if the median falls on the unlisted side - where the
    ladder says nothing about the size of the margin - the race is left out. No book, no
    one-sided ladder."""
    if len(brackets) < MIN_BRACKETS:
        return None
    s = sum(b[2] for b in brackets)
    if not SUM_RANGE[0] <= s <= SUM_RANGE[1]:
        return None
    has_d = any(lo is not None and lo >= 0 for lo, _, _, _ in brackets)
    has_r = any(hi is not None and hi <= 0 for _, hi, _, _ in brackets)
    p_other = 0.0                   # chance of the side with no brackets
    if not (has_d and has_r):
        if not isinstance(book, dict) or not any(k in book for k in "DRI"):
            return None
        p_other = (1 - book.get("R", 0)) if has_r else book.get("R", 0)
    scale = (1 - p_other) / s
    # close the open ends with the width of the neighbouring bracket
    # rows: [lo, hi, p, volume, open] with open -1 = "or more" toward the Republican, 1 = toward the
    # Democrat, 2 = the unlisted side (its chance from the winner market, no margin detail)
    rows = []
    for lo, hi, p, vol in brackets:
        rows.append([lo, hi, p * scale, vol, -1 if lo is None else 1 if hi is None else 0])
    widths = [r[1] - r[0] for r in rows if r[0] is not None and r[1] is not None]
    w = sorted(widths)[len(widths) // 2] if widths else 5.0
    for r in rows:
        if r[0] is None:
            r[0] = r[1] - w
        if r[1] is None:
            r[1] = r[0] + w
    if p_other > 0:
        rows.append([0.0, w, p_other, 0, 2] if has_r else [-w, 0.0, p_other, 0, 2])
    rows.sort(key=lambda r: r[0])
    cum, med, beyond = 0.0, None, None
    for lo, hi, p, _v, _ in rows:
        if med is None and cum + p >= 0.5:
            if _ == 2:              # the median is on the unlisted side: no margin to read
                return None
            med = lo + (hi - lo) * ((0.5 - cum) / p if p else 0.5)
            if _ in (-1, 1):        # in an open-ended bracket: the ladder only says "by this much or more"
                beyond = abs(hi if _ == -1 else lo)
        cum += p
    p_dem = sum(p * (1.0 if lo >= 0 else 0.0 if hi <= 0 else hi / (hi - lo)) for lo, hi, p, _, _ in rows)
    fmt = lambda r: [round(r[0], 1) + 0.0, round(r[1], 1) + 0.0, round(r[2], 4), r[4]]   # + 0.0: no "-0.0"
    out = {
        "m": round(med, 2),
        "p_d": round(p_dem, 4),
        "top": fmt(max((r for r in rows if r[4] != 2), key=lambda r: r[2])),
        "lad": [fmt(r) for r in rows],
        "vol": int(round(sum(b[3] for b in brackets))),
    }
    if beyond is not None:
        out["beyond"] = round(beyond, 1) + 0.0
    return out


def polymarket_margins(path, books=None):
    """books: {race_id: the venue's normalized winner book} for one-sided ladders (see summarize)."""
    path = Path(path)
    if not path.exists():
        return {}
    df = pd.read_csv(path, low_memory=False, usecols=lambda c: c in {"question", "race_id", "implied_prob", "volume"})
    out = {}
    for rid, br in parse_ladders(df).items():
        s = summarize(br, (books or {}).get(rid))
        if s:
            out[rid] = s
    return out



# ---------- Kalshi (2026-10-30) ----------
# KXMIDTERMMOV-{state}{district | AL | SEN | GOV}{side}: side D / R, or a candidate code (CA top-two,
# AK-Sen, NE-Sen's Osborn). Each market is P(that side wins by at least N points).
KALSHI_SERIES = "KXMIDTERMMOV"
KALSHI_EVENT = re.compile(r"^KXMIDTERMMOV-([A-Z]{2})(\d\d|AL|SEN|GOV)([A-Z]+)$")
KALSHI_TITLE = re.compile(r"^Will the margin of victory for (.+?) in (?:the )?(.+?) be at least "
                          r"(\d+(?:\.\d+)?) percentage points?\?$")
KALSHI_MAX_SPREAD = 0.30   # a wider book says nothing about the price
KALSHI_MIN_POINTS = 3      # thresholds needed across both sides


def kalshi_race_id(state, code, races):
    """Canonical race_id for an event's state + office code, or None if it is not on the ballot.
    Florida and Ohio vote only in their Senate specials, so SEN maps to the '-S' race there."""
    if code == "SEN":
        rid = f"2026-SEN-{state}"
        if rid not in races and rid + "-S" in races:
            rid += "-S"
    elif code == "GOV":
        rid = f"2026-GOV-{state}"
    else:
        rid = f"2026-H-{state}-{'01' if code == 'AL' else code}"
    return rid if rid in races else None


def _norm(n):
    n = unicodedata.normalize("NFKD", str(n)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", n).split()


def kalshi_side(who, race_cands):
    """'D' (Democrats, or an independent in the Democratic slot like Osborn), 'R', or None.
    who: 'Democrats' / 'Republicans' or a candidate's name, matched on surname to race_cands
    [(name, party), ...] from the forecast."""
    if who == "Democrats":
        return "D"
    if who == "Republicans":
        return "R"
    w = _norm(who)
    if not w:
        return None
    for name, party in race_cands or []:
        n = _norm(name)
        if n and n[-1] == w[-1]:
            return "R" if party == "REP" else "D" if party in ("DEM", "IND") else None
    return None


def _mid(bid, ask):
    """Order-book midpoint, or None when the book is empty or too wide to read. Not the last trade:
    those go stale (AZ-06 'R by 2+' last traded at 59c with the book at 8-16c, 2026-10-10)."""
    if ask is None or ask != ask or ask <= 0:
        return None
    bid = 0.0 if bid is None or bid != bid else bid
    return (bid + ask) / 2 if ask - bid <= KALSHI_MAX_SPREAD else None


def _pava_dec(ys):
    """Least-squares non-increasing fit (pool adjacent violators): noisy books can price
    'by 5+' above 'by 2+'."""
    blocks = []
    for y in ys:
        blocks.append([y, 1])
        while len(blocks) > 1 and blocks[-2][0] < blocks[-1][0]:
            y2, n2 = blocks.pop()
            y1, n1 = blocks[-1]
            blocks[-1] = [(y1 * n1 + y2 * n2) / (n1 + n2), n1 + n2]
    return [y for y, n in blocks for _ in range(n)]


def _segments(xs, ys):
    return list(zip(zip(xs, ys), zip(xs[1:], ys[1:])))


def summarize_kalshi(sides, book=None, vol=0):
    """sides: {'D': [(N, P(D wins by N+)), ...], 'R': [...]}; book: Kalshi's normalized winner book.
    Returns the same shape as summarize() (median margin toward the Democrat, p_d, top bracket,
    ladder, volume; 'beyond' = N when the median is past the last threshold, so all the ladder says
    is 'at least N') or None.

    Thresholds become points on S(x) = P(margin >= x); a Republican 'N+' is S(-N) = 1 - P, and the
    winner book gives S(0) when there is one. The far ends are closed one step past the last
    threshold, as summarize() closes Polymarket's open brackets. Most races list only the
    favourite's side: the median is still read when it falls inside that ladder (the favourite's
    lowest threshold priced at 50% or more), and the race is left out when it would fall in the
    stretch the ladder doesn't price. Ladder rows: [lo, hi, p, open], open -1 / 1 = the closed
    Republican / Democratic tail, 2 = the unlisted side (chance from the book), 3 = Republican win
    or a Democratic win under hi (no Republican ladder, no book), 4 = the mirror image, 0 = priced.
    p_d is None when neither the book nor a two-sided ladder gives it."""
    D, R = sides.get("D", []), sides.get("R", [])
    has_d, has_r = bool(D), bool(R)
    pts = {}
    for k, p in D:
        pts.setdefault(float(k), []).append(p)
    for k, p in R:
        pts.setdefault(-float(k), []).append(1 - p)
    if len(pts) < KALSHI_MIN_POINTS:
        return None
    s0 = None
    if isinstance(book, dict) and "R" in book and len([k for k in "DRI" if k in book]) >= 2:
        s0 = 1 - book["R"]
        pts.setdefault(0.0, []).append(s0)
    xs = sorted(pts)
    ys = _pava_dec([min(1.0, max(0.0, sum(pts[x]) / len(pts[x]))) for x in xs])
    th = [sorted(float(k) for k, _ in s) for s in (D, R)]
    gaps = sorted(b - a for t in th for a, b in zip(t, t[1:]) if b > a)
    w = gaps[len(gaps) // 2] if gaps else 3.0
    segs = [[x0, y0, x1, y1, 0] for (x0, y0), (x1, y1) in _segments(xs, ys)]
    if has_r:
        segs.insert(0, [xs[0] - w, 1.0, xs[0], ys[0], -1])
    else:   # xs[0] is the book's 0, or the lowest Democratic threshold
        segs.insert(0, [-w, 1.0, xs[0], ys[0], 2 if s0 is not None else 3])
    if has_d:
        segs.append([xs[-1], ys[-1], xs[-1] + w, 0.0, 1])
    else:
        segs.append([xs[-1], ys[-1], w, 0.0, 2 if s0 is not None else 4])
    med = beyond = None
    for x0, y0, x1, y1, op in segs:
        if y0 >= 0.5 >= y1 and y0 > y1:
            if op in (2, 3, 4):
                return None   # the median falls where no ladder prices the margin
            med = x0 + (x1 - x0) * (y0 - 0.5) / (y0 - y1)
            if op in (-1, 1):   # past the last threshold: the ladder only says "at least this much"
                beyond = abs(x1 if op == -1 else x0)
            break
    if med is None:
        return None
    p_d = s0
    if p_d is None and has_d and has_r:
        p_d = next((y0 + (y1 - y0) * (0 - x0) / (x1 - x0) if x1 > x0 else y0)
                   for x0, y0, x1, y1, _ in segs if x0 <= 0 <= x1)
    rows = [[round(x0, 1) + 0.0, round(x1, 1) + 0.0, round(max(0.0, y0 - y1), 4), op]
            for x0, y0, x1, y1, op in segs if x1 > x0]
    out = {"m": round(med, 2), "p_d": None if p_d is None else round(p_d, 4),
           "top": max((r for r in rows if r[3] in (-1, 0, 1)), key=lambda r: r[2]),
           "lad": rows, "vol": int(round(vol or 0))}
    if beyond is not None:
        out["beyond"] = round(beyond, 1) + 0.0
    return out


def kalshi_margins(path, books=None, cands=None, races=None):
    """{race_id: summary} from the Kalshi scrape (data/raw/kalshi_markets.csv).
    books: {race_id: Kalshi's normalized winner book}; cands: {race_id: [(name, party), ...]} to
    place candidate-named sides; races: the race_ids on the ballot (default utils/races.py).
    Same-party races (both sides Democrats, as in California's top-two) are skipped: the map's
    margin is between the parties."""
    path = Path(path)
    if not path.exists():
        return {}
    if races is None:
        from utils.races import ALL_RACES_2026
        races = {r.race_id for r in ALL_RACES_2026}
    df = pd.read_csv(path, low_memory=False, usecols=lambda c: c in
                     {"series_ticker", "event_ticker", "market_title", "yes_bid", "yes_ask", "volume"})
    df = df[df["series_ticker"] == KALSHI_SERIES]
    acc = {}   # race_id -> {"ev": {event: side}, "sides": {side: [(N, p)]}, "vol": contracts}
    for ev, title, bid, ask, vol in zip(df["event_ticker"], df["market_title"].fillna(""), df["yes_bid"],
                                        df["yes_ask"], df["volume"]):
        e, t = KALSHI_EVENT.match(str(ev)), KALSHI_TITLE.match(title.strip())
        if not e or not t or "first round" in t.group(2).lower():
            continue
        rid = kalshi_race_id(e.group(1), e.group(2), races)
        if not rid:
            continue
        side = kalshi_side(t.group(1), (cands or {}).get(rid))
        a = acc.setdefault(rid, {"ev": {}, "sides": {}, "vol": 0.0})
        a["ev"][ev] = side
        a["vol"] += float(vol) if vol is not None and vol == vol else 0.0
        p = _mid(bid, ask)
        if side and p is not None:
            a["sides"].setdefault(side, []).append((float(t.group(3)), p))
    out = {}
    for rid, a in acc.items():
        sides = list(a["ev"].values())
        if None in sides or len(set(sides)) != len(sides):   # an unplaced name, or same-party sides
            continue
        s = summarize_kalshi(a["sides"], (books or {}).get(rid), a["vol"])
        if s:
            out[rid] = s
    return out


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    res = polymarket_margins(ROOT / "data" / "raw" / "polymarket_markets.csv")
    print(f"{len(res)} races with a Polymarket margin ladder")
    for rid in list(res)[:5]:
        print(rid, res[rid]["m"], res[rid]["p_d"], res[rid]["top"])
