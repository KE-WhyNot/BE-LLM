# 📋 남은 작업 목록 (TODO)

**최종 업데이트**: 2025-01-05  
**현재 상태**: 동적 프롬프팅 시스템 통합 완료 ✅

---

## 🔴 **우선순위: HIGH (필수)**

### 1. 뉴스 웹스크래핑 구현
**현재 상태**: 더미 데이터 사용 중  
**목표**: 실제 한국 뉴스 사이트에서 금융 뉴스 수집

#### 작업 내용
- [ ] `app/services/workflow_components/news_scraper.py` 생성
  - Naver 뉴스 스크래핑
  - Daum 뉴스 스크래핑
  - 연합뉴스 스크래핑
  - 금융 키워드 필터링
  
- [ ] `data_agent_service.py` 개선
  - RSS 피드 실패 시 웹 스크래핑으로 대체
  - 더미 데이터 생성 로직 제거 또는 최후의 fallback으로 변경
  
- [ ] `news_service.py` 통합
  - 실제 스크래핑된 뉴스 사용
  - 뉴스 캐싱 추가 (중복 요청 방지)

#### 예상 시간: 2-3시간

#### 참고 코드
```python
# 기본 구조 예시
class RealNewsCollector:
    def scrape_naver_news(self, query: str, limit: int = 10):
        # BeautifulSoup으로 Naver 뉴스 스크래핑
        pass
    
    def scrape_daum_news(self, query: str, limit: int = 10):
        # BeautifulSoup으로 Daum 뉴스 스크래핑
        pass
```

---

## 🟡 **우선순위: MEDIUM (중요)**

### 2. Neo4j 지식 그래프 연동
**현재 상태**: py2neo 미설치, 연결 실패  
**목표**: KF-DeBERTa로 추출한 관계를 Neo4j에 저장

#### 작업 내용
- [ ] Neo4j 설치 및 실행
  ```bash
  brew install neo4j
  neo4j start
  ```

- [ ] py2neo 설치
  ```bash
  pip install py2neo
  ```

- [ ] 환경변수 설정
  ```bash
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
  ```

- [ ] `data_agent_service.py` 테스트
  - 뉴스 수집 → 관계 추출 → Neo4j 저장 전체 파이프라인 확인

#### 예상 시간: 1-2시간

---

### 3. 사용자 프로필 DB 연동
**현재 상태**: 모의 데이터 (`user_service.py`)  
**목표**: 실제 DB 또는 외부 API에서 사용자 정보 가져오기

#### 작업 내용
- [ ] `user_service.py` 개선
  - 실제 DB 연결 (PostgreSQL/MySQL)
  - 또는 외부 API 연동
  
- [ ] 사용자 프로필 필드 확장
  - 투자 성향 (공격형/안정형)
  - 보유 포트폴리오
  - 관심 종목
  - 투자 경험 레벨
  
- [ ] 동적 프롬프팅 연동
  - `prompt_manager`에 사용자 프로필 전달
  - 맞춤형 분석 제공

#### 예상 시간: 2-3시간

---

## 🟢 **우선순위: LOW (선택 사항)**

### 4. 실시간 주식 데이터 업데이트
**현재 상태**: yfinance API 사용 (지연 데이터)  
**목표**: 실시간 또는 준실시간 주식 데이터

#### 작업 내용
- [ ] 실시간 데이터 소스 조사
  - 한국투자증권 API
  - 키움증권 API
  - 네이버 금융 API
  
- [ ] `financial_data_service.py` 개선
  - 실시간 데이터 연동
  - 캐싱 전략 (불필요한 API 호출 방지)

#### 예상 시간: 3-4시간

---

### 5. 차트 생성 최적화
**현재 상태**: matplotlib으로 기본 차트 생성  
**목표**: 더 빠르고 예쁜 차트

#### 작업 내용
- [ ] 차트 캐싱
  - 동일 종목/기간 요청 시 캐시 사용
  
- [ ] 차트 스타일 개선
  - 전문적인 차트 템플릿
  - 한국어 폰트 최적화
  
- [ ] 차트 종류 확장
  - 볼린저 밴드
  - MACD
  - RSI

#### 예상 시간: 2-3시간

---

### 6. 성능 최적화
**현재 상태**: 기본 구현  
**목표**: 응답 시간 단축

#### 작업 내용
- [x] LLM 호출 최적화
  - 프롬프트 길이 줄이기 (PromptManager 구현)
  - 불필요한 LLM 호출 제거 (캐싱 전략)
  
- [x] 서비스 병렬 처리
  - 데이터 조회 + 뉴스 조회 동시 실행 (ServiceExecutor 구현)
  - ThreadPoolExecutor 사용

## 완료된 작업 (2025-01-05)

### 1. LangGraph 동적 프롬프팅 시스템 구축 ✅
- SimplifiedIntelligentWorkflow 구현
- QueryComplexityAnalyzer: 쿼리 복잡도 분석
- ServicePlanner: 서비스 실행 계획 수립
- ServiceExecutor: 병렬 서비스 실행
- ResultCombiner: 결과 조합
- ConfidenceCalculator: 신뢰도 계산
- PromptManager: 동적 프롬프트 생성

### 2. Neo4j 지식그래프 RAG 시스템 구축 ✅
- 매일경제 RSS 피드 스크래퍼 (mk_rss_scraper.py)
- KF-DeBERTa 임베딩 (카카오뱅크 금융 특화 모델)
- Neo4j 노드 및 관계 생성
- 코사인 유사도 기반 검색
- 수동 업데이트 시스템

### 3. Google RSS 실시간 뉴스 번역 시스템 구축 ✅
- google_rss_translator.py 구현
- deep-translator 라이브러리 사용
- 영어 → 한국어 자동 번역
- 실시간 뉴스 검색

### 4. 통합 뉴스 서비스 구축 ✅
- news_service.py 업데이트
- 3가지 뉴스 소스 통합:
  1. 매일경제 Neo4j RAG (수동 업데이트)
  2. Google RSS (실시간 + 번역)
  3. 기존 RSS (폴백)
- 중복 제거 (URL + 제목 유사도)
- 관련도 + 최신순 정렬

### 5. 클린코드 6원칙 준수 ✅
- 단일 책임 원칙 (SRP)
- 개방-폐쇄 원칙 (OCP)
- 리스코프 치환 원칙 (LSP)
- 인터페이스 분리 원칙 (ISP)
- 의존성 역전 원칙 (DIP)
- DRY 원칙

### 6. ARCHITECTURE.md 업데이트 ✅
- 전체 시스템 아키텍처 문서화
- 클린코드 원칙 설명
- LangGraph 동적 프롬프팅 플로우
- Neo4j RAG 시스템 구조
- 뉴스 처리 플로우
- 성능 최적화 전략
  
- [ ] 캐싱 전략
  - Redis 도입
  - 자주 조회되는 종목 캐싱

#### 예상 시간: 3-4시간

---

## 🧪 **테스트 관련**

### 7. 통합 테스트 추가
- [ ] API 엔드포인트 테스트
- [ ] 동적 프롬프팅 E2E 테스트
- [ ] 워크플로우 분기 테스트
- [ ] 에러 처리 테스트

#### 예상 시간: 2-3시간

---

### 8. LangSmith 모니터링 개선
- [ ] 커스텀 메트릭 추가
- [ ] 프롬프트 버전 관리
- [ ] A/B 테스트 설정

#### 예상 시간: 1-2시간

---

## 📚 **문서화**

### 9. 사용자 가이드 작성
- [ ] API 사용 가이드
- [ ] 동적 프롬프팅 가이드
- [ ] 배포 가이드
- [ ] 트러블슈팅 가이드

#### 예상 시간: 2-3시간

---

## 🎯 **다음 Sprint 추천 순서**

1. **뉴스 웹스크래핑** (2-3시간) - 가장 즉시 가치 제공
2. **Neo4j 연동** (1-2시간) - 지식 그래프 완성
3. **사용자 프로필 DB 연동** (2-3시간) - 맞춤형 서비스 제공
4. **성능 최적화** (3-4시간) - 사용자 경험 개선
5. **통합 테스트** (2-3시간) - 안정성 확보

**총 예상 시간**: 10-15시간

---

## ✅ **완료된 작업**

- ✅ 동적 프롬프팅 시스템 구현
- ✅ Prompt Manager를 모든 서비스에 통합
- ✅ 순환 import 문제 해결
- ✅ LangGraph Enhanced 시스템 정리
- ✅ Gemini 2.0 Flash 전용 시스템
- ✅ Chat Terminal 개선
- ✅ 배포 체크리스트 작성
- ✅ Data-Agent 문서화
- ✅ 서버 안정화

---

## 📞 **문의 및 이슈**

이슈가 발생하거나 질문이 있으면:
1. `DEPLOYMENT_CHECKLIST.md` 확인
2. `ARCHITECTURE.md` 참고
3. `DATA_AGENT_README.md` 참고
4. Git 이슈 등록

---

**마지막 커밋**: feat: 동적 프롬프팅 시스템 완전 통합 및 시스템 안정화 (40a4a0c2)

