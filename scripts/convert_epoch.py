"""Epoch AI 'AI data centers' CSV + 직접 조사(curated.json) -> 앱용 JSON.
사용: python3 scripts/convert_epoch.py <epoch_csv_folder> <output_json> [today YYYY-MM-DD]
결과 파일: {"generatedAt", "count", "attribution", "records": [...]}
"""
import json, re, sys, datetime
import pandas as pd
import zipcodes

src, out = sys.argv[1], sys.argv[2]
TODAY = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
MIN_MW = 100
EPOCH_URL = 'https://epoch.ai/data/ai-data-centers'

# 직접 조사한 레코드와 겹치는 항목은 제외 (직접 조사본 우선)
CURATED_OVERLAP = {'OpenAI Stargate Abilene', 'Colossus 1', 'Microsoft Fairwater Wisconsin', 'Meta Hyperion'}

COUNTRY_KO = {
    'United Arab Emirates': 'UAE',
}

# 우편번호로 찾지 못한 곳: 도시/지역 단위 근사 좌표 (lat, lng, 위치명)
MANUAL = {
    'DayOne Nusajaya': (1.42, 103.64, 'Iskandar Puteri, Johor'),
    'DayOne Kempas': (1.54, 103.71, 'Johor Bahru, Johor'),
    'Google Mesa': (33.35, -111.63, 'Mesa, Arizona'),
    'Google Council Bluffs (East)': (41.23, -95.79, 'Council Bluffs, Iowa'),
    'Bridge Data Centres MY06': (1.70, 103.53, 'Sedenak Tech Park, Johor'),
    'Amazon Madison Mega Site': (32.61, -90.04, 'Canton, Mississippi'),
    'Google Bristow': (38.72, -77.54, 'Bristow, Virginia'),
    'Microsoft Goodyear': (33.38, -112.43, 'Goodyear, Arizona'),
    'Google Kansas City East': (39.17, -94.47, 'Kansas City, Missouri'),
    'Google Omaha': (41.30, -96.10, 'Omaha, Nebraska'),
    'Google The Dalles': (45.63, -121.20, 'The Dalles, Oregon'),
    'Amazon Ridgeland': (32.42, -90.13, 'Ridgeland, Mississippi'),
    'Meta Huntsville': (34.85, -86.68, 'Toney, Alabama'),
    'YTL Johor': (1.66, 103.60, 'Kulai, Johor'),
    'Google Storey County': (39.53, -119.47, 'Storey County, Nevada'),
    'Google Waltham Cross': (51.70, -0.04, 'Cheshunt, England'),
    'VNET Bayin Ulanqab': (41.00, 113.10, 'Ulanqab, Inner Mongolia'),
    'Google Arcola': (38.97, -77.53, 'Sterling, Virginia'),
    'Meta Sarpy': (41.08, -96.13, 'Springfield, Nebraska'),
    'CoreWeave Chester VA': (37.36, -77.39, 'Chester, Virginia'),
    'Oracle Batam': (1.08, 104.03, 'Batam'),
    'Huawei Horinger': (40.38, 111.82, 'Horinger, Inner Mongolia'),
    'Microsoft SAT40': (29.38, -98.68, 'San Antonio, Texas'),
    'Microsoft-Nebius New Jersey': (39.45, -75.03, 'Vineland, New Jersey'),
    'Huawei Wuhu': (31.33, 118.43, 'Wuhu, Anhui'),
    'CoreWeave Norway': (58.30, 7.80, 'Øvrebø'),
    'Nebius Mantsala': (60.63, 25.32, 'Mäntsälä'),
    'Envision Galaxy Ulanqab': (41.03, 113.15, 'Ulanqab, Inner Mongolia'),
    'Southgate Melbourne': (-37.82, 144.84, 'Brooklyn, Melbourne'),
    'Stream Phoenix': (33.42, -112.36, 'Goodyear, Arizona'),
    'Alibaba Zhangbei': (41.15, 114.70, 'Zhangbei, Hebei'),
    'Start Campus Sines Data Campus': (37.95, -8.86, 'Sines'),
    'Nscale Keflavik': (63.97, -22.60, 'Reykjanesbær'),
    'Anthropic Barber Lake': (32.39, -100.86, 'Colorado City, Texas'),
    'CoreWeave Lancaster Greenfield site': (40.04, -76.31, 'Lancaster, Pennsylvania'),
    'EcoDataCenter 2': (60.48, 15.43, 'Borlänge'),
    'Meta Bowling Green': (41.38, -83.65, 'Bowling Green, Ohio'),
    'Microsoft Narvik Norway': (68.44, 17.43, 'Narvik'),
    'OpenAI Stargate Michigan': (42.17, -83.78, 'Saline Township, Michigan'),
    'OpenAI Stargate Milam': (30.79, -96.98, 'Milam County, Texas'),
    'OpenAI Stargate New Mexico': (31.86, -106.65, 'Doña Ana County, New Mexico'),
    'OpenAI Stargate UAE': (24.30, 54.60, 'Abu Dhabi'),
    'OpenAI Stargate Wisconsin': (43.39, -87.87, 'Port Washington, Wisconsin'),
    'OpenAI Stargate Shackelford': (32.73, -99.30, 'Shackelford County, Texas'),
    'AWS New Albany': (40.08, -82.79, 'New Albany, Ohio'),
    'Google Papillion': (41.13, -96.07, 'Papillion, Nebraska'),
}

STATE = {'AL':'Alabama','AZ':'Arizona','GA':'Georgia','IA':'Iowa','ID':'Idaho','IN':'Indiana','LA':'Louisiana','MN':'Minnesota',
 'MS':'Mississippi','NC':'North Carolina','ND':'North Dakota','NE':'Nebraska','NJ':'New Jersey','NM':'New Mexico','NV':'Nevada',
 'NY':'New York','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','SC':'South Carolina','TN':'Tennessee','TX':'Texas',
 'UT':'Utah','VA':'Virginia','WI':'Wisconsin','WY':'Wyoming','MI':'Michigan','MO':'Missouri','KY':'Kentucky','IL':'Illinois','AR':'Arkansas'}


def clean_party(s):
    if not isinstance(s, str) or not s.strip():
        return None
    parts = []
    for p in s.split(','):
        p = p.strip()
        if not p:
            continue
        name = re.sub(r'\s*#\w+', '', p).strip()
        if '#speculative' in p:
            name += ' (speculative)'
        elif '#likely' in p:
            name += ' (likely)'
        parts.append(name)
    return ', '.join(dict.fromkeys(parts)) or None


def links(md):
    res = []
    for t, u in re.findall(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', str(md)):
        res.append({'title': t.strip(), 'url': u.strip()})
    return res[:6]


def ym(date):
    return date[:7]


def fmt_cost(b):
    eok = round(b * 10)
    return f'About US${b:,.1f}bn (total capex incl. chips, 2025 USD)'


dc = pd.read_csv(f'{src}/data_centers.csv')
tl = pd.read_csv(f'{src}/data_center_timelines.csv')
tl = tl.sort_values('Date')

records = []
skipped_small = []
for _, r in dc.iterrows():
    name = r['Name']
    if name in CURATED_OVERLAP:
        continue
    t = tl[tl['Data center'] == name]
    if t.empty:
        continue
    max_p = float(t['Power (MW)'].max())
    if max_p < MIN_MW:
        skipped_small.append(name)
        continue
    max_it = float(t['IT power (MW)'].max())
    past = t[t['Date'] <= TODAY]
    cur_p = float(past['Power (MW)'].iloc[-1]) if not past.empty else 0.0
    full_date = t[t['Power (MW)'] >= max_p * 0.999]['Date'].iloc[0]
    max_cost = float(t['Total capital cost (2025 USD billions)'].max())

    # 좌표
    lat = lng = None
    loc = None
    addr = str(r['Address']) if isinstance(r['Address'], str) else ''
    if name in MANUAL:
        lat, lng, loc = MANUAL[name]
    else:
        # 주소 끝부분의 '주 약자 + 우편번호'를 사용 (번지수 오인 방지)
        m = re.findall(r'\b([A-Z]{2})\s+(\d{5})(?:-\d{4})?\b', addr)
        z = zipcodes.matching(m[-1][1]) if m else []
        if z and z[0]['state'] != m[-1][0]:
            z = []
        if z:
            lat, lng = float(z[0]['lat']), float(z[0]['long'])
            loc = f"{z[0]['city'].title()}, {STATE.get(z[0]['state'], z[0]['state'])}"
    if lat is None:
        print('좌표 없음:', name, addr, file=sys.stderr)
        continue

    if cur_p > 0:
        status = 'operational'
        note = 'Partially operational' if cur_p < max_p * 0.95 else 'Fully operational'
    else:
        status = 'construction'
        note = 'Under construction'
    note += ' (per Epoch AI satellite & permit analysis)'

    target = f"{ym(full_date)} — {'full capacity reached' if full_date <= TODAY else 'full capacity expected'} (Epoch estimate)"

    energy = r['Energy companies']
    power_sources = [f'Utility: {e.strip()}' for e in str(energy).split(',')] if isinstance(energy, str) else []

    srcs = [{'title': 'Epoch AI — AI Data Centers (CC BY 4.0)', 'url': EPOCH_URL}] + links(r['Selected Sources'])

    records.append({
        'id': 'epoch-' + re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
        'name': name,
        'operator': clean_party(r['Owner']) or 'Not disclosed',
        'tenant': clean_party(r['Users']),
        'country': COUNTRY_KO.get(r['Country'], r['Country']),
        'location': loc,
        'latitude': round(lat, 3),
        'longitude': round(lng, 3),
        'locationApproximate': True,
        'status': status,
        'statusNote': note,
        'facilityType': 'AI',
        'itLoad': {'mw': round(max_it), 'quality': 'estimate', 'note': 'IT load at full build-out (Epoch AI estimate)'} if max_it > 0 else None,
        'campusPower': {'mw': round(max_p), 'quality': 'estimate', 'note': 'Total facility power at full build-out (Epoch AI estimate)'},
        'gridConnection': None,
        'operationalNow': {'mw': round(cur_p), 'quality': 'estimate', 'note': f'Current operating power (Epoch AI estimate, as of {past["Date"].iloc[-1]})'} if cur_p > 0 else None,
        'investment': {'text': fmt_cost(max_cost), 'quality': 'estimate'} if max_cost > 0 else None,
        'powerSources': power_sources,
        'originalTargetDate': None,
        'currentTargetDate': target,
        'sources': srcs,
        'lastVerified': TODAY,
        'dataSource': 'Epoch AI',
    })

records.sort(key=lambda x: -x['campusPower']['mw'])

import os
curated_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'curated.json')
curated = json.load(open(curated_path, encoding='utf-8'))
allrec = curated + records
payload = {
    'generatedAt': TODAY,
    'count': len(allrec),
    'attribution': 'Epoch AI, "AI data centers" (CC BY 4.0), https://epoch.ai/data/ai-data-centers — transformed. Curated records cite their own sources.',
    'records': allrec,
}
json.dump(payload, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'변환 {len(records)}건, 100MW 미만 제외 {len(skipped_small)}건', file=sys.stderr)
