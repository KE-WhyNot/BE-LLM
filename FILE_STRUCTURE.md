# 📂 프로젝트 파일 구조 및 연결 관계

> **작성일**: 2025-10-10  
> **목적**: 모든 파일의 역할과 상호 연결 관계를 한눈에 파악

---

## 📋 목차

1. [전체 구조 개요](#전체-구조-개요)
2. [계층별 파일 분석](#계층별-파일-분석)
3. [연결 관계 맵](#연결-관계-맵)
4. [데이터 흐름](#데이터-흐름)
5. [주요 의존성](#주요-의존성)

---

## 🎯 전체 구조 개요

### 계층 구조 (Layered Architecture)

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: API Layer (routers/)                           │
│ - 요청 수신, 검증, 응답 반환                               │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 2: Service Layer (services/chatbot/)              │
│ - 비즈니스 로직, 워크플로우 선택                           │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Workflow Layer (langgraph_enhanced/)           │
│ - LangGraph 기반 동적 워크플로우, 에이전트 실행             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 4: Component Layer (workflow_components/)         │
│ - 개별 기능 컴포넌트 (데이터, 분석, 뉴스, 지식)             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 5: Data Layer (외부 API, DB)                      │
│ - Pinecone, Neo4j, Yahoo Finance, Google RSS            │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 계층별 파일 분석

### 1. 진입점 (Entry Points)

#### `app/main.py`
**역할**: FastAPI 애플리케이션 초기화
```python
역할:
- FastAPI 앱 생성
- CORS 미들웨어 설정
- 라우터 등록 (chat.router)
- 헬스 체크 엔드포인트

연결:
→ app/routers/chat.py (라우터 포함)
→ app/config.py (설정 로드)
```

#### `run_server.py`
**역할**: 서버 실행 스크립트
```python
역할:
- uvicorn으로 FastAPI 서버 실행
- 호스트/포트 설정

연결:
→ app.main:app (FastAPI 앱)
```

#### `chat_terminal.py`
**역할**: 터미널 기반 채팅 인터페이스
```python
역할:
- 대화형 CLI 제공
- API 호출 테스트

연결:
→ requests (HTTP 클라이언트)
→ http://localhost:8000/api/v1/chat
```

---

### 2. API 계층 (Layer 1)

#### `app/routers/chat.py`
**역할**: 채팅 API 엔드포인트
```python
역할:
- POST /api/v1/chat - 채팅 요청
- GET /api/v1/chat/history/{session_id} - 대화 기록
- DELETE /api/v1/chat/history/{session_id} - 기록 삭제
- GET /api/v1/chat/metrics - 성능 메트릭
- GET /api/v1/chat/report - 성능 리포트
- GET /api/v1/chat/knowledge-base/stats - RAG 통계
- POST /api/v1/chat/knowledge-base/update - RAG 업데이트

연결:
← app/schemas/chat_schema.py (ChatRequest, ChatResponse)
→ app/services/chatbot/chatbot_service.py (chatbot_service)
```

#### `app/schemas/chat_schema.py`
**역할**: 채팅 요청/응답 스키마
```python
역할:
- ChatRequest: user_id, session_id, message
- ChatResponse: reply_text, action_type, action_data, chart_image, pinecone_results

연결:
← app/routers/chat.py (스키마 사용)
```

#### `app/schemas/user_schema.py`
**역할**: 사용자 프로필 스키마
```python
역할:
- UserProfile: user_id, username, risk_appetite
- PortfolioItem: stock_code, quantity, average_purchase_price

연결:
← app/services/portfolio/portfolio_advisor.py (포트폴리오 분석)
```

---

### 3. 서비스 계층 (Layer 2)

#### `app/services/chatbot/chatbot_service.py`
**역할**: 챗봇 서비스 진입점
```python
역할:
- 채팅 요청 처리 (process_chat_request)
- Pinecone RAG 초기화
- 모니터링 통합
- 대화 기록 관리 (현재 비활성)

연결:
← app/routers/chat.py (API에서 호출)
→ app/services/chatbot/financial_workflow.py (financial_workflow)
→ app/services/monitoring_service.py (monitoring_service)
→ app/services/pinecone_rag_service.py (pinecone_rag_service)

데이터 흐름:
1. ChatRequest 수신
2. financial_workflow.process_query() 호출
3. 모니터링 로그 기록
4. Pinecone 검색 추가
5. ChatResponse 반환
```

#### `app/services/chatbot/financial_workflow.py`
**역할**: 워크플로우 통합
```python
역할:
- 메타 에이전트 워크플로우 사용
- 폴백 응답 생성
- 에러 처리

연결:
← app/services/chatbot/chatbot_service.py
→ app/services/langgraph_enhanced/workflow_router.py (WorkflowRouter)

실행 흐름:
1. WorkflowRouter 초기화
2. process_query() 호출
3. 결과 반환 (success, reply_text, action_type, action_data)
```

---

### 4. 워크플로우 계층 (Layer 3) - 핵심!

#### `app/services/langgraph_enhanced/workflow_router.py`
**역할**: LangGraph 워크플로우 라우터 (메인 오케스트레이터)
```python
역할:
- LangGraph StateGraph 구축
- 11개 에이전트 관리 및 실행
- 조건부 라우팅 (쿼리 분석 → 에이전트 선택)
- 병렬 실행 조율

연결:
→ app/services/langgraph_enhanced/agents/ (모든 에이전트)
→ app/services/langgraph_enhanced/llm_manager.py (LLMManager)

워크플로우 노드:
1. query_analyzer - 쿼리 분석
2. service_planner - 서비스 계획 수립
3. parallel_executor - 병렬 실행
4. data_agent - 데이터 조회
5. analysis_agent - 투자 분석
6. news_agent - 뉴스 수집
7. knowledge_agent - 지식 교육
8. visualization_agent - 차트 생성
9. result_combiner - 결과 통합
10. confidence_calculator - 신뢰도 계산
11. response_agent - 최종 응답
12. error_handler - 에러 처리

라우팅 함수:
- _route_after_planning: 서비스 계획 후 라우팅
- _route_after_data: 데이터 에이전트 후 라우팅

데이터 흐름:
사용자 쿼리 
  → WorkflowState 초기화
  → StateGraph 실행 (LangGraph)
  → 각 노드에서 에이전트 process() 호출
  → 최종 응답 반환
```

#### `app/services/langgraph_enhanced/llm_manager.py`
**역할**: LLM 통합 관리 (Gemini 전용)
```python
역할:
- Gemini LLM 인스턴스 생성 및 캐싱
- 용도별 최적화된 파라미터 (classification, analysis, news 등)
- 모델 선택 (기본: gemini-2.0-flash-exp)

연결:
→ langchain_google_genai (ChatGoogleGenerativeAI)
← 모든 에이전트 (LLM 요청)

최적화:
- 캐싱으로 중복 생성 방지
- 용도별 temperature, max_tokens 자동 설정
```

---

### 5. 에이전트 계층 (Layer 3.5)

#### `app/services/langgraph_enhanced/agents/base_agent.py`
**역할**: 모든 에이전트의 베이스 클래스
```python
역할:
- 공통 인터페이스 제공
- process() 메서드 정의 (추상 메서드)

연결:
← 모든 전문 에이전트 (상속)
```

#### `app/services/langgraph_enhanced/agents/query_analyzer.py`
**역할**: 쿼리 분석 에이전트
```python
역할:
- 사용자 쿼리의 의도 파악 (data/analysis/news/knowledge/visualization/general)
- 복잡도 평가 (simple/moderate/complex)
- 신뢰도 점수 계산
- 투자 질문 여부 감지

연결:
→ llm_manager (LLM 호출)
→ investment_intent_detector (투자 의도 감지)

출력:
{
  'primary_intent': 'analysis',
  'confidence': 0.95,
  'complexity': 'moderate',
  'required_services': ['data', 'analysis'],
  'next_agent': 'analysis_agent',
  'is_investment_question': True
}
```

#### `app/services/langgraph_enhanced/agents/service_planner.py`
**역할**: 서비스 실행 전략 수립 (메타 에이전트)
```python
역할:
- 쿼리 복잡도에 따라 병렬/순차 실행 전략 결정
- 실행 순서 최적화
- 예상 시간 계산

연결:
→ llm_manager (LLM 호출)

출력:
{
  'execution_strategy': 'hybrid',
  'parallel_groups': [['data_agent'], ['news_agent', 'knowledge_agent']],
  'execution_order': ['data_agent', 'parallel(...)', 'response_agent'],
  'estimated_time': 3.5
}
```

#### `app/services/langgraph_enhanced/agents/parallel_executor.py`
**역할**: 병렬 실행 관리 (메타 에이전트)
```python
역할:
- ThreadPoolExecutor 사용하여 독립적 에이전트 동시 실행
- 결과 수집 및 반환
- 타임아웃 처리

연결:
→ 전문 에이전트들 (data, news, knowledge 등)

실행 방식:
execute_parallel_sync(agents_to_execute, agents_dict, user_query, query_analysis)
  → ThreadPoolExecutor.submit()
  → 각 에이전트의 process() 동시 호출
  → 결과 딕셔너리 반환
```

#### `app/services/langgraph_enhanced/agents/data_agent.py`
**역할**: 금융 데이터 조회 에이전트
```python
역할:
- 실시간 주가 조회
- 간단한 요청 판단 (is_simple_request)
- 즉시 응답 생성 (간단한 경우)

연결:
→ app/services/workflow_components/financial_data_service.py
→ app/utils/stock_utils.py (심볼 추출)

출력:
{
  'success': True,
  'data': {...},  # 주가, PER, PBR 등
  'is_simple_request': True,  # 간단한 요청이면 True
  'simple_response': "삼성전자: 71,500원 (+2.1%)"  # 즉시 응답
}
```

#### `app/services/langgraph_enhanced/agents/analysis_agent.py`
**역할**: 투자 분석 에이전트 (RAG + Neo4j 통합)
```python
역할:
- 심층 투자 분석
- Pinecone RAG 검색
- Neo4j 뉴스 컨텍스트 통합
- LLM 기반 투자 의견 생성

연결:
→ app/services/workflow_components/financial_data_service.py (주가 데이터)
→ app/services/workflow_components/news_service.py (뉴스 컨텍스트)
→ app/services/pinecone_rag_service.py (RAG 검색)
→ llm_manager (LLM 호출)

데이터 흐름:
1. 주가 데이터 조회
2. Pinecone RAG 검색 (금융 지식)
3. Neo4j 뉴스 컨텍스트 (매일경제 KG)
4. LLM에 프롬프트 전달
5. 통합 투자 분석 반환
```

#### `app/services/langgraph_enhanced/agents/news_agent.py`
**역할**: 뉴스 수집 및 분석 에이전트
```python
역할:
- 실시간 뉴스 수집 (Google RSS)
- 자동 번역 (영어→한국어)
- 뉴스 영향도 분석

연결:
→ app/services/workflow_components/news_service.py

출력:
{
  'success': True,
  'news_data': [...],  # 뉴스 리스트
  'analysis_result': "뉴스 분석 결과..."
}
```

#### `app/services/langgraph_enhanced/agents/knowledge_agent.py`
**역할**: 금융 지식 교육 에이전트
```python
역할:
- Pinecone RAG 우선 검색
- 금융 용어 설명
- 개념 교육

연결:
→ app/services/pinecone_rag_service.py
→ llm_manager (LLM 호출)

데이터 흐름:
1. Pinecone 검색 (용어, 개념)
2. 검색 결과를 컨텍스트로 LLM 호출
3. 쉽게 풀어쓴 설명 반환
```

#### `app/services/langgraph_enhanced/agents/visualization_agent.py`
**역할**: 차트 생성 에이전트
```python
역할:
- 주가 차트 생성
- 타입 자동 선택 (line/bar/candle)
- 인사이트 도출

연결:
→ app/services/workflow_components/visualization_service.py

출력:
{
  'success': True,
  'chart_data': {...},
  'chart_image': "base64_encoded_image",
  'analysis_result': "차트 분석 결과..."
}
```

#### `app/services/langgraph_enhanced/agents/result_combiner.py`
**역할**: 결과 통합 에이전트 (메타 에이전트)
```python
역할:
- 여러 에이전트 결과를 LLM이 지능형으로 통합
- 일관성 있는 답변 생성
- 중복 제거 및 우선순위 결정

연결:
→ llm_manager (LLM 호출)

입력:
{
  'data_agent': {'financial_data': {...}},
  'news_agent': {'news_data': [...]},
  'knowledge_agent': {'explanation': '...'}
}

출력:
{
  'combined_response': '통합된 최종 답변',
  'confidence': 0.92
}
```

#### `app/services/langgraph_enhanced/agents/confidence_calculator.py`
**역할**: 신뢰도 계산 에이전트 (메타 에이전트)
```python
역할:
- 답변 신뢰도 평가 (A~F 등급)
- 품질 보장
- 개선 제안
- 경고 생성

연결:
→ llm_manager (LLM 호출)

평가 기준:
- 완전성 (0-25점): 질문 답변 완성도
- 일관성 (0-25점): 정보 일치 여부
- 정확성 (0-25점): 데이터 신뢰성
- 유용성 (0-25점): 실질적 도움

출력:
{
  'overall_confidence': 0.92,
  'total_score': 92,
  'grade': 'A',
  'reasoning': '모든 정보가 일관되고 정확함',
  'warnings': '실시간 데이터는 지연 가능'
}
```

#### `app/services/langgraph_enhanced/agents/response_agent.py`
**역할**: 최종 응답 생성 에이전트
```python
역할:
- 통합된 결과를 사용자 친화적으로 포맷팅
- 추가 질문 제안
- 맥락에 맞는 표현

연결:
→ llm_manager (LLM 호출)

데이터 흐름:
1. combined_result 또는 collected_data 수신
2. LLM에 최종 프롬프트 전달
3. 자연스러운 응답 생성
```

#### `app/services/langgraph_enhanced/agents/fallback_agent.py`
**역할**: 폴백 처리 유틸리티
```python
역할:
- 뉴스 소스 자동 폴백 (매일경제 → Google RSS)
- 에러 시 대체 경로 실행

연결:
→ app/services/workflow_components/news_service.py
→ app/services/workflow_components/mk_rss_scraper.py

전략:
1. Primary 소스 시도 (매일경제 KG)
2. 실패 시 Fallback 소스 (Google RSS)
3. 결과 반환 (성공한 소스 표시)
```

---

### 6. 컴포넌트 계층 (Layer 4)

#### `app/services/workflow_components/financial_data_service.py`
**역할**: 금융 데이터 조회
```python
역할:
- Yahoo Finance API 호출
- 주가, PER, PBR, ROE, 시가총액 조회
- 데이터 포맷팅

연결:
→ yfinance (외부 API)
← data_agent, analysis_agent

주요 함수:
- get_stock_data(symbol): 종목 데이터 조회
- get_financial_summary(symbol): 재무 요약
```

#### `app/services/workflow_components/analysis_service.py`
**역할**: 데이터 분석
```python
역할:
- 투자 지표 계산
- 트렌드 분석
- 신호 감지

연결:
← analysis_agent

주요 함수:
- analyze_investment_signals(data): 투자 신호 분석
- calculate_trend(prices): 트렌드 계산
```

#### `app/services/workflow_components/news_service.py`
**역할**: 뉴스 통합 서비스
```python
역할:
- 매일경제 KG 검색
- Google RSS 실시간 검색
- 뉴스 통합 및 중복 제거
- FallbackAgent 사용

연결:
→ mk_rss_scraper (MKKnowledgeGraphService)
→ google_rss_translator (search_google_news)
→ fallback_agent (NewsSourceFallback)
← news_agent, analysis_agent

주요 함수:
- get_comprehensive_news(query): 통합 뉴스 검색
- get_analysis_context_from_kg(query): 분석용 KG 컨텍스트
- get_mk_news_with_embedding(query): 매일경제 임베딩 검색
```

#### `app/services/workflow_components/mk_rss_scraper.py`
**역할**: 매일경제 RSS + Neo4j 지식그래프
```python
역할:
- RSS 피드 수집 (5개 카테고리)
- KF-DeBERTa 임베딩 생성
- Neo4j 저장 및 관계 구축
- 임베딩 기반 검색

연결:
→ neo4j (GraphDatabase)
→ SentenceTransformer (kakaobank/kf-deberta-base)
← news_service

주요 클래스:
- MKNewsScraper: RSS 수집 및 Neo4j 저장
- MKKnowledgeGraphService: 검색 인터페이스

RSS 피드:
- economy: https://www.mk.co.kr/rss/30100041/
- politics: https://www.mk.co.kr/rss/30200030/
- securities: https://www.mk.co.kr/rss/50200011/
- international: https://www.mk.co.kr/rss/50100032/
- headlines: https://www.mk.co.kr/rss/30000001/

Neo4j 구조:
- Article 노드: title, link, embedding (768차원)
- 관계: SIMILAR_TO, SAME_CATEGORY, MENTIONS
```

#### `app/services/workflow_components/google_rss_translator.py`
**역할**: Google RSS + 자동 번역
```python
역할:
- Google RSS 실시간 검색
- 영어→한국어 번역
- 뉴스 메타데이터 추가

연결:
→ feedparser (RSS 파싱)
→ deep_translator (번역)
← news_service

주요 함수:
- search_google_news(query, limit): RSS 검색
- translate_news_to_korean(news_list): 번역
```

#### `app/services/workflow_components/data_agent_service.py`
**역할**: 데이터 에이전트 컴포넌트
```python
역할:
- NewsCollector: RSS 뉴스 수집 (폴백용)
- 기사 필터링 및 분석

연결:
→ feedparser (RSS)
← news_service (폴백)
```

#### `app/services/workflow_components/visualization_service.py`
**역할**: 차트 시각화
```python
역할:
- matplotlib 기반 차트 생성
- base64 인코딩
- 인사이트 텍스트 생성

연결:
→ matplotlib
← visualization_agent

주요 함수:
- create_price_chart(data): 주가 차트
- create_volume_chart(data): 거래량 차트
```

#### `app/services/workflow_components/response_generator_service.py`
**역할**: 응답 생성 컴포넌트
```python
역할:
- 템플릿 기반 응답 생성
- 포맷팅

연결:
← response_agent (폴백)
```

---

### 7. 공통 서비스

#### `app/services/pinecone_rag_service.py`
**역할**: Pinecone RAG 서비스
```python
역할:
- Pinecone 벡터 DB 연결
- 임베딩 생성 (kf-deberta-base)
- 의미 기반 검색

연결:
→ Pinecone (클라우드 벡터 DB)
→ SentenceTransformer
← knowledge_agent, analysis_agent

주요 함수:
- search(query, top_k): 벡터 검색
- get_context_for_query(query): 컨텍스트 반환
- initialize(): 서비스 초기화

데이터:
- Index: finance-rag-index
- 벡터 수: 4,961개
- 차원: 768
```

#### `app/services/pinecone_config.py`
**역할**: Pinecone 설정
```python
역할:
- API 키, 인덱스명, 모델 설정
- 상수 관리

연결:
← pinecone_rag_service
```

#### `app/services/monitoring_service.py`
**역할**: LangSmith 모니터링
```python
역할:
- LangSmith 클라이언트 초기화
- 쿼리 추적 (trace_query)
- 성능 메트릭 수집
- 에러 로깅

연결:
→ LangSmith (langsmith.Client)
← chatbot_service

주요 함수:
- trace_query(user_query, response, metadata): 추적
- get_performance_metrics(days): 메트릭 조회
- generate_performance_report(): 리포트 생성
```

#### `app/services/user_service.py`
**역할**: 사용자 관리 (미래 기능)
```python
역할:
- 사용자 프로필 관리
- 대화 세션 관리

연결:
← chatbot_service (미래)
```

#### `app/services/portfolio/portfolio_advisor.py`
**역할**: 포트폴리오 제안
```python
역할:
- 포트폴리오 분석
- 리밸런싱 제안
- 리스크 평가

연결:
→ financial_data_service
← chatbot_service (미래)
```

---

### 8. 유틸리티 계층

#### `app/utils/stock_utils.py`
**역할**: 주식 심볼 매핑 및 유틸리티
```python
역할:
- 쿼리에서 심볼 추출 (extract_symbol_from_query)
- 회사명 → 심볼 변환
- 동적 YAML 설정 로딩

연결:
→ stock_config_loader (동적 로딩)
← data_agent, analysis_agent

주요 함수:
- extract_symbol_from_query(query): 단일 심볼 추출
- extract_symbols_for_news(query): 다중 심볼 추출
- get_company_name_from_symbol(symbol): 회사명 반환
- is_valid_symbol(symbol): 심볼 유효성 검사
```

#### `app/utils/stock_config_loader.py`
**역할**: YAML 동적 로딩
```python
역할:
- stocks.yaml 파싱
- 런타임 동적 검색
- 캐싱

연결:
→ config/stocks.yaml
← stock_utils

주요 함수:
- get_symbol(query): 쿼리로 심볼 찾기
- get_stock_info(symbol): 종목 정보 반환
- search_stocks(keyword, limit): 검색
- get_all_symbols(): 전체 심볼 목록
- get_symbols_by_sector(sector): 섹터별 목록
- get_symbols_by_country(country): 국가별 목록
- reload_config(): 설정 다시 로드
```

#### `app/utils/common_utils.py`
**역할**: 공통 유틸리티
```python
역할:
- 텍스트 처리
- 날짜 변환
- 공통 함수

연결:
← 다양한 서비스
```

#### `app/utils/formatters/formatters.py`
**역할**: 데이터 포맷터
```python
역할:
- 금융 데이터 포맷팅
- 숫자 천 단위 구분
- 날짜 형식 변환

연결:
← 다양한 서비스
```

#### `app/utils/external/external_api_service.py`
**역할**: 외부 API 호출
```python
역할:
- HTTP 요청 래퍼
- 에러 처리

연결:
→ requests
← 다양한 서비스
```

#### `app/utils/visualization/chart_display.py`
**역할**: 차트 표시 유틸리티
```python
역할:
- 차트 렌더링 지원
- base64 변환

연결:
← visualization_service
```

---

### 9. 설정 및 스크립트

#### `app/config.py`
**역할**: 환경 설정 관리
```python
역할:
- .env 파일 로드 (pydantic-settings)
- 환경 변수 검증
- 전역 설정 인스턴스 (settings)

연결:
← 모든 서비스 (설정 사용)

주요 설정:
- google_api_key
- langsmith_api_key
- neo4j_uri, neo4j_user, neo4j_password
- pinecone_api_key, pinecone_index_name
- embedding_model_name
```

#### `config/stocks.yaml`
**역할**: 종목 설정 파일
```python
역할:
- 58개 한국/미국 주요 종목 정의
- 섹터별 분류
- 동적 로딩 지원

구조:
korean_stocks:
  samsung_electronics:
    names: ["삼성전자", "삼성", "삼전"]
    symbol: "005930.KS"
    sector: "technology"
    market_cap_rank: 1

us_stocks:
  apple:
    names: ["애플", "apple", "aapl"]
    symbol: "AAPL"
    sector: "technology"

indices:
  kospi:
    names: ["코스피", "kospi"]
    symbol: "^KS11"
```

#### `daily_news_updater.py`
**역할**: 일일 뉴스 업데이트 크론 스크립트
```python
역할:
- 매일경제 RSS 수집
- Neo4j 업데이트
- 크론잡 설정 가능

연결:
→ mk_rss_scraper (update_mk_knowledge_graph)

실행:
python daily_news_updater.py

크론 예시:
0 9 * * * cd /path/to/BE-LLM && python daily_news_updater.py
```

#### `requirements.txt`
**역할**: Python 의존성
```
패키지 수: 79개
주요 패키지:
- fastapi==0.117.1
- langchain==0.3.27
- langgraph==0.6.7
- langsmith==0.4.29
- langchain-google-genai==2.1.12
- pinecone>=6.2.0
- neo4j>=5.27.0
- yfinance==0.2.66
- sentence-transformers==5.1.0
- torch==2.8.0
```

---

## 🔗 연결 관계 맵

### 데이터 흐름 (Data Flow)

```
사용자 쿼리
    ↓
main.py (FastAPI)
    ↓
routers/chat.py (API 엔드포인트)
    ↓
services/chatbot/chatbot_service.py (진입점)
    ↓
services/chatbot/financial_workflow.py (워크플로우 통합)
    ↓
services/langgraph_enhanced/workflow_router.py (LangGraph)
    ↓
┌─────────────────────────────────────────────────────┐
│ 에이전트 실행 (병렬 가능)                              │
├─────────────────────────────────────────────────────┤
│ 1. QueryAnalyzerAgent                               │
│    → query_analyzer.py                              │
│                                                     │
│ 2. ServicePlannerAgent                              │
│    → service_planner.py                             │
│                                                     │
│ 3. ParallelExecutor                                 │
│    → parallel_executor.py                           │
│    ├─ DataAgent (data_agent.py)                     │
│    │   → financial_data_service.py                  │
│    │   → yfinance API                               │
│    │                                                 │
│    ├─ NewsAgent (news_agent.py)                     │
│    │   → news_service.py                            │
│    │   ├─ mk_rss_scraper.py → Neo4j                 │
│    │   └─ google_rss_translator.py → Google RSS     │
│    │                                                 │
│    ├─ AnalysisAgent (analysis_agent.py)             │
│    │   → financial_data_service.py                  │
│    │   → news_service.py (KG 컨텍스트)              │
│    │   → pinecone_rag_service.py                    │
│    │   → llm_manager.py (Gemini)                    │
│    │                                                 │
│    ├─ KnowledgeAgent (knowledge_agent.py)           │
│    │   → pinecone_rag_service.py                    │
│    │   → llm_manager.py (Gemini)                    │
│    │                                                 │
│    └─ VisualizationAgent (visualization_agent.py)   │
│        → visualization_service.py                   │
│        → matplotlib                                 │
│                                                     │
│ 4. ResultCombinerAgent                              │
│    → result_combiner.py                             │
│    → llm_manager.py (Gemini)                        │
│                                                     │
│ 5. ConfidenceCalculatorAgent                        │
│    → confidence_calculator.py                       │
│    → llm_manager.py (Gemini)                        │
│                                                     │
│ 6. ResponseAgent                                    │
│    → response_agent.py                              │
│    → llm_manager.py (Gemini)                        │
└─────────────────────────────────────────────────────┘
    ↓
monitoring_service.py (LangSmith 추적)
    ↓
ChatResponse 반환
    ↓
사용자
```

---

## 📊 데이터 흐름 상세

### 1. 간단한 주가 조회 (단순 경로)

```
"삼성전자 주가 알려줘"
    ↓
QueryAnalyzerAgent
  → primary_intent: 'data', complexity: 'simple'
    ↓
ServicePlannerAgent
  → execution_mode: 'single'
    ↓
DataAgent
  → stock_utils.extract_symbol_from_query("삼성전자 주가")
  → symbol: "005930.KS"
  → financial_data_service.get_stock_data("005930.KS")
  → yfinance.Ticker("005930.KS").info
  → is_simple_request: True
  → simple_response: "삼성전자: 71,500원 (+2.1%)"
    ↓
ResponseAgent (간단한 요청이므로 바로 응답)
    ↓
"삼성전자: 71,500원 (+2.1%)"
```

### 2. 복잡한 투자 분석 (병렬 경로)

```
"네이버 투자 분석하고 최근 뉴스도 알려줘"
    ↓
QueryAnalyzerAgent
  → primary_intent: 'analysis', complexity: 'moderate'
  → required_services: ['data', 'analysis', 'news']
    ↓
ServicePlannerAgent
  → execution_mode: 'parallel'
  → parallel_groups: [['data_agent'], ['news_agent', 'knowledge_agent']]
    ↓
ParallelExecutor
  ├─ Thread 1: DataAgent
  │   → financial_data_service.get_stock_data("035420.KS")
  │   → 결과: {price: 180000, change: +3.2%, ...}
  │
  └─ Thread 2: NewsAgent + KnowledgeAgent (병렬)
      ├─ NewsAgent
      │   → news_service.get_comprehensive_news("네이버")
      │   ├─ mk_rss_scraper (Neo4j KG)
      │   │   → 임베딩 검색 → 관련 뉴스 3개
      │   └─ google_rss_translator (실시간)
      │       → 키워드 검색 + 번역 → 뉴스 2개
      │   → 중복 제거 → 5개 뉴스
      │
      └─ KnowledgeAgent (없음, 이 경우 스킵)
    ↓
AnalysisAgent (데이터 + 뉴스 기반 분석)
  → financial_data: {price: 180000, ...}
  → news_data: [5개 뉴스]
  → pinecone_rag_service.get_context_for_query("네이버 투자")
  → rag_context: "네이버는 인터넷 플랫폼..."
  → llm_manager.get_llm(purpose='analysis')
  → LLM 프롬프트: "다음 정보를 종합하여 투자 분석..."
  → analysis_result: "네이버는 긍정적인 투자 의견..."
    ↓
ResultCombinerAgent
  → LLM 기반 통합
  → combined_response: "네이버 투자 분석 결과: ..."
    ↓
ConfidenceCalculatorAgent
  → overall_confidence: 0.88 (B등급)
    ↓
ResponseAgent
  → 최종 포맷팅
    ↓
"📊 네이버 투자 분석 결과
주가: 180,000원 (+3.2%)
투자 의견: 매수
근거: ...
최근 뉴스: ..."
```

### 3. 금융 지식 질문

```
"PER이 뭐야?"
    ↓
QueryAnalyzerAgent
  → primary_intent: 'knowledge', complexity: 'simple'
    ↓
KnowledgeAgent
  → pinecone_rag_service.search("PER")
  → 검색 결과: "PER은 주가수익비율..."
  → llm_manager.get_llm(purpose='knowledge')
  → LLM 프롬프트: "다음 자료를 바탕으로 PER을 쉽게 설명..."
  → explanation: "PER은 주가를 주당순이익으로 나눈 값..."
    ↓
ResponseAgent
  → 최종 포맷팅
    ↓
"📚 PER(주가수익비율)이란?
PER은 주가를 주당순이익으로 나눈 값...
💡 해석: PER < 15: 저평가..."
```

---

## 🔑 주요 의존성

### 내부 의존성

```
workflow_router.py
├─ llm_manager.py
├─ agents/
│  ├─ query_analyzer.py
│  ├─ service_planner.py
│  ├─ parallel_executor.py
│  ├─ data_agent.py → financial_data_service.py
│  ├─ analysis_agent.py → financial_data_service.py, news_service.py, pinecone_rag_service.py
│  ├─ news_agent.py → news_service.py
│  ├─ knowledge_agent.py → pinecone_rag_service.py
│  ├─ visualization_agent.py → visualization_service.py
│  ├─ result_combiner.py
│  ├─ confidence_calculator.py
│  └─ response_agent.py

news_service.py
├─ mk_rss_scraper.py → Neo4j
├─ google_rss_translator.py → feedparser, deep_translator
└─ fallback_agent.py

stock_utils.py
└─ stock_config_loader.py → stocks.yaml
```

### 외부 의존성

```
데이터베이스:
- Pinecone: 벡터 검색 (4,961 docs)
- Neo4j Aura: 지식그래프 (30,000+ 관계)

API:
- Yahoo Finance: 실시간 주가
- Google RSS: 실시간 뉴스
- Google Gemini: LLM (2.0 Flash Exp)
- LangSmith: 모니터링

라이브러리:
- LangChain/LangGraph: 워크플로우
- Sentence Transformers: 임베딩
- PyTorch: 모델 추론
- feedparser: RSS 파싱
- deep-translator: 번역
- matplotlib: 차트
```

---

## 🎯 핵심 설계 패턴

### 1. 계층화 아키텍처 (Layered Architecture)
각 계층이 독립적으로 동작하며 상위 계층만 의존

### 2. 메타 에이전트 패턴
전문 에이전트를 조율하는 메타 에이전트 (Planner, Executor, Combiner, Calculator)

### 3. 폴백 패턴
실패 시 자동으로 대체 경로 실행 (NewsSourceFallback)

### 4. 동적 라우팅
쿼리 복잡도에 따라 실행 경로 자동 선택

### 5. 병렬 실행
독립적 작업 동시 처리로 50% 시간 단축

### 6. RAG 통합
Pinecone + Neo4j 이중 RAG 시스템

### 7. 동적 설정
YAML 기반 런타임 종목 설정 로딩

---

## 📝 파일 수정 가이드

### 새로운 종목 추가
1. `config/stocks.yaml` 수정
2. 서버 재시작 (또는 `stock_config_loader.reload_config()` 호출)

### 새로운 에이전트 추가
1. `agents/new_agent.py` 생성 (BaseAgent 상속)
2. `agents/__init__.py`에 import 추가
3. `workflow_router.py`에서 노드 및 엣지 추가

### 새로운 뉴스 소스 추가
1. `workflow_components/new_news_source.py` 생성
2. `news_service.py`에 통합
3. `fallback_agent.py`에 폴백 추가

### 설정 변경
1. `.env` 파일 수정
2. `config.py`에 필드 추가 (필요시)
3. 서버 재시작

---

## 🔍 디버깅 팁

### 로그 확인
```bash
# 서버 로그
tail -f logs/server.log

# LangSmith 대시보드
https://smith.langchain.com
```

### 테스트 실행
```bash
# 전체 테스트
pytest tests/

# 특정 테스트
pytest tests/test_langgraph_enhanced.py

# 성능 벤치마크
python tests/performance_test/simple_benchmark.py
```

### 디버그 모드
```python
# workflow_router.py에서 디버그 출력
print(f"🔍 state 키: {list(state.keys())}")
print(f"   financial_data: {state.get('financial_data')}")
```

---

**작성자**: AI Assistant  
**최종 업데이트**: 2025-10-10  
**버전**: 1.0  

이 문서는 프로젝트의 모든 파일과 연결 관계를 상세히 설명합니다. 새로운 개발자가 코드베이스를 빠르게 이해하고 기여할 수 있도록 작성되었습니다.

