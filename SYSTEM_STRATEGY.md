# 🎯 시스템 전략 문서

## 📋 뉴스 및 분석 전략

### 핵심 원칙

#### 1. 뉴스 요청 → Google RSS 실시간
**모든 뉴스 관련 요청은 Google RSS에서 실시간으로 가져와 번역하여 제공**

**예시**:
- ✅ "삼성전자 뉴스 알려줘" → Google RSS 검색 + 번역
- ✅ "최신 금융 뉴스" → Google RSS 검색 + 번역
- ✅ "Apple stock news" → Google RSS 검색 + 번역

**구현**:
- `news_service.get_comprehensive_news()` → Google RSS 우선
- 실시간 검색, 자동 번역 (deep-translator)
- 기존 RSS (Naver/Daum)는 폴백용

---

#### 2. 분석/판단 요청 → 매일경제 Neo4j KG 컨텍스트
**분석 및 판단 시에는 매일경제 지식그래프를 컨텍스트로 활용**

**예시**:
- ✅ "삼성전자 투자 분석해줘" → KG에서 관련 기사 컨텍스트 제공
- ✅ "최근 반도체 시장 전망은?" → KG에서 배경 지식 제공
- ✅ "카카오 매수 타이밍은?" → KG에서 시장 동향 컨텍스트

**구현**:
- `news_service.get_analysis_context_from_kg()` → 컨텍스트 생성
- `analysis_service.get_investment_recommendation_with_context()` → KG 기반 분석
- 매일경제 250개 기사 (경제, 정치, 증권, 국제, 헤드라인)

---

## 🏗️ 아키텍처 구조

### 뉴스 서비스 계층

```
사용자 요청
    ↓
쿼리 분류 (query_classifier)
    ↓
┌─────────────────┬─────────────────┐
│   뉴스 요청     │   분석 요청     │
└─────────────────┴─────────────────┘
         ↓                   ↓
   Google RSS          매일경제 KG
   (실시간 검색)       (컨텍스트 제공)
         ↓                   ↓
      번역 (KO)         임베딩 검색
         ↓                   ↓
   뉴스 리스트         분석 컨텍스트
         ↓                   ↓
      사용자 ← ─ ─ ─ ─ ─ → LLM 분석
```

### 데이터 흐름

#### 뉴스 요청 플로우
```
1. 사용자: "삼성전자 뉴스 알려줘"
2. query_classifier: query_type = "news"
3. news_service.get_comprehensive_news("삼성전자")
   ├─ Google RSS 검색 (5개)
   ├─ 번역 (영어 → 한국어)
   ├─ 기존 RSS 폴백 (필요시)
   └─ 중복 제거 + 정렬
4. 응답: 실시간 뉴스 리스트
```

#### 분석 요청 플로우
```
1. 사용자: "삼성전자 투자 분석해줘"
2. query_classifier: query_type = "analysis"
3. financial_data_service.get_stock_data("삼성전자")
4. news_service.get_analysis_context_from_kg("삼성전자")
   ├─ 매일경제 KG 임베딩 검색 (3개)
   └─ 컨텍스트 문자열 생성
5. analysis_service.get_investment_recommendation_with_context(data, context)
   ├─ 기본 분석 (PER, 거래량, 추세)
   ├─ KG 컨텍스트 결합
   └─ LLM 종합 분석
6. 응답: 투자 의견 + 참고 자료
```

---

## 🔧 주요 컴포넌트

### 1. NewsService (`news_service.py`)

**메서드**:
- `get_comprehensive_news(query)`: 실시간 뉴스 검색 (Google RSS 우선)
- `get_mk_news_with_embedding(query)`: 매일경제 KG 컨텍스트 검색 (분석용)
- `get_analysis_context_from_kg(query)`: 분석용 컨텍스트 문자열 생성

**전략**:
- 뉴스 요청 → Google RSS
- 분석 요청 → 매일경제 KG

### 2. AnalysisService (`analysis_service.py`)

**메서드**:
- `analyze_financial_data(data)`: 기본 금융 데이터 분석
- `get_investment_recommendation(data)`: 기본 투자 추천
- `get_investment_recommendation_with_context(data, query)`: KG 컨텍스트 기반 투자 추천 (신규)

**전략**:
- 분석 시 매일경제 KG 컨텍스트 자동 결합

### 3. MKKnowledgeGraphService (`mk_rss_scraper.py`)

**역할**:
- 매일경제 RSS 수집 (5개 카테고리)
- KF-DeBERTa 임베딩 생성
- Neo4j 저장 및 검색

**데이터**:
- 총 250개 기사 (각 카테고리 50개)
- 임베딩: `kakaobank/kf-deberta-base`
- 저장: Neo4j Article 노드

### 4. GoogleRSSTranslator (`google_rss_translator.py`)

**역할**:
- Google RSS 실시간 검색
- deep-translator로 자동 번역
- 최신순 정렬

**특징**:
- 실시간 검색 (캐싱 없음)
- 다국어 지원 (영어 → 한국어)

---

## 📊 데이터 소스

| 소스 | 용도 | 업데이트 | 특징 |
|------|------|----------|------|
| **Google RSS** | 뉴스 요청 | 실시간 | 다국어, 번역 지원 |
| **매일경제 Neo4j** | 분석 컨텍스트 | 수동 | 임베딩 검색, 한국 금융 특화 |
| **Naver/Daum RSS** | 폴백 | 실시간 | 한국어 전용 |
| **ChromaDB** | 금융 지식 | 정적 | RAG 기반 Q&A |

---

## 🎯 사용 시나리오

### 시나리오 1: 뉴스 조회
```
사용자: "삼성전자 최신 뉴스 알려줘"

처리:
1. query_type = "news"
2. Google RSS 검색: "삼성전자"
3. 5개 뉴스 수집 + 번역
4. 응답: 실시간 뉴스 리스트

매일경제 KG: 사용 안 함 ❌
```

### 시나리오 2: 투자 분석
```
사용자: "삼성전자 투자 분석해줘"

처리:
1. query_type = "analysis"
2. 주가 데이터 조회
3. 매일경제 KG 컨텍스트 검색 (3개 기사)
4. 기본 분석 + KG 컨텍스트 결합
5. LLM 종합 분석
6. 응답: 투자 의견 + 참고 자료

Google RSS: 사용 안 함 ❌
매일경제 KG: 컨텍스트로 사용 ✅
```

### 시나리오 3: 시장 전망
```
사용자: "최근 반도체 시장 전망은?"

처리:
1. query_type = "analysis"
2. 매일경제 KG 컨텍스트 검색: "반도체 시장"
3. 관련 기사 3개 추출
4. LLM 종합 분석
5. 응답: 시장 전망 + 참고 자료

Google RSS: 사용 안 함 ❌
매일경제 KG: 컨텍스트로 사용 ✅
```

### 시나리오 4: 영문 뉴스
```
사용자: "Apple stock news"

처리:
1. query_type = "news"
2. Google RSS 검색: "Apple stock news"
3. 영문 뉴스 수집
4. 한국어 번역
5. 응답: 번역된 뉴스 리스트

매일경제 KG: 사용 안 함 ❌
```

---

## 🚀 테스트 가이드

### 뉴스 요청 테스트
```bash
python chat_terminal.py

💬 당신: 삼성전자 뉴스 알려줘
# 예상: Google RSS 검색 → 번역 → 뉴스 리스트

💬 당신: Apple stock news
# 예상: Google RSS 검색 → 번역 → 뉴스 리스트
```

### 분석 요청 테스트
```bash
python chat_terminal.py

💬 당신: 삼성전자 투자 분석해줘
# 예상: 주가 데이터 + 매일경제 KG 컨텍스트 → 종합 분석

💬 당신: 최근 반도체 시장 전망은?
# 예상: 매일경제 KG 컨텍스트 → 시장 전망
```

---

## 📝 개발 체크리스트

- [x] Google RSS 실시간 검색 구현
- [x] deep-translator 번역 통합
- [x] 매일경제 Neo4j KG 구축 (250개 기사)
- [x] KF-DeBERTa 임베딩 생성
- [x] `get_analysis_context_from_kg()` 구현
- [x] `get_investment_recommendation_with_context()` 구현
- [x] `get_comprehensive_news()` 전략 변경 (Google RSS 우선)
- [x] 뉴스 vs 분석 전략 분리
- [ ] 성능 테스트 (응답 시간, 정확도)
- [ ] Redis 캐싱 도입 (TODO)

---

**작성일**: 2025-10-05
**버전**: 2.0.0
**작성자**: AI Assistant
