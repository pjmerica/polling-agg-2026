"""Regenerate all dashboard JS data files, filtering polls to 2026 only."""
import pandas as pd, numpy as np, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from utils.races import RACE_BY_ID

def wavg(g, vc, wc):
    w = g[wc].values.astype(float); v = g[vc].values.astype(float)
    return np.average(v, weights=w) if w.sum() > 0 else v.mean()

def get_meta(race_id):
    r = RACE_BY_ID.get(race_id)
    if not r: return '', '', ''
    lbl = f"{r.state_abbrev}-{str(r.district).zfill(2)}" if r.office == 'H' else f"{r.state_abbrev} {r.office}"
    return r.state, r.office, lbl

def parse_iso(s):
    try: return pd.to_datetime(s, format='%m/%d/%y').date().isoformat()
    except:
        try: return pd.to_datetime(s).date().isoformat()
        except: return ''

ABBREV = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California',
    'CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia',
    'HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas',
    'KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland','MA':'Massachusetts',
    'MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri','MT':'Montana',
    'NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico',
    'NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma',
    'OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina',
    'SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont',
    'VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming',
}

# ── Load + filter to 2026 polls only ──
polls_raw = pd.read_csv(ROOT / 'data/raw/nyt_polls.csv')
polls_raw['end_date_iso'] = polls_raw['end_date'].apply(parse_iso)
polls = polls_raw[polls_raw['end_date_iso'].str.startswith('2026')].copy()
print(f"Polls after 2026 filter: {len(polls)} / {len(polls_raw)}")

# ── data.js ──
agg = pd.read_csv(ROOT / 'data/processed/aggregated.csv').fillna('')
def label(row):
    if row['office'] == 'H':
        d = str(row['district'])
        return f"{row['state_abbrev']}-{d.zfill(2) if d else '?'}"
    return f"{row['state_abbrev']} {row['office']}"
agg['label'] = agg.apply(label, axis=1)
with open(ROOT / 'docs/data.js', 'w') as f:
    f.write('const RACES = ')
    json.dump(agg.to_dict(orient='records'), f, separators=(',',':'))
    f.write(';')
print(f"data.js: {len(agg)} races")

# ── polls_data.js ──
races = {}
for race_id, rdf in polls.groupby('race_id'):
    poll_list = []
    for (poll_id, question_id), qdf in rdf.groupby(['poll_id', 'question_id']):
        row0 = qdf.iloc[0]
        cands = sorted([{
            'name': r['candidate'], 'party': r['party'],
            'pct': round(r['implied_prob'] * 100, 1),
            'over50': bool(r['implied_prob'] > 0.50),
        } for _, r in qdf.iterrows()], key=lambda c: -c['pct'])
        poll_list.append({
            'poll_id': poll_id, 'question_id': question_id,
            'pollster': str(row0['pollster']), 'end_date': str(row0['end_date']),
            'end_date_iso': str(row0['end_date_iso']),
            'sample_size': int(row0['sample_size']) if str(row0['sample_size']) not in ('nan', '') else None,
            'stage': str(row0['stage']),
            'partisan': str(row0['partisan']) if str(row0['partisan']) != 'nan' else '',
            'candidates': cands, 'any_over50': any(c['over50'] for c in cands),
        })
    poll_list.sort(key=lambda p: p['end_date_iso'], reverse=True)
    office = race_id.split('-')[1]; sa = race_id.split('-')[2]
    parts = race_id.split('-'); district = parts[3] if len(parts) > 3 and office == 'H' else ''
    lbl = f"{sa}-{district}" if office == 'H' else f"{sa} {office}"
    n_over50 = sum(1 for p in poll_list if p['any_over50'])
    races[race_id] = {
        'race_id': race_id, 'label': lbl, 'office': office,
        'state': ABBREV.get(sa, sa), 'state_abbrev': sa, 'district': district,
        'n_polls': len(poll_list), 'n_over50': n_over50, 'polls': poll_list,
    }
out = sorted(races.values(), key=lambda r: (-r['n_over50'], -r['n_polls']))
with open(ROOT / 'docs/polls_data.js', 'w') as f:
    f.write('const POLLS = '); json.dump(out, f, separators=(',',':')); f.write(';')
print(f"polls_data.js: {len(out)} races")

# ── mismatch_data.js ──
k = pd.read_csv(ROOT / 'data/raw/kalshi_markets.csv')
k = k[k['race_id'].notna() & k['implied_prob'].notna()].copy()
k['weight'] = pd.to_numeric(k['open_interest'], errors='coerce').fillna(
    pd.to_numeric(k['volume'], errors='coerce')).fillna(1.0)

# General
k_gen_dem = k[
    k['market_title'].str.contains('Democratic|Democrat', case=False, na=False) &
    ~k['market_title'].str.contains('nominee|primary|nominate', case=False, na=False)
].copy()
kalshi_gen = k_gen_dem.groupby('race_id').apply(
    lambda g: wavg(g, 'implied_prob', 'weight'), include_groups=False).rename('kalshi_dem_prob')

nyt_gen = polls[(polls['stage'] == 'general') & (polls['party'] == 'DEM')].copy()
nyt_gen['weight'] = pd.to_numeric(nyt_gen['weight'], errors='coerce').fillna(1.0)
nyt_gen = nyt_gen[nyt_gen['weight'] > 0]
nyt_gen_avg = nyt_gen.groupby('race_id').apply(
    lambda g: wavg(g, 'implied_prob', 'weight'), include_groups=False).rename('nyt_dem_share')

gen = pd.DataFrame({'kalshi_dem_prob': kalshi_gen, 'nyt_dem_share': nyt_gen_avg}).dropna().reset_index()
gen['gap'] = (gen['kalshi_dem_prob'] - gen['nyt_dem_share']).round(4)
gen['abs_gap'] = gen['gap'].abs().round(4)
gen['stage'] = 'general'
gen[['state', 'office', 'label']] = gen['race_id'].apply(lambda x: pd.Series(get_meta(x)))

# Primary
k_prim = k[k['market_title'].str.contains('nominee|primary|nominate', case=False, na=False)].copy()
k_prim['prim_party'] = np.where(
    k_prim['market_title'].str.contains('Republican', case=False, na=False), 'REP',
    np.where(k_prim['market_title'].str.contains('Democrat|Democratic', case=False, na=False), 'DEM', 'OTHER'))
k_prim = k_prim[k_prim['prim_party'].isin(['DEM', 'REP'])].copy()
k_prim_leader = k_prim.groupby(['race_id', 'prim_party']).apply(
    lambda g: g.loc[g['implied_prob'].idxmax(), ['market_title', 'implied_prob', 'weight']],
    include_groups=False).reset_index()

nyt_prim = polls[polls['stage'].isin(['primary', 'primary runoff'])].copy()
nyt_prim['weight'] = pd.to_numeric(nyt_prim['weight'], errors='coerce').fillna(1.0)
nyt_prim = nyt_prim[nyt_prim['weight'] > 0]

def top_candidate(g):
    ca = g.groupby('candidate').apply(lambda c: wavg(c, 'implied_prob', 'weight'), include_groups=False)
    top = ca.idxmax()
    return pd.Series({'candidate': top, 'nyt_share': ca[top]})

nyt_prim_leader = nyt_prim.groupby(['race_id', 'party']).apply(
    top_candidate, include_groups=False).reset_index().rename(columns={'party': 'prim_party'})

prim = k_prim_leader.merge(nyt_prim_leader, on=['race_id', 'prim_party'], how='inner')
prim = prim.rename(columns={'implied_prob': 'kalshi_dem_prob', 'nyt_share': 'nyt_dem_share'})
prim['gap'] = (prim['kalshi_dem_prob'] - prim['nyt_dem_share']).round(4)
prim['abs_gap'] = prim['gap'].abs().round(4)
prim['stage'] = 'primary'
prim[['state', 'office', 'label']] = prim['race_id'].apply(lambda x: pd.Series(get_meta(x)))

with open(ROOT / 'docs/mismatch_data.js', 'w') as f:
    f.write('const MISMATCH = ')
    json.dump({'general': gen.to_dict(orient='records'), 'primary': prim.to_dict(orient='records')},
              f, separators=(',', ':'))
    f.write(';')
print(f"mismatch_data.js: {len(gen)} general, {len(prim)} primary")
