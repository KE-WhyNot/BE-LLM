# 금융 전문가 챗봇 (Financial Expert Chatbot)

RAG, LangChain, LangGraph, LangSmith를 활용한 고급 금융 분석 챗봇 시스템입니다.

## 🚀 주요 기능

### 1. RAG (Retrieval-Augmented Generation)
- **금융 지식 베이스**: 포괄적인 금융 지식 문서 저장
- **벡터 검색**: ChromaDB를 활용한 의미 기반 문서 검색
- **실시간 데이터**: Yahoo Finance API를 통한 주식 데이터 조회
- **한국어 임베딩**: ko-sroberta-multitask 모델 사용

### 2. LangChain 에이전트
- **도구 기반 응답**: 금융 데이터 조회, 분석, 뉴스 검색 도구
- **대화 메모리**: 최근 5개 대화 기억
- **멀티 LLM 지원**: OpenAI GPT-4, Google Gemini Pro
- **에러 핸들링**: 견고한 예외 처리 및 복구

### 3. LangGraph 워크플로우
- **복잡한 쿼리 처리**: 다단계 분석 워크플로우
- **상태 관리**: TypedDict 기반 상태 추적
- **조건부 라우팅**: 쿼리 유형별 처리 경로
- **병렬 처리**: 여러 도구의 동시 실행

### 4. LangSmith 모니터링
- **실시간 추적**: 모든 쿼리와 응답 추적
- **성능 메트릭**: 응답 시간, 성공률, 에러율
- **평가 시스템**: 정확성, 관련성, 안전성 평가
- **리포트 생성**: 자동화된 성능 리포트

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
│   (ChromaDB)    │    │   (LangSmith)   │    │   Base          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 프로젝트 구조

```
BE-LLM/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── config.py              # 설정 관리
│   ├── database.py            # 데이터베이스 연결
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py            # 채팅 API 라우터
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat_schema.py     # Pydantic 스키마
│   └── services/
│       ├── __init__.py
│       ├── rag_service.py     # RAG 시스템
│       ├── financial_agent.py # LangChain 에이전트
│       ├── financial_workflow.py # LangGraph 워크플로우
│       ├── monitoring_service.py # LangSmith 모니터링
│       ├── knowledge_base_service.py # 지식 베이스 관리
│       └── chatbot_service.py # 통합 챗봇 서비스
├── requirements.txt           # 의존성 패키지
└── README.md                 # 프로젝트 문서
```

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Google AI API Key (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# LangSmith 설정
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=financial-chatbot

# 데이터베이스 설정
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1/financial_db

# 벡터 데이터베이스 설정
CHROMA_PERSIST_DIRECTORY=./chroma_db
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

- **FastAPI**: 고성능 웹 프레임워크
- **LangChain**: LLM 애플리케이션 프레임워크
- **LangGraph**: 복잡한 워크플로우 관리
- **LangSmith**: LLM 모니터링 및 디버깅
- **ChromaDB**: 벡터 데이터베이스
- **HuggingFace**: 한국어 임베딩 모델
- **Yahoo Finance**: 실시간 주식 데이터
- **Pydantic**: 데이터 검증 및 직렬화

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

## 🚀 향후 개발 계획

1. **다국어 지원**: 영어, 일본어 등 추가 언어 지원
2. **음성 인터페이스**: STT/TTS 기능 추가
3. **포트폴리오 관리**: 개인 투자 포트폴리오 추천
4. **실시간 알림**: 주가 변동 알림 서비스
5. **모바일 앱**: React Native 기반 모바일 앱
6. **고급 분석**: 머신러닝 기반 예측 모델

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
LLM
