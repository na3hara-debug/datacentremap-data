"""주소 → 정확한 좌표. 미국은 US Census Geocoder, 그 외는 OpenStreetMap Nominatim.
결과는 data/geocode-cache.json에 저장해 같은 주소는 다시 조회하지 않음.
근사 좌표에서 40km 이상 떨어진 결과는 오류로 보고 버림.
사용: python3 scripts/geocode.py data/datacentres.json data/geocode-cache.json
"""
import json, math, sys, time, urllib.parse, urllib.request, os

data_p, cache_p = sys.argv[1], sys.argv[2]
UA = 'GlobalDataCentreMap/1.0 (https://github.com/na3hara-debug/datacentremap-data)'
cache = json.load(open(cache_p, encoding='utf-8')) if os.path.exists(cache_p) else {}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def census(addr):
    q = urllib.parse.urlencode({'address': addr, 'benchmark': 'Public_AR_Current', 'format': 'json'})
    res = get('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?' + q)
    m = res.get('result', {}).get('addressMatches', [])
    if m:
        c = m[0]['coordinates']
        return {'lat': c['y'], 'lng': c['x'], 'by': 'US Census Geocoder'}
    return None


def nominatim(addr):
    q = urllib.parse.urlencode({'q': addr, 'format': 'json', 'limit': 1})
    res = get('https://nominatim.openstreetmap.org/search?' + q)
    time.sleep(1.1)  # 사용 정책: 초당 1회
    if res:
        return {'lat': float(res[0]['lat']), 'lng': float(res[0]['lon']), 'by': 'OpenStreetMap Nominatim'}
    return None


def km(a1, o1, a2, o2):
    p = math.pi / 180
    h = 0.5 - math.cos((a2 - a1) * p) / 2 + math.cos(a1 * p) * math.cos(a2 * p) * (1 - math.cos((o2 - o1) * p)) / 2
    return 12742 * math.asin(math.sqrt(h))


payload = json.load(open(data_p, encoding='utf-8'))
done = 0
for r in payload['records']:
    addr = r.get('address')
    if not addr or r.get('coordsVerified'):
        continue  # 직접 확인한 좌표는 그대로
    full = f"{addr}, {r['country']}" if r['country'] not in addr else addr
    if full not in cache:
        try:
            hit = census(addr) if r['country'] == 'United States' else None
            if not hit:
                hit = nominatim(full)
        except Exception as e:
            print('geocode error', r['id'], e, file=sys.stderr)
            continue
        cache[full] = hit
    hit = cache[full]
    if not hit:
        continue
    if km(r['latitude'], r['longitude'], hit['lat'], hit['lng']) > 40:
        print('too far, skipped:', r['id'], file=sys.stderr)
        continue
    r['latitude'], r['longitude'] = round(hit['lat'], 5), round(hit['lng'], 5)
    r['locationApproximate'] = False
    r['locationSource'] = f'Street address ({hit["by"]})'
    done += 1

json.dump(payload, open(data_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(cache, open(cache_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(f'정확 좌표 {done}건', file=sys.stderr)
