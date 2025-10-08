"""
Google RSS 뉴스 수집 및 한국어 번역 서비스

사용자 요청 시 실시간으로 Google RSS에서 뉴스를 수집하고
한국어로 자동 번역하여 제공합니다.

Author: Financial Chatbot Team
Date: 2025-01-05
"""

import asyncio
import logging
import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from deep_translator import GoogleTranslator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TranslatedNews:
    """번역된 뉴스 데이터 클래스"""
    title: str
    title_en: str
    summary: str
    summary_en: str
    link: str
    published: str
    source: str = "google_rss"
    translated: bool = True
    language: str = "ko"


class GoogleRSSTranslator:
    """Google RSS 뉴스 수집 및 번역 서비스"""
    
    def __init__(self):
        # Google Translator 초기화
        self.translator = GoogleTranslator(source='auto', target='ko')
        
        # Google RSS 검색 URL
        self.google_rss_base_url = "https://news.google.com/rss/search"
    
    async def search_and_translate(self, 
                                   query: str, 
                                   limit: int = 5,
                                   language: str = 'en') -> List[TranslatedNews]:
        """Google RSS에서 뉴스 검색 및 번역
        
        Args:
            query: 검색 쿼리
            limit: 반환할 뉴스 개수
            language: 검색 언어 (기본: 영어)
            
        Returns:
            List[TranslatedNews]: 번역된 뉴스 리스트
        """
        try:
            logger.info(f"Google RSS 뉴스 검색: {query} (언어: {language})")
            
            # 1. Google RSS 검색
            rss_url = self._build_rss_url(query, language)
            feed = feedparser.parse(rss_url)
            
            if feed.bozo or len(feed.entries) == 0:
                logger.warning(f"Google RSS 피드 파싱 실패: {rss_url}")
                return []
            
            # 2. 뉴스 수집 및 번역
            translated_news = []
            for entry in feed.entries[:limit]:
                try:
                    news = await self._translate_entry(entry)
                    if news:
                        translated_news.append(news)
                except Exception as e:
                    logger.error(f"뉴스 번역 실패: {e}")
                    continue
            
            logger.info(f"✅ Google RSS 뉴스 {len(translated_news)}개 수집 및 번역 완료")
            return translated_news
            
        except Exception as e:
            logger.error(f"Google RSS 검색 실패: {e}")
            return []
    
    def _build_rss_url(self, query: str, language: str) -> str:
        """Google RSS 검색 URL 생성"""
        # 쿼리 인코딩
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        # 언어 파라미터 추가
        lang_param = f"&hl={language}" if language else ""
        
        return f"{self.google_rss_base_url}?q={encoded_query}{lang_param}"
    
    async def _translate_entry(self, entry: Dict) -> Optional[TranslatedNews]:
        """RSS 엔트리 번역"""
        try:
            # 원문 추출
            title_en = entry.get('title', '').strip()
            summary_en = entry.get('summary', '').strip()
            
            if not title_en:
                return None
            
            # 제목 번역
            title_ko = await self._translate_text(title_en)
            
            # 요약 번역 (있으면)
            summary_ko = ""
            if summary_en:
                # HTML 태그 제거
                summary_en_clean = self._remove_html_tags(summary_en)
                summary_ko = await self._translate_text(summary_en_clean[:500])  # 500자 제한
            
            # 발행일 파싱
            published = self._parse_date(entry.get('published', ''))
            
            return TranslatedNews(
                title=title_ko,
                title_en=title_en,
                summary=summary_ko,
                summary_en=summary_en,
                link=entry.get('link', ''),
                published=published,
                source="google_rss",
                translated=True,
                language="ko"
            )
            
        except Exception as e:
            logger.error(f"엔트리 번역 실패: {e}")
            return None
    
    async def _translate_text(self, text: str) -> str:
        """텍스트 번역 (비동기)"""
        try:
            # 비동기 실행을 위해 ThreadPoolExecutor 사용
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(
                None, 
                self.translator.translate, 
                text
            )
            return translated
            
        except Exception as e:
            logger.error(f"번역 실패: {e}")
            return text  # 번역 실패 시 원문 반환
    
    def _remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text().strip()
    
    def _parse_date(self, date_str: str) -> str:
        """날짜 파싱"""
        try:
            if not date_str:
                return datetime.now().isoformat()
            
            # feedparser의 날짜 파싱 결과 사용
            import feedparser
            parsed_time = feedparser._parse_date_w3dtf(date_str)
            
            if parsed_time:
                return parsed_time.isoformat()
            
            return datetime.now().isoformat()
            
        except Exception:
            return datetime.now().isoformat()
    
    async def search_financial_news(self, 
                                   company_name: str, 
                                   limit: int = 5) -> List[TranslatedNews]:
        """특정 회사의 금융 뉴스 검색 및 번역
        
        Args:
            company_name: 회사명 (예: "Samsung Electronics")
            limit: 반환할 뉴스 개수
            
        Returns:
            List[TranslatedNews]: 번역된 뉴스 리스트
        """
        # 금융 관련 키워드 추가
        query = f"{company_name} stock market finance"
        return await self.search_and_translate(query, limit, language='en')
    
    async def search_market_news(self, 
                                market: str = "stock market", 
                                limit: int = 5) -> List[TranslatedNews]:
        """시장 뉴스 검색 및 번역
        
        Args:
            market: 시장 키워드 (예: "stock market", "cryptocurrency")
            limit: 반환할 뉴스 개수
            
        Returns:
            List[TranslatedNews]: 번역된 뉴스 리스트
        """
        query = f"{market} news today"
        return await self.search_and_translate(query, limit, language='en')


# 전역 서비스 인스턴스
google_rss_translator = GoogleRSSTranslator()


async def search_google_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Google RSS 뉴스 검색 함수 (외부 호출용)"""
    news_list = await google_rss_translator.search_and_translate(query, limit)
    
    # Dict 형식으로 변환
    return [
        {
            'title': news.title,
            'title_en': news.title_en,
            'summary': news.summary,
            'summary_en': news.summary_en,
            'url': news.link,
            'published': news.published,
            'source': news.source,
            'translated': news.translated,
            'language': news.language
        }
        for news in news_list
    ]


if __name__ == "__main__":
    """직접 실행 시 테스트"""
    async def main():
        # 테스트 1: 삼성전자 뉴스 검색
        print("🔍 삼성전자 뉴스 검색 및 번역 테스트...")
        samsung_news = await search_google_news("Samsung Electronics", limit=3)
        
        print(f"\n✅ 검색 결과: {len(samsung_news)}개")
        for i, news in enumerate(samsung_news, 1):
            print(f"\n{i}. {news['title']}")
            print(f"   원문: {news['title_en']}")
            print(f"   링크: {news['url']}")
            print(f"   발행일: {news['published']}")
        
        # 테스트 2: 시장 뉴스 검색
        print("\n\n🔍 주식 시장 뉴스 검색 및 번역 테스트...")
        market_news = await google_rss_translator.search_market_news(limit=2)
        
        print(f"\n✅ 검색 결과: {len(market_news)}개")
        for i, news in enumerate(market_news, 1):
            print(f"\n{i}. {news.title}")
            print(f"   원문: {news.title_en}")
    
    # 비동기 실행
    asyncio.run(main())
