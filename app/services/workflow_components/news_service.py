"""뉴스 조회 서비스 (동적 프롬프팅 지원)"""

import asyncio
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.services.workflow_components.data_agent_service import NewsCollector
from app.utils.stock_utils import get_company_name_from_symbol
from app.services.langgraph_enhanced import prompt_manager


class NewsService:
    """금융 뉴스 조회를 담당하는 서비스 (data_agent의 NewsCollector 사용 + 동적 프롬프팅)"""
    
    def __init__(self):
        self.news_collector = NewsCollector()  # data_agent의 수집기 재사용
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
                google_api_key=settings.google_api_key
            )
        return None
    
    def get_financial_news(self, query: str) -> List[Dict[str, Any]]:
        """한국어 금융 뉴스를 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            query: 뉴스 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 한국어 뉴스 리스트
        """
        try:
            print(f"📰 한국어 금융 뉴스 검색: {query}")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = asyncio.run(self.news_collector.collect_news(days_back=1))
            
            # 쿼리와 관련된 기사 필터링
            relevant_articles = []
            for article in articles:
                # 제목이나 내용에 쿼리 키워드가 포함된 경우
                if (query.lower() in article.title.lower() or 
                    (article.content and query.lower() in article.content.lower())):
                    
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score
                    }
                    relevant_articles.append(news_item)
            
            print(f"✅ 관련 뉴스 {len(relevant_articles)}개 발견")
            return relevant_articles[:5]  # 최대 5개 반환
            
        except Exception as e:
            print(f"❌ 한국어 뉴스 조회 중 오류: {e}")
            return []
    
    def get_latest_market_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최신 한국 시장 뉴스 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 한국어 시장 뉴스 리스트
        """
        try:
            print(f"📈 최신 한국 시장 뉴스 조회 (최대 {limit}개)")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = asyncio.run(self.news_collector.collect_news(days_back=1))
            
            # 시장 관련 키워드로 필터링
            market_keywords = ['시장', '주식', '증시', '코스피', '코스닥', '거래량', '상승', '하락']
            market_articles = []
            
            for article in articles:
                # 시장 관련 키워드가 포함된 기사만 선택
                if any(keyword in article.title.lower() for keyword in market_keywords):
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score
                    }
                    market_articles.append(news_item)
            
            print(f"✅ 시장 뉴스 {len(market_articles)}개 발견")
            return market_articles[:limit]
            
        except Exception as e:
            print(f"❌ 최신 시장 뉴스 조회 중 오류: {e}")
            return []
    
    def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """특정 종목의 한국어 뉴스 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            symbol: 주식 심볼 (예: "005930.KS")
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 한국어 종목 뉴스 리스트
        """
        try:
            # 심볼에서 회사명 추출하여 검색
            company_name = get_company_name_from_symbol(symbol)
            if not company_name:
                # 심볼을 직접 사용
                company_name = symbol.replace(".KS", "")
            
            print(f"📊 {company_name} 관련 한국어 뉴스 검색")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = asyncio.run(self.news_collector.collect_news(days_back=3))  # 3일간의 뉴스
            
            # 해당 종목과 관련된 기사 필터링
            stock_articles = []
            for article in articles:
                # 제목이나 내용에 회사명이 포함된 경우
                if (company_name.lower() in article.title.lower() or 
                    (article.content and company_name.lower() in article.content.lower())):
                    
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score,
                        'symbol': symbol,
                        'company_name': company_name
                    }
                    stock_articles.append(news_item)
            
            print(f"✅ {company_name} 관련 뉴스 {len(stock_articles)}개 발견")
            return stock_articles[:limit]
            
        except Exception as e:
            print(f"❌ 종목 뉴스 조회 중 오류: {e}")
            return []
    
    def generate_news_analysis(self, 
                               query: str, 
                               news_data: List[Dict[str, Any]]) -> str:
        """✨ LLM 기반 동적 프롬프팅 뉴스 분석 (새로운 메서드)
        
        Args:
            query: 사용자 질문
            news_data: 뉴스 데이터 리스트
            
        Returns:
            str: AI 생성 뉴스 분석 결과
        """
        if not self.llm or not news_data:
            # LLM이 없거나 뉴스가 없으면 단순 나열
            return self._format_news_simple(news_data)
        
        try:
            # ✨ 동적 프롬프트 생성
            messages = prompt_manager.generate_news_prompt(
                news_data=news_data,
                user_query=query
            )
            
            # LLM 호출
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"❌ AI 뉴스 분석 생성 오류: {e}")
            # 오류 시 단순 나열로 폴백
            return self._format_news_simple(news_data)
    
    def _format_news_simple(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 단순 포맷팅 (폴백용)"""
        if not news_data:
            return "관련 뉴스를 찾을 수 없습니다."
        
        result = f"📰 총 {len(news_data)}개의 뉴스:\n\n"
        for i, news in enumerate(news_data, 1):
            result += f"{i}. {news['title']}\n"
            result += f"   {news.get('summary', '')[:100]}...\n"
            result += f"   🔗 {news['url']}\n\n"
        
        return result


# 전역 서비스 인스턴스
news_service = NewsService()
