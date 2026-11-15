"""위키미디어 커먼즈에서 데이터센터별 자유 라이선스 사진 후보를 찾아 썸네일과 목록을 만든다.
사람(또는 Claude)이 썸네일을 직접 보고 맞는 사진만 overrides.json의 photoFile에 넣는다.
사용: python3 scripts/photo_candidates.py data/datacentres.json out_dir [max_records]
"""
import json, os, re, sys, time, urllib.parse, urllib.request, html

UA = 'GlobalDataCentreMap/1.0 (https://github.com/na3hara-debug/datacentremap-data)'
OK = re.compile(r'^(cc[ -]by(-sa)?[ -][\d.]+.*|cc0.*|public domain.*|pd.*)$', re.I)
data_p, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 60
os.makedirs(out, exist_ok=True)


def api(params):
    q = urllib.parse.urlencode({**params, 'format': 'json'})
    req = urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + q, headers={'User-Agent': UA})
    time.sleep(0.3)
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))


def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s or '')).strip()


def cap(r):
    v = r.get('campusPower') or r.get('gridConnection') or r.get('itLoad')
    return v['mw'] if v else 0


recs = json.load(open(data_p, encoding='utf-8'))['records']
recs = [r for r in recs if not r.get('photo')]
recs.sort(key=cap, reverse=True)
result = {}
for r in recs[:N]:
    op = re.sub(r'\(.*?\)', '', r['operator']).split('/')[0].split(',')[0].strip()
    city = r['location'].split(',')[0].strip()
    queries = [f'"{r["name"]}"', f'{op} data center {city}', f'{op} data centre {city}', f'data center {city}']
    seen, cands = set(), []
    for q in queries:
        try:
            res = api({'action': 'query', 'list': 'search', 'srsearch': q + ' filetype:bitmap', 'srnamespace': 6, 'srlimit': 6})
        except Exception as e:
            print('search error', q, e, file=sys.stderr)
            continue
        for h in res['query']['search']:
            if h['title'] not in seen:
                seen.add(h['title'])
                cands.append(h['title'])
    if not cands:
        continue
    info = api({'action': 'query', 'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'iiurlwidth': 400, 'titles': '|'.join(cands[:12])})
    keep = []
    for p in info['query']['pages'].values():
        if 'imageinfo' not in p:
            continue
        ii = p['imageinfo'][0]
        md = ii.get('extmetadata', {})
        lic = strip(md.get('LicenseShortName', {}).get('value'))
        if not OK.match(lic):
            continue
        idx = len(keep)
        fn = f'{r["id"]}__{idx}.jpg'
        try:
            req = urllib.request.Request(ii['thumburl'], headers={'User-Agent': UA})
            open(os.path.join(out, fn), 'wb').write(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print('thumb error', p['title'], e, file=sys.stderr)
            continue
        keep.append({
            'file': p['title'], 'thumb': fn, 'license': lic,
            'desc': strip(md.get('ImageDescription', {}).get('value'))[:300],
            'date': strip(md.get('DateTimeOriginal', {}).get('value'))[:20],
            'coords': [md.get('GPSLatitude', {}).get('value'), md.get('GPSLongitude', {}).get('value')],
        })
    if keep:
        result[r['id']] = {'name': r['name'], 'location': f'{r["location"]}, {r["country"]}', 'candidates': keep}
json.dump(result, open(os.path.join(out, 'candidates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'후보가 있는 레코드 {len(result)}개', file=sys.stderr)
