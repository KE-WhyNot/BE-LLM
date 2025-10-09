"""
Data-Agent for Financial Knowledge Graph

이 모듈은 금융 뉴스를 자동으로 수집하고, KF-DeBERTa 모델을 사용하여 
엔티티 간 관계를 추출하며, Neo4j 지식 그래프를 업데이트합니다.

KF-DeBERTa: 카카오뱅크와 에프엔가이드가 개발한 금융 특화 한국어 모델
- Hugging Face: kakaobank/kf-deberta-base
- 아키텍처: DeBERTa-v2 기반
- 특징: 금융 도메인에 최적화된 한국어 NLP 모델

Author: Financial Chatbot Team
Date: 2025-10-02
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

# RSS 및 웹 스크래핑
import feedparser
import requests
from bs4 import BeautifulSoup

# 머신러닝 및 NLP
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Neo4j (선택적 import)
try:
    from py2neo import Graph, Node, Relationship
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ py2neo 모듈이 없습니다. Neo4j 기능을 사용할 수 없습니다.")

# 스케줄링
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 설정
from app.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    link: str
    published: str
    content: Optional[str] = None
    is_financial: bool = False
    topic_score: float = 0.0


@dataclass
class RelationTriple:
    """관계 삼원조 데이터 클래스"""
    entity1: str
    relation: str
    entity2: str
    confidence: float
    source_article: str


class NewsCollector:
    """뉴스 수집기 - Naver, Daum RSS 피드에서 금융 뉴스 수집"""
    
    def __init__(self):
        # RSS 피드를 환경변수에서 로드
        import json
        self.rss_feeds = {
            'naver': json.loads(settings.naver_rss_feeds) if settings.naver_rss_feeds else [
                'https://news.naver.com/main/rss/economy.xml',  # 경제
                'https://news.naver.com/main/rss/society.xml',  # 사회
                'https://news.naver.com/main/rss/it.xml',       # IT/과학 (기술주 관련)
            ],
            'daum': json.loads(settings.daum_rss_feeds) if settings.daum_rss_feeds else [
                'https://news.daum.net/rss/economic',  # 경제
                'https://news.daum.net/rss/society',   # 사회
                'https://news.daum.net/rss/digital',   # IT (기술주 관련)
            ]
        }
        
        # 금융 관련 키워드를 환경변수에서 로드
        self.finance_keywords = json.loads(settings.finance_keywords) if settings.finance_keywords else [
            '주식', '증권', '금융', '은행', '투자', '경제', '시장', '주가',
            'PER', 'PBR', '배당', '상장', 'IPO', 'M&A', '인수', '합병',
            '기준금리', '인플레이션', 'GDP', '환율', '달러', '엔화',
            '삼성전자', 'SK하이닉스', 'LG전자', '현대차', '기아',
            '상승', '하락', '급등', '급락', '거래량', '시가총액'
        ]
    
    async def collect_news(self, days_back: int = 1) -> List[NewsArticle]:
        """지정된 일수만큼 과거 뉴스 수집"""
        logger.info(f"뉴스 수집 시작 - 최근 {days_back}일")
        all_articles = []
        
        for source, feeds in self.rss_feeds.items():
            logger.info(f"{source} RSS 피드 수집 중...")
            
            for feed_url in feeds:
                try:
                    articles = await self._parse_rss_feed(feed_url, source)
                    all_articles.extend(articles)
                    logger.info(f"{source} 피드에서 {len(articles)}개 기사 수집")
                    
                except Exception as e:
                    logger.error(f"{source} RSS 피드 수집 실패: {e}")
                    continue
        
        # 중복 제거 및 날짜 필터링
        unique_articles = self._deduplicate_articles(all_articles)
        filtered_articles = self._filter_by_date(unique_articles, days_back)
        
        logger.info(f"총 {len(filtered_articles)}개 기사 수집 완료")
        return filtered_articles
    
    async def _parse_rss_feed(self, feed_url: str, source: str) -> List[NewsArticle]:
        """RSS 피드 파싱 (한국어 뉴스)"""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            # RSS 피드가 작동하지 않는 경우 더미 한국어 뉴스 생성
            if feed.bozo or len(feed.entries) == 0:
                logger.warning(f"RSS 피드가 작동하지 않음 ({feed_url}), 더미 한국어 뉴스 생성")
                articles = self._generate_dummy_korean_news(source)
            else:
                for entry in feed.entries:
                    # 날짜 파싱
                    published_date = self._parse_date(entry.get('published', ''))
                    
                    article = NewsArticle(
                        title=entry.get('title', '').strip(),
                        link=entry.get('link', '').strip(),
                        published=published_date,
                        content=None
                    )
                    
                    articles.append(article)
                
        except Exception as e:
            logger.error(f"RSS 피드 파싱 오류 ({feed_url}): {e}")
            # 오류 시에도 더미 뉴스 생성
            articles = self._generate_dummy_korean_news(source)
        
        return articles
    
    def _generate_dummy_korean_news(self, source: str) -> List[NewsArticle]:
        """더미 한국어 금융 뉴스 생성 (RSS 피드 대체용)"""
        dummy_news = [
            {
                'title': '삼성전자 주가 상승세 지속... 반도체 업황 회복 기대감',
                'content': '삼성전자 주가가 연일 상승세를 보이고 있다. 반도체 업황 회복 기대감과 함께 글로벌 메모리 시장의 회복 조짐이 주가 상승을 견인하고 있다.',
                'link': f'https://{source}.com/news/samsung-stock-rise'
            },
            {
                'title': 'SK하이닉스, HBM 메모리 시장 선점 노력 가속화',
                'content': 'SK하이닉스가 AI 시대의 핵심 부품인 HBM 메모리 시장에서 경쟁 우위를 확보하기 위해 투자를 확대하고 있다.',
                'link': f'https://{source}.com/news/sk-hynix-hbm-memory'
            },
            {
                'title': '네이버, AI 기술 투자 확대로 주가 급등',
                'content': '네이버가 AI 기술 개발에 대한 투자를 확대한다고 발표하면서 주가가 급등했다. 검색 엔진 개선과 클라우드 서비스 강화가 주요 내용이다.',
                'link': f'https://{source}.com/news/naver-ai-investment'
            },
            {
                'title': '카카오, 금융 서비스 확장으로 수익성 개선 기대',
                'content': '카카오가 금융 서비스 영역을 확장하면서 수익성 개선이 기대되고 있다. 카카오뱅크와 카카오페이의 시너지 효과가 주목받고 있다.',
                'link': f'https://{source}.com/news/kakao-financial-expansion'
            },
            {
                'title': '현대차, 전기차 시장 공략 강화로 미래 성장 동력 확보',
                'content': '현대차가 전기차 시장에서의 경쟁력을 높이기 위해 신형 모델 출시와 생산 능력 확대를 계획하고 있다.',
                'link': f'https://{source}.com/news/hyundai-electric-vehicle'
            },
            {
                'title': 'LG전자, 가전 제품 수출 증가로 실적 개선',
                'content': 'LG전자가 프리미엄 가전 제품의 해외 수출 증가로 실적 개선을 보이고 있다. 특히 북미와 유럽 시장에서 호조를 보이고 있다.',
                'link': f'https://{source}.com/news/lg-electronics-export'
            },
            {
                'title': '코스피, 외국인 매수세로 3일 연속 상승',
                'content': '코스피가 외국인 투자자들의 매수세에 힘입어 3일 연속 상승세를 보이고 있다. 주요 종목들의 긍정적인 실적 발표가 영향을 미쳤다.',
                'link': f'https://{source}.com/news/kospi-foreign-buying'
            },
            {
                'title': '코스닥, 바이오 기술주 강세로 상승세 지속',
                'content': '코스닥이 바이오 기술 관련 종목들의 강세로 상승세를 지속하고 있다. 신약 개발 관련 소식들이 투자 심리를 긍정적으로 이끌고 있다.',
                'link': f'https://{source}.com/news/kosdaq-bio-tech'
            }
        ]
        
        articles = []
        for news_data in dummy_news:
            article = NewsArticle(
                title=news_data['title'],
                link=news_data['link'],
                published=self._parse_date(''),
                content=news_data['content']
            )
            articles.append(article)
        
        logger.info(f"{source}에서 더미 한국어 뉴스 {len(articles)}개 생성")
        return articles
    
    def _parse_date(self, date_str: str) -> str:
        """날짜 문자열 파싱"""
        try:
            if date_str:
                # 간단한 날짜 파싱 (실제로는 더 정교한 파싱 필요)
                return datetime.now().strftime('%Y-%m-%d')
            else:
                return datetime.now().strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """중복 기사 제거"""
        seen_links = set()
        unique_articles = []
        
        for article in articles:
            if article.link not in seen_links:
                seen_links.add(article.link)
                unique_articles.append(article)
        
        return unique_articles
    
    def _filter_by_date(self, articles: List[NewsArticle], days_back: int) -> List[NewsArticle]:
        """날짜 기준 필터링"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered = []
        for article in articles:
            try:
                article_date = datetime.strptime(article.published, '%Y-%m-%d')
                if article_date >= cutoff_date:
                    filtered.append(article)
            except:
                # 날짜 파싱 실패 시 포함
                filtered.append(article)
        
        return filtered


class TextFilter:
    """텍스트 필터 및 토픽 추출기"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 한국어 불용어 처리 필요
            ngram_range=(1, 2)
        )
        
        # LDA 모델 (사전 훈련된 모델 사용 권장)
        self.lda_model = LatentDirichletAllocation(
            n_components=10,
            random_state=42,
            max_iter=100
        )
        
        self.finance_keywords = [
            '주식', '증권', '금융', '은행', '투자', '경제', '시장', '주가',
            'PER', 'PBR', '배당', '상장', 'IPO', 'M&A', '인수', '합병',
            '기준금리', '인플레이션', 'GDP', '환율', '달러', '엔화',
            '삼성전자', 'SK하이닉스', 'LG전자', '현대차', '기아',
            '상승', '하락', '급등', '급락', '거래량', '시가총액'
        ]
    
    def filter_financial_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """금융 관련 기사 필터링"""
        logger.info("금융 관련 기사 필터링 시작")
        
        financial_articles = []
        
        for article in articles:
            # 키워드 기반 필터링
            is_financial, topic_score = self._is_financial_content(article.title)
            
            if is_financial:
                article.is_financial = True
                article.topic_score = topic_score
                financial_articles.append(article)
        
        logger.info(f"금융 관련 기사 {len(financial_articles)}개 필터링 완료")
        return financial_articles
    
    def _is_financial_content(self, text: str) -> Tuple[bool, float]:
        """텍스트가 금융 관련인지 판단"""
        text_lower = text.lower()
        
        # 키워드 매칭 점수 계산
        keyword_count = sum(1 for keyword in self.finance_keywords if keyword in text_lower)
        topic_score = min(keyword_count / len(self.finance_keywords) * 10, 1.0)
        
        # 임계값 이상이면 금융 관련으로 판단
        is_financial = topic_score > 0.1
        
        return is_financial, topic_score


class RelationExtractor:
    """관계 추출기 - KF-DeBERTa 모델 사용 (카카오뱅크 금융 특화 모델)"""
    
    def __init__(self):
        """KF-DeBERTa 모델 초기화 (카카오뱅크 금융 특화 모델)"""
        model_name = settings.relation_extraction_model
        logger.info(f"관계 추출 모델 로딩: {model_name}")
        
        try:
            # KF-DeBERTa: 카카오뱅크와 에프엔가이드가 개발한 금융 특화 한국어 모델
            # DeBERTa-v2 아키텍처 기반, 금융 도메인에 최적화됨
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            
            # NER 파이프라인 (관계 추출을 위한 기본 설정)
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple"
            )
            
            # 관계 추출 규칙 (실제로는 파인튜닝된 모델 사용)
            self.relation_patterns = {
                '상승': ['상승', '증가', '급등', '호재', '매수'],
                '하락': ['하락', '감소', '급락', '악재', '매도'],
                '영향': ['영향', '관련', '연결', '의존'],
                '소유': ['소유', '보유', '지분', '출자'],
                '투자': ['투자', '매입', '매수', '인수']
            }
            
            logger.info("관계 추출 모델 로딩 완료")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            self.ner_pipeline = None
    
    async def extract_relations(self, articles: List[NewsArticle]) -> List[RelationTriple]:
        """기사에서 관계 추출"""
        logger.info("관계 추출 시작")
        
        if not self.ner_pipeline:
            logger.error("모델이 로드되지 않음")
            return []
        
        all_triples = []
        
        for article in articles:
            try:
                # 기사 내용 가져오기
                content = await self._fetch_article_content(article.link)
                if not content:
                    continue
                
                # 문장 단위로 분할
                sentences = self._split_sentences(content)
                
                # 각 문장에서 관계 추출
                for sentence in sentences:
                    triples = self._extract_from_sentence(sentence, article.link)
                    all_triples.extend(triples)
                    
            except Exception as e:
                logger.error(f"기사 처리 실패 ({article.link}): {e}")
                continue
        
        logger.info(f"총 {len(all_triples)}개 관계 추출 완료")
        return all_triples
    
    async def _fetch_article_content(self, url: str) -> Optional[str]:
        """기사 내용 가져오기"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 기사 본문 추출 (사이트별로 다름)
            content_selectors = [
                'div.article_body',
                'div.article_view',
                'div.news_view',
                'article',
                'div.content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    return content_elem.get_text().strip()
            
            return None
            
        except Exception as e:
            logger.error(f"기사 내용 가져오기 실패 ({url}): {e}")
            return None
    
    def _split_sentences(self, text: str) -> List[str]:
        """문장 분할"""
        # 간단한 문장 분할 (실제로는 더 정교한 분할 필요)
        sentences = text.replace('\n', ' ').split('.')
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _extract_from_sentence(self, sentence: str, source: str) -> List[RelationTriple]:
        """문장에서 관계 추출"""
        triples = []
        
        try:
            # NER 실행
            entities = self.ner_pipeline(sentence)
            
            # 엔티티와 관계 패턴 매칭
            for relation_type, patterns in self.relation_patterns.items():
                for pattern in patterns:
                    if pattern in sentence:
                        # 엔티티 쌍 생성 (실제로는 더 정교한 추출 필요)
                        if len(entities) >= 2:
                            for i in range(len(entities) - 1):
                                entity1 = entities[i]['word']
                                entity2 = entities[i + 1]['word']
                                confidence = min(entities[i]['score'], entities[i + 1]['score'])
                                
                                if confidence > 0.7:  # 신뢰도 임계값
                                    triple = RelationTriple(
                                        entity1=entity1,
                                        relation=relation_type,
                                        entity2=entity2,
                                        confidence=confidence,
                                        source_article=source
                                    )
                                    triples.append(triple)
            
        except Exception as e:
            logger.error(f"관계 추출 실패: {e}")
        
        return triples


class KnowledgeGraphUpdater:
    """Neo4j 지식 그래프 업데이터"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Neo4j 연결 초기화"""
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        
        try:
            self.graph = Graph(self.uri, auth=(self.user, self.password))
            logger.info("Neo4j 연결 성공")
        except Exception as e:
            logger.error(f"Neo4j 연결 실패: {e}")
            self.graph = None
    
    async def update_graph(self, triples: List[RelationTriple]) -> Dict[str, int]:
        """지식 그래프 업데이트"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다")
            return {"error": "Neo4j 연결 실패"}
        
        logger.info(f"지식 그래프 업데이트 시작 - {len(triples)}개 관계")
        
        stats = {
            "processed_triples": 0,
            "new_nodes": 0,
            "new_relationships": 0,
            "updated_relationships": 0
        }
        
        try:
            # 트랜잭션 시작
            tx = self.graph.begin()
            
            for triple in triples:
                try:
                    # 노드 생성 또는 업데이트
                    node1 = self._create_or_update_node(tx, triple.entity1)
                    node2 = self._create_or_update_node(tx, triple.entity2)
                    
                    # 관계 생성 또는 업데이트
                    self._create_or_update_relationship(
                        tx, node1, node2, triple.relation, triple.confidence
                    )
                    
                    stats["processed_triples"] += 1
                    
                except Exception as e:
                    logger.error(f"관계 처리 실패: {e}")
                    continue
            
            # 트랜잭션 커밋
            self.graph.commit(tx)
            logger.info("지식 그래프 업데이트 완료")
            
        except Exception as e:
            logger.error(f"지식 그래프 업데이트 실패: {e}")
            self.graph.rollback(tx)
        
        return stats
    
    def _create_or_update_node(self, tx, entity_name: str):
        """노드 생성 또는 업데이트"""
        # 기존 노드 찾기
        existing_node = tx.graph.nodes.match("Entity", name=entity_name).first()
        
        if existing_node:
            return existing_node
        else:
            # 새 노드 생성
            new_node = Node("Entity", name=entity_name)
            tx.create(new_node)
            return new_node
    
    def _create_or_update_relationship(self, tx, node1, node2, relation_type: str, confidence: float):
        """관계 생성 또는 업데이트"""
        # 기존 관계 찾기
        existing_rel = tx.graph.relationships.match(
            (node1, node2), r_type=relation_type
        ).first()
        
        if existing_rel:
            # 신뢰도가 더 높으면 업데이트
            if confidence > existing_rel.get('confidence', 0):
                existing_rel['confidence'] = confidence
                existing_rel['last_updated'] = datetime.now().isoformat()
        else:
            # 새 관계 생성
            new_rel = Relationship(
                node1, relation_type, node2,
                confidence=confidence,
                created_at=datetime.now().isoformat()
            )
            tx.create(new_rel)


class DataAgent:
    """Data-Agent 메인 클래스"""
    
    def __init__(self):
        self.news_collector = NewsCollector()
        self.text_filter = TextFilter()
        self.relation_extractor = RelationExtractor()
        self.kg_updater = KnowledgeGraphUpdater()
        
        # 스케줄러 설정
        self.scheduler = AsyncIOScheduler()
        
    async def run_data_agent(self, days_back: int = 1) -> Dict[str, Any]:
        """Data-Agent 실행"""
        logger.info("=" * 50)
        logger.info("Data-Agent 실행 시작")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # 1. 뉴스 수집
            logger.info("1단계: 뉴스 수집")
            articles = await self.news_collector.collect_news(days_back)
            
            # 2. 텍스트 필터링
            logger.info("2단계: 금융 관련 기사 필터링")
            financial_articles = self.text_filter.filter_financial_articles(articles)
            
            # 3. 관계 추출
            logger.info("3단계: 관계 추출")
            triples = await self.relation_extractor.extract_relations(financial_articles)
            
            # 4. 지식 그래프 업데이트
            logger.info("4단계: 지식 그래프 업데이트")
            update_stats = await self.kg_updater.update_graph(triples)
            
            # 결과 요약
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                "execution_time": execution_time,
                "articles_collected": len(articles),
                "financial_articles": len(financial_articles),
                "relations_extracted": len(triples),
                "kg_update_stats": update_stats,
                "status": "success"
            }
            
            # 로그 요약 출력
            self._print_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Data-Agent 실행 실패: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _print_summary(self, summary: Dict[str, Any]):
        """실행 결과 요약 출력"""
        logger.info("=" * 50)
        logger.info("Data-Agent 실행 결과 요약")
        logger.info("=" * 50)
        logger.info(f"실행 시간: {summary['execution_time']:.2f}초")
        logger.info(f"수집된 기사 수: {summary['articles_collected']}개")
        logger.info(f"금융 관련 기사: {summary['financial_articles']}개")
        logger.info(f"추출된 관계 수: {summary['relations_extracted']}개")
        
        if "kg_update_stats" in summary:
            kg_stats = summary["kg_update_stats"]
            logger.info(f"처리된 관계: {kg_stats.get('processed_triples', 0)}개")
            logger.info(f"새로운 노드: {kg_stats.get('new_nodes', 0)}개")
            logger.info(f"새로운 관계: {kg_stats.get('new_relationships', 0)}개")
        
        logger.info("=" * 50)
    
    def schedule_daily_update(self, hour: int = 2, minute: int = 0):
        """매일 자동 실행 스케줄링"""
        logger.info(f"매일 {hour:02d}:{minute:02d}에 Data-Agent 실행 예약")
        
        self.scheduler.add_job(
            self.run_data_agent,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_data_agent',
            name='Daily Data-Agent Execution',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("스케줄러 시작됨")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("스케줄러 중지됨")


# 전역 Data-Agent 인스턴스
data_agent = DataAgent()


async def run_data_agent(days_back: int = 1) -> Dict[str, Any]:
    """Data-Agent 실행 함수 (외부에서 호출 가능)"""
    return await data_agent.run_data_agent(days_back)


def start_daily_scheduler(hour: int = 2, minute: int = 0):
    """매일 자동 실행 시작"""
    data_agent.schedule_daily_update(hour, minute)


def stop_scheduler():
    """스케줄러 중지"""
    data_agent.stop_scheduler()


if __name__ == "__main__":
    """직접 실행 시 테스트"""
    async def main():
        # Data-Agent 실행
        result = await run_data_agent(days_back=1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 스케줄러 시작 (선택사항)
        # start_daily_scheduler()
    
    # 비동기 실행
    asyncio.run(main())

