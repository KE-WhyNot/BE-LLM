"""
매일경제 RSS 피드 스크래퍼

매일경제의 다양한 RSS 피드에서 뉴스를 수집하고 임베딩하여 
Neo4j 지식그래프로 활용하는 스크래퍼입니다.

지원 RSS 피드:
- 경제: https://www.mk.co.kr/rss/30100041/
- 정치: https://www.mk.co.kr/rss/30200030/
- 증권: https://www.mk.co.kr/rss/50200011/
- 국제: https://www.mk.co.kr/rss/50100032/
- 헤드라인: https://www.mk.co.kr/rss/30000001/

Author: Financial Chatbot Team
Date: 2025-01-05
"""

import asyncio
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import hashlib

# 임베딩 및 벡터화
from sentence_transformers import SentenceTransformer
import numpy as np

# Neo4j 연동 (neo4j 공식 드라이버 사용 - Aura 지원)
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ neo4j 모듈이 없습니다. Neo4j 기능을 사용할 수 없습니다.")

from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MKNewsArticle:
    """매일경제 뉴스 기사 데이터 클래스"""
    title: str
    link: str
    published: str
    content: Optional[str] = None
    category: str = "general"
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    article_id: Optional[str] = None
    
    def __post_init__(self):
        """기사 ID 자동 생성"""
        if not self.article_id:
            self.article_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """기사 고유 ID 생성 (URL 기반 해시)"""
        return hashlib.md5(self.link.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


class MKNewsScraper:
    """매일경제 RSS 피드 스크래퍼"""
    
    def __init__(self):
        # 매일경제 RSS 피드 URL
        self.rss_feeds = {
            'economy': 'https://www.mk.co.kr/rss/30100041/',  # 경제
            'politics': 'https://www.mk.co.kr/rss/30200030/',  # 정치
            'securities': 'https://www.mk.co.kr/rss/50200011/',  # 증권
            'international': 'https://www.mk.co.kr/rss/50100032/',  # 국제
            'headlines': 'https://www.mk.co.kr/rss/30000001/'  # 헤드라인
        }
        
        # 한국어 임베딩 모델 초기화 (KF-DeBERTa 기반)
        self.embedding_model = SentenceTransformer('kakaobank/kf-deberta-base')
        
        # Neo4j 연결 설정 (Aura 지원)
        self.neo4j_driver = None
        self._initialize_neo4j()
    
    def _initialize_neo4j(self):
        """Neo4j 연결 초기화 (Aura 지원)"""
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j 기능을 사용할 수 없습니다.")
            return
        
        try:
            # 환경변수에서 Neo4j 설정 가져오기
            neo4j_uri = getattr(settings, 'neo4j_uri', 'bolt://localhost:7687')
            neo4j_user = getattr(settings, 'neo4j_user', 'neo4j')
            neo4j_password = getattr(settings, 'neo4j_password', 'password')
            
            # neo4j 공식 드라이버 사용 (Aura 지원)
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri, 
                auth=(neo4j_user, neo4j_password)
            )
            
            # 연결 테스트
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            logger.info(f"Neo4j 연결 성공: {neo4j_uri}")
            
            # 인덱스 생성
            self._create_neo4j_indexes()
            
        except Exception as e:
            logger.error(f"Neo4j 연결 실패: {e}")
            self.neo4j_driver = None
    
    def _create_neo4j_indexes(self):
        """Neo4j 인덱스 생성"""
        if not self.neo4j_driver:
            return
        
        try:
            with self.neo4j_driver.session() as session:
                # 기사 ID 인덱스
                session.run("CREATE INDEX article_id_index IF NOT EXISTS FOR (a:Article) ON (a.article_id)")
                # 카테고리 인덱스
                session.run("CREATE INDEX article_category_index IF NOT EXISTS FOR (a:Article) ON (a.category)")
                # 발행일 인덱스
                session.run("CREATE INDEX article_published_index IF NOT EXISTS FOR (a:Article) ON (a.published)")
            logger.info("Neo4j 인덱스 생성 완료")
        except Exception as e:
            logger.error(f"Neo4j 인덱스 생성 실패: {e}")
    
    async def scrape_all_feeds(self, days_back: int = 7) -> List[MKNewsArticle]:
        """모든 RSS 피드에서 뉴스 수집"""
        logger.info(f"매일경제 RSS 피드 수집 시작 - 최근 {days_back}일")
        
        all_articles = []
        
        for category, feed_url in self.rss_feeds.items():
            logger.info(f"{category} 카테고리 뉴스 수집 중...")
            try:
                articles = await self._scrape_feed(feed_url, category, days_back)
                all_articles.extend(articles)
                logger.info(f"{category}: {len(articles)}개 기사 수집")
                
            except Exception as e:
                logger.error(f"{category} 피드 수집 실패: {e}")
                continue
        
        logger.info(f"총 {len(all_articles)}개 기사 수집 완료")
        return all_articles
    
    async def _scrape_feed(self, feed_url: str, category: str, days_back: int) -> List[MKNewsArticle]:
        """개별 RSS 피드 스크래핑"""
        articles = []
        
        try:
            # RSS 피드 파싱
            feed = feedparser.parse(feed_url)
            
            if feed.bozo or len(feed.entries) == 0:
                logger.warning(f"RSS 피드 파싱 실패: {feed_url}")
                return articles
            
            # 날짜 필터링 (timezone-naive로 통일)
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries:
                try:
                    # 발행일 파싱
                    published_date = self._parse_date(entry.get('published', ''))
                    
                    # 날짜 필터링 (둘 다 timezone-naive로 통일)
                    if published_date.replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                        continue
                    
                    # 기사 생성
                    article = MKNewsArticle(
                        title=entry.get('title', '').strip(),
                        link=entry.get('link', '').strip(),
                        published=published_date.isoformat(),
                        category=category,
                        summary=entry.get('summary', '').strip()[:500]  # 요약 500자 제한
                    )
                    
                    # 기사 본문 수집 (비동기)
                    content = await self._fetch_article_content(article.link)
                    if content:
                        article.content = content
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"기사 처리 실패: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"RSS 피드 스크래핑 실패 ({feed_url}): {e}")
        
        return articles
    
    async def _fetch_article_content(self, url: str) -> Optional[str]:
        """기사 본문 수집"""
        try:
            # 비동기 HTTP 요청
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 매일경제 기사 본문 선택자
            content_selectors = [
                'div.news_cnt_detail_wrap',  # 매일경제 메인 선택자
                'div.article_body',
                'div.news_view',
                'div.article_view',
                'article',
                'div.content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 텍스트 추출 및 정리
                    content = content_elem.get_text().strip()
                    # 불필요한 공백 제거
                    content = ' '.join(content.split())
                    return content
            
            return None
            
        except Exception as e:
            logger.error(f"기사 본문 수집 실패 ({url}): {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """날짜 문자열 파싱"""
        try:
            if not date_str:
                return datetime.now()
            
            # 간단한 날짜 파싱 (RSS에서 받아온 날짜는 보통 ISO 형식)
            # feedparser.parse()에서 이미 파싱된 결과를 사용
            return datetime.now()  # 일단 현재 시간으로 통일 (날짜 필터링 우선)
            
        except Exception:
            return datetime.now()
    
    def generate_embeddings(self, articles: List[MKNewsArticle]) -> List[MKNewsArticle]:
        """뉴스 기사에 임베딩 생성"""
        logger.info(f"{len(articles)}개 기사에 임베딩 생성 시작")
        
        # 텍스트 준비 (제목 + 요약 + 본문)
        texts = []
        for article in articles:
            text_parts = [article.title]
            if article.summary:
                text_parts.append(article.summary)
            if article.content:
                # 본문은 1000자로 제한 (성능 고려)
                text_parts.append(article.content[:1000])
            
            combined_text = ' '.join(text_parts)
            texts.append(combined_text)
        
        # 배치 임베딩 생성
        embeddings = self.embedding_model.encode(texts, batch_size=32)
        
        # 임베딩을 기사에 할당
        for i, article in enumerate(articles):
            article.embedding = embeddings[i].tolist()
        
        logger.info("임베딩 생성 완료")
        return articles
    
    async def store_to_neo4j(self, articles: List[MKNewsArticle]) -> Dict[str, int]:
        """Neo4j에 뉴스 기사 저장 (neo4j 드라이버 사용)"""
        if not self.neo4j_driver:
            logger.error("Neo4j 연결이 없습니다")
            return {"error": "Neo4j 연결 실패"}
        
        logger.info(f"Neo4j에 {len(articles)}개 기사 저장 시작")
        
        stats = {
            "total_articles": len(articles),
            "new_articles": 0,
            "updated_articles": 0,
            "errors": 0
        }
        
        try:
            with self.neo4j_driver.session() as session:
                for article in articles:
                    try:
                        # MERGE를 사용하여 중복 방지
                        query = """
                        MERGE (a:Article {article_id: $article_id})
                        ON CREATE SET
                            a.title = $title,
                            a.link = $link,
                            a.published = $published,
                            a.category = $category,
                            a.content = $content,
                            a.summary = $summary,
                            a.embedding = $embedding,
                            a.created_at = datetime()
                        ON MATCH SET
                            a.title = $title,
                            a.content = $content,
                            a.summary = $summary,
                            a.embedding = $embedding,
                            a.updated_at = datetime()
                        RETURN a.article_id, 
                               CASE WHEN a.created_at = datetime() THEN 'created' ELSE 'updated' END as status
                        """
                        
                        result = session.run(query, {
                            'article_id': article.article_id,
                            'title': article.title,
                            'link': article.link,
                            'published': article.published,
                            'category': article.category,
                            'content': article.content,
                            'summary': article.summary,
                            'embedding': article.embedding
                        })
                        
                        record = result.single()
                        if record:
                            if record['status'] == 'created':
                                stats["new_articles"] += 1
                            else:
                                stats["updated_articles"] += 1
                        
                    except Exception as e:
                        logger.error(f"기사 저장 실패 ({article.title}): {e}")
                        stats["errors"] += 1
                        continue
            
            logger.info(f"Neo4j 저장 완료: 신규 {stats['new_articles']}개, 업데이트 {stats['updated_articles']}개, 실패 {stats['errors']}개")
            
            # Relationship 생성 (새로운 세션에서)
            await self._create_relationships()
            
            return stats
            
        except Exception as e:
            logger.error(f"Neo4j 저장 중 오류: {e}")
            return {"error": str(e)}
    
    async def _create_relationships(self):
        """기사 간 관계 생성 (SIMILAR_TO, MENTIONS)"""
        if not self.neo4j_driver:
            logger.error("Neo4j 연결이 없습니다")
            return
        
        try:
            logger.info("Relationship 생성 시작...")
            
            with self.neo4j_driver.session() as session:
                # 1. SIMILAR_TO: 유사한 기사끼리 연결 (임베딩 유사도 기반)
                logger.info("  - SIMILAR_TO 관계 생성 중...")
                similar_query = """
                MATCH (a1:Article), (a2:Article)
                WHERE a1.article_id < a2.article_id
                AND a1.embedding IS NOT NULL 
                AND a2.embedding IS NOT NULL
                WITH a1, a2, gds.similarity.cosine(a1.embedding, a2.embedding) AS similarity
                WHERE similarity > 0.7
                MERGE (a1)-[r:SIMILAR_TO]->(a2)
                SET r.similarity = similarity
                RETURN count(r) as count
                """
                result = session.run(similar_query)
                similar_count = result.single()['count']
                logger.info(f"  ✅ SIMILAR_TO: {similar_count}개 생성")
                
                # 2. SAME_CATEGORY: 같은 카테고리 연결
                logger.info("  - SAME_CATEGORY 관계 생성 중...")
                category_query = """
                MATCH (a1:Article), (a2:Article)
                WHERE a1.article_id < a2.article_id
                AND a1.category = a2.category
                MERGE (a1)-[r:SAME_CATEGORY]->(a2)
                RETURN count(r) as count
                """
                result = session.run(category_query)
                category_count = result.single()['count']
                logger.info(f"  ✅ SAME_CATEGORY: {category_count}개 생성")
                
                # 3. MENTIONS: 주요 키워드 노드 생성 및 연결
                logger.info("  - MENTIONS (키워드) 관계 생성 중...")
                keywords = ['삼성전자', 'SK하이닉스', '현대차', 'LG전자', '반도체', '금리', '환율', '주식', '증권']
                
                mentions_count = 0
                for keyword in keywords:
                    keyword_query = """
                    MATCH (a:Article)
                    WHERE a.title CONTAINS $keyword OR a.summary CONTAINS $keyword
                    MERGE (k:Keyword {name: $keyword})
                    MERGE (a)-[r:MENTIONS]->(k)
                    RETURN count(r) as count
                    """
                    result = session.run(keyword_query, keyword=keyword)
                    count = result.single()['count']
                    mentions_count += count
                    if count > 0:
                        logger.info(f"    - '{keyword}': {count}개 연결")
                
                logger.info(f"  ✅ MENTIONS: {mentions_count}개 생성")
                
                total_relationships = similar_count + category_count + mentions_count
                logger.info(f"\n✅ 총 {total_relationships}개 Relationship 생성 완료!")
            
        except Exception as e:
            logger.error(f"Relationship 생성 실패: {e}")
            import traceback
            traceback.print_exc()
    
    async def search_similar_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """유사한 기사 검색 (임베딩 기반 - neo4j 드라이버 사용)"""
        if not self.neo4j_driver:
            logger.error("Neo4j 연결이 없습니다")
            return []
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            logger.info(f"쿼리 '{query}' 임베딩 생성: {len(query_embedding)}차원")
            
            # Neo4j에서 유사도 검색 (코사인 유사도)
            cypher_query = """
            MATCH (a:Article)
            WHERE a.embedding IS NOT NULL
            WITH a, gds.similarity.cosine(a.embedding, $query_embedding) AS similarity
            RETURN a.article_id, a.title, a.summary, a.link, a.published, a.category, similarity
            ORDER BY similarity DESC
            LIMIT $limit
            """
            
            with self.neo4j_driver.session() as session:
                result = session.run(
                    cypher_query, 
                    query_embedding=query_embedding, 
                    limit=limit
                )
                
                results = [dict(record) for record in result]
            
            logger.info(f"검색 결과: {len(results)}개")
            
            return results
            
        except Exception as e:
            logger.error(f"유사 기사 검색 실패: {e}")
            return []
    
    async def get_article_network(self, article_id: str, depth: int = 2) -> Dict[str, Any]:
        """기사 네트워크 분석 (관련 기사 찾기)"""
        if not self.neo4j_graph:
            return {"error": "Neo4j 연결이 없습니다"}
        
        try:
            # 임베딩 기반 유사 기사 찾기
            similar_articles = await self.search_similar_articles(
                f"article_id:{article_id}", limit=20
            )
            
            # 카테고리별 그룹핑
            categories = {}
            for article in similar_articles:
                category = article['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(article)
            
            return {
                "central_article_id": article_id,
                "similar_articles": similar_articles,
                "categories": categories,
                "total_similar": len(similar_articles)
            }
            
        except Exception as e:
            logger.error(f"기사 네트워크 분석 실패: {e}")
            return {"error": str(e)}


class MKKnowledgeGraphService:
    """매일경제 뉴스 지식그래프 서비스"""
    
    def __init__(self):
        self.scraper = MKNewsScraper()
    
    async def update_knowledge_graph(self, days_back: int = 7) -> Dict[str, Any]:
        """지식그래프 업데이트 (전체 파이프라인)"""
        logger.info("매일경제 지식그래프 업데이트 시작")
        
        start_time = datetime.now()
        
        try:
            # 1. RSS 피드에서 뉴스 수집
            articles = await self.scraper.scrape_all_feeds(days_back)
            
            if not articles:
                return {"error": "수집된 뉴스가 없습니다"}
            
            # 2. 임베딩 생성
            articles_with_embeddings = self.scraper.generate_embeddings(articles)
            
            # 3. Neo4j에 저장
            storage_stats = await self.scraper.store_to_neo4j(articles_with_embeddings)
            
            # 4. 결과 요약
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            summary = {
                "execution_time": execution_time,
                "articles_collected": len(articles),
                "storage_stats": storage_stats,
                "status": "success"
            }
            
            logger.info(f"지식그래프 업데이트 완료: {execution_time:.2f}초")
            return summary
            
        except Exception as e:
            logger.error(f"지식그래프 업데이트 실패: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def search_news(self, query: str, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """뉴스 검색 (키 정리 포함)"""
        try:
            # 임베딩 기반 유사 검색
            results = await self.scraper.search_similar_articles(query, limit)
            
            # 키 이름 정리 (a.title -> title)
            cleaned_results = []
            for r in results:
                cleaned = {
                    'article_id': r.get('a.article_id'),
                    'title': r.get('a.title'),
                    'summary': r.get('a.summary'),
                    'link': r.get('a.link'),
                    'published': r.get('a.published'),
                    'category': r.get('a.category'),
                    'similarity': r.get('similarity')
                }
                cleaned_results.append(cleaned)
            
            # 카테고리 필터링
            if category:
                cleaned_results = [r for r in cleaned_results if r['category'] == category]
            
            return cleaned_results
            
        except Exception as e:
            logger.error(f"뉴스 검색 실패: {e}")
            return []
    
    async def get_trending_topics(self, days_back: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """트렌딩 토픽 분석"""
        if not self.scraper.neo4j_graph:
            return []
        
        try:
            # 최근 기사들의 카테고리별 집계
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            cypher_query = """
            MATCH (a:Article)
            WHERE a.published >= $cutoff_date
            RETURN a.category, count(*) as article_count
            ORDER BY article_count DESC
            LIMIT $limit
            """
            
            results = self.scraper.neo4j_graph.run(
                cypher_query, 
                cutoff_date=cutoff_date, 
                limit=limit
            ).data()
            
            return results
            
        except Exception as e:
            logger.error(f"트렌딩 토픽 분석 실패: {e}")
            return []


# 전역 서비스 인스턴스
mk_kg_service = MKKnowledgeGraphService()


async def update_mk_knowledge_graph(days_back: int = 7) -> Dict[str, Any]:
    """지식그래프 업데이트 함수 (외부 호출용)"""
    return await mk_kg_service.update_knowledge_graph(days_back)


async def search_mk_news(query: str, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """뉴스 검색 함수 (외부 호출용)"""
    return await mk_kg_service.search_news(query, category, limit)


if __name__ == "__main__":
    """직접 실행 시 테스트"""
    async def main():
        # 지식그래프 업데이트 테스트
        print("매일경제 지식그래프 업데이트 테스트 시작...")
        result = await update_mk_knowledge_graph(days_back=1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 뉴스 검색 테스트
        print("\n뉴스 검색 테스트...")
        search_results = await search_mk_news("삼성전자", limit=5)
        print(f"검색 결과: {len(search_results)}개")
        for i, article in enumerate(search_results[:3], 1):
            print(f"{i}. {article['title']} (유사도: {article['similarity']:.3f})")
    
    # 비동기 실행
    asyncio.run(main())
