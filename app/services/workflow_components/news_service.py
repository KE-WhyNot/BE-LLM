"""뉴스 조회 서비스"""

from typing import List, Dict, Any
from app.services.external_api_service import external_api_service
from app.utils.stock_utils import get_company_name_from_symbol


class NewsService:
    """금융 뉴스 조회를 담당하는 서비스"""
    
    def __init__(self):
        pass
    
    def get_financial_news(self, query: str) -> List[Dict[str, Any]]:
        """금융 뉴스를 조회
        
        Args:
            query: 뉴스 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 뉴스 리스트
        """
        try:
            # 외부 API 서비스를 통한 뉴스 조회
            news = external_api_service.get_news_from_rss(query)
            return news if news else []
            
        except Exception as e:
            print(f"뉴스 조회 중 오류: {e}")
            return []
    
    def get_latest_market_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최신 시장 뉴스 조회
        
        Args:
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 뉴스 리스트
        """
        try:
            news = external_api_service.get_news_from_rss("한국 증시 시장", max_results=limit)
            return news if news else []
            
        except Exception as e:
            print(f"최신 뉴스 조회 중 오류: {e}")
            return []
    
    def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """특정 종목 뉴스 조회
        
        Args:
            symbol: 주식 심볼 (예: "005930.KS")
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 뉴스 리스트
        """
        try:
            # 심볼에서 회사명 추출하여 검색
            company_name = get_company_name_from_symbol(symbol)
            if not company_name:
                # 심볼을 직접 사용
                company_name = symbol.replace(".KS", "")
            
            news = external_api_service.get_news_from_rss(company_name, max_results=limit)
            return news if news else []
            
        except Exception as e:
            print(f"종목 뉴스 조회 중 오류: {e}")
            return []


# 전역 서비스 인스턴스
news_service = NewsService()
