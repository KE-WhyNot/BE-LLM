#!/usr/bin/env python3
"""Neo4j Relation 구조 확인 스크립트"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from neo4j import GraphDatabase
from app.config import settings

def check_neo4j_relations():
    """Neo4j Relation 구조 확인"""
    
    print("=" * 80)
    print("🔍 Neo4j Relation 구조 확인")
    print("=" * 80)
    print()
    
    if not all([settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password]):
        print("❌ Neo4j 설정이 없습니다!")
        return
    
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        
        print("✅ Neo4j 연결 성공!")
        print()
        
        with driver.session() as session:
            # 1. 노드 통계
            print("📊 노드 통계:")
            print("-" * 40)
            
            node_types = ['SectorOutlook', 'News', 'GlobalTrend']
            for node_type in node_types:
                result = session.run(f"""
                    MATCH (n:{node_type})
                    RETURN count(n) AS count
                """)
                count = result.single()["count"]
                print(f"  {node_type}: {count}개")
            print()
            
            # 2. Relation 통계
            print("🔗 Relation 통계:")
            print("-" * 40)
            
            # HAS_NEWS relation
            result = session.run("""
                MATCH ()-[r:HAS_NEWS]->()
                RETURN count(r) AS count
            """)
            has_news_count = result.single()["count"]
            print(f"  HAS_NEWS (섹터→뉴스): {has_news_count}개")
            
            # AFFECTS_SECTOR relation
            result = session.run("""
                MATCH ()-[r:AFFECTS_SECTOR]->()
                RETURN count(r) AS count
            """)
            affects_sector_count = result.single()["count"]
            print(f"  AFFECTS_SECTOR (글로벌→섹터): {affects_sector_count}개")
            print()
            
            # 3. 섹터별 뉴스 개수
            print("📰 섹터별 뉴스 연결:")
            print("-" * 40)
            
            result = session.run("""
                MATCH (so:SectorOutlook)-[r:HAS_NEWS]->(n:News)
                RETURN so.sector_name AS sector, count(n) AS news_count
                ORDER BY so.sector_name
            """)
            
            for record in result:
                sector = record["sector"]
                news_count = record["news_count"]
                print(f"  🏢 {sector}: {news_count}개 뉴스")
            print()
            
            # 4. GlobalTrend와 연결된 섹터
            print("🌍 국제 동향과 섹터 연결:")
            print("-" * 40)
            
            result = session.run("""
                MATCH (gt:GlobalTrend)-[r:AFFECTS_SECTOR]->(so:SectorOutlook)
                RETURN gt.date AS date, count(so) AS sector_count
                ORDER BY gt.date DESC
                LIMIT 5
            """)
            
            global_trends = list(result)
            if global_trends:
                for record in global_trends:
                    date = record["date"]
                    sector_count = record["sector_count"]
                    print(f"  📅 {date}: {sector_count}개 섹터에 영향")
            else:
                print(f"  ⚠️ GlobalTrend 데이터 없음")
            print()
            
            # 5. 샘플 데이터 조회 (특정 섹터의 뉴스)
            print("📋 샘플 데이터 (전기·전자 섹터):")
            print("-" * 40)
            
            result = session.run("""
                MATCH (so:SectorOutlook {sector_name: "전기·전자"})-[:HAS_NEWS]->(n:News)
                RETURN n.title AS title, n.published AS published
                ORDER BY n.created_at DESC
                LIMIT 5
            """)
            
            news_list = list(result)
            if news_list:
                for i, record in enumerate(news_list, 1):
                    title = record["title"][:60] + "..." if len(record["title"]) > 60 else record["title"]
                    published = record["published"][:10] if record["published"] else "N/A"
                    print(f"  {i}. [{published}] {title}")
            else:
                print("  ⚠️ 전기·전자 섹터 뉴스 없음")
            print()
            
            # 6. Relation 구조 시각화
            print("🗺️  Relation 구조:")
            print("-" * 40)
            print()
            print("  GlobalTrend")
            print("       │")
            print("       │ AFFECTS_SECTOR")
            print("       ↓")
            print("  SectorOutlook (섹터 전망)")
            print("       │")
            print("       │ HAS_NEWS")
            print("       ↓")
            print("  News (개별 뉴스)")
            print()
            
            # 7. 데이터 품질 체크
            print("✅ 데이터 품질 체크:")
            print("-" * 40)
            
            issues = []
            
            # 뉴스 없는 섹터 확인
            result = session.run("""
                MATCH (so:SectorOutlook)
                WHERE NOT (so)-[:HAS_NEWS]->()
                RETURN so.sector_name AS sector
            """)
            empty_sectors = [r["sector"] for r in result]
            if empty_sectors:
                issues.append(f"뉴스 없는 섹터: {', '.join(empty_sectors)}")
            
            # GlobalTrend 연결 확인
            result = session.run("""
                MATCH (gt:GlobalTrend)
                WHERE NOT (gt)-[:AFFECTS_SECTOR]->()
                RETURN count(gt) AS count
            """)
            unconnected_trends = result.single()["count"]
            if unconnected_trends > 0:
                issues.append(f"연결 안 된 GlobalTrend: {unconnected_trends}개")
            
            if issues:
                for issue in issues:
                    print(f"  ⚠️ {issue}")
            else:
                print("  ✅ 모든 데이터 정상!")
            print()
            
        driver.close()
        print("=" * 80)
        print("✅ Neo4j Relation 구조 확인 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_neo4j_relations()

