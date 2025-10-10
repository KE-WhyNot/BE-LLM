# 금융 전문가 챗봇 (Financial Expert Chatbot)

RAG, LangChain, LangGraph, LangSmith를 활용한 금융 분석 AI 시스템입니다.

## 🚀 주요 기능

### 1. 메타 에이전트 시스템 (LangGraph) ✨
- **지능형 쿼리 분석**: LLM 기반 의도 파악 및 복잡도 평가
- **11개 전문 에이전트**: Query Analyzer, Data, Analysis, News, Knowledge, Visualization, Response + 4개 메타 에이전트
- **병렬 실행 최적화**: 독립적 작업 동시 처리로 최대 50% 시간 단축
- **동적 워크플로우**: 쿼리 복잡도에 따라 자동으로 최적 경로 선택
- **신뢰도 평가**: 응답 품질을 A~F 등급으로 실시간 평가

### 2. RAG (Retrieval-Augmented Generation)
- **Pinecone 벡터 DB**: 4,961개 금융 문서 임베딩, 의미 기반 검색
- **Neo4j 지식 그래프**: 30,000+ 관계 (SIMILAR_TO, SAME_CATEGORY, MENTIONS)
- **한국어 임베딩**: kakaobank/kf-deberta-base 모델 (768차원)
- **매일경제 RSS**: 경제/증권/국제/정치 뉴스 자동 수집 및 임베딩
- **실시간 뉴스**: Google RSS + 자동 번역 (영어→한국어)

### 3. 통합 금융 데이터
- **실시간 주가**: Yahoo Finance API (58개 한국/미국 주요 종목)
- **재무 지표**: PER, PBR, ROE, 배당수익률, 시가총액
- **뉴스 분석**: 매일경제 KG + Google RSS 통합
- **차트 시각화**: matplotlib 기반 주가/거래량 차트
- **동적 설정**: YAML 기반 종목 설정으로 쉬운 확장

### 4. LangSmith 모니터링 & 최적화
- **실시간 추적**: 모든 쿼리와 응답의 전체 라이프사이클 추적
- **성능 메트릭**: 응답 시간, 성공률, 에러율 대시보드
- **워크플로우 시각화**: LangGraph 실행 흐름 및 에이전트 경로
- **비용 최적화**: Gemini 2.0 Flash Exp 사용으로 저비용 고성능

## 🏗️ 시스템 아키텍처

```
사용자 쿼리
    ↓
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Router                        │
│              (chat.py - API 엔드포인트)                   │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│                 ChatbotService (진입점)                   │
│       - 워크플로우 선택 및 모니터링 통합                    │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│              FinancialWorkflow (메인 라우터)              │
│           - WorkflowRouter로 LangGraph 워크플로우 실행     │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│          🧠 WorkflowRouter (LangGraph 기반)              │
├──────────────────────────────────────────────────────────┤
│  1. QueryAnalyzerAgent - 쿼리 의도 & 복잡도 분석          │
│  2. ServicePlannerAgent - 병렬/순차 실행 전략 수립 ✨     │
│  3. ParallelExecutor - 에이전트 동시 실행 ⚡              │
│  4. 전문 에이전트들 (Data/Analysis/News/Knowledge/Viz)    │
│  5. ResultCombinerAgent - LLM 기반 결과 통합 🔗          │
│  6. ConfidenceCalculatorAgent - 신뢰도 평가 📊           │
│  7. ResponseAgent - 최종 응답 생성                       │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│                 워크플로우 컴포넌트                         │
├───────────────┬──────────────┬──────────────┬───────────┤
│FinancialData  │ NewsService  │ Analysis     │ Pinecone  │
│Service        │              │ Service      │ RAG       │
│(yfinance)     │(MK+Google)   │              │           │
└───────────────┴──────────────┴──────────────┴───────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│                      데이터 계층                           │
├────────────┬──────────────┬──────────────┬──────────────┤
│ Pinecone   │    Neo4j     │  Yahoo       │  Google      │
│ 벡터 DB    │  지식그래프   │  Finance     │  RSS         │
│(4,961 docs)│(30K+ 관계)   │(실시간 주가)  │(실시간 뉴스)  │
└────────────┴──────────────┴──────────────┴──────────────┘
```

## 📁 프로젝트 구조

```
BE-LLM/
├── app/
│   ├── main.py                              # FastAPI 애플리케이션
│   ├── config.py                            # 환경 설정 관리
│   │
│   ├── routers/                             # 🌐 API 라우터
│   │   └── chat.py                          # 채팅 API 엔드포인트
│   │
│   ├── schemas/                             # 📋 데이터 스키마
│   │   ├── chat_schema.py                   # 채팅 요청/응답
│   │   └── user_schema.py                   # 사용자 프로필
│   │
│   ├── services/                            # 🔧 비즈니스 로직
│   │   ├── chatbot/                         # 🤖 챗봇 서비스
│   │   │   ├── chatbot_service.py           # 메인 진입점
│   │   │   └── financial_workflow.py        # 워크플로우 통합
│   │   │
│   │   ├── langgraph_enhanced/              # 🧠 메타 에이전트 시스템
│   │   │   ├── workflow_router.py           # LangGraph 워크플로우 라우터
│   │   │   ├── llm_manager.py               # LLM 통합 관리 (Gemini 전용)
│   │   │   └── agents/                      # 11개 에이전트
│   │   │       ├── base_agent.py            # 베이스 클래스
│   │   │       ├── query_analyzer.py        # 쿼리 분석
│   │   │       ├── data_agent.py            # 데이터 조회
│   │   │       ├── analysis_agent.py        # 투자 분석 (RAG+Neo4j)
│   │   │       ├── news_agent.py            # 뉴스 수집
│   │   │       ├── knowledge_agent.py       # 금융 지식 교육
│   │   │       ├── visualization_agent.py   # 차트 생성
│   │   │       ├── response_agent.py        # 최종 응답
│   │   │       ├── service_planner.py       # 서비스 전략 수립 ✨
│   │   │       ├── parallel_executor.py     # 병렬 실행 ⚡
│   │   │       ├── result_combiner.py       # 결과 통합 🔗
│   │   │       ├── confidence_calculator.py # 신뢰도 계산 📊
│   │   │       ├── fallback_agent.py        # 폴백 처리
│   │   │       └── investment_intent_detector.py
│   │   │
│   │   ├── workflow_components/             # ⚙️ 워크플로우 컴포넌트
│   │   │   ├── financial_data_service.py    # 금융 데이터 조회
│   │   │   ├── analysis_service.py          # 데이터 분석
│   │   │   ├── news_service.py              # 뉴스 통합 서비스
│   │   │   ├── mk_rss_scraper.py            # 매일경제 RSS + Neo4j
│   │   │   ├── google_rss_translator.py     # Google RSS + 번역
│   │   │   ├── data_agent_service.py        # 데이터 에이전트
│   │   │   ├── visualization_service.py     # 차트 시각화
│   │   │   └── response_generator_service.py # 응답 생성
│   │   │
│   │   ├── portfolio/                       # 💼 포트폴리오
│   │   │   └── portfolio_advisor.py         # 포트폴리오 제안
│   │   │
│   │   ├── pinecone_rag_service.py          # Pinecone RAG
│   │   ├── pinecone_config.py               # Pinecone 설정
│   │   ├── monitoring_service.py            # LangSmith 모니터링
│   │   └── user_service.py                  # 사용자 관리
│   │
│   └── utils/                               # 🛠️ 유틸리티
│       ├── stock_utils.py                   # 주식 심볼 매핑
│       ├── stock_config_loader.py           # YAML 동적 로딩
│       ├── common_utils.py                  # 공통 유틸
│       ├── formatters/                      # 포맷터
│       │   └── formatters.py
│       ├── external/                        # 외부 API
│       │   └── external_api_service.py
│       └── visualization/                   # 시각화
│           └── chart_display.py
│
├── config/                                  # ⚙️ 설정 파일
│   └── stocks.yaml                          # 58개 종목 설정 (동적)
│
├── docs/                                    # 📚 문서
│   ├── AGENT_SYSTEM_GUIDE.md                # 에이전트 시스템 가이드
│   ├── WORKFLOW_TREE.md                     # 워크플로우 트리
│   └── DEPLOYMENT_CHECKLIST.md              # 배포 체크리스트
│
├── tests/                                   # 🧪 테스트
│   ├── test_langgraph_enhanced.py           # LangGraph 테스트
│   ├── test_chatbot_workflow.py             # 워크플로우 테스트
│   ├── test_stock_utils_integration.py      # 주식 유틸 테스트
│   ├── performance_test/                    # 성능 벤치마크
│   │   ├── simple_benchmark.py
│   │   └── benchmark_analysis.md
│   └── examples/                            # 예제 코드
│       └── data_agent_example.py
│
├── requirements.txt                         # 의존성 (79개 패키지)
├── daily_news_updater.py                    # 일일 뉴스 업데이트 스크립트
├── chat_terminal.py                         # 터미널 채팅 인터페이스
├── run_server.py                            # 서버 실행 스크립트
├── ARCHITECTURE.md                          # 시스템 아키텍처 문서
├── TODO.md                                  # 작업 목록
└── README.md                                # 이 파일
```

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# Google AI API Key (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# LangSmith 설정 (선택)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=financial-chatbot

# Neo4j Aura 설정 (매일경제 뉴스 지식그래프)
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_aura_password

# Pinecone 설정 (RAG 벡터 DB)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=finance-rag-index
EMBEDDING_MODEL_NAME=kakaobank/kf-deberta-base
BATCH_SIZE=32
MAX_LENGTH=256
TOP_K=10
```

### 3. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API 사용법

### 1. 채팅 요청
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "session_id": "session_123",
       "message": "삼성전자 주가 분석해줘"
     }'
```

### 2. 대화 기록 조회
```bash
curl -X GET "http://localhost:8000/api/v1/chat/history/session_123"
```

### 3. 성능 메트릭 조회
```bash
curl -X GET "http://localhost:8000/api/v1/chat/metrics"
```

### 4. 성능 리포트 생성
```bash
curl -X GET "http://localhost:8000/api/v1/chat/report"
```

## 💡 사용 예시

### 기본 주식 정보 조회
```
사용자: "삼성전자 주가 알려줘"
챗봇: "📊 삼성전자 (005930.KS) 실시간 정보
현재가: 75,000원
전일대비: +1,500원 (+2.04%)
거래량: 12,345,678주
..."
```

### 투자 분석 요청
```
사용자: "삼성전자 투자 분석해줘"
챗봇: "🔍 투자 분석 결과:
📈 긍정적 신호: 전일 대비 +2.04% 상승
🔥 높은 관심도: 거래량 12,345,678주 (평소 대비 높음)
💰 저평가: PER 12.5 (투자 매력도 높음)
🏢 섹터: Technology
..."
```

### 금융 지식 질문
```
사용자: "PER이 뭔가요?"
챗봇: "📚 금융 지식:
PER (Price-to-Earnings Ratio)는 주가수익비율을 의미합니다.
- 계산법: 주가 ÷ 주당순이익(EPS)
- 의미: 현재 주가가 1년 순이익의 몇 배인지 나타냄
- 해석: 낮을수록 저평가, 높을수록 고평가
- 일반적 기준: 15 이하 저평가, 25 이상 고평가
..."
```

## 🔧 주요 기술 스택

### 핵심 프레임워크
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangChain**: LLM 애플리케이션 프레임워크 (0.3.27)
- **LangGraph**: 상태 기반 워크플로우 관리 (0.6.7)
- **LangSmith**: LLM 모니터링 및 디버깅 (0.4.29)

### AI/LLM
- **Google Gemini**: 2.0 Flash Exp 모델 (저비용 고성능, 4M 토큰 컨텍스트)
- **Sentence Transformers**: kakaobank/kf-deberta-base (한국어 금융 특화 임베딩, 768차원)
- **PyTorch**: 2.8.0 (모델 추론)
- **Transformers**: 4.56.2 (HuggingFace)

### 데이터베이스
- **Pinecone**: 클라우드 벡터 DB (4,961개 금융 문서 RAG)
- **Neo4j Aura**: 그래프 DB + GDS (30,000+ 뉴스 관계)

### 금융 데이터
- **yfinance**: 실시간 주식 데이터 (Yahoo Finance API)
- **matplotlib**: 차트 시각화

### 뉴스 & 번역
- **feedparser**: RSS 피드 파싱 (매일경제)
- **deep-translator**: 자동 번역 (영어→한국어)
- **BeautifulSoup4**: 웹 스크래핑

### 유틸리티
- **PyYAML**: 동적 종목 설정
- **APScheduler**: 스케줄링 (일일 뉴스 업데이트)
- **python-dotenv**: 환경 변수 관리

## 📊 모니터링 및 분석

### LangSmith 대시보드
- 실시간 쿼리 추적
- 응답 품질 분석
- 에러 패턴 감지
- 성능 메트릭 시각화

### 성능 지표
- 평균 응답 시간
- 쿼리 성공률
- 사용자 만족도
- 에러 발생률

## 🚀 최근 업데이트 (2025-10-10)

✅ **완료된 작업:**
1. **메타 에이전트 시스템 완성** (11개 에이전트)
   - ServicePlannerAgent: 병렬/순차 실행 전략 수립
   - ParallelExecutor: 독립적 작업 동시 처리로 50% 시간 단축
   - ResultCombinerAgent: LLM 기반 지능형 결과 통합
   - ConfidenceCalculatorAgent: A~F 등급 신뢰도 평가

2. **Neo4j 지식그래프 통합**
   - 매일경제 RSS 자동 수집 (5개 카테고리)
   - 30,000+ 관계 구축 (SIMILAR_TO, SAME_CATEGORY, MENTIONS)
   - KF-DeBERTa 임베딩 검색 (코사인 유사도)

3. **실시간 뉴스 번역 시스템**
   - Google RSS 실시간 검색
   - 자동 한국어 번역 (deep-translator)
   - 매일경제 + Google RSS 통합

4. **동적 종목 설정**
   - YAML 기반 종목 관리 (stocks.yaml)
   - 58개 한국/미국 주요 종목
   - 런타임 동적 로딩

5. **코드 최적화**
   - requirements.txt 정리 (79개 패키지)
   - Gemini 전용 LLM 관리자
   - 폴백 시스템 구축


## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**⚠️ 주의사항**: 이 챗봇은 교육 및 참고 목적으로 제작되었습니다. 실제 투자 결정은 신중히 하시고, 전문가의 조언을 구하시기 바랍니다.
