"""섹터별 뉴스 및 시장 동향 사전 수집 & Neo4j 저장 서비스"""

import asyncio
import time
from typing import Dict, Any, List, Set
from datetime import datetime, timezone
from neo4j import GraphDatabase
import yaml

from app.config import settings
from app.services.workflow_components.news_service import NewsService
from app.services.langgraph_enhanced.agents.news_agent import NewsAgent
from langchain_google_genai import ChatGoogleGenerativeAI


class SectorDataBuilderService:
    """
    portfolio_stocks.yaml의 모든 섹터 정보를 읽어서
    1. 섹터별 뉴스 수집 & 분석
    2. 국제 시장 동향 수집
    3. Neo4j에 저장
    
    → 포트폴리오 추천 시 Neo4j에서 읽기만 하면 됨 (초고속)
    """
    
    def __init__(self):
        self.driver = None
        self.news_service = NewsService()
        self.news_agent = NewsAgent()
        self.llm = self._initialize_llm()
        self._connect_neo4j()
        
        # 섹터별 뉴스 검색 키워드
        self.sector_keywords = {
            "화학": ["화학", "chemical", "petrochemical"],
            "제약": ["제약", "pharmaceutical", "biotech"],
            "전기·전자": ["반도체", "semiconductor", "electronics"],
            "운송장비·부품": ["자동차", "automobile", "EV", "electric vehicle"],
            "기타금융": ["금융", "banking", "financial"],
            "기계·장비": ["기계", "machinery", "equipment"],
            "금속": ["철강", "steel", "metal"],
            "건설": ["건설", "construction", "infrastructure"],
            "IT 서비스": ["IT", "software", "cloud", "AI"]
        }
        
        # 전망 평가 키워드
        self.positive_keywords = [
            "성장", "증가", "상승", "호전", "개선", "확대", "긍정", "기대", "회복",
            "growth", "increase", "rise", "improvement", "expansion", "positive"
        ]
        
        self.negative_keywords = [
            "하락", "감소", "악화", "축소", "부정", "우려", "위험", "둔화",
            "decline", "decrease", "deterioration", "negative", "concern", "risk"
        ]
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.3,
                google_api_key=settings.google_api_key
            )
        return None
    
    def _connect_neo4j(self):
        """Neo4j 연결"""
        try:
            if settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                print("✅ 섹터 데이터 빌더: Neo4j 연결 성공")
                self._create_indexes()
            else:
                print("⚠️ Neo4j 설정 없음")
        except Exception as e:
            print(f"❌ Neo4j 연결 실패: {e}")
            self.driver = None
    
    def _create_indexes(self):
        """Neo4j 인덱스 생성"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # 섹터 노드 인덱스
                session.run("""
                    CREATE INDEX sector_name_index IF NOT EXISTS
                    FOR (s:Sector) ON (s.name)
                """)
                
                # 섹터 전망 인덱스
                session.run("""
                    CREATE INDEX sector_outlook_index IF NOT EXISTS
                    FOR (so:SectorOutlook) ON (so.sector_name)
                """)
                
                # 글로벌 동향 인덱스
                session.run("""
                    CREATE INDEX global_trend_date_index IF NOT EXISTS
                    FOR (gt:GlobalTrend) ON (gt.date)
                """)
                
                print("✅ Neo4j 인덱스 생성 완료")
        except Exception as e:
            print(f"⚠️ 인덱스 생성 실패: {e}")
    
    def load_sectors_from_yaml(self, yaml_path: str = "config/portfolio_stocks.yaml") -> Set[str]:
        """portfolio_stocks.yaml에서 모든 섹터 추출"""
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            sectors = set()
            for stock in data.get('stocks', []):
                sector = stock.get('sector')
                if sector:
                    sectors.add(sector)
            
            print(f"📊 YAML에서 {len(sectors)}개 섹터 로드: {', '.join(sorted(sectors))}")
            return sectors
            
        except Exception as e:
            print(f"❌ YAML 파일 로드 실패: {e}")
            return set()
    
    async def collect_and_save_all_sector_data(
        self,
        yaml_path: str = "config/portfolio_stocks.yaml",
        include_global_trends: bool = True
    ):
        """모든 섹터 데이터 수집 및 Neo4j 저장 (메인 함수)"""
        
        total_start = time.time()
        print("=" * 80)
        print("🚀 섹터 데이터 수집 & Neo4j 저장 시작")
        print("=" * 80)
        
        # 1. YAML에서 섹터 로드
        sectors = self.load_sectors_from_yaml(yaml_path)
        
        if not sectors:
            print("❌ 섹터 정보 없음")
            return
        
        # 2. 각 섹터별 뉴스 수집 & 분석 & 저장
        print(f"\n📊 {len(sectors)}개 섹터 뉴스 수집 시작...")
        
        sector_results = {}
        for i, sector in enumerate(sorted(sectors), 1):
            print(f"\n[{i}/{len(sectors)}] 🏢 {sector} 섹터 처리 중...")
            
            sector_start = time.time()
            
            try:
                # 뉴스 수집
                news_data = await self._collect_sector_news(sector)
                
                if news_data:
                    # LLM 분석
                    outlook = await self._analyze_sector_outlook(sector, news_data)
                    
                    # Neo4j 저장
                    self._save_sector_outlook_to_neo4j(sector, outlook, news_data)
                    
                    sector_results[sector] = {
                        "status": "success",
                        "news_count": len(news_data),
                        "outlook": outlook.get("outlook", "중립"),
                        "time": time.time() - sector_start
                    }
                else:
                    print(f"  ⚠️ {sector}: 뉴스 없음")
                    sector_results[sector] = {"status": "no_news", "time": time.time() - sector_start}
                
            except Exception as e:
                print(f"  ❌ {sector} 처리 실패: {e}")
                sector_results[sector] = {"status": "error", "error": str(e), "time": time.time() - sector_start}
            
            # API 부하 방지
            if i < len(sectors):
                print(f"  ⏳ 다음 섹터 전 대기 (2초)...")
                await asyncio.sleep(2)
        
        # 3. 국제 시장 동향 수집 & 저장
        if include_global_trends:
            print(f"\n🌍 국제 시장 동향 수집 중...")
            global_start = time.time()
            
            try:
                global_trends = await self._collect_global_market_trends()
                self._save_global_trends_to_neo4j(global_trends)
                print(f"  ✅ 국제 동향 저장 완료 ({time.time() - global_start:.1f}초)")
            except Exception as e:
                print(f"  ❌ 국제 동향 수집 실패: {e}")
        
        # 4. 결과 요약
        total_time = time.time() - total_start
        
        print("\n" + "=" * 80)
        print("📊 섹터 데이터 수집 완료 요약")
        print("=" * 80)
        
        success_count = sum(1 for r in sector_results.values() if r.get("status") == "success")
        
        print(f"✅ 성공: {success_count}/{len(sectors)} 섹터")
        print(f"⏱️  총 소요 시간: {total_time:.1f}초")
        
        for sector, result in sorted(sector_results.items()):
            status_icon = "✅" if result.get("status") == "success" else "⚠️"
            outlook = result.get("outlook", "N/A")
            news_count = result.get("news_count", 0)
            sector_time = result.get("time", 0)
            print(f"  {status_icon} {sector}: {outlook} ({news_count}개 뉴스, {sector_time:.1f}초)")
        
        print("\n🎉 Neo4j에 모든 데이터 저장 완료!")
        print(f"💡 포트폴리오 추천 시 Neo4j에서 즉시 읽어올 수 있습니다 (초고속)")
    
    async def _collect_sector_news(self, sector: str) -> List[Dict[str, Any]]:
        """섹터별 뉴스 수집 (Google RSS)"""
        
        keywords = self.sector_keywords.get(sector, [sector])
        all_news = []
        
        for keyword in keywords[:4]:  # 상위 4개 키워드만
            try:
                google_news = await self.news_service.get_comprehensive_news(
                    query=keyword,
                    use_google_rss=True,
                    translate=True
                )
                all_news.extend(google_news[:10])  # 키워드당 최대 10개
                await asyncio.sleep(0.3)  # API 부하 방지
            except Exception as e:
                print(f"    ⚠️ {keyword} 뉴스 검색 실패: {e}")
                continue
        
        # 중복 제거
        unique_news = self._remove_duplicate_news(all_news)
        print(f"  📰 뉴스 수집: {len(unique_news)}개")
        
        return unique_news[:30]  # 최대 30개
    
    def _remove_duplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 뉴스 제거"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news
    
    async def _analyze_sector_outlook(
        self, 
        sector: str, 
        news_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """섹터 전망 LLM 분석"""
        
        if not self.llm or not news_data:
            return self._get_neutral_outlook(sector)
        
        # 뉴스 요약 준비
        news_summary = "\n".join([
            f"- {news.get('title', '')} ({news.get('published', '')})"
            for news in news_data[:10]
        ])
        
        prompt = f"""당신은 금융 시장 분석 전문가입니다. {sector} 섹터의 최신 뉴스를 분석하여 투자 전망을 평가해주세요.

=== {sector} 섹터 최신 뉴스 ===
{news_summary}

=== 분석 요청 ===
위 뉴스들을 종합하여 다음 형식으로 분석해주세요:

sentiment_score: [-1.0 ~ +1.0 사이 점수, -1=매우부정, 0=중립, +1=매우긍정]
outlook: [매우긍정/긍정/중립/부정/매우부정 중 하나]
confidence: [0.0 ~ 1.0 사이 신뢰도]
key_factors: ["핵심 요인1", "핵심 요인2", "핵심 요인3"]
summary: [2-3문장으로 섹터 전망 요약]
market_impact: [시장에 미칠 영향 1-2문장]
time_horizon: [단기/중기/장기 중 투자 권장 기간]

응답 형식을 정확히 따라주세요."""

        try:
            response = await self.llm.ainvoke(prompt)
            return self._parse_outlook_response(response.content, sector, news_data)
        except Exception as e:
            print(f"    ⚠️ LLM 분석 실패: {e}")
            return self._get_neutral_outlook(sector)
    
    def _parse_outlook_response(
        self, 
        response_text: str, 
        sector: str,
        news_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """LLM 응답 파싱"""
        
        result = {
            "sector": sector,
            "sentiment_score": 0.0,
            "outlook": "중립",
            "confidence": 0.5,
            "key_factors": [],
            "summary": "",
            "market_impact": "",
            "time_horizon": "중기",
            "news_count": len(news_data)
        }
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'sentiment_score' in key:
                        try:
                            score = float(value)
                            result["sentiment_score"] = max(-1.0, min(1.0, score))
                        except:
                            pass
                    elif 'outlook' in key:
                        if value in ["매우긍정", "긍정", "중립", "부정", "매우부정"]:
                            result["outlook"] = value
                    elif 'confidence' in key:
                        try:
                            conf = float(value)
                            result["confidence"] = max(0.0, min(1.0, conf))
                        except:
                            pass
                    elif 'key_factors' in key:
                        factors = self._parse_array_field(value)
                        result["key_factors"] = factors[:5]
                    elif 'summary' in key:
                        result["summary"] = value
                    elif 'market_impact' in key:
                        result["market_impact"] = value
                    elif 'time_horizon' in key:
                        if value in ["단기", "중기", "장기"]:
                            result["time_horizon"] = value
        except Exception as e:
            print(f"    ⚠️ 응답 파싱 실패: {e}")
        
        print(f"  🧠 분석 완료: {result['outlook']} (신뢰도: {result['confidence']:.2f})")
        return result
    
    def _parse_array_field(self, value: str) -> List[str]:
        """배열 필드 파싱"""
        try:
            if '[' in value and ']' in value:
                clean_value = value.replace('[', '').replace(']', '').replace('"', '')
                items = [item.strip() for item in clean_value.split(',')]
                return [item for item in items if item and len(item) > 1]
            else:
                return [value] if value else []
        except:
            return []
    
    def _get_neutral_outlook(self, sector: str) -> Dict[str, Any]:
        """중립적 전망 반환 (폴백)"""
        return {
            "sector": sector,
            "sentiment_score": 0.0,
            "outlook": "중립",
            "confidence": 0.3,
            "key_factors": ["추가 분석 필요"],
            "summary": f"{sector} 섹터의 시장 전망은 현재 중립적입니다.",
            "market_impact": "시장 전반적인 흐름과 유사한 움직임 예상",
            "time_horizon": "중기",
            "news_count": 0
        }
    
    def _save_sector_outlook_to_neo4j(
        self,
        sector: str,
        outlook: Dict[str, Any],
        news_data: List[Dict[str, Any]]
    ):
        """섹터 전망을 Neo4j에 저장 (Relation 포함)"""
        
        if not self.driver:
            print(f"  ⚠️ Neo4j 연결 없음, 저장 스킵")
            return
        
        try:
            with self.driver.session() as session:
                # 1. 섹터 전망 저장 (MERGE: 있으면 업데이트, 없으면 생성)
                session.run("""
                    MERGE (so:SectorOutlook {sector_name: $sector})
                    SET so.sentiment_score = $sentiment_score,
                        so.outlook = $outlook,
                        so.confidence = $confidence,
                        so.key_factors = $key_factors,
                        so.summary = $summary,
                        so.market_impact = $market_impact,
                        so.time_horizon = $time_horizon,
                        so.news_count = $news_count,
                        so.updated_at = $updated_at
                """,
                    sector=sector,
                    sentiment_score=outlook.get("sentiment_score", 0.0),
                    outlook=outlook.get("outlook", "중립"),
                    confidence=outlook.get("confidence", 0.5),
                    key_factors=outlook.get("key_factors", []),
                    summary=outlook.get("summary", ""),
                    market_impact=outlook.get("market_impact", ""),
                    time_horizon=outlook.get("time_horizon", "중기"),
                    news_count=len(news_data),
                    updated_at=datetime.now(timezone.utc).isoformat()
                )
                
                # 2. 개별 뉴스 노드 생성 및 Relation 설정
                saved_news_count = 0
                for i, news in enumerate(news_data[:20]):  # 최대 20개 저장
                    news_id = f"{sector}_{i}_{news.get('title', '')[:30]}"  # ID 길이 증가
                    
                    try:
                        session.run("""
                            MERGE (so:SectorOutlook {sector_name: $sector})
                            MERGE (n:News {
                                news_id: $news_id,
                                sector: $sector
                            })
                            SET n.title = $title,
                                n.summary = $summary,
                                n.url = $url,
                                n.published = $published,
                                n.source = $source,
                                n.created_at = $created_at
                            MERGE (so)-[:HAS_NEWS]->(n)
                        """,
                            sector=sector,
                            news_id=news_id,
                            title=news.get('title', ''),
                            summary=news.get('summary', ''),
                            url=news.get('url', ''),
                            published=news.get('published', ''),
                            source=news.get('source', 'Google RSS'),
                            created_at=datetime.now(timezone.utc).isoformat()
                        )
                        saved_news_count += 1
                    except Exception as e:
                        print(f"    ⚠️ 뉴스 {i} 저장 실패: {e}")
                        continue
                
                print(f"  💾 Neo4j 저장 완료: {sector} (뉴스 {saved_news_count}/{len(news_data)}개 저장)")
                
        except Exception as e:
            print(f"  ❌ Neo4j 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    
    async def _collect_global_market_trends(self) -> Dict[str, Any]:
        """국제 시장 동향 수집"""
        
        global_keywords = [
            "global stock market",
            "US market trends", 
            "international finance"
        ]
        
        all_global_news = []
        
        for keyword in global_keywords:
            try:
                news = await self.news_service.get_comprehensive_news(
                    query=keyword,
                    use_google_rss=True,
                    translate=True
                )
                all_global_news.extend(news[:3])
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"    ⚠️ {keyword} 수집 실패: {e}")
                continue
        
        unique_news = self._remove_duplicate_news(all_global_news)
        
        # LLM으로 국제 동향 분석
        if self.llm and unique_news:
            news_summary = "\n".join([
                f"- {news.get('title', '')}"
                for news in unique_news[:10]
            ])
            
            prompt = f"""국제 금융 시장의 최신 동향을 분석해주세요.

=== 국제 시장 뉴스 ===
{news_summary}

다음 형식으로 분석해주세요:
overall_sentiment: [긍정/중립/부정]
key_trends: ["트렌드1", "트렌드2", "트렌드3"]
regional_impacts: ["영향1", "영향2"]
summary: [2-3문장 요약]
"""

            try:
                response = await self.llm.ainvoke(prompt)
                content = response.content
                
                return {
                    "overall_sentiment": "중립",
                    "key_trends": self._extract_from_response(content, "key_trends"),
                    "regional_impacts": self._extract_from_response(content, "regional_impacts"),
                    "summary": self._extract_from_response(content, "summary")[0] if self._extract_from_response(content, "summary") else "국제 시장 동향 분석 중",
                    "news_count": len(unique_news),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                print(f"    ⚠️ 국제 동향 분석 실패: {e}")
        
        return {
            "overall_sentiment": "중립",
            "key_trends": ["추가 분석 필요"],
            "regional_impacts": [],
            "summary": "국제 시장 동향을 모니터링 중입니다.",
            "news_count": len(unique_news),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _extract_from_response(self, text: str, field: str) -> List[str]:
        """응답에서 특정 필드 추출"""
        for line in text.split('\n'):
            if field in line.lower() and ':' in line:
                value = line.split(':', 1)[1].strip()
                return self._parse_array_field(value)
        return []
    
    def _save_global_trends_to_neo4j(self, trends: Dict[str, Any]):
        """국제 동향을 Neo4j에 저장 (Relation 포함)"""
        
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # 오늘 날짜 문자열 (YYYY-MM-DD)
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                
                # GlobalTrend 노드 저장
                session.run("""
                    MERGE (gt:GlobalTrend {date: $date})
                    SET gt.overall_sentiment = $overall_sentiment,
                        gt.key_trends = $key_trends,
                        gt.regional_impacts = $regional_impacts,
                        gt.summary = $summary,
                        gt.news_count = $news_count,
                        gt.updated_at = $updated_at
                """,
                    date=today,
                    overall_sentiment=trends.get("overall_sentiment", "중립"),
                    key_trends=trends.get("key_trends", []),
                    regional_impacts=trends.get("regional_impacts", []),
                    summary=trends.get("summary", ""),
                    news_count=trends.get("news_count", 0),
                    updated_at=trends.get("updated_at", datetime.now(timezone.utc).isoformat())
                )
                
                # 모든 섹터와 GlobalTrend 연결 (Relation)
                session.run("""
                    MATCH (gt:GlobalTrend {date: $date})
                    MATCH (so:SectorOutlook)
                    MERGE (gt)-[:AFFECTS_SECTOR]->(so)
                """, date=today)
                
                print(f"  💾 국제 동향 Neo4j 저장 완료 (날짜: {today}, 섹터 연결됨)")
                
        except Exception as e:
            print(f"  ❌ 국제 동향 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        """Neo4j 연결 종료"""
        if self.driver:
            self.driver.close()
            print("🔌 섹터 데이터 빌더: Neo4j 연결 종료")


# 전역 인스턴스
sector_data_builder_service = SectorDataBuilderService()

