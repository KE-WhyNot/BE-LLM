#!/usr/bin/env python3
"""Neo4j 섹터 데이터 확인 스크립트"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from neo4j import GraphDatabase
from app.config import settings

def check_neo4j_connection():
    """Neo4j 연결 및 섹터 데이터 확인"""
    
    print("=" * 80)
    print("🔍 Neo4j 섹터 데이터 확인")
    print("=" * 80)
    print()
    
    # Neo4j 설정 확인
    print("📋 Neo4j 설정:")
    print(f"  URI: {settings.neo4j_uri}")
    print(f"  User: {settings.neo4j_user}")
    print(f"  Password: {'*' * len(settings.neo4j_password) if settings.neo4j_password else 'None'}")
    print()
    
    if not all([settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password]):
        print("❌ Neo4j 설정이 없습니다!")
        return
    
    try:
        # Neo4j 연결
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        
        print("✅ Neo4j 연결 성공!")
        print()
        
        with driver.session() as session:
            # 1. SectorOutlook 노드 개수 확인
            print("📊 저장된 섹터 데이터:")
            print("-" * 40)
            
            result = session.run("""
                MATCH (so:SectorOutlook)
                RETURN count(so) AS total_count
            """)
            
            total = result.single()["total_count"]
            print(f"  총 SectorOutlook 노드: {total}개")
            
            if total == 0:
                print()
                print("  ⚠️ 섹터 데이터가 없습니다!")
                print("  💡 다음 명령으로 데이터 빌드:")
                print("     python build_sector_data.py")
                print()
            else:
                # 2. 각 섹터별 상세 정보
                print()
                print("📋 섹터별 상세:")
                print("-" * 40)
                
                result = session.run("""
                    MATCH (so:SectorOutlook)
                    RETURN so.sector_name AS sector,
                           so.outlook AS outlook,
                           so.sentiment_score AS sentiment,
                           so.confidence AS confidence,
                           so.news_count AS news_count,
                           so.updated_at AS updated_at
                    ORDER BY so.sector_name
                """)
                
                for record in result:
                    sector = record["sector"]
                    outlook = record["outlook"] or "N/A"
                    sentiment = record["sentiment"] or 0
                    confidence = record["confidence"] or 0
                    news_count = record["news_count"] or 0
                    updated = record["updated_at"] or "N/A"
                    
                    print(f"  🏢 {sector}:")
                    print(f"     전망: {outlook} (신뢰도: {confidence:.2f})")
                    print(f"     감정: {sentiment:.2f}, 뉴스: {news_count}개")
                    print(f"     갱신: {updated[:19] if len(updated) > 19 else updated}")
                    print()
            
            # 3. GlobalTrend 노드 확인
            print("🌍 국제 시장 동향:")
            print("-" * 40)
            
            result = session.run("""
                MATCH (gt:GlobalTrend)
                RETURN count(gt) AS count
            """)
            
            global_count = result.single()["count"]
            print(f"  총 GlobalTrend 노드: {global_count}개")
            
            if global_count > 0:
                result = session.run("""
                    MATCH (gt:GlobalTrend)
                    RETURN gt.overall_sentiment AS sentiment,
                           gt.summary AS summary,
                           gt.news_count AS news_count,
                           gt.updated_at AS updated_at
                    ORDER BY gt.updated_at DESC
                    LIMIT 1
                """)
                
                record = result.single()
                if record:
                    print(f"  최신 동향: {record['sentiment']}")
                    print(f"  요약: {record['summary'][:60]}...")
                    print(f"  뉴스: {record['news_count']}개")
            print()
            
            # 4. 인덱스 확인
            print("🔍 인덱스 상태:")
            print("-" * 40)
            
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            
            sector_indexes = [idx for idx in indexes if 'sector' in str(idx).lower()]
            print(f"  총 인덱스: {len(indexes)}개")
            print(f"  섹터 관련 인덱스: {len(sector_indexes)}개")
            
            for idx in sector_indexes[:5]:
                index_info = dict(idx)
                index_name = index_info.get('name', 'N/A')
                print(f"    - {index_name}")
            print()
            
        driver.close()
        print("✅ Neo4j 데이터 확인 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_neo4j_connection()

