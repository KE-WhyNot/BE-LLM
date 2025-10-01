"""금융 데이터 조회 서비스"""

from typing import Dict, Any
from app.services.external_api_service import external_api_service
from app.utils.stock_utils import extract_symbol_from_query


class FinancialDataService:
    """금융 데이터 조회를 담당하는 서비스"""
    
    def __init__(self):
        pass
    
    def get_financial_data(self, query: str) -> Dict[str, Any]:
        """쿼리에서 심볼을 추출하고 금융 데이터를 조회
        
        Args:
            query: 사용자 질문
            
        Returns:
            Dict[str, Any]: 금융 데이터 또는 에러 정보
        """
        try:
            # 심볼 추출 (통합 유틸리티 사용)
            symbol = extract_symbol_from_query(query)
            if not symbol:
                return {"error": "주식 심볼을 찾을 수 없습니다."}
            
            # 외부 API 서비스를 통한 데이터 조회
            data = external_api_service.get_stock_data(symbol)
            if "error" in data:
                return data
            
            return data
            
        except Exception as e:
            return {"error": f"데이터 조회 중 오류: {str(e)}"}


# 전역 서비스 인스턴스
financial_data_service = FinancialDataService()
