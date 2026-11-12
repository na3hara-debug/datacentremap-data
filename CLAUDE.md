# datacentremap-data — 작업 규칙

Global Data Centre Map 앱(Android)의 데이터 저장소. 앱은 `data/datacentres.json`을 읽는다.

## 파일
- `data/curated.json` — 직접 조사 레코드. **사람/Claude가 편집하는 유일한 데이터 파일.**
- `data/datacentres.json` — 자동 생성 (curated + Epoch AI). 직접 편집 금지. curated.json을 push하면 GitHub Actions가 재생성한다.
- `scripts/convert_epoch.py` — Epoch CSV + curated → datacentres.json

## 포함 기준
캠퍼스 전체 용량 → 없으면 그리드 연결 용량 → 없으면 IT 부하가 100MW 이상. 용량 미공개라도 공식 발표상 초대형이 분명하면 포함 가능.

## 레코드 스키마 (curated.json 배열 원소)
id(지역접두-이름, 예 au-nextdc-s4), name, operator, tenant?(선택), country(English country name), location, latitude, longitude,
locationApproximate(true), status(announced|permitting|approved|construction|operational|on_hold|cancelled), statusNote(English),
facilityType("AI training"|"AI inference"|AI (용도 미구분)|"Hyperscale cloud"|Colocation|Enterprise — 공식 자료가 학습/추론을 밝힌 경우에만 구분), itLoad/campusPower/gridConnection/operationalNow: {mw, quality(confirmed|reported|estimate), note?} 또는 null,
investment: {text, quality} 또는 null, powerSources: string[], originalTargetDate, currentTargetDate (문자열 또는 null),
investors?: string[] (지분 투자자·금융 제공자 회사명, 출처로 확인된 경우만. 예: ["Blackstone","Brookfield"]. 운영사·임차인·장비 공급사는 넣지 않음),
sources: [{title,url}] (최소 1개, 실제 확인한 URL만), lastVerified: YYYY-MM-DD

## 데이터 품질 규칙 (반드시 준수)
- 지어내지 않는다. 확인 안 된 값은 null(앱에서 "미공개"로 표시).
- confirmed = 회사·정부 공식 발표, reported = 언론·리서치, estimate = 추정.
- MW와 MWh 혼동 금지. IT 부하/캠퍼스/그리드 구분.
- 발표된 프로젝트를 가동중으로 표시하지 않는다.
- 상태가 바뀌면 statusNote에 날짜와 근거, originalTargetDate는 처음 값을 유지하고 currentTargetDate만 갱신(지연 추적).
- Epoch AI 데이터에 이미 있는 시설(대부분 미국 AI 데이터센터)은 curated에 중복 추가하지 않는다. 예외로 이미 curated에 있는 미국 5건(stargate-abilene, meta-hyperion, xai-colossus-1, ms-fairwater-1/2)은 convert_epoch.py의 CURATED_OVERLAP으로 처리됨.
- **All text fields in English** (country names in English, e.g. "Australia", "South Korea"). The app translates UI labels itself; data text stays English.
