# 📁 프로젝트 구조

```
BE-LLM/
├── app/                          # 메인 애플리케이션
│   ├── main.py                   # FastAPI 앱 진입점
│   ├── config.py                 # 설정 관리
│   ├── routers/                  # API 라우터
│   ├── schemas/                  # Pydantic 스키마
│   ├── services/                 # 비즈니스 로직
│   │   ├── chatbot/              # 챗봇 서비스
│   │   ├── langgraph_enhanced/   # LangGraph 워크플로우
│   │   ├── portfolio/            # 포트폴리오 서비스
│   │   ├── workflow_components/  # 워크플로우 컴포넌트
│   │   ├── pinecone_rag_service.py  # Pinecone RAG
│   │   └── pinecone_config.py    # Pinecone 설정
│   └── utils/                    # 유틸리티 함수
│
├── config/                       # 설정 파일
│   └── stocks.yaml               # 주식 설정
│
├── data/                         # 데이터 파일
│   └── *.txt                     # 금융 지식 베이스
│
├── docs/                         # 📚 문서 (NEW)
│   ├── DATA_AGENT_README.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── IMPROVEMENT_REPORT.md
│   └── TEST_GUIDE.md
│
├── logs/                         # 📊 로그 파일 (NEW)
│   └── server.log
│
├── tests/                        # 테스트 파일
│   ├── performance_test/         # 성능 테스트 (MOVED)
│   ├── legacy/                   # 레거시 테스트
│   ├── examples/                 # 예시 코드
│   ├── test_*.py                 # 각종 테스트
│   └── README.md
│
├── run_server.py                 # 🚀 서버 실행 스크립트
├── chat_terminal.py              # 💬 터미널 채팅 클라이언트
├── requirements.txt              # Python 패키지 의존성
│
├── README.md                     # 프로젝트 개요
├── ARCHITECTURE.md               # 시스템 아키텍처
├── SYSTEM_STRATEGY.md            # 시스템 전략
└── TODO.md                       # 할 일 목록
```

## 🎯 주요 변경사항

### ✅ 정리 완료
1. **docs/ 디렉토리 생성** - 문서 파일 정리
2. **logs/ 디렉토리 생성** - 로그 파일 정리
3. **ChromaDB 삭제** - Pinecone으로 전환
4. **테스트 파일 통합** - 모든 테스트를 tests/로

### 📍 실행 방법

**서버 실행:**
```bash
source venv/bin/activate
python run_server.py
```

**채팅 터미널:**
```bash
source venv/bin/activate
python chat_terminal.py
```

### 🔧 환경 설정

`.env` 파일에 다음 설정 추가:
```bash
# Pinecone 설정
PINECONE_API_KEY=your_api_key
PINECONE_INDEX_NAME=finance-rag-index
EMBEDDING_MODEL_NAME=kakaobank/kf-deberta-base

# Google API
GOOGLE_API_KEY=your_google_api_key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```
