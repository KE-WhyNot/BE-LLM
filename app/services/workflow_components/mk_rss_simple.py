"""
매일경제 RSS 간단 수집기 (Neo4j 없이 RSS만 사용)

Neo4j GDS 오류를 우회하기 위한 단순 RSS 수집기입니다.
임베딩 검색 없이 최신 뉴스만 수집합니다.
"""

import asyncio
import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MKRSSSimple:
    """매일경제 RSS 간단 수집기"""
    
    def __init__(self):
        # 매일경제 RSS 피드 URL
        self.rss_feeds = {
            'economy': 'https://www.mk.co.kr/rss/30100041/',  # 경제
            'politics': 'https://www.mk.co.kr/rss/30200030/',  # 정치
            'securities': 'https://www.mk.co.kr/rss/50200011/',  # 증권
            'international': 'https://www.mk.co.kr/rss/50100032/',  # 국제
            'headlines': 'https://www.mk.co.kr/rss/30000001/'  # 헤드라인
        }
    
    async def fetch_latest_news(self, 
                                category: Optional[str] = None, 
                                limit: int = 10) -> List[Dict[str, Any]]:
        """
        최신 뉴스 가져오기 (RSS 피드에서 직접)
        
        Args:
            category: 카테고리 ('economy', 'securities' 등) 또는 None (전체)
            limit: 가져올 뉴스 개수
            
        Returns:
            List[Dict]: 뉴스 리스트
        """
        all_news = []
        
        # 카테고리 선택
        if category and category in self.rss_feeds:
            feeds_to_fetch = {category: self.rss_feeds[category]}
        else:
            # 금융 관련 카테고리만
            feeds_to_fetch = {
                'economy': self.rss_feeds['economy'],
                'securities': self.rss_feeds['securities'],
                'headlines': self.rss_feeds['headlines']
            }
        
        # 각 RSS 피드에서 뉴스 수집
        for cat_name, feed_url in feeds_to_fetch.items():
            try:
                logger.info(f"매일경제 RSS 수집 중: {cat_name}")
                
                # RSS 파싱
                feed = await asyncio.to_thread(feedparser.parse, feed_url)
                
                if feed.bozo:
                    logger.warning(f"RSS 파싱 오류: {cat_name}")
                    continue
                
                # 엔트리 변환
                for entry in feed.entries[:limit]:
                    news_item = {
                        'title': entry.get('title', '').strip(),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', '').strip() if 'summary' in entry else '',
                        'category': cat_name,
                        'source': 'mk_rss'
                    }
                    
                    if news_item['title']:
                        all_news.append(news_item)
                
                logger.info(f"✅ {cat_name}에서 {len(feed.entries[:limit])}개 뉴스 수집")
                
            except Exception as e:
                logger.error(f"❌ RSS 수집 실패 ({cat_name}): {e}")
                continue
        
        # 날짜순 정렬 (최신순)
        all_news.sort(
            key=lambda x: x.get('published', ''), 
            reverse=True
        )
        
        logger.info(f"✅ 총 {len(all_news)}개 매일경제 뉴스 수집 완료")
        return all_news[:limit]
    
    async def search_news(self, 
                         query: str, 
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        키워드로 뉴스 검색 (단순 텍스트 매칭)
        
        Args:
            query: 검색 키워드
            limit: 반환할 뉴스 개수
            
        Returns:
            List[Dict]: 검색된 뉴스 리스트
        """
        # 최신 뉴스 가져오기 (더 많이)
        all_news = await self.fetch_latest_news(limit=30)
        
        # 키워드로 필터링
        query_lower = query.lower()
        filtered_news = []
        
        for news in all_news:
            title = news.get('title', '').lower()
            summary = news.get('summary', '').lower()
            
            # 제목이나 요약에 키워드가 포함되면 추가
            if query_lower in title or query_lower in summary:
                filtered_news.append(news)
                
                if len(filtered_news) >= limit:
                    break
        
        logger.info(f"✅ '{query}' 검색 결과: {len(filtered_news)}개")
        return filtered_news


# 전역 인스턴스
_mk_rss_simple = None


def get_mk_rss_simple():
    """매일경제 RSS 간단 수집기 인스턴스 반환"""
    global _mk_rss_simple
    if _mk_rss_simple is None:
        _mk_rss_simple = MKRSSSimple()
    return _mk_rss_simple


async def fetch_mk_news_simple(category: Optional[str] = None, 
                               limit: int = 10) -> List[Dict[str, Any]]:
    """매일경제 최신 뉴스 가져오기 (편의 함수)"""
    scraper = get_mk_rss_simple()
    return await scraper.fetch_latest_news(category, limit)


async def search_mk_news_simple(query: str, 
                                limit: int = 5) -> List[Dict[str, Any]]:
    """매일경제 뉴스 검색 (편의 함수)"""
    scraper = get_mk_rss_simple()
    return await scraper.search_news(query, limit)

