#!/usr/bin/env python3
"""
뉴스 지식 베이스 업데이트 스크립트
실제 뉴스 데이터를 수집하여 RAG 지식 베이스에 추가합니다.
"""

import asyncio
from app.services.rag_service import rag_service

async def main():
    """뉴스 지식 베이스 업데이트"""
    print("🚀 뉴스 지식 베이스 업데이트를 시작합니다...")
    
    # 특정 쿼리로 뉴스 수집
    test_queries = ["삼성전자", "KOSPI", "금리", "ai"]
    
    for query in test_queries:
        print(f"\n📰 '{query}' 관련 뉴스 수집 중...")
        try:
            # 뉴스 가져오기 테스트
            news_list = rag_service.get_financial_news(query, max_results=3)
            print(f"  - {len(news_list)}개의 뉴스를 찾았습니다.")
            
            for i, news in enumerate(news_list, 1):
                print(f"    {i}. {news.get('title', 'No title')[:50]}...")
            
            # 지식 베이스에 추가
            rag_service.add_news_to_knowledge_base(query, max_news=3)
            
        except Exception as e:
            print(f"  - 오류: {e}")
    
    print("\n✅ 뉴스 지식 베이스 업데이트가 완료되었습니다!")

if __name__ == "__main__":
    asyncio.run(main())
