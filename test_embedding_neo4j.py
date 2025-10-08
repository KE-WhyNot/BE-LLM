#!/usr/bin/env python3
"""
매일경제 RSS + 임베딩 + Neo4j 통합 테스트
실제 RSS 데이터로 임베딩 생성하고 Neo4j에 저장하는 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.workflow_components.mk_rss_scraper import MKNewsScraper


async def test_full_pipeline():
    """전체 파이프라인 테스트 (RSS → 임베딩 → Neo4j)"""
    print("🚀 매일경제 RSS + 임베딩 + Neo4j 통합 테스트")
    print("=" * 60)
    
    scraper = MKNewsScraper()
    
    try:
        # 1. RSS 피드에서 뉴스 수집 (최근 3일, 적은 수로 테스트)
        print("📰 1단계: RSS 피드에서 뉴스 수집...")
        articles = await scraper.scrape_all_feeds(days_back=3)
        
        if not articles:
            print("❌ 수집된 뉴스가 없습니다.")
            return False
        
        print(f"✅ {len(articles)}개 기사 수집 완료")
        
        # 처음 5개 기사만 테스트용으로 사용
        test_articles = articles[:5]
        print(f"🧪 테스트용 {len(test_articles)}개 기사로 진행")
        
        # 2. 임베딩 생성
        print("\n🧠 2단계: 임베딩 생성...")
        articles_with_embeddings = scraper.generate_embeddings(test_articles)
        
        print(f"✅ {len(articles_with_embeddings)}개 기사에 임베딩 생성 완료")
        
        # 임베딩 정보 출력
        for i, article in enumerate(articles_with_embeddings, 1):
            if article.embedding:
                print(f"   {i}. {article.title[:50]}... (임베딩 차원: {len(article.embedding)})")
            else:
                print(f"   {i}. {article.title[:50]}... (임베딩 생성 실패)")
        
        # 3. Neo4j 저장 (Neo4j가 있을 때만)
        print("\n🔗 3단계: Neo4j 저장...")
        if scraper.neo4j_graph:
            storage_stats = await scraper.store_to_neo4j(articles_with_embeddings)
            print(f"✅ Neo4j 저장 완료: {storage_stats}")
            
            # 4. 검색 테스트
            print("\n🔍 4단계: 검색 테스트...")
            search_results = await scraper.search_similar_articles("삼성전자", limit=3)
            print(f"✅ 검색 결과: {len(search_results)}개")
            
            for i, result in enumerate(search_results, 1):
                print(f"   {i}. {result['title'][:50]}... (유사도: {result['similarity']:.3f})")
        else:
            print("⚠️ Neo4j 연결이 없어 저장 및 검색 테스트를 스킵합니다.")
            print("   Neo4j를 설치하고 실행한 후 다시 테스트하세요.")
        
        print("\n🎉 전체 파이프라인 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    if success:
        print("\n✅ 매일경제 RSS → 임베딩 → Neo4j 파이프라인이 정상 작동합니다!")
        print("\n📝 사용 방법:")
        print("1. Neo4j 설치 및 실행 (선택사항)")
        print("2. 지식그래프 업데이트: await update_mk_knowledge_graph()")
        print("3. 뉴스 검색: await search_mk_news('검색어')")
    else:
        print("\n❌ 테스트가 실패했습니다.")
        sys.exit(1)

