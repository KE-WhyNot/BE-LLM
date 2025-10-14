"""섹터 뉴스 Neo4j 캐시 서비스 - 속도 최적화"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from neo4j import GraphDatabase
from app.config import settings


class SectorNewsCacheService:
    """섹터별 뉴스와 시장 전망을 Neo4j에 캐싱하여 속도 최적화"""
    
    def __init__(self):
        self.driver = None
        self.cache_ttl_minutes = 60  # 1시간 캐시 유지
        self._connect_neo4j()
    
    def _connect_neo4j(self):
        """Neo4j 연결"""
        try:
            if settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                print("✅ 섹터 뉴스 캐시: Neo4j 연결 성공")
                self._create_cache_indexes()
            else:
                print("⚠️ 섹터 뉴스 캐시: Neo4j 설정 없음, 캐싱 비활성화")
        except Exception as e:
            print(f"⚠️ 섹터 뉴스 캐시: Neo4j 연결 실패: {e}")
            self.driver = None
    
    def _create_cache_indexes(self):
        """캐시용 인덱스 생성"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # 섹터 캐시 노드 인덱스
                session.run("""
                    CREATE INDEX sector_cache_name_index IF NOT EXISTS
                    FOR (s:SectorCache) ON (s.sector_name)
                """)
                
                # 캐시 시간 인덱스 (만료 체크용)
                session.run("""
                    CREATE INDEX sector_cache_time_index IF NOT EXISTS
                    FOR (s:SectorCache) ON (s.cached_at)
                """)
                
                print("✅ 섹터 뉴스 캐시 인덱스 생성 완료")
        except Exception as e:
            print(f"⚠️ 캐시 인덱스 생성 실패: {e}")
    
    def get_cached_sector_outlook(self, sector: str) -> Optional[Dict[str, Any]]:
        """섹터 전망 캐시 조회"""
        
        if not self.driver:
            return None
        
        cache_start = time.time()
        
        try:
            with self.driver.session() as session:
                # TTL 체크: 현재 시각 - 캐시 생성 시각 < TTL
                current_time = datetime.now(timezone.utc).isoformat()
                ttl_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=self.cache_ttl_minutes)).isoformat()
                
                result = session.run("""
                    MATCH (sc:SectorCache {sector_name: $sector})
                    WHERE sc.cached_at > $ttl_cutoff
                    RETURN sc.sector_name AS sector,
                           sc.analysis_time AS analysis_time,
                           sc.news_count AS news_count,
                           sc.sentiment_score AS sentiment_score,
                           sc.outlook AS outlook,
                           sc.key_factors AS key_factors,
                           sc.confidence AS confidence,
                           sc.summary AS summary,
                           sc.weight_adjustment AS weight_adjustment,
                           sc.market_impact AS market_impact,
                           sc.cached_at AS cached_at
                    LIMIT 1
                """, sector=sector, ttl_cutoff=ttl_minutes_ago)
                
                record = result.single()
                
                if record:
                    cache_time = time.time() - cache_start
                    cached_data = {
                        "sector": record["sector"],
                        "analysis_time": record["analysis_time"],
                        "news_count": record["news_count"],
                        "sentiment_score": record["sentiment_score"],
                        "outlook": record["outlook"],
                        "key_factors": record["key_factors"] or [],
                        "confidence": record["confidence"],
                        "summary": record["summary"] or "",
                        "weight_adjustment": record["weight_adjustment"],
                        "market_impact": record.get("market_impact", "")
                    }
                    print(f"🎯 캐시 히트! {sector} 섹터 전망 ({cache_time:.3f}초)")
                    return cached_data
                else:
                    print(f"⚠️ 캐시 미스: {sector} (새로 분석 필요)")
                    return None
                    
        except Exception as e:
            print(f"❌ 캐시 조회 실패: {e}")
            return None
    
    def save_sector_outlook_cache(
        self, 
        sector: str, 
        outlook_data: Dict[str, Any]
    ) -> bool:
        """섹터 전망을 Neo4j에 캐싱"""
        
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # 기존 캐시 삭제 후 새로 저장 (MERGE 사용)
                session.run("""
                    MERGE (sc:SectorCache {sector_name: $sector})
                    SET sc.analysis_time = $analysis_time,
                        sc.news_count = $news_count,
                        sc.sentiment_score = $sentiment_score,
                        sc.outlook = $outlook,
                        sc.key_factors = $key_factors,
                        sc.confidence = $confidence,
                        sc.summary = $summary,
                        sc.weight_adjustment = $weight_adjustment,
                        sc.market_impact = $market_impact,
                        sc.cached_at = $cached_at
                """, 
                    sector=sector,
                    analysis_time=outlook_data.get("analysis_time", ""),
                    news_count=outlook_data.get("news_count", 0),
                    sentiment_score=outlook_data.get("sentiment_score", 0.0),
                    outlook=outlook_data.get("outlook", "중립"),
                    key_factors=outlook_data.get("key_factors", []),
                    confidence=outlook_data.get("confidence", 0.5),
                    summary=outlook_data.get("summary", ""),
                    weight_adjustment=outlook_data.get("weight_adjustment", 0),
                    market_impact=outlook_data.get("market_impact", ""),
                    cached_at=datetime.now(timezone.utc).isoformat()
                )
                
                print(f"💾 캐시 저장 완료: {sector} (TTL: {self.cache_ttl_minutes}분)")
                return True
                
        except Exception as e:
            print(f"❌ 캐시 저장 실패: {e}")
            return False
    
    def invalidate_sector_cache(self, sector: str) -> bool:
        """특정 섹터 캐시 무효화 (강제 갱신용)"""
        
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (sc:SectorCache {sector_name: $sector})
                    DELETE sc
                    RETURN count(sc) AS deleted_count
                """, sector=sector)
                
                record = result.single()
                deleted = record["deleted_count"] if record else 0
                
                if deleted > 0:
                    print(f"🗑️ 캐시 무효화: {sector}")
                    return True
                else:
                    print(f"⚠️ 캐시 없음: {sector}")
                    return False
                    
        except Exception as e:
            print(f"❌ 캐시 무효화 실패: {e}")
            return False
    
    def get_all_cached_sectors(self) -> List[str]:
        """캐시된 모든 섹터 목록 조회"""
        
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                ttl_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=self.cache_ttl_minutes)).isoformat()
                
                result = session.run("""
                    MATCH (sc:SectorCache)
                    WHERE sc.cached_at > $ttl_cutoff
                    RETURN sc.sector_name AS sector, 
                           sc.cached_at AS cached_at
                    ORDER BY sc.cached_at DESC
                """, ttl_cutoff=ttl_minutes_ago)
                
                cached_sectors = [record["sector"] for record in result]
                
                if cached_sectors:
                    print(f"📦 캐시된 섹터: {len(cached_sectors)}개 - {', '.join(cached_sectors)}")
                
                return cached_sectors
                
        except Exception as e:
            print(f"❌ 캐시 목록 조회 실패: {e}")
            return []
    
    def cleanup_expired_cache(self) -> int:
        """만료된 캐시 정리"""
        
        if not self.driver:
            return 0
        
        try:
            with self.driver.session() as session:
                ttl_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=self.cache_ttl_minutes)).isoformat()
                
                result = session.run("""
                    MATCH (sc:SectorCache)
                    WHERE sc.cached_at <= $ttl_cutoff
                    DELETE sc
                    RETURN count(sc) AS deleted_count
                """, ttl_cutoff=ttl_minutes_ago)
                
                record = result.single()
                deleted = record["deleted_count"] if record else 0
                
                if deleted > 0:
                    print(f"🧹 만료된 캐시 정리: {deleted}개")
                
                return deleted
                
        except Exception as e:
            print(f"❌ 캐시 정리 실패: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        
        if not self.driver:
            return {"enabled": False}
        
        try:
            with self.driver.session() as session:
                ttl_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=self.cache_ttl_minutes)).isoformat()
                
                # 유효한 캐시 수
                valid_result = session.run("""
                    MATCH (sc:SectorCache)
                    WHERE sc.cached_at > $ttl_cutoff
                    RETURN count(sc) AS valid_count
                """, ttl_cutoff=ttl_minutes_ago)
                
                valid_count = valid_result.single()["valid_count"]
                
                # 만료된 캐시 수
                expired_result = session.run("""
                    MATCH (sc:SectorCache)
                    WHERE sc.cached_at <= $ttl_cutoff
                    RETURN count(sc) AS expired_count
                """, ttl_cutoff=ttl_minutes_ago)
                
                expired_count = expired_result.single()["expired_count"]
                
                return {
                    "enabled": True,
                    "ttl_minutes": self.cache_ttl_minutes,
                    "valid_cache_count": valid_count,
                    "expired_cache_count": expired_count,
                    "total_cache_count": valid_count + expired_count
                }
                
        except Exception as e:
            print(f"❌ 캐시 통계 조회 실패: {e}")
            return {"enabled": True, "error": str(e)}
    
    def close(self):
        """Neo4j 연결 종료"""
        if self.driver:
            self.driver.close()
            print("🔌 섹터 뉴스 캐시: Neo4j 연결 종료")


# 전역 인스턴스
sector_news_cache_service = SectorNewsCacheService()

