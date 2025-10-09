# 🚀 동적 프롬프팅 챗봇 배포 전 체크리스트

**작성일**: 2025-01-05  
**대상 시스템**: LangGraph Enhanced (Gemini 2.0 Flash 전용) + 동적 프롬프팅

---

## 📋 **현재 시스템 상태 분석**

### ✅ **완료된 항목**

#### 1. **LangGraph Enhanced 시스템**
- ✅ `llm_manager.py`: Gemini 전용 LLM 관리자
- ✅ `model_selector.py`: Gemini 전용 모델 선택기
- ✅ `prompt_manager.py`: 중앙화된 프롬프트 관리자 (구현됨, 미통합)
- ✅ `config.py`: 동적 환경변수 설정
- ✅ `error_handler.py`: 통합 에러 핸들링
- ✅ `simplified_intelligent_workflow.py`: 간소화된 지능형 워크플로우
- ✅ `components/`: 단일 책임 원칙에 따른 컴포넌트 분리
  - QueryComplexityAnalyzer
  - ServicePlanner
  - ServiceExecutor
  - ResultCombiner
  - ConfidenceCalculator

#### 2. **Workflow Components**
- ✅ `query_classifier_service.py`: 쿼리 분류
- ✅ `financial_data_service.py`: 주식 데이터 조회
- ✅ `analysis_service.py`: AI 분석 서비스
- ✅ `news_service.py`: 뉴스 수집 (현재 더미 데이터 사용)
- ✅ `response_generator_service.py`: 응답 생성
- ✅ `visualization_service.py`: 차트 생성
- ✅ `data_agent_service.py`: 뉴스 수집 및 관계 추출 (KF-DeBERTa)

#### 3. **통합 시스템**
- ✅ `chatbot_service.py`: 메인 챗봇 서비스 (지능형 워크플로우 자동 선택)
- ✅ `financial_workflow.py`: LangGraph 기반 워크플로우 (기본 + 지능형)
- ✅ `user_service.py`: 사용자 프로필 관리 (모의 데이터)
- ✅ RAG 서비스: ChromaDB + HuggingFace Embeddings

---

## ⚠️ **미완료 항목 (배포 전 필수)**

### 🔴 **1. 동적 프롬프팅 통합 (최우선)**

#### 문제점
- `prompt_manager.py`가 구현되어 있지만 **실제 서비스에 통합되지 않음**
- 현재 `analysis_service.py`, `news_service.py`, `response_generator_service.py` 등에서 **하드코딩된 프롬프트 사용**

#### 해야 할 작업
```python
# 통합 필요 파일:
1. app/services/workflow_components/analysis_service.py
   - generate_analysis() → prompt_manager.generate_analysis_prompt() 사용

2. app/services/workflow_components/news_service.py
   - get_news() → prompt_manager.generate_news_prompt() 사용

3. app/services/workflow_components/response_generator_service.py
   - generate_response() → prompt_manager의 각종 프롬프트 사용

4. app/services/workflow_components/query_classifier_service.py
   - classify() → prompt_manager.generate_classification_prompt() 사용

5. app/services/langgraph_enhanced/simplified_intelligent_workflow.py
   - _generate_final_response() → prompt_manager 통합
```

#### 우선순위: 🔴 **HIGH**

---

### 🟡 **2. 뉴스 웹스크래핑 구현 (중요)**

#### 문제점
- `data_agent_service.py`가 RSS 피드 파싱 실패 시 **더미 데이터 생성**
- 실제 뉴스 사이트 접근 불가 (봇 차단, RSS 파싱 오류)

#### 해야 할 작업
```python
# 새로운 파일 생성:
1. app/services/workflow_components/news_scraper.py
   - RealNewsCollector 클래스 구현
   - BeautifulSoup + requests로 실제 뉴스 수집
   - Naver/Daum/연합뉴스 등 웹 스크래핑

2. app/services/workflow_components/data_agent_service.py 수정
   - NewsCollector 클래스의 collect_news() 메서드 개선
   - 더미 데이터 대신 실제 웹 스크래핑 사용

3. app/services/workflow_components/news_service.py 통합
   - 실제 뉴스 데이터를 챗봇 응답에 사용
```

#### 우선순위: 🟡 **MEDIUM**

---

### 🟢 **3. 사용자 프로필 기반 동적 프롬프팅 (추가 기능)**

#### 문제점
- `user_service.py`가 모의 데이터만 제공
- 사용자 프로필이 프롬프트 생성에 반영되지 않음

#### 해야 할 작업
```python
# 통합 작업:
1. app/services/user_service.py 개선
   - 실제 DB 또는 외부 API 연동
   - 사용자 투자 성향, 포트폴리오, 관심사 수집

2. prompt_manager.py의 동적 프롬프트 활용
   - generate_analysis_prompt(user_context=user_profile)
   - 사용자 경험 레벨에 맞는 설명 수준 조정

3. simplified_intelligent_workflow.py에 사용자 컨텍스트 전달
   - process_query(query, user_id, session_id) → 사용자 프로필 자동 로드
```

#### 우선순위: 🟢 **LOW** (선택 사항)

---

### 🟢 **4. Neo4j 지식 그래프 통합 (선택)**

#### 문제점
- `data_agent_service.py`가 Neo4j 연결 실패 (py2neo 미설치)
- 관계 추출 결과가 지식 그래프에 저장되지 않음

#### 해야 할 작업
```bash
# 설치:
pip install py2neo

# 환경변수 설정:
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Neo4j 실행:
neo4j start
```

#### 우선순위: 🟢 **LOW** (선택 사항)

---

## 🛠️ **배포 전 필수 작업 목록**

### **Phase 1: 동적 프롬프팅 통합 (1-2시간)**

1. **`analysis_service.py` 수정**
   ```python
   from app.services.langgraph_enhanced import prompt_manager
   
   # 기존 하드코딩 프롬프트 제거
   # prompt_manager.generate_analysis_prompt() 사용
   ```

2. **`news_service.py` 수정**
   ```python
   from app.services.langgraph_enhanced import prompt_manager
   
   # prompt_manager.generate_news_prompt() 사용
   ```

3. **`response_generator_service.py` 수정**
   ```python
   from app.services.langgraph_enhanced import prompt_manager
   
   # 각 응답 유형별로 prompt_manager 메서드 사용
   ```

4. **`query_classifier_service.py` 수정**
   ```python
   from app.services.langgraph_enhanced import prompt_manager
   
   # prompt_manager.generate_classification_prompt() 사용
   ```

5. **통합 테스트 실행**
   ```bash
   python -m pytest tests/ -v
   ```

---

### **Phase 2: 뉴스 웹스크래핑 구현 (2-3시간)**

1. **`news_scraper.py` 생성**
   - Naver, Daum, 연합뉴스 웹 스크래핑
   - 금융 키워드 필터링
   - 10개 뉴스 수집 제한

2. **`data_agent_service.py` 수정**
   - `_parse_rss_feed()` 메서드 개선
   - 더미 데이터 대신 `news_scraper` 사용

3. **`news_service.py` 통합**
   - 실제 뉴스 데이터 사용

4. **웹 스크래핑 테스트**
   ```bash
   python tests/test_news_scraper.py
   ```

---

### **Phase 3: 최종 테스트 및 배포 (1시간)**

1. **통합 테스트**
   ```bash
   # 서버 실행
   python run_server.py --port 8001
   
   # 터미널 챗봇 테스트
   python chat_terminal.py
   ```

2. **LangSmith 트레이싱 확인**
   - https://smith.langchain.com
   - 동적 프롬프팅 동작 확인
   - 워크플로우 분기 추적

3. **성능 벤치마크**
   ```bash
   python performance_test/simple_benchmark.py
   ```

4. **Git 커밋**
   ```bash
   git add .
   git commit -m "feat: 동적 프롬프팅 통합 및 뉴스 웹스크래핑 구현"
   git push origin PRJ-85-feature-chatbot-news-search
   ```

---

## 📊 **예상 작업 시간**

| 작업 | 예상 시간 | 우선순위 |
|------|----------|---------|
| 동적 프롬프팅 통합 | 1-2시간 | 🔴 HIGH |
| 뉴스 웹스크래핑 구현 | 2-3시간 | 🟡 MEDIUM |
| 사용자 프로필 통합 | 1-2시간 | 🟢 LOW |
| Neo4j 통합 | 1시간 | 🟢 LOW |
| 최종 테스트 및 배포 | 1시간 | 🔴 HIGH |

**총 예상 시간**: 4-6시간 (필수 작업만)

---

## 🎯 **배포 완료 기준**

### **필수 (Must Have)**
- ✅ 동적 프롬프팅이 모든 서비스에 통합됨
- ✅ 실제 뉴스 데이터 수집 기능 작동
- ✅ 지능형 워크플로우가 자동으로 선택됨
- ✅ LangSmith 트레이싱이 정상 작동
- ✅ 터미널 챗봇이 정상 응답

### **선택 (Nice to Have)**
- ⚪ 사용자 프로필 기반 맞춤형 응답
- ⚪ Neo4j 지식 그래프 통합
- ⚪ 실시간 주식 데이터 업데이트
- ⚪ 차트 생성 최적화

---

## 🚨 **현재 즉시 해결 필요한 이슈**

### 1. **Prompt Manager 미통합**
**파일**: `analysis_service.py`, `news_service.py`, `response_generator_service.py`, `query_classifier_service.py`  
**문제**: 하드코딩된 프롬프트 사용  
**해결**: `prompt_manager` import 및 메서드 호출로 변경

### 2. **더미 뉴스 데이터**
**파일**: `data_agent_service.py`, `news_service.py`  
**문제**: RSS 파싱 실패 시 더미 데이터 생성  
**해결**: 웹 스크래핑으로 실제 뉴스 수집

### 3. **사용자 프로필 미활용**
**파일**: `user_service.py`  
**문제**: 모의 데이터만 제공, 동적 프롬프팅에 미반영  
**해결**: 사용자 프로필을 `prompt_manager`에 전달

---

## 📝 **다음 커밋 메시지 (추천)**

```bash
# Phase 1: 동적 프롬프팅 통합
git commit -m "feat: 동적 프롬프팅 시스템을 모든 워크플로우 서비스에 통합

- prompt_manager를 analysis_service, news_service, response_generator_service에 통합
- 하드코딩된 프롬프트를 중앙화된 prompt_manager로 교체
- 사용자 프로필 기반 동적 프롬프트 생성 지원
- LangSmith 트레이싱으로 프롬프트 동작 확인 가능

Related: PRJ-85-feature-chatbot-news-search"

# Phase 2: 뉴스 웹스크래핑 구현
git commit -m "feat: 실제 뉴스 웹스크래핑 기능 구현

- news_scraper.py 생성: Naver/Daum/연합뉴스 웹 스크래핑
- data_agent_service.py 개선: 더미 데이터 대신 실제 뉴스 사용
- 금융 키워드 필터링으로 관련 뉴스만 수집
- KF-DeBERTa 모델로 관계 추출 정상 작동

Related: PRJ-85-feature-chatbot-news-search"
```

---

## 🎉 **배포 후 확인사항**

1. **LangSmith 대시보드**
   - 동적 프롬프트 생성 확인
   - 워크플로우 분기 추적
   - 응답 품질 모니터링

2. **로그 확인**
   - 뉴스 수집 성공 여부
   - 프롬프트 생성 정상 작동
   - 에러 발생 여부

3. **사용자 테스트**
   - 터미널 챗봇으로 다양한 쿼리 테스트
   - 동적 프롬프팅 응답 품질 확인
   - 실제 뉴스 데이터 정확도 검증

---

**작성자**: AI Assistant  
**검토 필요**: 배포 담당자  
**최종 업데이트**: 2025-01-05

