#!/usr/bin/env python3
"""
Stock Utils 통합 테스트
"""

import sys
import os
# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.stock_utils import (
    extract_symbol_from_query,
    extract_symbols_for_news,
    get_company_name_from_symbol,
    is_valid_symbol
)
from app.services.workflow_components.financial_data_service import financial_data_service
from app.services.workflow_components.news_service import news_service


def test_stock_utils():
    """Stock Utils 기능 테스트"""
    print("=" * 60)
    print("🧪 Stock Utils 통합 테스트")
    print("=" * 60)
    
    # 1. 단일 심볼 추출 테스트
    print("\n1️⃣ 단일 심볼 추출 테스트")
    print("-" * 40)
    test_queries = [
        "삼성전자 주가",
        "SK하이닉스 시세",
        "005930 현재가",
        "네이버 주식",
        "현대 차 정보"  # 띄어쓰기 테스트
    ]
    
    for query in test_queries:
        symbol = extract_symbol_from_query(query)
        print(f"  '{query}' → {symbol}")
    
    # 2. 다중 심볼 추출 테스트 (뉴스용)
    print("\n2️⃣ 다중 심볼 추출 테스트")
    print("-" * 40)
    news_queries = [
        "삼성전자 뉴스",
        "SK하이닉스 최신 소식",
        "코스피 동향"
    ]
    
    for query in news_queries:
        symbols = extract_symbols_for_news(query)
        print(f"  '{query}' → {symbols}")
    
    # 3. 회사명 역검색 테스트
    print("\n3️⃣ 회사명 역검색 테스트")
    print("-" * 40)
    test_symbols = ["005930.KS", "000660.KS", "035420.KS"]
    
    for symbol in test_symbols:
        name = get_company_name_from_symbol(symbol)
        print(f"  {symbol} → {name}")
    
    # 4. 심볼 유효성 테스트
    print("\n4️⃣ 심볼 유효성 테스트")
    print("-" * 40)
    test_symbols = ["005930.KS", "AAPL", "^KS11", "INVALID"]
    
    for symbol in test_symbols:
        valid = is_valid_symbol(symbol)
        print(f"  {symbol} → {'✅ 유효' if valid else '❌ 무효'}")
    
    # 5. Financial Data Service 통합 테스트
    print("\n5️⃣ Financial Data Service 통합 테스트")
    print("-" * 40)
    result = financial_data_service.get_financial_data("삼성전자 주가")
    if "error" in result:
        print(f"  ❌ 에러: {result['error']}")
    else:
        print(f"  ✅ 성공: {result.get('company_name')} - {result.get('current_price')}원")
    
    # 6. News Service 통합 테스트
    print("\n6️⃣ News Service 통합 테스트")
    print("-" * 40)
    news = news_service.get_stock_news("005930.KS", limit=2)
    print(f"  뉴스 개수: {len(news)}")
    if news:
        print(f"  첫 번째 뉴스: {news[0].get('title', 'N/A')[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_stock_utils()

