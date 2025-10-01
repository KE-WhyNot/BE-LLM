#!/usr/bin/env python3
"""
뉴스 URL 분석 테스트 스크립트
"""
import asyncio
from app.services.financial_agent import NewsAnalysisTool

async def main():
    """뉴스 URL 분석 테스트"""
    print("🔍 뉴스 URL 분석 테스트를 시작합니다...")
    
    # 테스트할 뉴스 URL들 (실제 Yahoo Finance 뉴스 URL)
    test_urls = [
        "https://finance.yahoo.com/news/verizon-communications-inc-vz-expands-224427610.html?.tsrc=rss",
        "https://finance.yahoo.com/news/memory-hunger-game-begins-know-093031847.html?.tsrc=rss"
    ]
    
    news_tool = NewsAnalysisTool()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📰 테스트 {i}: 뉴스 URL 분석")
        print("=" * 80)
        print(f"URL: {url}")
        print("-" * 80)
        
        try:
            result = news_tool(url)
            print(result)
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
