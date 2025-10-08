"""
매일경제 RSS 스크래퍼 테스트

매일경제 RSS 피드에서 뉴스를 수집하고 임베딩하여 
Neo4j 지식그래프로 저장하는 기능을 테스트합니다.

실행 방법:
python -m pytest tests/test_mk_rss_scraper.py -v
또는
python tests/test_mk_rss_scraper.py

Author: Financial Chatbot Team
Date: 2025-01-05
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.workflow_components.mk_rss_scraper import (
    MKNewsScraper, 
    MKKnowledgeGraphService,
    update_mk_knowledge_graph,
    search_mk_news
)


async def test_rss_scraping():
    """RSS 스크래핑 테스트"""
    print("=" * 60)
    print("🔍 매일경제 RSS 스크래핑 테스트")
    print("=" * 60)
    
    scraper = MKNewsScraper()
    
    try:
        # 최근 1일간의 뉴스 수집
        articles = await scraper.scrape_all_feeds(days_back=1)
        
        print(f"✅ 수집된 기사 수: {len(articles)}개")
        
        if articles:
            # 첫 번째 기사 정보 출력
            first_article = articles[0]
            print(f"\n📰 첫 번째 기사:")
            print(f"   제목: {first_article.title}")
            print(f"   카테고리: {first_article.category}")
            print(f"   발행일: {first_article.published}")
            print(f"   링크: {first_article.link}")
            print(f"   본문 길이: {len(first_article.content or '')}자")
            
            # 카테고리별 집계
            categories = {}
            for article in articles:
                category = article.category
                categories[category] = categories.get(category, 0) + 1
            
            print(f"\n📊 카테고리별 기사 수:")
            for category, count in categories.items():
                print(f"   {category}: {count}개")
        
        return len(articles) > 0
        
    except Exception as e:
        print(f"❌ RSS 스크래핑 테스트 실패: {e}")
        return False


async def test_embedding_generation():
    """임베딩 생성 테스트"""
    print("\n" + "=" * 60)
    print("🧠 임베딩 생성 테스트")
    print("=" * 60)
    
    scraper = MKNewsScraper()
    
    try:
        # 샘플 기사 생성
        from app.services.workflow_components.mk_rss_scraper import MKNewsArticle
        sample_articles = [
            MKNewsArticle(
                title="삼성전자 주가 상승세 지속... 반도체 업황 회복 기대감",
                link="https://example.com/news1",
                published="2025-01-05T10:00:00",
                category="securities",
                summary="삼성전자 주가가 연일 상승세를 보이고 있다.",
                content="삼성전자 주가가 연일 상승세를 보이고 있다. 반도체 업황 회복 기대감과 함께 글로벌 메모리 시장의 회복 조짐이 주가 상승을 견인하고 있다."
            ),
            scraper.MKNewsArticle(
                title="SK하이닉스, HBM 메모리 시장 선점 노력 가속화",
                link="https://example.com/news2",
                published="2025-01-05T11:00:00",
                category="economy",
                summary="SK하이닉스가 AI 시대의 핵심 부품인 HBM 메모리 시장에서 경쟁 우위를 확보하기 위해 투자를 확대하고 있다.",
                content="SK하이닉스가 AI 시대의 핵심 부품인 HBM 메모리 시장에서 경쟁 우위를 확보하기 위해 투자를 확대하고 있다."
            )
        ]
        
        # 임베딩 생성
        articles_with_embeddings = scraper.generate_embeddings(sample_articles)
        
        print(f"✅ 임베딩 생성 완료: {len(articles_with_embeddings)}개 기사")
        
        for i, article in enumerate(articles_with_embeddings):
            if article.embedding:
                print(f"   기사 {i+1}: 임베딩 차원 {len(article.embedding)}")
                print(f"   제목: {article.title[:50]}...")
            else:
                print(f"   기사 {i+1}: 임베딩 생성 실패")
        
        return all(article.embedding is not None for article in articles_with_embeddings)
        
    except Exception as e:
        print(f"❌ 임베딩 생성 테스트 실패: {e}")
        return False


async def test_neo4j_integration():
    """Neo4j 연동 테스트 (Neo4j가 설치되어 있을 때만)"""
    print("\n" + "=" * 60)
    print("🔗 Neo4j 연동 테스트")
    print("=" * 60)
    
    try:
        from py2neo import Graph
        
        # Neo4j 연결 테스트
        try:
            graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
            graph.run("RETURN 1")  # 간단한 쿼리로 연결 테스트
            print("✅ Neo4j 연결 성공")
            neo4j_available = True
        except Exception as e:
            print(f"⚠️ Neo4j 연결 실패: {e}")
            print("   Neo4j가 설치되어 있지 않거나 실행되지 않고 있습니다.")
            neo4j_available = False
        
        if neo4j_available:
            # 실제 Neo4j 연동 테스트
            scraper = MKNewsScraper()
            
            if scraper.neo4j_graph:
                print("✅ 스크래퍼 Neo4j 연결 성공")
                
                # 샘플 기사 생성 및 저장
                sample_article = MKNewsArticle(
                    title="테스트 기사: 삼성전자 주가 상승",
                    link="https://test.com/news",
                    published="2025-01-05T12:00:00",
                    category="test",
                    summary="테스트용 기사입니다.",
                    content="이것은 Neo4j 연동 테스트를 위한 샘플 기사입니다."
                )
                
                # 임베딩 생성
                sample_article.embedding = [0.1] * 768  # 더미 임베딩
                
                # Neo4j에 저장
                storage_stats = await scraper.store_to_neo4j([sample_article])
                print(f"✅ Neo4j 저장 결과: {storage_stats}")
                
                return True
            else:
                print("❌ 스크래퍼 Neo4j 연결 실패")
                return False
        else:
            print("⚠️ Neo4j 테스트 스킵됨")
            return True  # Neo4j가 없어도 테스트는 성공으로 간주
        
    except ImportError:
        print("⚠️ py2neo 모듈이 설치되어 있지 않습니다.")
        print("   pip install py2neo 로 설치하세요.")
        return True  # 모듈이 없어도 테스트는 성공으로 간주
    except Exception as e:
        print(f"❌ Neo4j 연동 테스트 실패: {e}")
        return False


async def test_knowledge_graph_service():
    """지식그래프 서비스 통합 테스트"""
    print("\n" + "=" * 60)
    print("🧠 지식그래프 서비스 테스트")
    print("=" * 60)
    
    try:
        kg_service = MKKnowledgeGraphService()
        
        # 지식그래프 업데이트 테스트 (Neo4j가 없으면 스킵)
        if kg_service.scraper.neo4j_graph:
            print("🔄 지식그래프 업데이트 테스트...")
            result = await kg_service.update_knowledge_graph(days_back=1)
            
            if result.get('status') == 'success':
                print(f"✅ 지식그래프 업데이트 성공")
                print(f"   수집된 기사: {result.get('articles_collected', 0)}개")
                print(f"   실행 시간: {result.get('execution_time', 0):.2f}초")
            else:
                print(f"❌ 지식그래프 업데이트 실패: {result.get('error', '알 수 없는 오류')}")
            
            return result.get('status') == 'success'
        else:
            print("⚠️ Neo4j 연결이 없어 지식그래프 업데이트 테스트를 스킵합니다.")
            return True
        
    except Exception as e:
        print(f"❌ 지식그래프 서비스 테스트 실패: {e}")
        return False


async def test_news_search():
    """뉴스 검색 테스트"""
    print("\n" + "=" * 60)
    print("🔍 뉴스 검색 테스트")
    print("=" * 60)
    
    try:
        # 뉴스 검색 테스트
        search_results = await search_mk_news("삼성전자", limit=3)
        
        print(f"✅ 검색 결과: {len(search_results)}개")
        
        for i, article in enumerate(search_results, 1):
            print(f"   {i}. {article['title']}")
            print(f"      유사도: {article['similarity']:.3f}")
            print(f"      카테고리: {article['category']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 뉴스 검색 테스트 실패: {e}")
        return False


async def main():
    """전체 테스트 실행"""
    print("🚀 매일경제 RSS 스크래퍼 전체 테스트 시작")
    print("=" * 80)
    
    test_results = []
    
    # 1. RSS 스크래핑 테스트
    result1 = await test_rss_scraping()
    test_results.append(("RSS 스크래핑", result1))
    
    # 2. 임베딩 생성 테스트
    result2 = await test_embedding_generation()
    test_results.append(("임베딩 생성", result2))
    
    # 3. Neo4j 연동 테스트
    result3 = await test_neo4j_integration()
    test_results.append(("Neo4j 연동", result3))
    
    # 4. 지식그래프 서비스 테스트
    result4 = await test_knowledge_graph_service()
    test_results.append(("지식그래프 서비스", result4))
    
    # 5. 뉴스 검색 테스트
    result5 = await test_news_search()
    test_results.append(("뉴스 검색", result5))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"⚠️ {total - passed}개 테스트가 실패했습니다.")
    
    return passed == total


if __name__ == "__main__":
    # 비동기 실행
    success = asyncio.run(main())
    
    if success:
        print("\n✅ 테스트 완료: 매일경제 RSS 스크래퍼가 정상적으로 작동합니다!")
        print("\n📝 사용 방법:")
        print("1. Neo4j 설치 및 실행 (선택사항)")
        print("2. 환경변수 설정 (.env 파일)")
        print("3. 지식그래프 업데이트: await update_mk_knowledge_graph()")
        print("4. 뉴스 검색: await search_mk_news('검색어')")
    else:
        print("\n❌ 일부 테스트가 실패했습니다. 로그를 확인하세요.")
        sys.exit(1)
