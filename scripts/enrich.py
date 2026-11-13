"""공통: 전력원 분류, 예정일 숫자화, 지연 개월 계산"""
import re

# ---- 자동 보강: 전력원 분류 + 예정일 숫자화 + 지연 개월 ----
POWER_RULES = [
    ('nuclear', r'nuclear|smr|reactor|uprate'),
    ('gas', r'\bgas\b|turbine|thermal|lng|diesel'),
    ('renewable', r'solar|wind|renewable|hydro|geothermal|first solar|nextera'),
    ('battery', r'battery|bess|megapack|storage'),
    ('fuel_cell', r'fuel cell|bloom'),
    ('grid', r'grid|utility|transmission|substation|\bkv\b|connection|pln|tva|ercot|energy|power'),
]


def power_categories(sources):
    cats = []
    for s in sources:
        low = s.lower()
        hit = False
        for cat, pat in POWER_RULES:
            if re.search(pat, low):
                if cat == 'grid' and hit:
                    continue  # 이미 다른 분류에 걸린 문장은 grid로 중복 분류하지 않음
                if cat not in cats:
                    cats.append(cat)
                hit = True
    return cats


SEASON = {'early': 3, 'mid': 6, 'late': 10, 'end': 12, 'h1': 6, 'h2': 12,
          'q1': 3, 'q2': 6, 'q3': 9, 'q4': 12, 'first half': 6, 'second half': 12}


def to_ym(text):
    """'2027-06 ...', 'Mid 2026', 'Late 2027–early 2028', '2028' -> 'YYYY-MM' (첫 번째 날짜 기준)"""
    if not text:
        return None
    m = re.search(r'(20\d\d)-(\d\d)', text)
    if m:
        return f'{m.group(1)}-{m.group(2)}'
    low = text.lower()
    MON = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    m = re.search(r'\b(' + '|'.join(MON) + r')[a-z]*\.?\s+(20\d\d)', low)
    if m:
        return f'{m.group(2)}-{MON.index(m.group(1)) + 1:02d}'
    m = re.search(r'(early|mid|late|end|h1|h2|q1|q2|q3|q4|first half|second half)\s*(?:of\s*)?(20\d\d)', low)
    if m:
        return f'{m.group(2)}-{SEASON[m.group(1)]:02d}'
    m = re.search(r'(20\d\d)\s*(h1|h2|q1|q2|q3|q4)', low)
    if m:
        return f'{m.group(1)}-{SEASON[m.group(2)]:02d}'
    m = re.search(r'\b(20\d\d)\b', low)
    if m:
        return f'{m.group(1)}-12'  # 연도만 있으면 연말로 간주 (보수적)
    return None


def months(a, b):
    ya, ma = map(int, a.split('-'))
    yb, mb = map(int, b.split('-'))
    return (yb - ya) * 12 + (mb - ma)


def enrich(x):
    x = dict(x)
    if not x.get('powerCategories'):
        x['powerCategories'] = power_categories(x.get('powerSources') or [])
    o = x.get('originalTargetYM') or to_ym(x.get('originalTargetDate'))
    c = x.get('currentTargetYM') or to_ym(x.get('currentTargetDate'))
    x['originalTargetYM'], x['currentTargetYM'] = o, c
    x['delayMonths'] = months(o, c) if (o and c) else None
    return x

