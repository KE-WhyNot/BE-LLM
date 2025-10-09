"""응답 생성 서비스 - 폴백 전용 (레거시)

⚠️ 주의: 이 서비스는 메타 에이전트 시스템 실패 시 폴백 용도로만 사용됩니다.
실제 응답 생성은 langgraph_enhanced/agents/response_agent.py에서 처리합니다.
"""

from typing import Dict, Any


class ResponseGeneratorService:
    """폴백 전용 응답 생성 서비스"""
    
    def __init__(self):
        pass
    
    def generate_error_response(self, error_msg: str) -> str:
        """에러 응답 생성 (폴백 전용)"""
        return f"""❌ 죄송합니다. 요청 처리 중 문제가 발생했습니다.

**오류 내용**
{error_msg}

**해결 방법**
1. 질문을 다시 입력해주세요
2. 다른 표현으로 질문해보세요
3. 잠시 후 다시 시도해주세요

더 궁금한 점이 있으시면 언제든 말씀해 주세요! 😊"""
    
    def generate_fallback_response(self, user_query: str) -> str:
        """일반 폴백 응답"""
        return f"""안녕하세요! 금융 챗봇입니다.

"{user_query}"에 대해 처리하려고 했지만, 현재 시스템에 일시적인 문제가 있습니다.

**이용 가능한 서비스**
📊 주가 조회: "삼성전자 주가 알려줘"
📈 종목 분석: "네이버 분석해줘"
📰 뉴스 검색: "반도체 뉴스"
📚 금융 지식: "PER이 뭐야?"

잠시 후 다시 시도해주세요! 😊"""


# 전역 인스턴스 (하위 호환성 유지)
response_generator = ResponseGeneratorService()
