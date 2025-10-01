#!/usr/bin/env python3
"""
자동 뉴스 분석 테스트 스크립트
"""
import asyncio
from app.services.financial_agent import AutoNewsAnalysisTool

async def main():
    """자동 뉴스 분석 테스트"""
    print("🔍 자동 뉴스 분석 테스트를 시작합니다...")
    
    # 테스트 쿼리들
    test_queries = [
        "삼성전자 최근 동향",
        "KOSPI 뉴스 분석",
        "메모리 시장 동향"
    ]
    
    auto_news_tool = AutoNewsAnalysisTool()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📰 테스트 {i}: {query}")
        print("=" * 80)
        
        try:
            result = auto_news_tool(query)
            print(result)
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
