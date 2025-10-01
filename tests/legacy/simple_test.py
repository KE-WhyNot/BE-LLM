#!/usr/bin/env python3
"""
간단한 뉴스 검색 테스트 스크립트
"""
import asyncio
from app.services.financial_agent import financial_agent

async def main():
    """뉴스 검색 테스트"""
    print("🔍 뉴스 검색 테스트를 시작합니다...")
    
    # 테스트 쿼리들
    test_queries = [
        "삼성전자 뉴스 알려줘",
        "KOSPI 뉴스",
        "금리 뉴스"
    ]
    
    for query in test_queries:
        print(f"\n📰 쿼리: {query}")
        print("-" * 50)
        
        try:
            # 뉴스 도구 직접 호출
            from app.services.financial_agent import FinancialNewsTool
            news_tool = FinancialNewsTool()
            result = news_tool(query)
            print(result)
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
