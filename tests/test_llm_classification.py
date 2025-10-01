#!/usr/bin/env python3
"""
LLM 기반 의도 분류 테스트
"""

import sys
import os
# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.services.chatbot.chatbot_service import chatbot_service
from app.schemas.chat_schema import ChatRequest


async def test_queries():
    """다양한 쿼리로 LLM 분류 테스트"""
    
    test_cases = [
        ("삼성전자 주가 알려줘", "data"),
        ("네이버 현재 주식 알려줘", "data"),
        ("하이닉스 전망은 어때", "analysis"),
        ("네이버 투자 전략이", "analysis"),
        ("현대차 투자전략이", "analysis"),
        ("삼성전자 뉴스", "news"),
        ("배당주의 의미는", "knowledge"),
        ("투자전략이 어떻게 될까", "general"),  # 종목 없으면 general
    ]
    
    print("🔍 LLM 기반 의도 분류 테스트")
    print("=" * 70)
    
    for query, expected in test_cases:
        request = ChatRequest(
            message=query,
            user_id=1,
            session_id="test_session"
        )
        
        response = await chatbot_service.process_chat_request(request)
        
        # 응답 내용으로 분류 결과 추정
        if "주식 정보" in response.reply_text or "현재가:" in response.reply_text:
            actual = "data"
        elif "분석 결과" in response.reply_text or "투자 고려사항" in response.reply_text:
            actual = "analysis"
        elif "뉴스" in response.reply_text:
            actual = "news"
        elif "금융 지식" in response.reply_text:
            actual = "knowledge"
        else:
            actual = "general"
        
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{query}'")
        print(f"   예상: {expected}, 실제: {actual}")
        print(f"   응답: {response.reply_text[:100]}...")
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(test_queries())

