# Global Data Centre Map — Data

Global Data Centre Map 앱이 사용하는 데이터 저장소입니다.

- `data/datacentres.json` — 앱이 읽는 최종 데이터 (자동 생성, 직접 수정하지 마세요)
- `data/curated.json` — 직접 조사한 레코드 (수동 관리)
- `scripts/convert_epoch.py` — Epoch AI CSV를 앱 형식으로 변환
- `.github/workflows/update-data.yml` — 매주 자동 업데이트

## 포함 기준
캠퍼스 전체 용량(없으면 그리드 연결 용량) 100MW 이상.

## Attribution
Includes data from Epoch AI, "AI data centers", https://epoch.ai/data/ai-data-centers,
licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Data has been transformed
(filtered to ≥100 MW, status/field mapping, approximate geocoding).
