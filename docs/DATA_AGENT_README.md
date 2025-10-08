# 🤖 Data-Agent for Financial Knowledge Graph

금융 챗봇을 위한 자동화된 데이터 수집 및 지식 그래프 업데이트 시스템입니다.

## 📋 개요

Data-Agent는 다음과 같은 기능을 수행합니다:

1. **뉴스 수집**: Naver, Daum RSS 피드에서 금융 뉴스 자동 수집
2. **텍스트 필터링**: 금융 관련 기사만 선별
3. **관계 추출**: KF-DeBERTa 모델을 사용한 엔티티 간 관계 추출
4. **지식 그래프 업데이트**: Neo4j에 관계 데이터 자동 저장
5. **스케줄링**: 24시간마다 자동 실행

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News Collector│    │  Text Filter    │    │Relation Extractor│
│                 │───▶│                 │───▶│                 │
│ • Naver RSS     │    │ • LDA/TF-IDF    │    │ • KF-DeBERTa    │
│ • Daum RSS      │    │ • 금융 필터링      │    │ • 관계 추출       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐              │
│   Scheduler     │    │ Knowledge Graph │◀─────────────┘
│                 │───▶│    Updater      │
│ • APScheduler   │    │ • Neo4j         │
│ • 24시간 주기      │    │ • Cypher 쿼리   │
└─────────────────┘    └─────────────────┘
```

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Neo4j 데이터베이스 설정

```bash
# Docker로 Neo4j 실행
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

### 3. 환경 변수 설정

`.env` 파일에 다음 설정을 추가:

```env
# Neo4j 설정
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 모델 설정
TRANSFORMERS_MODEL=kakaobank/kf-deberta-base
```

## 📖 사용법

### 기본 사용법

```python
import asyncio
from data_agent import run_data_agent

async def main():
    # Data-Agent 실행
    result = await run_data_agent(days_back=1)
    print(result)

asyncio.run(main())
```

### 스케줄링 설정

```python
from data_agent import start_daily_scheduler, stop_scheduler

# 매일 새벽 2시에 자동 실행
start_daily_scheduler(hour=2, minute=0)

# 스케줄러 중지
stop_scheduler()
```

### 챗봇과 통합

```python
from app.services.chatbot.chatbot_service import FinancialChatbotService
from data_agent import run_data_agent

class EnhancedChatbotService(FinancialChatbotService):
    async def update_knowledge_base(self):
        """지식 베이스 업데이트"""
        result = await run_data_agent(days_back=1)
        
        if result["status"] == "success":
            # RAG 서비스 새로고침
            await self.refresh_rag_service()
            
        return result
```

## 🔧 구성 요소

### 1. NewsCollector

**기능**: RSS 피드에서 뉴스 수집

**주요 메서드**:
- `collect_news(days_back)`: 지정된 일수만큼 과거 뉴스 수집
- `_parse_rss_feed()`: RSS 피드 파싱
- `_filter_by_date()`: 날짜 기준 필터링

### 2. TextFilter

**기능**: 금융 관련 기사 필터링

**주요 메서드**:
- `filter_financial_articles()`: 금융 관련 기사 필터링
- `_is_financial_content()`: 금융 관련성 판단

### 3. RelationExtractor

**기능**: KF-DeBERTa 모델을 사용한 관계 추출

**주요 메서드**:
- `extract_relations()`: 기사에서 관계 추출
- `_extract_from_sentence()`: 문장에서 관계 추출

### 4. KnowledgeGraphUpdater

**기능**: Neo4j 지식 그래프 업데이트

**주요 메서드**:
- `update_graph()`: 지식 그래프 업데이트
- `_create_or_update_node()`: 노드 생성/업데이트
- `_create_or_update_relationship()`: 관계 생성/업데이트

## 📊 출력 형식

### 뉴스 기사

```python
@dataclass
class NewsArticle:
    title: str          # "삼성전자 주가 상승"
    link: str           # "https://..."
    published: str      # "2025-10-02"
    content: str        # 기사 본문
    is_financial: bool  # 금융 관련 여부
    topic_score: float  # 토픽 점수
```

### 관계 삼원조

```python
@dataclass
class RelationTriple:
    entity1: str        # "삼성전자"
    relation: str       # "상승"
    entity2: str        # "주가"
    confidence: float   # 0.93
    source_article: str # "https://..."
```

## 🔍 실행 결과 예시

```json
{
  "execution_time": 45.2,
  "articles_collected": 150,
  "financial_articles": 89,
  "relations_extracted": 234,
  "kg_update_stats": {
    "processed_triples": 234,
    "new_nodes": 45,
    "new_relationships": 189,
    "updated_relationships": 12
  },
  "status": "success"
}
```

## 🛠️ 고급 설정

### 커스텀 RSS 피드 추가

```python
# NewsCollector 클래스 수정
self.rss_feeds = {
    'naver': [
        'https://news.naver.com/main/rss/section.naver?sid=101',
        'https://news.naver.com/main/rss/section.naver?sid=102',
        # 새로운 피드 추가
        'https://news.naver.com/main/rss/section.naver?sid=105'
    ],
    'custom': [
        'https://your-custom-feed.com/rss'
    ]
}
```

### 관계 패턴 커스터마이징

```python
# RelationExtractor 클래스 수정
self.relation_patterns = {
    '상승': ['상승', '증가', '급등', '호재', '매수'],
    '하락': ['하락', '감소', '급락', '악재', '매도'],
    '영향': ['영향', '관련', '연결', '의존'],
    # 새로운 관계 타입 추가
    '파트너십': ['제휴', '협력', '파트너십', 'MOU']
}
```

## 🚨 주의사항

1. **모델 로딩**: KF-DeBERTa 모델 로딩에 시간이 걸릴 수 있습니다.
2. **메모리 사용량**: 대량의 뉴스 처리 시 메모리 사용량을 모니터링하세요.
3. **API 제한**: RSS 피드 제공자의 요청 제한을 확인하세요.
4. **Neo4j 연결**: Neo4j 서버가 실행 중인지 확인하세요.

## 🔧 문제 해결

### 일반적인 문제들

**1. Neo4j 연결 실패**
```
해결방법: Neo4j 서버 상태 확인 및 인증 정보 확인
```

**2. 모델 로딩 실패**
```
해결방법: 인터넷 연결 확인 및 모델 이름 검증
```

**3. RSS 피드 파싱 오류**
```
해결방법: 피드 URL 유효성 확인 및 네트워크 연결 확인
```

## 📈 성능 최적화

1. **배치 처리**: 여러 기사를 배치로 처리
2. **캐싱**: 중복 기사 제거 및 결과 캐싱
3. **병렬 처리**: 비동기 처리로 성능 향상
4. **모델 최적화**: 경량화된 모델 사용

## 🔮 향후 계획

- [ ] 실시간 뉴스 스트리밍 지원
- [ ] 다국어 뉴스 처리
- [ ] 고급 관계 추출 모델 적용
- [ ] 시각화 대시보드 추가
- [ ] 클러스터링 및 이상 탐지

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 등록해 주세요.

---

*Data-Agent v1.0 - 2025-10-02*

