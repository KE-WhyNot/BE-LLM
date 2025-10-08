# 🧪 시스템 테스트 가이드

## 📋 테스트 전 체크리스트

### 1. Neo4j 지식 그래프 실행 (필수)

매일경제 뉴스 RAG를 사용하려면 Neo4j가 실행되어야 합니다.

```bash
# Docker로 Neo4j 실행
docker run -d \
  --name neo4j-financial \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/financial123 \
  neo4j:latest

# 또는 기존 컨테이너가 있다면 시작
docker start neo4j-financial
```

**Neo4j 브라우저 접속**: http://localhost:7474
- Username: `neo4j`
- Password: `financial123`

### 2. 환경 변수 확인

`.env` 파일에 다음 설정이 있는지 확인:

```env
# Google AI API Key (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# Neo4j 설정
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=financial123

# LangSmith (선택)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
```

### 3. 의존성 설치 확인

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 시스템 실행 방법

### 방법 1: FastAPI 서버 실행 + chat_terminal.py

#### Step 1: 서버 실행 (터미널 1)

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate
python run_server.py
```

서버가 실행되면 다음과 같은 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

#### Step 2: 채팅 터미널 실행 (터미널 2)

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate
python chat_terminal.py
```

---

## 📊 지식 그래프 상태 확인

### Neo4j 연결 테스트

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate

# 간단한 연결 테스트
python -c "
from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService
import asyncio

async def test():
    kg = MKKnowledgeGraphService()
    if kg.driver:
        print('✅ Neo4j 연결 성공!')
        # 노드 수 확인
        with kg.driver.session() as session:
            result = session.run('MATCH (n:NewsArticle) RETURN count(n) as count')
            count = result.single()['count']
            print(f'📰 저장된 뉴스 기사: {count}개')
    else:
        print('❌ Neo4j 연결 실패')

asyncio.run(test())
"
```

### 매일경제 뉴스 수집 및 임베딩 (초기 설정)

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate

python -c "
from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService
import asyncio

async def update_knowledge_base():
    print('📰 매일경제 RSS 뉴스 수집 시작...')
    kg = MKKnowledgeGraphService()
    await kg.update_knowledge_graph()
    print('✅ 지식 그래프 업데이트 완료!')

asyncio.run(update_knowledge_base())
"
```

**예상 소요 시간**: 5-10분 (뉴스 수집, 임베딩 생성, Neo4j 저장)

---

## 💬 테스트 시나리오

### 1. 매일경제 Neo4j RAG 테스트

```
💬 당신: 삼성전자 관련 최신 뉴스 알려줘
```

**예상 동작**:
- 매일경제 Neo4j에서 임베딩 기반 검색
- 관련도 높은 뉴스 3개 우선 반환
- Google RSS 실시간 뉴스 추가
- 중복 제거 후 최종 응답

### 2. Google RSS 실시간 번역 테스트

```
💬 당신: Apple stock news
```

**예상 동작**:
- Google RSS에서 영문 뉴스 검색
- 한국어로 자동 번역
- 최신순으로 정렬

### 3. 종합 금융 분석 테스트

```
💬 당신: 카카오 주가 분석해줘
```

**예상 동작**:
- 실시간 주가 데이터 조회
- 기술적 분석 (이동평균, RSI 등)
- 관련 뉴스 검색 (매일경제 + Google RSS)
- 종합 투자 의견 생성

### 4. 시각화 테스트

```
💬 당신: 네이버 차트 보여줘
```

**예상 동작**:
- 주가 데이터 조회
- 차트 이미지 생성
- 기술적 지표 추가

### 5. 금융 지식 RAG 테스트

```
💬 당신: PER이 뭐야?
```

**예상 동작**:
- ChromaDB에서 금융 지식 검색
- RAG 기반 답변 생성
- 예시와 함께 설명

---

## 🔍 디버깅 및 로그 확인

### 1. 서버 로그 확인

```bash
tail -f /Users/doyun/Desktop/KEF/BE-LLM/server.log
```

### 2. Neo4j 브라우저에서 데이터 확인

http://localhost:7474 접속 후 다음 쿼리 실행:

```cypher
// 전체 뉴스 기사 수
MATCH (n:NewsArticle) RETURN count(n) as total_articles

// 최근 뉴스 10개
MATCH (n:NewsArticle) 
RETURN n.title, n.published_date, n.category 
ORDER BY n.published_date DESC 
LIMIT 10

// 카테고리별 분포
MATCH (n:NewsArticle) 
RETURN n.category, count(n) as count 
ORDER BY count DESC

// 특정 키워드 검색 (예: 삼성)
MATCH (n:NewsArticle) 
WHERE n.title CONTAINS '삼성' OR n.summary CONTAINS '삼성'
RETURN n.title, n.published_date
LIMIT 5
```

### 3. 워크플로우 추적

LangSmith 대시보드에서 실시간 추적:
- https://smith.langchain.com/

---

## ⚠️ 문제 해결

### Neo4j 연결 실패

```bash
# Neo4j 컨테이너 상태 확인
docker ps -a | grep neo4j

# Neo4j 재시작
docker restart neo4j-financial

# 로그 확인
docker logs neo4j-financial
```

### 모듈 없음 오류

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate
pip install -r requirements.txt
```

### 서버 포트 충돌

```bash
# 8001 포트 사용 중인 프로세스 확인
lsof -i :8001

# 프로세스 종료
kill -9 <PID>
```

### 임베딩 모델 다운로드 느림

첫 실행 시 `kakaobank/kf-deberta-base` 모델을 다운로드합니다 (~500MB).
인터넷 연결이 느리면 시간이 걸릴 수 있습니다.

---

## 📈 성능 모니터링

### 1. 메트릭 조회

```bash
curl http://localhost:8001/api/v1/chat/metrics
```

### 2. 지식 베이스 통계

```bash
curl http://localhost:8001/api/v1/chat/knowledge-base/stats
```

### 3. 성능 리포트

```bash
curl http://localhost:8001/api/v1/chat/report
```

---

## 🎯 주요 기능 확인 체크리스트

- [ ] Neo4j 실행 및 연결 확인
- [ ] 매일경제 RSS 뉴스 수집 (초기 1회)
- [ ] FastAPI 서버 실행
- [ ] chat_terminal.py로 채팅 테스트
- [ ] 매일경제 Neo4j RAG 검색 동작 확인
- [ ] Google RSS 실시간 번역 동작 확인
- [ ] 주가 데이터 조회 동작 확인
- [ ] 차트 생성 동작 확인
- [ ] 금융 지식 RAG 동작 확인
- [ ] LangGraph 워크플로우 분기 확인

---

## 📝 추가 참고 사항

### 지식 그래프 업데이트 주기

매일경제 뉴스는 **수동 업데이트** 방식입니다. 주기적으로 다음 명령어 실행:

```bash
cd /Users/doyun/Desktop/KEF/BE-LLM
source venv/bin/activate

python -c "
from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService
import asyncio
asyncio.run(MKKnowledgeGraphService().update_knowledge_graph())
"
```

### Google RSS는 실시간

사용자 요청 시마다 실시간으로 Google RSS에서 뉴스를 가져와 번역합니다.

### 모델 선택

- **임베딩**: `kakaobank/kf-deberta-base` (한국 금융 특화)
- **LLM**: `gemini-2.0-flash-exp` (빠른 응답)
- **관계 추출**: `kakaobank/kf-deberta-base` (Data Agent용)

---

## 🎉 테스트 완료 후

모든 기능이 정상 동작하면 다음 단계로 진행:

1. **프로덕션 배포**: `DEPLOYMENT_CHECKLIST.md` 참고
2. **성능 최적화**: Redis 캐싱 도입 (TODO 참고)
3. **모니터링 강화**: LangSmith 대시보드 활용

---

**작성일**: 2025-10-05
**버전**: 1.0.0
