"""금융 데이터 조회 서비스"""

from typing import Dict, Any
from app.utils.external import external_api_service
from app.utils.stock_utils import extract_symbol_from_query


class FinancialDataService:
    """금융 데이터 조회를 담당하는 서비스"""
    
    def __init__(self):
        pass
    
    async def get_financial_data(self, query: str) -> Dict[str, Any]:
        """쿼리에서 심볼을 추출하고 금융 데이터를 조회
        
        Args:
            query: 사용자 질문 또는 티커 심볼 (LLM이 이미 변환한 경우)
            
        Returns:
            Dict[str, Any]: 금융 데이터 또는 에러 정보
        """
        try:
            # LLM이 이미 심볼을 변환했을 가능성이 높으므로, 티커 심볼 패턴인지 먼저 확인
            import re
            
            # 1. 미국 주식 심볼 패턴 (1~5자 대문자 알파벳)
            if re.match(r'^[A-Z]{1,5}$', query):
                symbol = query
            # 2. 한국 주식 심볼 패턴 (6자리.KS)
            elif re.match(r'^\d{6}\.KS$', query):
                symbol = query
            # 3. 유럽/기타 주식 심볼 패턴 (1~5자 + .XX, 예: MC.PA, BP.L, BMW.DE)
            elif re.match(r'^[A-Z]{1,5}\.[A-Z]{1,3}$', query):
                symbol = query
            # 4. 자연어 질문인 경우에만 stock_utils 사용 (한글 종목명 등)
            else:
                symbol = extract_symbol_from_query(query)
                if not symbol:
                    return {"error": f"'{query}' 종목을 찾을 수 없습니다. 정확한 종목명이나 티커 심볼을 입력해주세요."}
            
            # 외부 API 서비스를 통한 데이터 조회 (비동기)
            data = await external_api_service.get_stock_data(symbol)
            if "error" in data:
                return data
            
            return data
            
        except Exception as e:
            return {"error": f"데이터 조회 중 오류: {str(e)}"}


# 전역 서비스 인스턴스
financial_data_service = FinancialDataService()
