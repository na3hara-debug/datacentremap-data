"""이전 datacentres.json과 새 파일을 비교해 data/changes.json(변경 이력)에 추가.
사용: python3 scripts/diff_changes.py <prev_json> <new_json> <changes_json> <date>
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrich import to_ym  # noqa: E402

prev_p, new_p, ch_p, date = sys.argv[1:5]
KEEP = 300  # 최근 변경 300건 보관


def load(p):
    try:
        return {r['id']: r for r in json.load(open(p, encoding='utf-8'))['records']}
    except Exception:
        return None


def cap(r):
    v = r.get('campusPower') or r.get('gridConnection') or r.get('itLoad')
    return v['mw'] if v else None


prev, new = load(prev_p), load(new_p)
log = json.load(open(ch_p, encoding='utf-8')) if os.path.exists(ch_p) else {'changes': []}
items = []
if prev is not None and new is not None:
    for i, r in new.items():
        base = {'date': date, 'id': i, 'name': r['name'], 'country': r['country']}
        if i not in prev:
            items.append({**base, 'type': 'new', 'to': r['status']})
            continue
        p = prev[i]
        if p['status'] != r['status']:
            items.append({**base, 'type': 'status', 'from': p['status'], 'to': r['status']})
        pa, pb = to_ym(p.get('currentTargetDate')), to_ym(r.get('currentTargetDate'))
        if pa and pb and pa != pb:
            items.append({**base, 'type': 'timeline', 'from': p.get('currentTargetDate'), 'to': r.get('currentTargetDate')})
        a, b = cap(p), cap(r)
        if a and b and abs(a - b) >= max(50, a * 0.1):
            items.append({**base, 'type': 'capacity', 'from': a, 'to': b})
    for i, p in prev.items():
        if i not in new:
            items.append({'date': date, 'id': i, 'name': p['name'], 'country': p['country'], 'type': 'removed'})

log['changes'] = (items + log['changes'])[:KEEP]
log['updatedAt'] = date
json.dump(log, open(ch_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'변경 {len(items)}건 기록', file=sys.stderr)
