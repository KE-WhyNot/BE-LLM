#!/usr/bin/env python3
"""
매일경제 RSS 피드 간단 테스트
실제 RSS에서 데이터를 받아오는지 확인
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.workflow_components.mk_rss_scraper import MKNewsScraper


async def test_real_rss():
    """실제 RSS 피드 테스트"""
    print("🔍 매일경제 RSS 피드 실제 테스트")
    print("=" * 50)
    
    scraper = MKNewsScraper()
    
    # 최근 7일간의 뉴스 수집 (더 많은 데이터를 위해)
    articles = await scraper.scrape_all_feeds(days_back=7)
    
    print(f"✅ 수집된 기사 수: {len(articles)}개")
    
    if articles:
        print("\n📰 수집된 기사들:")
        for i, article in enumerate(articles[:5], 1):  # 처음 5개만 출력
            print(f"{i}. {article.title}")
            print(f"   카테고리: {article.category}")
            print(f"   발행일: {article.published}")
            print(f"   링크: {article.link}")
            print()
        
        # 카테고리별 집계
        categories = {}
        for article in articles:
            category = article.category
            categories[category] = categories.get(category, 0) + 1
        
        print("📊 카테고리별 기사 수:")
        for category, count in categories.items():
            print(f"   {category}: {count}개")
        
        return True
    else:
        print("❌ 수집된 기사가 없습니다.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_real_rss())
    if success:
        print("\n✅ RSS 피드에서 실제 데이터 수집 성공!")
    else:
        print("\n❌ RSS 피드에서 데이터 수집 실패!")

