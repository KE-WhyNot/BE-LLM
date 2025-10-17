import asyncio
import time


def _print_sample(news, max_items=3):
    n = len(news or [])
    print(f"총 {n}건")
    for i, item in enumerate((news or [])[:max_items], 1):
        t = item.get("title", "N/A")
        src = item.get("source", "?")
        lang = item.get("language", "?")
        pub = item.get("published", "")
        print(f"  {i}. [{src}|{lang}] {t} ({pub[:19]})")


async def _run_once(query: str):
    from app.services.workflow_components.news_service import news_service
    t0 = time.perf_counter()
    news = await news_service.get_comprehensive_news(query=query, translate=True)
    dt = (time.perf_counter() - t0) * 1000
    print(f"⏱ '{query}' 1차: {dt:.1f}ms", end=" | ")
    _print_sample(news)
    t1 = time.perf_counter()
    news2 = await news_service.get_comprehensive_news(query=query, translate=True)
    dt2 = (time.perf_counter() - t1) * 1000
    print(f"⏱ '{query}' 2차(캐시 기대): {dt2:.1f}ms", end=" | ")
    _print_sample(news2)


def test_news_yfinance_multiple_symbols():
    # 다양한 종목/표현 테스트
    queries = [
        "TSLA",                # 미국
        "AAPL",                # 미국
        "MSFT",                # 미국
        "NVDA",                # 미국
        "005930.KS",           # 한국(삼성전자)
        "035420.KS",           # 한국(네이버)
        "Samsung Electronics", # 영문 회사명
        "Naver",               # 영문 회사명
        "삼성전자",              # 한글 회사명(심볼 추출 경로)
        "네이버",                # 한글 회사명(심볼 추출 경로)
    ]

    async def main():
        # 캐시 초기화 (매 실행 시 동일 조건)
        from app.services.workflow_components.news_service import news_service
        try:
            news_service.news_cache.clear()
            print("🧹 뉴스 캐시 초기화 완료")
        except Exception:
            pass

        for q in queries:
            print(f"\n=== 테스트: {q} ===")
            await _run_once(q)

    asyncio.run(main())


