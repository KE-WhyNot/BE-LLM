# 🌳 금융 챗봇 워크플로우 트리 구조 (Intelligent Workflow)

## 📥 사용자 쿼리 입력
```
    │
    ▼
┌─────────────────────────────────────────────────┐
│   🤖 QueryAnalyzerAgent (쿼리 분석)              │
│   - LLM이 쿼리 의도, 복잡도, 필요 서비스 분석    │
│   - 신뢰도 점수 계산                             │
│   - 다음 에이전트 결정                           │
└─────────────────────────────────────────────────┘
    │
    ├──[data_agent]────────────────────────────────┐
    │                                               │
    │   📊 DataAgent (데이터 조회)                  │
    │   - 주가, 시세, 거래량 실시간 조회             │
    │   - stock_utils 사용                          │
    │   - 간단한 요청 판단 (simple_request)         │
    │                                               │
    │   → 🔀 조건부 라우팅                           │
    │        ├─ [simple] → 즉시 응답 → 📤 END       │
    │        └─ [complex] → ResponseAgent           │
    │
    ├──[analysis_agent]────────────────────────────┐
    │                                               │
    │   📈 AnalysisAgent (투자 분석)                │
    │   - 종목 데이터 조회                           │
    │   - Neo4j KG 컨텍스트 통합                    │
    │   - Pinecone RAG 금융 지식 참조               │
    │   - LLM 기반 투자 의견 생성                   │
    │   - PER/PBR/ROE/배당 분석                     │
    │                                               │
    │   → ResponseAgent → 📤 END                    │
    │
    ├──[news_agent]────────────────────────────────┐
    │                                               │
    │   📰 NewsAgent (뉴스 수집 및 분석)            │
    │   - Google RSS 실시간 뉴스                    │
    │   - LLM 기반 동적 쿼리 판단                   │
    │   - 자동 한글 번역                            │
    │   - 뉴스 영향도 분석                          │
    │   - 감정 분석 (긍정/부정/중립)                │
    │                                               │
    │   → ResponseAgent → 📤 END                    │
    │
    ├──[knowledge_agent]───────────────────────────┐
    │                                               │
    │   📚 KnowledgeAgent (금융 지식 교육)          │
    │   - Pinecone RAG 검색 (우선)                  │
    │   - kf-deberta 임베딩 (4,961 벡터)           │
    │   - LLM이 컨텍스트 기반 설명 생성             │
    │   - 용어 정의 + 예시 + 실전 활용 팁          │
    │                                               │
    │   → ResponseAgent → 📤 END                    │
    │
    ├──[visualization_agent]───────────────────────┐
    │                                               │
    │   📊 VisualizationAgent (차트 생성)           │
    │   - 데이터 조회                               │
    │   - 차트 타입 결정 (line/bar/candle)         │
    │   - matplotlib/plotly 차트 생성               │
    │   - 차트 설명 및 인사이트                     │
    │                                               │
    │   → ResponseAgent → 📤 END                    │
    │
    └──[general/unknown]───────────────────────────┐
                                                    │
        💬 ResponseAgent (직접 응답)                │
        - Pinecone RAG 검색 시도                    │
        - 관련 컨텍스트 있으면 활용                 │
        - 없으면 일반 대화 응답                     │
                                                    │
        → 📤 END                                    │

## 🔧 각 에이전트의 상세 역할

### 1️⃣ QueryAnalyzerAgent (쿼리 분석)
**파일**: `app/services/langgraph_enhanced/agents/query_analyzer.py`

**역할**:
- 사용자 쿼리의 의도 파악 (data/analysis/news/knowledge/visualization/general)
- 쿼리 복잡도 평가 (simple/medium/complex)
- 필요한 서비스 식별
- 신뢰도 점수 계산 (0.0-1.0)
- 다음 에이전트 결정

**출력**:
```json
{
  "primary_intent": "analysis",
  "confidence": 0.95,
  "complexity": "medium",
  "reasoning": "종목 분석 및 투자 의견 요청",
  "next_agent": "analysis_agent"
}
```

**프롬프트**: LLM 기반 동적 분석

---

### 2️⃣ DataAgent (금융 데이터 조회)
**파일**: `app/services/langgraph_enhanced/agents/data_agent.py`

**역할**:
- 실시간 주가 데이터 조회
- 기본 재무 지표 수집 (PER, PBR, ROE, 시가총액)
- 간단한 요청 판단 (예: "삼성전자 주가 알려줘")
- Simple request인 경우 즉시 응답 생성

**서비스**: `financial_data_service`

**데이터 소스**: Yahoo Finance / 한국 증시 API

**특징**: 
- 간단한 주가 조회는 추가 분석 없이 바로 응답
- 복잡한 요청은 다른 에이전트로 전달

---

### 3️⃣ AnalysisAgent (투자 분석)
**파일**: `app/services/langgraph_enhanced/agents/analysis_agent.py`

**역할**:
- 심층 투자 분석 및 의견 생성
- **Neo4j Knowledge Graph 통합** (매일경제 뉴스 관계)
- **Pinecone RAG** 금융 지식 베이스 참조
- 기술적/기본적 분석
- 투자 등급 (강력매수/매수/보유/매도/강력매도)
- 목표가 제시

**서비스**: `analysis_service`

**LLM 프롬프트**:
```
당신은 전문 투자 분석가입니다.
다음 정보를 종합하여 투자 의견을 제시하세요:

1. 현재 주가 데이터: {financial_data}
2. Neo4j 관계 그래프: {kg_context}
3. Pinecone 지식 베이스: {rag_context}

분석 결과:
- 투자 의견: [강력매수/매수/보유/매도]
- 근거: ...
- 리스크: ...
- 목표가: ...
```

**특징**: 
- 다중 소스 통합 분석
- 컨텍스트 기반 정교한 의견

---

### 4️⃣ NewsAgent (뉴스 수집 및 분석)
**파일**: `app/services/langgraph_enhanced/agents/news_agent.py`

**역할**:
- 실시간 금융 뉴스 수집
- LLM 기반 동적 검색 쿼리 생성
- 뉴스 자동 번역 (Google RSS → 한글)
- 뉴스 영향도 분석
- 감정 분석 (긍정/부정/중립)
- 주요 포인트 요약

**서비스**: `news_service` + `google_rss_translator`

**데이터 소스**: Google RSS

**LLM 활용**:
1. 검색 쿼리 최적화
2. 뉴스 영향도 평가
3. 투자 시사점 도출

---

### 5️⃣ KnowledgeAgent (금융 지식 교육)
**파일**: `app/services/langgraph_enhanced/agents/knowledge_agent.py`

**역할**:
- 금융 용어 설명
- 투자 개념 교육
- 전략 가이드
- **Pinecone RAG 우선 활용**
- LLM이 검색 결과를 쉽게 설명

**서비스**: `pinecone_rag_service`

**데이터베이스**:
- Pinecone Index: `finance-rag-index`
- 벡터 수: 4,961개
- 임베딩 모델: `kakaobank/kf-deberta-base`
- 차원: 768

**프롬프트**:
```
당신은 금융 교육 전문가입니다.
사용자 질문: {query}

참고 자료 (Pinecone):
{rag_context}

다음 형식으로 설명해주세요:
1. 용어/개념 정의
2. 구체적 예시
3. 실전 투자 활용법
4. 주의사항
```

---

### 6️⃣ VisualizationAgent (차트 생성)
**파일**: `app/services/langgraph_enhanced/agents/visualization_agent.py`

**역할**:
- 데이터 시각화
- 차트 타입 자동 선택 (line/bar/candlestick)
- 인사이트 도출
- 차트 설명 생성

**서비스**: `visualization_service`

**라이브러리**: matplotlib / plotly

**차트 종류**:
- 주가 추이 (라인)
- 거래량 (바)
- 캔들스틱 (OHLC)
- 비교 차트

---

### 7️⃣ ResponseAgent (최종 응답 생성)
**파일**: `app/services/langgraph_enhanced/agents/response_agent.py`

**역할**:
- 모든 에이전트 결과 통합
- 사용자 친화적 응답 생성
- 맥락에 맞는 포맷팅
- 추가 질문 제안

**통합 정보**:
- financial_data (데이터)
- analysis_result (분석)
- news_data (뉴스)
- knowledge_context (지식)
- chart_data (차트)

**프롬프트**:
```
다음 정보를 바탕으로 사용자에게 유용한 응답을 생성하세요:
{all_context}

요구사항:
- 명확하고 이해하기 쉽게
- 핵심 정보 우선
- 추가 도움말 제공
```

---

## 🔄 워크플로우 실행 흐름

```
User Query
    ↓
[WorkflowRouter - LangGraph]
    ↓
QueryAnalyzerAgent (LLM 분석)
    ↓
┌─────────────────────────────────┐
│  조건부 라우팅 (Intent 기반)     │
├─────────────────────────────────┤
│  • data → DataAgent             │
│  • analysis → AnalysisAgent     │
│  • news → NewsAgent             │
│  • knowledge → KnowledgeAgent   │
│  • visualization → VisAgent     │
│  • general → ResponseAgent      │
└─────────────────────────────────┘
    ↓
각 전문 에이전트 실행
    ↓
[Optional] Pinecone RAG 참조
    ↓
ResponseAgent (결과 통합)
    ↓
User Response
```

---

## 🎯 Intelligent Workflow의 장점

### ✅ LLM 기반 동적 분석
- 키워드가 아닌 **의미 기반 분류**
- 쿼리 복잡도 자동 평가
- 신뢰도 점수 계산

### ✅ 전문화된 에이전트
- 각 도메인별 **전문 에이전트**
- 독립적인 프롬프트 관리
- 유지보수 용이

### ✅ Pinecone RAG 통합
- 모든 에이전트가 **지식 베이스 참조 가능**
- 4,961개 금융 문서 임베딩
- 실시간 컨텍스트 검색

### ✅ Neo4j Knowledge Graph
- 매일경제 뉴스 **관계 그래프**
- 기업-뉴스-키워드 연결
- 맥락 기반 분석

### ✅ 조건부 라우팅
- 쿼리에 따른 **최적 경로**
- 불필요한 처리 스킵
- 응답 속도 최적화

### ✅ 결과 통합
- 여러 소스의 정보 **LLM이 통합**
- 일관성 있는 응답
- 컨텍스트 유지

---

## 📊 에이전트 비교표

| 에이전트 | 주요 기능 | RAG 사용 | Neo4j 사용 | 응답 시간 |
|---------|----------|---------|-----------|----------|
| **QueryAnalyzer** | 의도 분석 | ❌ | ❌ | ~0.5s |
| **DataAgent** | 데이터 조회 | ❌ | ❌ | ~1s |
| **AnalysisAgent** | 투자 분석 | ✅ | ✅ | ~3s |
| **NewsAgent** | 뉴스 수집 | ❌ | ❌ | ~2s |
| **KnowledgeAgent** | 지식 교육 | ✅✅ | ❌ | ~2s |
| **VisualizationAgent** | 차트 생성 | ❌ | ❌ | ~1.5s |
| **ResponseAgent** | 응답 생성 | (선택) | ❌ | ~1s |

---

## 📍 코드 위치

### 메인 워크플로우
- **라우터**: `app/services/langgraph_enhanced/workflow_router.py`
- **LLM 매니저**: `app/services/langgraph_enhanced/llm_manager.py`

### 에이전트
- **디렉토리**: `app/services/langgraph_enhanced/agents/`
  - `query_analyzer.py` - 쿼리 분석
  - `data_agent.py` - 데이터 조회
  - `analysis_agent.py` - 투자 분석
  - `news_agent.py` - 뉴스 수집
  - `knowledge_agent.py` - 지식 교육
  - `visualization_agent.py` - 차트 생성
  - `response_agent.py` - 최종 응답
  - `base_agent.py` - 공통 베이스

### 서비스
- **컴포넌트**: `app/services/workflow_components/`
- **RAG**: `app/services/pinecone_rag_service.py`
- **Neo4j**: `app/services/workflow_components/data_agent_service.py`

---

## 🔄 Fallback 시스템

Intelligent Workflow 실패 시 자동 폴백:
```
Intelligent Workflow (우선)
    ↓ (실패 시)
Basic Workflow (폴백)
    ↓
financial_workflow.py
```

---

## 🚀 실행 방법

**서버 실행**:
```bash
source venv/bin/activate
python run_server.py
```

**채팅 터미널**:
```bash
python chat_terminal.py
```

**로그 확인**:
```bash
tail -f logs/server.log
```

---

## 📈 성능 최적화

### 병렬 실행 (향후 계획)
- 독립적인 에이전트 **병렬 실행**
- 데이터 + 뉴스 동시 수집
- 응답 시간 단축

### 캐싱 (향후 계획)
- 쿼리 분석 결과 캐싱
- Pinecone 검색 결과 캐싱
- 중복 요청 최적화

### 스트리밍 (향후 계획)
- LLM 응답 스트리밍
- 실시간 진행 상황 표시
- 사용자 경험 향상

---

## 🎓 예시 실행 흐름

### 예시 1: "삼성전자 주가 알려줘"
```
QueryAnalyzer → "data" (confidence: 0.95, simple)
    ↓
DataAgent → 실시간 주가 조회
    ↓
즉시 응답 (추가 에이전트 스킵)
    ↓
"삼성전자: 71,500원 (+2.1%)"
```

### 예시 2: "네이버 분석해줘"
```
QueryAnalyzer → "analysis" (confidence: 0.92, complex)
    ↓
AnalysisAgent → 데이터 조회
    ↓
Pinecone RAG → 투자 지식 참조
    ↓
Neo4j KG → 관련 뉴스 관계
    ↓
LLM → 종합 분석 생성
    ↓
ResponseAgent → 최종 응답 포맷팅
    ↓
"네이버 투자 분석 결과: [매수] ..."
```

### 예시 3: "PER이 뭐야?"
```
QueryAnalyzer → "knowledge" (confidence: 0.9, medium)
    ↓
KnowledgeAgent → Pinecone RAG 검색
    ↓
검색 결과: "PER(주가수익비율)은 ..."
    ↓
LLM → 쉬운 설명 생성
    ↓
ResponseAgent → 예시 추가
    ↓
"PER은 주가를 주당순이익(EPS)으로 나눈 값입니다..."
```

---

## 📝 관련 문서

- **프로젝트 구조**: `README_PROJECT_STRUCTURE.md`
- **아키텍처**: `ARCHITECTURE.md`
- **배포 가이드**: `docs/DEPLOYMENT_CHECKLIST.md`
- **시스템 전략**: `SYSTEM_STRATEGY.md`
