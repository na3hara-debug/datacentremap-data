"""photoFile(위키미디어 커먼즈 파일명) → 사진 URL, 촬영자, 라이선스를 커먼즈 API에서 직접 받아옴.
자유 라이선스(CC BY, CC BY-SA, CC0, Public domain)만 허용. 그 외는 사진을 넣지 않음.
사용: python3 scripts/photos.py data/datacentres.json
"""
import json, re, sys, urllib.parse, urllib.request, html

UA = 'GlobalDataCentreMap/1.0 (https://github.com/na3hara-debug/datacentremap-data)'
OK = re.compile(r'^(cc[ -]by(-sa)?[ -][\d.]+.*|cc0.*|public domain.*|pd.*)$', re.I)


def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s or '')).strip()


payload = json.load(open(sys.argv[1], encoding='utf-8'))
want = {r['photoFile']: r for r in payload['records'] if r.get('photoFile')}
info = {}
files = list(want)
for i in range(0, len(files), 40):
    q = urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'prop': 'imageinfo', 'iiprop': 'url|extmetadata',
        'iiurlwidth': 1000, 'titles': '|'.join(files[i:i + 40]),
    })
    req = urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + q, headers={'User-Agent': UA})
    res = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))
    norm = {n['to']: n['from'] for n in res['query'].get('normalized', [])}
    for p in res['query']['pages'].values():
        if 'imageinfo' not in p:
            print('missing file:', p.get('title'), file=sys.stderr)
            continue
        ii = p['imageinfo'][0]
        md = ii.get('extmetadata', {})
        lic = strip(md.get('LicenseShortName', {}).get('value'))
        if not OK.match(lic):
            print('licence not allowed:', p['title'], lic, file=sys.stderr)
            continue
        info[norm.get(p['title'], p['title'])] = {
            'url': ii.get('thumburl') or ii['url'],
            'page': ii['descriptionurl'],
            'author': strip(md.get('Artist', {}).get('value')) or 'Unknown',
            'license': lic,
            'licenseUrl': strip(md.get('LicenseUrl', {}).get('value')) or None,
        }

n = 0
for r in payload['records']:
    f = r.pop('photoFile', None)
    if f and f in info:
        r['photo'] = info[f]
        n += 1
json.dump(payload, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'사진 {n}건', file=sys.stderr)
