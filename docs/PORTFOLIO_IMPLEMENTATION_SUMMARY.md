# 포트폴리오 추천 시스템 구현 요약

## 구현 완료 날짜
2025-10-11

## 구현 개요

Finance 백엔드와 연동하여 사용자 투자 프로필을 받아 맞춤형 주식 포트폴리오를 추천하는 API 시스템을 구현했습니다.

## 구현된 주요 기능

### 1. API 엔드포인트
- `POST /api/v1/portfolio` - 포트폴리오 추천
- `GET /api/v1/portfolio/sectors` - 사용 가능한 섹터 목록 조회

### 2. 핵심 컴포넌트

#### 데이터 계층
- **`config/portfolio_stocks.yaml`**: 9개 섹터, 총 38개 종목 데이터
  - 화학 (4개), 제약 (4개), 전기·전자 (4개)
  - 운송장비·부품 (6개), 기타금융 (3개)
  - 기계·장비 (4개), 금속 (6개), 건설 (5개), IT 서비스 (6개)
  

#### 서비스 계층
- **`app/utils/portfolio_stock_loader.py`**: 주식 데이터 로더
  - 섹터별 종목 조회
  - 투자 성향별 최적 종목 선정
  - 안정/고변동/배당주 필터링

- **`app/services/portfolio/portfolio_recommendation_service.py`**: 추천 서비스
  - 투자 성향별 자산 배분 (예적금 vs 주식)
  - 관심 섹터 기반 종목 선정
  - 추천 이유 자동 생성

#### API 계층
- **`app/routers/portfolio.py`**: FastAPI 라우터
- **`app/schemas/portfolio_schema.py`**: Pydantic 스키마

## 추천 로직

### 자산 배분 규칙
| 투자 성향 | 예적금 | 주식 |
|----------|-------|------|
| 안정형 | 80% | 20% |
| 안정추구형 | 60% | 40% |
| 위험중립형 | 50% | 50% |
| 적극투자형 | 30% | 70% |
| 공격투자형 | 20% | 80% |

### 종목 선정 전략

**안정형/안정추구형**
- 시가총액 상위 + 안정 특성
- 배당주 우선
- 저변동성

**적극투자형/공격투자형**
- 시가총액 상위 + 고변동
- 성장 가능성 중시
- 수익 기회 우선

## 테스트 결과

### 유닛 테스트 (✅ 통과)
```bash
./venv/bin/python tests/test_portfolio_api.py
```

**테스트 항목:**
1. 주식 데이터 로더 기능 검증
2. 포트폴리오 추천 서비스 검증
   - 안정형 투자자
   - 공격투자형 투자자
   - 관심 섹터 없음 (기본 추천)
3. API 응답 형식 검증
4. 비율 합계 검증 (100% 일치 확인)

**테스트 결과 예시:**
```
[안정형 투자자]
✓ 예적금 비율: 80%
✓ 추천 종목: 삼성전자 (8%), KB금융 (6%), 삼성바이오로직스 (6%)

[공격투자형 투자자]
✓ 예적금 비율: 20%
✓ 추천 종목: 카카오 (28%), SK하이닉스 (26%), 삼성바이오로직스 (26%)
```

## 파일 구조

```
BE-LLM/
├── config/
│   └── portfolio_stocks.yaml              # 주식 데이터 (신규)
│
├── app/
│   ├── main.py                            # 라우터 등록 (수정)
│   ├── routers/
│   │   └── portfolio.py                   # API 라우터 (신규)
│   ├── schemas/
│   │   └── portfolio_schema.py            # 스키마 (신규)
│   ├── services/
│   │   └── portfolio/
│   │       ├── portfolio_advisor.py       # 기존 (유지)
│   │       └── portfolio_recommendation_service.py  # 추천 서비스 (신규)
│   └── utils/
│       └── portfolio_stock_loader.py      # 데이터 로더 (신규)
│
├── tests/
│   ├── test_portfolio_api.py              # 유닛 테스트 (신규)
│   └── test_portfolio_endpoint.sh         # API 테스트 스크립트 (신규)
│
└── docs/
    ├── PORTFOLIO_API_GUIDE.md             # API 가이드 (신규)
    └── PORTFOLIO_IMPLEMENTATION_SUMMARY.md # 이 파일 (신규)
```

## API 사용 예시

### Request
```bash
curl -X POST http://localhost:8000/api/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 1,
    "userId": "user123",
    "investmentProfile": "안정형",
    "availableAssets": 10000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "기타금융", "제약"]
  }'
```

### Response
```json
{
  "timestamp": "2025-10-11T09:05:42.892559Z",
  "code": "SUCCESS",
  "message": "포트폴리오 추천 성공",
  "result": {
    "portfolioId": 1,
    "userId": "user123",
    "recommendedStocks": [
      {
        "stockId": "005930",
        "stockName": "삼성전자",
        "allocationPct": 8,
        "sectorName": "전기·전자",
        "reason": "시가총액 상위 기업으로 안정적인 투자처입니다..."
      },
      {
        "stockId": "105560",
        "stockName": "KB금융",
        "allocationPct": 6,
        "sectorName": "기타금융",
        "reason": "금융 섹터의 대표 기업으로 안정적인 배당 수익..."
      }
    ],
    "allocationSavings": 80,
    "createdAt": "2025-10-11T09:05:42.892559Z",
    "updatedAt": "2025-10-11T09:05:42.892559Z"
  }
}
```

## 검증 사항

- ✅ Finance 백엔드 요청 형식 준수
- ✅ 응답 형식 일치 (timestamp, code, message, result)
- ✅ 예적금 + 주식 비율 합계 100% 보장
- ✅ 섹터별 종목 매핑 정확성
- ✅ 투자 성향별 추천 로직 작동
- ✅ 추천 이유 자동 생성
- ✅ 에러 처리 및 응답

## 다음 단계

1. **서버 실행 및 테스트**
   ```bash
   ./venv/bin/python run_server.py
   ```

2. **엔드포인트 테스트**
   ```bash
   ./tests/test_portfolio_endpoint.sh
   ```

3. **프런트엔드 연동**
   - API 엔드포인트: `POST /api/v1/portfolio`
   - 요청/응답 형식은 `docs/PORTFOLIO_API_GUIDE.md` 참조

## 주요 특징

1. **유연한 섹터 선택**: 사용자가 관심 섹터를 선택하지 않아도 자동으로 적절한 섹터 선정
2. **투자 성향 기반 최적화**: 각 투자 성향에 맞는 종목 특성 고려
3. **상세한 추천 이유**: 각 종목에 대한 맞춤형 추천 이유 제공
4. **확장 가능한 구조**: 새로운 종목 추가는 YAML 파일 수정만으로 가능

## 개선 가능 사항

- 실시간 주가 정보 연동
- 과거 수익률 기반 추천
- 포트폴리오 리밸런싱
- 백테스팅 기능
- 사용자별 포트폴리오 히스토리

## 참고 문서

- 상세 API 가이드: `docs/PORTFOLIO_API_GUIDE.md`
- 테스트 파일: `tests/test_portfolio_api.py`
- 주식 데이터: `config/portfolio_stocks.yaml`

