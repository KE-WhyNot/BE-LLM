"""섹터별 뉴스 전망 분석 서비스"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.services.workflow_components.news_service import NewsService
from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService
from app.services.langgraph_enhanced.agents.news_agent import NewsAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class SectorAnalysisService:
    """섹터별 뉴스 분석 및 전망 평가 서비스"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.mk_kg_service = MKKnowledgeGraphService()
        self.news_agent = NewsAgent()
        self.llm = self._initialize_llm()
        
        # 섹터 키워드 매핑
        self.sector_keywords = {
            "화학": ["화학", "chemical", "petrochemical", "specialty chemical"],
            "제약": ["제약", "pharmaceutical", "biotech", "drug development", "medicine"],
            "전기·전자": ["반도체", "semiconductor", "electronics", "chip", "memory", "display"],
            "운송장비·부품": ["자동차", "automobile", "automotive", "electric vehicle", "EV", "battery"],
            "기타금융": ["금융", "banking", "financial", "insurance", "fintech"],
            "기계·장비": ["기계", "machinery", "equipment", "industrial equipment"],
            "금속": ["철강", "steel", "metal", "aluminum", "copper"],
            "건설": ["건설", "construction", "infrastructure", "real estate"],
            "IT 서비스": ["IT", "software", "platform", "cloud", "AI", "technology"]
        }
        
        # 전망 평가 키워드
        self.positive_keywords = [
            "성장", "증가", "상승", "호전", "개선", "확대", "긍정", "기대", "회복", "안정",
            "growth", "increase", "rise", "improvement", "expansion", "positive", "optimistic"
        ]
        
        self.negative_keywords = [
            "하락", "감소", "악화", "축소", "부정", "우려", "위험", "둔화", "변동성",
            "decline", "decrease", "deterioration", "negative", "concern", "risk", "volatility"
        ]
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.3,
                google_api_key=settings.google_api_key
            )
        return None
    
    async def analyze_sector_outlook(
        self, 
        sector: str, 
        time_range: str = "week"
    ) -> Dict[str, Any]:
        """섹터별 전망 분석"""
        
        try:
            print(f"📊 {sector} 섹터 전망 분석 시작...")
            
            # 1. 섹터 관련 뉴스 수집
            news_data = await self._collect_sector_news(sector, time_range)
            
            if not news_data:
                return self._get_neutral_outlook(sector)
            
            # 2. 뉴스 분석 및 전망 평가
            outlook_analysis = await self._analyze_news_sentiment(news_data, sector)
            
            # 3. 결과 종합
            sector_outlook = {
                "sector": sector,
                "analysis_time": datetime.now(timezone.utc).isoformat(),
                "news_count": len(news_data),
                "sentiment_score": outlook_analysis.get("sentiment_score", 0),
                "outlook": outlook_analysis.get("outlook", "중립"),
                "key_factors": outlook_analysis.get("key_factors", []),
                "confidence": outlook_analysis.get("confidence", 0.5),
                "summary": outlook_analysis.get("summary", ""),
                "weight_adjustment": self._calculate_weight_adjustment(
                    outlook_analysis.get("sentiment_score", 0)
                )
            }
            
            print(f"✅ {sector} 섹터 분석 완료: {sector_outlook['outlook']} (신뢰도: {sector_outlook['confidence']:.2f})")
            return sector_outlook
            
        except Exception as e:
            print(f"❌ {sector} 섹터 분석 실패: {e}")
            return self._get_neutral_outlook(sector)
    
    async def _collect_sector_news(self, sector: str, time_range: str) -> List[Dict[str, Any]]:
        """섹터 관련 뉴스 수집"""
        
        keywords = self.sector_keywords.get(sector, [sector])
        all_news = []
        
        # 각 키워드로 뉴스 검색
        for keyword in keywords[:2]:  # 상위 2개 키워드만 사용
            try:
                # 한글 키워드는 매일경제에서, 영문 키워드는 Google RSS에서
                if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7AF for char in keyword):
                    # 한글 키워드 - 매일경제 검색
                    mk_news = await self.mk_kg_service.search_news(
                        query=keyword, 
                        limit=3
                    )
                    for news in mk_news:
                        news['source'] = 'mk_rss'
                        all_news.append(news)
                else:
                    # 영문 키워드 - Google RSS 검색
                    google_news = await self.news_service.get_comprehensive_news(
                        query=keyword,
                        use_google_rss=True,
                        translate=True
                    )
                    all_news.extend(google_news[:3])
                
                # API 부하 방지를 위한 딜레이
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️ {keyword} 뉴스 검색 실패: {e}")
                continue
        
        # 중복 제거 및 최신순 정렬
        unique_news = self._remove_duplicate_news(all_news)
        return unique_news[:10]  # 최대 10개
    
    async def _analyze_news_sentiment(
        self, 
        news_data: List[Dict[str, Any]], 
        sector: str
    ) -> Dict[str, Any]:
        """뉴스 감정 분석 및 전망 평가 (파장 예상 포함)"""
        
        if not self.llm:
            return self._fallback_sentiment_analysis(news_data, sector)
        
        # 뉴스 텍스트 추출
        news_texts = []
        for news in news_data:
            title = news.get('title', '')
            summary = news.get('summary', news.get('content', ''))
            published = news.get('published', '')
            source = news.get('source', 'Unknown')
            news_texts.append(f"[{source}] {title}\n내용: {summary}\n발행: {published}")
        
        combined_text = "\n\n".join(news_texts[:5])  # 상위 5개 뉴스만 분석
        
        # 강화된 LLM 프롬프트 (파장 예상 포함)
        prompt = f"""당신은 금융 전문 애널리스트입니다. {sector} 섹터 관련 뉴스들을 분석하여 시장 전망과 예상되는 파장을 평가해주세요.

=== 뉴스 내용 ===
{combined_text}

=== 분석 요청 ===
위 뉴스들을 종합적으로 분석하여 다음 형식으로 응답해주세요:

sentiment_score: [감정 점수 -1.0(매우 부정) ~ +1.0(매우 긍정)]
outlook: [긍정적/중립적/부정적 중 하나]
confidence: [신뢰도 0.0 ~ 1.0 (뉴스의 신뢰성과 일관성 고려)]
key_factors: ["요인1", "요인2", "요인3"]
market_impact: [예상되는 시장 파장과 영향 범위 설명]
time_horizon: [단기(1-3개월)/중기(3-12개월)/장기(1년 이상) 중 주요 영향 기간]
risk_factors: ["리스크1", "리스크2"]
opportunity_factors: ["기회1", "기회2"]
summary: [투자자 관점에서의 핵심 요약 (2-3문장)]

=== 분석 기준 ===
1. 뉴스의 신뢰성: 출처와 내용의 구체성 평가
2. 시장 파장: 해당 섹터뿐만 아니라 연관 산업에 미칠 영향
3. 시점별 영향: 단기 vs 중장기 관점 구분
4. 투자 관점: 실제 투자 결정에 도움이 되는 구체적 근거

응답은 반드시 위 형식을 정확히 따라주세요."""

        try:
            response = await self.llm.ainvoke(prompt)
            return self._parse_enhanced_sentiment_response(response.content, sector, news_data)
        except Exception as e:
            print(f"⚠️ LLM 감정 분석 실패: {e}")
            return self._fallback_sentiment_analysis(news_data, sector)
    
    def _parse_enhanced_sentiment_response(
        self, 
        response_text: str, 
        sector: str, 
        news_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """강화된 LLM 응답 파싱 (파장 예상 포함)"""
        
        result = {
            "sentiment_score": 0.0,
            "outlook": "중립적",
            "confidence": 0.5,
            "key_factors": [],
            "market_impact": f"{sector} 섹터에 대한 명확한 영향 분석이 어려운 상황입니다.",
            "time_horizon": "중기",
            "risk_factors": [],
            "opportunity_factors": [],
            "summary": f"{sector} 섹터 전망 분석 결과",
            "news_sources": len(news_data),
            "analysis_depth": "enhanced"
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
                        if value in ["긍정적", "중립적", "부정적"]:
                            result["outlook"] = value
                    elif 'confidence' in key:
                        try:
                            conf = float(value)
                            result["confidence"] = max(0.0, min(1.0, conf))
                        except:
                            pass
                    elif 'market_impact' in key:
                        result["market_impact"] = value
                    elif 'time_horizon' in key:
                        if any(t in value for t in ["단기", "중기", "장기"]):
                            result["time_horizon"] = value
                    elif 'summary' in key:
                        result["summary"] = value
                    elif any(factor_key in key for factor_key in ['key_factors', 'risk_factors', 'opportunity_factors']):
                        # 배열 파싱
                        factors = self._parse_array_field(value)
                        if 'key_factors' in key:
                            result["key_factors"] = factors[:3]
                        elif 'risk_factors' in key:
                            result["risk_factors"] = factors[:2]
                        elif 'opportunity_factors' in key:
                            result["opportunity_factors"] = factors[:2]
            
            # 신뢰도 추가 검증 (뉴스 품질 고려)
            result["confidence"] = self._adjust_confidence_by_news_quality(
                result["confidence"], news_data
            )
            
        except Exception as e:
            print(f"⚠️ 강화된 응답 파싱 실패: {e}")
        
        return result
    
    def _parse_array_field(self, value: str) -> List[str]:
        """배열 형태 필드 파싱"""
        try:
            # 대괄호 제거 후 쉼표로 분할
            if '[' in value and ']' in value:
                clean_value = value.replace('[', '').replace(']', '').replace('"', '')
                items = [item.strip() for item in clean_value.split(',')]
                return [item for item in items if item]
            else:
                return [value] if value else []
        except:
            return [value] if value else []
    
    def _adjust_confidence_by_news_quality(
        self, 
        base_confidence: float, 
        news_data: List[Dict[str, Any]]
    ) -> float:
        """뉴스 품질에 따른 신뢰도 조정"""
        
        if not news_data:
            return 0.3
        
        quality_factors = []
        
        for news in news_data:
            source = news.get('source', '')
            title_length = len(news.get('title', ''))
            content_length = len(news.get('summary', news.get('content', '')))
            
            # 출처별 가중치
            if 'mk' in source.lower() or 'maeil' in source.lower():
                quality_factors.append(0.9)  # 매일경제 높은 신뢰도
            elif 'google' in source.lower():
                quality_factors.append(0.7)  # Google RSS 중간 신뢰도
            else:
                quality_factors.append(0.5)
            
            # 콘텐츠 품질 평가
            if title_length > 10 and content_length > 50:
                quality_factors.append(0.8)
            elif title_length > 5 and content_length > 20:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.4)
        
        avg_quality = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        # 기본 신뢰도와 뉴스 품질을 결합
        adjusted_confidence = (base_confidence * 0.7) + (avg_quality * 0.3)
        
        return max(0.2, min(0.9, adjusted_confidence))
    
    def _fallback_sentiment_analysis(
        self, 
        news_data: List[Dict[str, Any]], 
        sector: str
    ) -> Dict[str, Any]:
        """폴백 감정 분석 (키워드 기반)"""
        
        positive_count = 0
        negative_count = 0
        total_count = 0
        
        for news in news_data:
            text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
            
            pos_matches = sum(1 for keyword in self.positive_keywords if keyword in text)
            neg_matches = sum(1 for keyword in self.negative_keywords if keyword in text)
            
            positive_count += pos_matches
            negative_count += neg_matches
            total_count += len(text.split())
        
        # 점수 계산
        if positive_count + negative_count == 0:
            sentiment_score = 0.0
            outlook = "중립적"
        else:
            sentiment_score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            if sentiment_score > 0.2:
                outlook = "긍정적"
            elif sentiment_score < -0.2:
                outlook = "부정적"
            else:
                outlook = "중립적"
        
        return {
            "sentiment_score": sentiment_score,
            "outlook": outlook,
            "confidence": min(0.7, (positive_count + negative_count) / 10),
            "key_factors": [f"{sector} 관련 뉴스 동향"],
            "summary": f"{sector} 섹터는 {outlook} 전망을 보이고 있습니다."
        }
    
    def _calculate_weight_adjustment(self, sentiment_score: float) -> float:
        """감정 점수를 비중 조정값으로 변환"""
        
        # -1.0 ~ +1.0 점수를 -15% ~ +15% 조정값으로 변환
        max_adjustment = 15
        adjustment = sentiment_score * max_adjustment
        
        # -15% ~ +15% 범위로 제한
        return max(-15, min(15, adjustment))
    
    def _remove_duplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 뉴스 제거"""
        
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '').strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news
    
    def _get_neutral_outlook(self, sector: str) -> Dict[str, Any]:
        """중립적 전망 반환 (뉴스 수집 실패 시)"""
        
        return {
            "sector": sector,
            "analysis_time": datetime.now(timezone.utc).isoformat(),
            "news_count": 0,
            "sentiment_score": 0.0,
            "outlook": "중립적",
            "key_factors": ["충분한 뉴스 데이터 없음"],
            "confidence": 0.3,
            "summary": f"{sector} 섹터의 최신 전망 데이터가 부족합니다.",
            "weight_adjustment": 0.0
        }
    
    async def analyze_multiple_sectors(
        self, 
        sectors: List[str], 
        time_range: str = "week"
    ) -> Dict[str, Dict[str, Any]]:
        """여러 섹터 동시 분석"""
        
        print(f"📊 {len(sectors)}개 섹터 전망 분석 시작...")
        
        # 동시 분석 (부하 방지를 위해 3개씩 묶어서 처리)
        results = {}
        
        for i in range(0, len(sectors), 3):
            batch_sectors = sectors[i:i+3]
            
            # 배치별 동시 실행
            tasks = [
                self.analyze_sector_outlook(sector, time_range) 
                for sector in batch_sectors
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for sector, result in zip(batch_sectors, batch_results):
                if isinstance(result, Exception):
                    print(f"❌ {sector} 분석 실패: {result}")
                    results[sector] = self._get_neutral_outlook(sector)
                else:
                    results[sector] = result
            
            # 배치 간 딜레이
            if i + 3 < len(sectors):
                await asyncio.sleep(2)
        
        print(f"✅ 섹터 분석 완료: {len(results)}개")
        return results


# 전역 인스턴스
sector_analysis_service = SectorAnalysisService()
