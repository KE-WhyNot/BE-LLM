"""
매일경제 뉴스 일일 자동 업데이트 스크립트

사용법:
1. 수동 실행: python daily_news_updater.py
2. Cron 설정 (매일 아침 9시):
   0 9 * * * cd /Users/doyun/Desktop/KEF/BE-LLM && source venv/bin/activate && python daily_news_updater.py >> logs/daily_update.log 2>&1
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.workflow_components.mk_rss_scraper import update_mk_knowledge_graph


async def daily_update():
    """매일 최신 뉴스 업데이트"""
    
    print("="*70)
    print(f"매일경제 뉴스 일일 업데이트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        # 최근 1일치 뉴스만 수집 (매일 실행 기준)
        result = await update_mk_knowledge_graph(days_back=1)
        
        print(f"\n✅ 업데이트 완료!")
        print(f"   - 총 수집: {result['articles_collected']}개")
        print(f"   - 신규 저장: {result['storage_stats']['new_articles']}개")
        print(f"   - 업데이트: {result['storage_stats']['updated_articles']}개")
        print(f"   - 오류: {result['storage_stats']['errors']}개")
        print(f"   - 소요 시간: {result['execution_time']:.1f}초")
        print(f"   - 상태: {result['status']}")
        
        # 현재 DB 통계
        print(f"\n📊 현재 Neo4j KG 통계:")
        from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService
        kg = MKKnowledgeGraphService()
        total = kg.scraper.neo4j_graph.run("MATCH (a:Article) RETURN count(a) AS total").data()
        print(f"   - 총 기사 수: {total[0]['total']}개")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(daily_update())
    
    # 종료 코드 (cron 모니터링용)
    exit(0 if result and result.get('status') == 'success' else 1)

