# 포트폴리오 추천 API 가이드

## 개요

사용자의 투자 프로필을 기반으로 맞춤형 주식 포트폴리오를 추천하는 API입니다.

## API 엔드포인트

### 1. 포트폴리오 추천

**Endpoint:** `POST /api/v1/portfolio`

**설명:** 사용자의 투자 프로필을 받아 맞춤형 포트폴리오를 추천합니다.

#### Request Body

```json
{
  "profileId": 1,
  "userId": "user123",
  "investmentProfile": "안정형",
  "availableAssets": 10000000,
  "lossTolerance": "30",
  "financialKnowledge": "보통",
  "expectedProfit": "150",
  "investmentGoal": "학비",
  "interestedSectors": [
    "전기·전자",
    "기타금융",
    "화학"
  ]
}
```

#### Request Parameters

| 필드 | 타입 | 필수 | 설명 | 가능한 값 |
|------|------|------|------|----------|
| profileId | integer | O | 프로필 ID | - |
| userId | string | O | 사용자 ID | - |
| investmentProfile | string | O | 투자 성향 | 안정형, 안정추구형, 위험중립형, 적극투자형, 공격투자형 |
| availableAssets | integer | O | 투자 가능 자산 | - |
| lossTolerance | string | O | 감당 가능 손실 (원금의 %) | 10, 30, 50, 70, 100 |
| financialKnowledge | string | O | 금융 이해도 | 매우 낮음, 낮음, 보통, 높음, 매우 높음 |
| expectedProfit | string | O | 기대 이익 (%) | 150, 200, 250, 300 이상 |
| investmentGoal | string | O | 투자 목표 | 학비, 생활비, 주택마련, 자산증식, 채무상환 |
| interestedSectors | array[string] | O | 관심 섹터 목록 | 화학, 제약, 전기·전자, 운송장비·부품, 기타금융, 기계·장비, 금속, 건설, IT 서비스 |

#### Response

```json
{
  "timestamp": "2025-10-10T04:31:48.133Z",
  "code": "SUCCESS",
  "message": "포트폴리오 추천 성공",
  "result": {
    "portfolioId": 1,
    "userId": "user123",
    "recommendedStocks": [
      {
        "stockId": "005930",
        "stockName": "삼성전자",
        "allocationPct": 15,
        "sectorName": "전기·전자",
        "reason": "시가총액 상위 기업으로 안정적인 투자처입니다. 귀하의 안정 지향적 투자 성향에 적합합니다."
      },
      {
        "stockId": "105560",
        "stockName": "KB금융",
        "allocationPct": 5,
        "sectorName": "기타금융",
        "reason": "금융 섹터의 대표 기업으로 안정적인 배당 수익을 기대할 수 있습니다."
      }
    ],
    "allocationSavings": 80,
    "createdAt": "2025-01-01T10:30:00",
    "updatedAt": "2025-01-01T15:45:00"
  }
}
```

#### Response Fields

| 필드 | 타입 | 설명 |
|------|------|------|
| timestamp | string | 응답 시간 (ISO 8601) |
| code | string | 응답 코드 (SUCCESS, ERROR 등) |
| message | string | 응답 메시지 |
| result.portfolioId | integer | 포트폴리오 ID |
| result.userId | string | 사용자 ID |
| result.recommendedStocks | array | 추천 주식 목록 |
| result.recommendedStocks[].stockId | string | 주식 종목 코드 |
| result.recommendedStocks[].stockName | string | 주식 종목명 |
| result.recommendedStocks[].allocationPct | integer | 투자 비중 (%) |
| result.recommendedStocks[].sectorName | string | 섹터명 |
| result.recommendedStocks[].reason | string | 추천 이유 |
| result.allocationSavings | integer | 예적금 비율 (%) |
| result.createdAt | string | 생성 시간 |
| result.updatedAt | string | 수정 시간 |

### 2. 섹터 목록 조회

**Endpoint:** `GET /api/v1/portfolio/sectors`

**설명:** 포트폴리오 추천에 사용 가능한 모든 섹터 목록을 반환합니다.

#### Response

```json
{
  "timestamp": "2025-10-10T04:31:48.133Z",
  "code": "SUCCESS",
  "message": "섹터 목록 조회 성공",
  "result": {
    "sectors": [
      "IT 서비스",
      "건설",
      "금속",
      "기계·장비",
      "기타금융",
      "운송장비·부품",
      "전기·전자",
      "제약",
      "화학"
    ],
    "count": 9
  }
}
```

## 포트폴리오 추천 로직

### 1. 자산 배분 규칙

투자 성향에 따라 예적금과 주식의 비율이 자동으로 결정됩니다:

| 투자 성향 | 예적금 비율 | 주식 비율 |
|----------|-----------|----------|
| 안정형 | 80% | 20% |
| 안정추구형 | 60% | 40% |
| 위험중립형 | 50% | 50% |
| 적극투자형 | 30% | 70% |
| 공격투자형 | 20% | 80% |

### 2. 주식 선정 전략

#### 안정형 / 안정추구형
- 시가총액 상위 종목 우선
- "안정" 특성 보유 종목 선호
- 배당주 포함
- 저변동성 종목 위주

#### 위험중립형
- 시가총액 상위 종목 중심
- 다양한 특성 고려
- 균형잡힌 포트폴리오 구성

#### 적극투자형 / 공격투자형
- 고변동성 종목 포함
- 성장 가능성 높은 종목 선호
- 시가총액 상위 + 고변동 조합

### 3. 섹터 다양화

- 사용자가 선택한 관심 섹터를 우선 고려
- 관심 섹터가 없는 경우 투자 성향에 맞는 기본 섹터 선정
- 최대 5개 종목으로 분산 투자
- 각 섹터에서 1-2개 대표 종목 선정

### 4. 추천 이유 생성

각 종목에 대해 다음 요소를 고려하여 추천 이유를 생성합니다:
- 섹터 특성
- 시가총액 및 시장 지위
- 안정성 / 변동성
- 배당 여부
- 사용자의 투자 성향 부합도

## 데이터 구조

### 주식 데이터

포트폴리오 추천에 사용되는 주식 데이터는 `config/portfolio_stocks.yaml` 파일에 정의되어 있습니다.

각 주식은 다음 정보를 포함합니다:
- 섹터명
- 종목명
- 종목 코드
- 시가총액
- 현재가
- 최고가 / 최저가
- 특성 (시가총액 상위, 안정, 고변동, 배당주)

### 지원 섹터

총 9개 섹터를 지원합니다:
1. 화학
2. 제약
3. 전기·전자
4. 운송장비·부품
5. 기타금융
6. 기계·장비
7. 금속
8. 건설
9. IT 서비스

## 테스트

### 유닛 테스트 실행

```bash
./venv/bin/python tests/test_portfolio_api.py
```

### API 엔드포인트 테스트

서버가 실행 중인 상태에서:

```bash
./tests/test_portfolio_endpoint.sh
```

또는 curl을 직접 사용:

```bash
curl -X POST http://localhost:8000/api/v1/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 1,
    "userId": "test_user",
    "investmentProfile": "안정형",
    "availableAssets": 10000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "기타금융"]
  }'
```

## 에러 처리

### 에러 응답 형식

```json
{
  "timestamp": "2025-10-10T04:31:48.133Z",
  "code": "INTERNAL_ERROR",
  "message": "포트폴리오 추천 중 오류가 발생했습니다: 상세 오류 메시지"
}
```

### HTTP 상태 코드

- `200 OK`: 성공
- `422 Unprocessable Entity`: 잘못된 요청 파라미터
- `500 Internal Server Error`: 서버 내부 오류

## 주요 파일 구조

```
app/
├── routers/
│   └── portfolio.py              # API 라우터
├── schemas/
│   └── portfolio_schema.py       # Pydantic 스키마
├── services/
│   └── portfolio/
│       ├── portfolio_advisor.py  # 기존 어드바이저 (섹터 기반)
│       └── portfolio_recommendation_service.py  # 새 추천 서비스
└── utils/
    └── portfolio_stock_loader.py  # 주식 데이터 로더

config/
└── portfolio_stocks.yaml          # 주식 데이터

tests/
├── test_portfolio_api.py          # 유닛 테스트
└── test_portfolio_endpoint.sh     # API 테스트 스크립트
```

## 주의사항

1. **비율 합계**: 추천된 주식들의 `allocationPct` 합계 + `allocationSavings`는 항상 100이 되어야 합니다.

2. **섹터 선택**: `interestedSectors`는 빈 배열일 수 있으며, 이 경우 투자 성향에 맞는 기본 섹터가 자동 선정됩니다.

3. **종목 수**: 최소 1개, 최대 5개의 종목이 추천됩니다.

4. **데이터 업데이트**: 주식 데이터를 추가/수정하려면 `config/portfolio_stocks.yaml` 파일을 편집하면 됩니다.

## 향후 개선 사항

- [ ] 실시간 주가 정보 연동
- [ ] 과거 수익률 데이터 활용
- [ ] 시장 상황에 따른 동적 비율 조정
- [ ] 사용자별 포트폴리오 히스토리 관리
- [ ] 포트폴리오 리밸런싱 추천
- [ ] 백테스팅 기능

