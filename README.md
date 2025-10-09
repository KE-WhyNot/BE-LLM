# 금융 전문가 챗봇 (Financial Expert Chatbot)

RAG, LangChain, LangGraph, LangSmith를 활용한 고급 금융 분석 챗봇 시스템입니다.

## 🚀 주요 기능

### 1. RAG (Retrieval-Augmented Generation)
- **금융 지식 베이스**: Pinecone 벡터 DB를 활용한 의미 기반 검색
- **실시간 데이터**: Yahoo Finance API를 통한 주식 데이터 조회
- **한국어 임베딩**: kakaobank/kf-deberta-base 모델 (768차원)
- **멀티 네임스페이스**: 재무제표, 시장분석, 투자전략별 분리 저장

### 2. 뉴스 지식 그래프 (Neo4j)
- **매일경제 RSS**: 경제/증권/국제/정치 뉴스 수집 및 저장
- **관계 그래프**: 30,000+ 관계 (SIMILAR_TO, SAME_CATEGORY, MENTIONS)
- **임베딩 검색**: GDS 코사인 유사도 기반 뉴스 검색
- **일일 업데이트**: 자동 크론잡으로 최신 뉴스 수집

### 3. 메타 에이전트 시스템 (LangGraph)
- **지능형 라우팅**: 쿼리 분석 후 최적 에이전트 선택
- **11개 전문 에이전트**: News, Data, Analysis, Knowledge, Visualization 등
- **병렬 실행**: 독립적 태스크 동시 처리
- **Fallback 전략**: 실패 시 자동 대체 경로

### 4. LangSmith 모니터링
- **실시간 추적**: 모든 쿼리와 응답 추적
- **성능 메트릭**: 응답 시간, 성공률, 에러율
- **워크플로우 추적**: LangGraph 실행 흐름 시각화
- **에러 분석**: 실패 패턴 감지 및 알림

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   LangChain     │    │   LangGraph     │
│   Router        │───▶│   Agent         │───▶│   Workflow      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Service   │    │   Monitoring    │    │   Knowledge     │
│   (Pinecone)    │    │   (LangSmith)   │    │   Graph (Neo4j) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 프로젝트 구조

```
BE-LLM/
├── app/
│   ├── main.py                     # FastAPI 애플리케이션
│   ├── config.py                   # 설정 관리
│   ├── routers/
│   │   └── chat.py                 # 채팅 API 라우터
│   ├── schemas/
│   │   ├── chat_schema.py          # Pydantic 스키마
│   │   └── user_schema.py
│   └── services/
│       ├── langgraph_enhanced/     # 메타 에이전트 시스템
│       │   ├── agents/             # 11개 전문 에이전트
│       │   ├── workflow_router.py  # 워크플로우 라우터
│       │   └── llm_manager.py      # LLM 관리
│       ├── workflow_components/    # 워크플로우 컴포넌트
│       │   ├── mk_rss_scraper.py   # 매일경제 RSS + Neo4j
│       │   ├── news_service.py     # 뉴스 통합 서비스
│       │   └── google_rss_translator.py  # Google RSS
│       ├── pinecone_rag_service.py # Pinecone RAG
│       ├── portfolio/              # 포트폴리오 분석
│       └── chatbot_service.py      # 통합 챗봇 서비스
├── config/
│   └── stocks.yaml                 # 58개 종목 설정
├── requirements.txt                # 의존성 (74줄로 최적화)
├── daily_news_updater.py           # 일일 뉴스 업데이트 크론
└── README.md
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

- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangChain**: LLM 애플리케이션 프레임워크
- **LangGraph**: 메타 에이전트 워크플로우 관리
- **LangSmith**: LLM 모니터링 및 디버깅
- **Google Gemini**: 2.0 Flash Exp 모델 (저비용 고성능)
- **Pinecone**: 클라우드 벡터 데이터베이스 (RAG)
- **Neo4j Aura**: 관리형 그래프 데이터베이스 + GDS
- **Sentence Transformers**: kakaobank/kf-deberta-base (한국어 임베딩)
- **Yahoo Finance**: 실시간 주식 데이터
- **Deep Translator**: 뉴스 자동 번역
- **APScheduler**: 일일 자동 뉴스 수집

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

## 🚀 최근 업데이트 (2025-10-09)

✅ **완료된 작업:**
1. Neo4j Aura 연동 및 30,283개 관계 그래프 구축
2. requirements.txt 최적화 (170줄 → 74줄, 56% 감소)
3. 매일경제 RSS 자동 수집 시스템 구축
4. 메타 에이전트 시스템 안정화
5. 레거시 코드 제거 및 문서 정리

📋 **향후 계획:**
1. 사용자 프로필 기반 맞춤형 응답
2. 실시간 주식 알림 서비스
3. 포트폴리오 자동 리밸런싱
4. 모바일 앱 개발
5. 고급 차트 분석 (캔들스틱, 이동평균)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**⚠️ 주의사항**: 이 챗봇은 교육 및 참고 목적으로 제작되었습니다. 실제 투자 결정은 신중히 하시고, 전문가의 조언을 구하시기 바랍니다.
