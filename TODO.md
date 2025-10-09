# 📋 배포 전 작업 목록 (TODO)

**최종 업데이트**: 2025-10-09  
**현재 브랜치**: PRJ-85-feature-chatbot-news-search  
**현재 상태**: 메타 에이전트 시스템 + 뉴스 검색 기능 완료 ✅

---

## 🔴 **우선순위: CRITICAL (배포 전 필수)**

### 1. ✅ 뉴스 검색 기능 async 처리 완료
**현재 상태**: 완료  
**완료 내용**:
- `NewsAgent.process()` async 처리 완료
- `workflow_router.py`에서 ThreadPoolExecutor로 async 함수 실행
- Google RSS 실시간 뉴스 수집 및 번역 정상 작동
- 테스트 완료: "삼성전자 뉴스 분석해줘" → 정상 응답

#### 관련 파일
- ✅ `app/services/langgraph_enhanced/agents/news_agent.py`
- ✅ `app/services/langgraph_enhanced/workflow_router.py`
- ✅ `app/services/workflow_components/news_service.py`
- ✅ `app/services/workflow_components/google_rss_translator.py`

---

### 2. 환경 변수 및 민감 정보 관리
**현재 상태**: ⚠️ 진행 중  
**목표**: 프로덕션 배포를 위한 보안 강화

#### 작업 내용

**2.1. 필수 환경 변수 확인 및 문서화**
- [ ] `.env.example` 파일 생성
  ```env
  # API Keys (필수)
  GOOGLE_API_KEY=your_google_api_key_here
  
  # LangSmith 설정 (선택)
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
  LANGCHAIN_API_KEY=your_langsmith_api_key_here
  LANGCHAIN_PROJECT=financial-chatbot
  
  # Neo4j 설정 (필수)
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_neo4j_password
  
  # Pinecone 설정 (필수)
  PINECONE_API_KEY=your_pinecone_api_key_here
  PINECONE_INDEX_NAME=finance-rag-index
  EMBEDDING_MODEL_NAME=kakaobank/kf-deberta-base
  BATCH_SIZE=32
  MAX_LENGTH=256
  TOP_K=20
  
  # 데이터베이스 (선택)
  DATABASE_URL=mysql+pymysql://user:password@localhost/db_name
  
  # 벡터 데이터베이스 (선택)
  CHROMA_PERSIST_DIRECTORY=./chroma_db
  
  # 서버 설정
  ENVIRONMENT=production
  DEBUG=false
  ```

**2.2. .gitignore 검증**
- [x] `.env` 파일이 gitignore에 포함되어 있는지 확인 (완료)
- [ ] 민감한 로그 파일 제외 확인
  - `server.log`
  - `*.log`
  - `.env*`

**2.3. 환경 변수 검증 로직 추가**
- [ ] `config.py`에 필수 환경 변수 검증 추가
  ```python
  def validate_env_vars():
      required_vars = [
          "GOOGLE_API_KEY",
          "NEO4J_URI",
          "PINECONE_API_KEY"
      ]
      missing = [var for var in required_vars if not getattr(settings, var.lower(), None)]
      if missing:
          raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
  ```

**2.4. 프로덕션 환경 설정**
- [ ] CORS 설정 강화 (`main.py`)
  ```python
  # 현재: allow_origins=["*"]  ← 개발용
  # 변경: allow_origins=["https://yourdomain.com"]  ← 프로덕션용
  ```

#### 예상 시간: 1시간

---

### 3. ✅ Neo4j GDS 임베딩 검색 시스템 구축 완료
**현재 상태**: ✅ 완료  
**완료 내용**:
- Neo4j 5.15.0 + GDS 2.6.9 설치
- 매일경제 RSS → Neo4j KG 저장 (253개 기사)
- 임베딩 기반 유사도 검색 정상 작동
- 한국어 임베딩 모델: kakaobank/kf-deberta-base (768차원)

#### 테스트 결과
```
'반도체' 검색:
  - "삼성전자·하이닉스가 세계 D램의 절반을?…" (유사도 0.457)
  - "오랜만에 듣는 '반도체 슈퍼사이클'…" (유사도 0.452)
  
'금리' 검색:
  - "'잔인한 금리' 포화 맞은 서민대출..." (유사도 0.378)
  - "먹고 살기도 빠듯해요"…서민금융..." (유사도 0.377)
```

#### 일일 자동 업데이트 설정
```bash
# 매일 아침 9시 자동 업데이트 (Cron)
0 9 * * * cd /Users/doyun/Desktop/KEF/BE-LLM && source venv/bin/activate && python daily_news_updater.py >> logs/daily_update.log 2>&1

# 수동 실행
python daily_news_updater.py
```

#### 환경 변수 (사용자가 직접 수정함)
```env
NEO4J_URI=bolt://localhost:7688  # 새 컨테이너
NEO4J_USER=neo4j
NEO4J_PASSWORD=financial123
```

---

### 4. requirements.txt 정리
**현재 상태**: ⚠️ 중복 및 미사용 패키지 존재

#### 작업 내용
- [ ] 중복 패키지 제거
  ```txt
  # 중복 발견
  sentence-transformers==5.1.0  # 라인 130
  sentence-transformers>=2.2.0  # 라인 171
  ```

- [ ] 미사용 패키지 확인 및 제거
  - `py2neo` (Neo4j 사용하지 않을 경우)
  - `openai` (Gemini만 사용)
  - `faiss-cpu` (Pinecone만 사용)

- [ ] 패키지 버전 고정
  ```bash
  pip freeze > requirements_frozen.txt
  # 프로덕션에서는 정확한 버전 사용
  ```

- [ ] `nest_asyncio` 추가 (뉴스 async 처리용)
  ```txt
  nest-asyncio==1.6.0
  ```

#### 예상 시간: 30분

---

## 🟡 **우선순위: HIGH (배포 전 권장)**

### 5. 코드 정리 (클린업)
**현재 상태**: ✅ 일부 완료  
**완료 내용**:
- ✅ `financial_workflow.py` - 레거시 워크플로우 로직 제거 (400줄 삭제)
- ✅ `response_generator_service.py` - 미사용 메서드 제거 (800줄 삭제)

#### 남은 작업
- [ ] 테스트 파일 정리
  ```
  tests/legacy/  ← 삭제 또는 아카이브
    - auto_news_test.py
    - news_analysis_test.py
    - simple_test.py
  
  tests/  ← 정리 필요
    - test_embedding_neo4j.py  # Neo4j 미사용 시 삭제
    - test_mk_rss_scraper.py  # Neo4j 미사용 시 삭제
    - test_rss_simple.py  # 중복
  ```

- [ ] 루트 디렉토리 테스트 파일 이동/삭제
  ```
  /test_analysis_integrated.py  → tests/
  /test_namespace_classification.py  → tests/
  /test_namespace_data.py  → tests/
  ```

- [ ] 문서 정리
  ```
  docs/IMPLEMENTATION_SUMMARY.md  # 삭제 (구버전)
  docs/TEST_GUIDE.md  # 업데이트 필요
  ```

- [ ] 디버그 로그 제거
  - `print()` 문을 `logger.debug()`로 변경
  - 프로덕션에서 불필요한 출력 제거

#### 예상 시간: 1-2시간

---

### 6. 에러 처리 강화
**현재 상태**: 기본 에러 처리만 존재

#### 작업 내용
- [ ] API 레이트 리밋 처리
  ```python
  # Google API, Pinecone API 호출 시 재시도 로직
  from tenacity import retry, stop_after_attempt, wait_exponential
  
  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
  def call_external_api():
      pass
  ```

- [ ] 타임아웃 설정
  ```python
  # news_agent.py의 뉴스 수집 타임아웃
  future.result(timeout=60)  # 이미 구현됨, 다른 곳도 확인 필요
  ```

- [ ] 에러 메시지 개선
  - 사용자에게 친절한 에러 메시지
  - 로그에는 상세한 스택 트레이스

- [ ] Fallback 전략 명확화
  ```python
  # WorkflowRouter 초기화 실패 시
  # 현재: "시스템을 사용할 수 없습니다" ← 너무 간단
  # 개선: 구체적인 원인과 해결 방법 제시
  ```

#### 예상 시간: 2시간

---

### 7. 성능 최적화
**현재 상태**: 기본 구현

#### 작업 내용
- [ ] LLM 응답 스트리밍
  ```python
  # ResponseAgent에서 스트리밍 응답 지원
  for chunk in llm.stream(prompt):
      yield chunk
  ```

- [ ] 캐싱 전략
  ```python
  # 주가 데이터 캐싱 (5분)
  @lru_cache(maxsize=100)
  def get_stock_price(symbol: str, cache_time: int = 300):
      pass
  ```

- [ ] Pinecone 배치 검색 최적화
  - 현재 top_k=20 → 필요한 경우만 높은 값 사용
  - 쿼리 임베딩 캐싱

- [ ] 병렬 처리 개선
  - `ParallelExecutor` 성능 모니터링
  - 불필요한 에이전트 실행 방지

#### 예상 시간: 3시간

---

## 🟢 **우선순위: MEDIUM (선택 사항)**

### 8. 테스트 커버리지 개선
**현재 상태**: 통합 테스트 부족

#### 작업 내용
- [ ] 단위 테스트 추가
  ```python
  # tests/test_news_agent.py
  def test_news_agent_async():
      agent = NewsAgent()
      result = asyncio.run(agent.process("삼성전자 뉴스", {...}))
      assert result['success'] == True
      assert len(result['news_data']) > 0
  ```

- [ ] E2E 테스트 추가
  ```python
  # tests/test_e2e_workflow.py
  def test_complete_workflow():
      response = client.post("/api/v1/chat", json={...})
      assert response.status_code == 200
  ```

- [ ] 성능 테스트
  ```bash
  python tests/performance_test/simple_benchmark.py
  ```

#### 예상 시간: 3-4시간

---

### 9. 모니터링 및 로깅 개선
**현재 상태**: LangSmith 트레이싱 활성화됨

#### 작업 내용
- [ ] 구조화된 로깅
  ```python
  import structlog
  logger = structlog.get_logger()
  logger.info("request_processed", user_id=1, query="...", duration_ms=123)
  ```

- [ ] 메트릭 수집
  - 응답 시간
  - 에러율
  - API 호출 횟수

- [ ] 알림 설정
  - 에러율 5% 이상 시 알림
  - 응답 시간 10초 이상 시 알림

#### 예상 시간: 2시간

---

### 10. 문서화 업데이트
**현재 상태**: 기본 문서 존재, 업데이트 필요

#### 작업 내용
- [ ] README.md 업데이트
  - 뉴스 검색 기능 추가 설명
  - 메타 에이전트 시스템 설명
  - 최신 API 예시

- [ ] API 문서 자동 생성
  ```python
  # FastAPI Swagger UI 개선
  @app.post("/api/v1/chat", summary="채팅 요청", description="...")
  ```

- [ ] 배포 가이드 작성
  - Docker 배포
  - 환경 변수 설정
  - 트러블슈팅

#### 예상 시간: 2시간

---

## 🟢 **우선순위: LOW (향후 개선)**

### 11. 사용자 프로필 기반 맞춤형 응답
**현재 상태**: 모의 데이터만 사용

#### 작업 내용
- [ ] 실제 DB 연동
- [ ] 사용자 투자 성향 분석
- [ ] 맞춤형 프롬프트 생성

#### 예상 시간: 3-4시간

---

### 12. 실시간 주식 데이터
**현재 상태**: yfinance (지연 데이터)

#### 작업 내용
- [ ] 한국투자증권 API 연동
- [ ] WebSocket 실시간 데이터

#### 예상 시간: 4-5시간

---

## 📊 **작업 우선순위 및 예상 시간**

| 우선순위 | 작업 | 예상 시간 | 상태 |
|---------|------|----------|------|
| 🔴 CRITICAL | 1. 뉴스 검색 async 처리 | 2시간 | ✅ 완료 |
| 🔴 CRITICAL | 2. 환경 변수 관리 | 1시간 | ⏳ 진행 중 |
| 🟡 CRITICAL | 3. Neo4j 안정성 | 2-3시간 | ⏳ 대기 |
| 🔴 CRITICAL | 4. requirements.txt 정리 | 30분 | ⏳ 대기 |
| 🟡 HIGH | 5. 코드 정리 | 1-2시간 | 🔄 일부 완료 |
| 🟡 HIGH | 6. 에러 처리 강화 | 2시간 | ⏳ 대기 |
| 🟡 HIGH | 7. 성능 최적화 | 3시간 | ⏳ 대기 |
| 🟢 MEDIUM | 8. 테스트 커버리지 | 3-4시간 | ⏳ 대기 |
| 🟢 MEDIUM | 9. 모니터링 개선 | 2시간 | ⏳ 대기 |
| 🟢 MEDIUM | 10. 문서화 업데이트 | 2시간 | ⏳ 대기 |
| 🟢 LOW | 11. 사용자 프로필 | 3-4시간 | 📅 향후 |
| 🟢 LOW | 12. 실시간 주식 데이터 | 4-5시간 | 📅 향후 |

**배포 전 필수 작업 시간**: 5.5 - 7.5시간  
**권장 작업 포함 시간**: 13.5 - 19.5시간  
**전체 작업 시간**: 30+ 시간

---

## 🎯 **배포 완료 기준**

### **필수 (Must Have) - 배포 전 반드시 완료**
- [x] 뉴스 검색 기능 정상 작동
- [ ] 환경 변수 검증 및 .env.example 파일 생성
- [ ] CORS 설정 프로덕션 환경으로 변경
- [ ] requirements.txt 정리 및 버전 고정
- [ ] 민감 정보 gitignore 확인
- [ ] 기본 에러 처리 및 fallback 전략
- [ ] 프로덕션 환경 테스트 1회 이상

### **권장 (Should Have) - 배포 후 빠르게 추가**
- [ ] 구조화된 로깅
- [ ] API 레이트 리밋 처리
- [ ] 테스트 커버리지 50% 이상
- [ ] README.md 최신화
- [ ] Neo4j GDS 오류 해결 또는 대체

### **선택 (Nice to Have) - 향후 개선**
- [ ] 성능 모니터링 대시보드
- [ ] 사용자 프로필 맞춤형 응답
- [ ] 실시간 주식 데이터
- [ ] Docker 배포 자동화

---

## 🚨 **현재 즉시 해결 필요한 이슈**

### 1. **nest_asyncio 설치 완료**
**상태**: ✅ 해결됨  
**해결 방법**: `pip install nest-asyncio==1.6.0`

### 2. **Neo4j GDS 함수 오류**
**상태**: ⚠️ 진행 중  
**오류**: `Unknown function 'gds.similarity.cosine'`  
**임시 해결**: Google RSS로 뉴스 수집 (정상 작동)  
**장기 해결**: Option 3 권장 (Pinecone으로 통합)

### 3. **프로덕션 CORS 설정**
**상태**: ⚠️ 개발용 설정  
**현재**: `allow_origins=["*"]`  
**변경 필요**: `allow_origins=["https://yourdomain.com"]`

---

## 📝 **다음 커밋 예정**

```bash
# 1. 뉴스 검색 완료 커밋
git add app/services/langgraph_enhanced/agents/news_agent.py
git add app/services/langgraph_enhanced/workflow_router.py
git commit -m "feat: 뉴스 검색 async 처리 완료 및 Google RSS 통합

- NewsAgent.process()를 async로 변경
- workflow_router에서 ThreadPoolExecutor로 async 함수 실행
- Google RSS 실시간 뉴스 수집 및 자동 번역
- nest_asyncio 패키지 추가
- 테스트 완료: 삼성전자 뉴스 분석 정상 작동

Related: PRJ-85-feature-chatbot-news-search"

# 2. 코드 정리 커밋 (이미 완료됨, 커밋 대기 중)
git add app/services/chatbot/financial_workflow.py
git add app/services/workflow_components/response_generator_service.py
git commit -m "refactor: 레거시 워크플로우 및 미사용 코드 제거

- financial_workflow.py: 레거시 워크플로우 로직 제거 (400줄)
- response_generator_service.py: 미사용 메서드 제거 (800줄)
- 메타 에이전트 시스템만 유지
- 코드베이스 간소화 및 유지보수성 향상

Related: PRJ-85-feature-chatbot-news-search"

# 3. 환경 변수 및 보안 강화 커밋 (작업 예정)
git add .env.example
git add app/config.py
git add app/main.py
git commit -m "feat: 프로덕션 배포를 위한 보안 및 환경 변수 관리 강화

- .env.example 파일 추가
- 필수 환경 변수 검증 로직 추가
- CORS 설정 프로덕션 환경으로 변경
- requirements.txt 정리 및 버전 고정

Related: PRJ-85-feature-chatbot-news-search"
```

---

## 📞 **문의 및 이슈**

이슈가 발생하거나 질문이 있으면:
1. `CODEBASE_ANALYSIS_REPORT.md` 확인
2. `docs/DEPLOYMENT_CHECKLIST.md` 확인
3. `ARCHITECTURE.md` 참고
4. Git 이슈 등록

---

**마지막 업데이트**: 2025-10-09  
**작성자**: AI Assistant  
**다음 리뷰 일정**: 배포 전 최종 검토
