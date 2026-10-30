"""Polymarket's margin-of-victory ladders -> each race's market-implied margin (2026-10-30).

Polymarket lists, under most 2026 races, a ladder of bracket markets: "Will the Democratic Party
candidate win the 2026 AZ-06 House election by 3%-6%?", ..., "... by 18% or more?", and the same
for the Republican. Normalized, the brackets are the market's distribution of the final margin.
The map page's Margin view shows its median beside our margin model's projection.

Kalshi has no per-race equivalent (only "which race is closer" pairs), so this is Polymarket only.
These markets never enter the arb scanner or the party-winner book: utils/election_shapes keeps
margin brackets out of every party leg on purpose (they were the fake "guaranteed" arbs of
2026-09-24).

Margins are signed toward the Democrat (D +4 = Democrat wins by 4 points). First-round ladders
(Maine's ranked-choice first round) are skipped: the model projects the final round.
"""
import re
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
    cum, med = 0.0, None
    for lo, hi, p, _v, _ in rows:
        if med is None and cum + p >= 0.5:
            if _ == 2:              # the median is on the unlisted side: no margin to read
                return None
            med = lo + (hi - lo) * ((0.5 - cum) / p if p else 0.5)
        cum += p
    p_dem = sum(p * (1.0 if lo >= 0 else 0.0 if hi <= 0 else hi / (hi - lo)) for lo, hi, p, _, _ in rows)
    fmt = lambda r: [round(r[0], 1) + 0.0, round(r[1], 1) + 0.0, round(r[2], 4), r[4]]   # + 0.0: no "-0.0"
    return {
        "m": round(med, 2),
        "p_d": round(p_dem, 4),
        "top": fmt(max((r for r in rows if r[4] != 2), key=lambda r: r[2])),
        "lad": [fmt(r) for r in rows],
        "vol": int(round(sum(b[3] for b in brackets))),
    }


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


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    res = polymarket_margins(ROOT / "data" / "raw" / "polymarket_markets.csv")
    print(f"{len(res)} races with a Polymarket margin ladder")
    for rid in list(res)[:5]:
        print(rid, res[rid]["m"], res[rid]["p_d"], res[rid]["top"])
