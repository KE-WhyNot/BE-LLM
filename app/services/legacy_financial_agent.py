"""
금융 전문가 에이전트 (레거시 - 현재는 financial_workflow로 대체됨)
공용 포맷터로 로직이 이동되어 이 파일은 참고용으로만 유지
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.services.rag_service import rag_service
from app.services.formatters import stock_data_formatter, news_formatter, analysis_formatter
from app.config import settings


class FinancialAgent:
    """금융 전문가 에이전트 (레거시)"""
    
    def __init__(self):
        print("⚠️ FinancialAgent는 레거시입니다. financial_workflow를 사용하세요.")
        self.rag_service = rag_service
    
    def chat(self, message: str, user_id: int = 1) -> Dict[str, Any]:
        """채팅 처리 (레거시)"""
        print("⚠️ FinancialAgent.chat()은 더 이상 사용되지 않습니다.")
        return {
            "success": False,
            "reply_text": "FinancialAgent는 더 이상 사용되지 않습니다. financial_workflow를 사용하세요.",
            "action_type": "error",
            "action_data": {}
        }
    
    def get_conversation_history(self) -> list:
        """대화 기록 조회 (레거시)"""
        return []
    
    def clear_memory(self):
        """메모리 초기화 (레거시)"""
        pass


# 레거시 인스턴스 (호환성을 위해 유지)
financial_agent = FinancialAgent()