"""뉴스 + 재무제표 종합 분석 서비스"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.services.portfolio.sector_analysis_service import sector_analysis_service
from app.services.portfolio.financial_data_service import financial_data_service
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class ComprehensiveAnalysisService:
    """뉴스 분석 + 재무제표 분석 종합 서비스"""
    
    def __init__(self):
        self.sector_analyzer = sector_analysis_service
        self.financial_analyzer = financial_data_service
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.3,
                google_api_key=settings.google_api_key
            )
        return None
    
    async def comprehensive_stock_analysis(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        sector_outlook: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """개별 종목 종합 분석 (뉴스 + 재무제표)"""
        
        stock_code = stock.get('code', '')
        stock_name = stock.get('name', '')
        
        print(f"🔍 {stock_name} 종합 분석 시작...")
        
        try:
            # 1. 재무제표 분석 (동시 실행을 위해 태스크 생성)
            financial_task = self.financial_analyzer.get_financial_analysis(
                stock_code, 
                stock_name, 
                investment_profile
            )
            
            # 2. 섹터 전망이 없으면 개별 분석
            if not sector_outlook:
                sector_task = self.sector_analyzer.analyze_sector_outlook(sector)
                sector_outlook, financial_analysis = await asyncio.gather(
                    sector_task, financial_task
                )
            else:
                financial_analysis = await financial_task
            
            # 3. 종합 분석 실행
            comprehensive_result = await self._synthesize_analysis(
                stock=stock,
                sector=sector,
                investment_profile=investment_profile,
                financial_analysis=financial_analysis,
                sector_outlook=sector_outlook
            )
            
            return comprehensive_result
            
        except Exception as e:
            print(f"❌ {stock_name} 종합 분석 실패: {e}")
            return self._get_fallback_analysis(stock, sector, investment_profile)
    
    async def _synthesize_analysis(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        financial_analysis: Dict[str, Any],
        sector_outlook: Dict[str, Any]
    ) -> Dict[str, Any]:
        """뉴스 + 재무제표 종합 분석"""
        
        if not self.llm:
            return self._fallback_synthesis(
                stock, sector, investment_profile, financial_analysis, sector_outlook
            )
        
        stock_name = stock.get('name', '')
        
        # 분석 데이터 정리
        financial_summary = financial_analysis.get('analysis_summary', '')
        financial_score = financial_analysis.get('financial_score', 50)
        key_metrics = financial_analysis.get('key_metrics', {})
        
        sector_summary = sector_outlook.get('summary', '')
        market_impact = sector_outlook.get('market_impact', '')
        sentiment_score = sector_outlook.get('sentiment_score', 0)
        
        # 종합 분석 프롬프트  
        prompt = f"""당신은 금융 전문가입니다. {stock_name}({sector} 섹터)에 대한 종합 투자 분석을 수행해주세요.

=== 재무제표 분석 결과 ===
재무 점수: {financial_score}/100
핵심 지표: {key_metrics}
재무 요약: {financial_summary}

=== 섹터 뉴스 분석 결과 ===
시장 전망: {sector_summary}
예상 파장: {market_impact}
감정 점수: {sentiment_score} (-1~+1)

=== 투자자 정보 ===
투자 성향: {investment_profile}

=== 종합 분석 요청 ===
위 정보를 종합하여 다음 형식으로 분석해주세요:

comprehensive_score: [0-100점 (종합 투자 매력도)]
investment_rating: [매우추천/추천/보통/주의/비추천 중 하나]
risk_level: [저위험/중위험/고위험 중 하나]
expected_return: [저수익/중수익/고수익 중 하나]
time_horizon: [단기/중기/장기 중 추천 투자 기간]
key_drivers: ["핵심 투자 동력1", "핵심 투자 동력2", "핵심 투자 동력3"]
risk_factors: ["리스크1", "리스크2"]
financial_highlights: ["재무 강점1", "재무 강점2"]
market_opportunities: ["시장 기회1", "시장 기회2"]
investment_thesis: [핵심 투자 논리 2-3문장]

=== 분석 가이드라인 ===
1. 재무제표 분석(40%)과 시장 뉴스 분석(60%) 가중 평균
2. {investment_profile} 투자자에게 적합한 관점으로 평가
3. 단기 뉴스 이슈와 중장기 재무 펀더멘털 균형 고려
4. 구체적이고 실용적인 투자 근거 제시

응답은 반드시 위 형식을 정확히 따라주세요."""

        try:
            response = await self.llm.ainvoke(prompt)
            return self._parse_comprehensive_analysis(
                response.content, 
                stock, 
                sector,
                investment_profile,
                financial_analysis,
                sector_outlook
            )
        except Exception as e:
            print(f"⚠️ 종합 분석 LLM 실패: {e}")
            return self._fallback_synthesis(
                stock, sector, investment_profile, financial_analysis, sector_outlook
            )
    
    def _parse_comprehensive_analysis(
        self,
        response_text: str,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        financial_analysis: Dict[str, Any],
        sector_outlook: Dict[str, Any]
    ) -> Dict[str, Any]:
        """종합 분석 결과 파싱"""
        
        result = {
            "stock_code": stock.get('code', ''),
            "stock_name": stock.get('name', ''),
            "sector": sector,
            "investment_profile": investment_profile,
            "comprehensive_score": 50,
            "investment_rating": "보통",
            "risk_level": "중위험",
            "expected_return": "중수익",
            "time_horizon": "중기",
            "key_drivers": [],
            "risk_factors": [],
            "financial_highlights": [],
            "market_opportunities": [],
            "investment_thesis": "",
            "analysis_components": {
                "financial_score": financial_analysis.get('financial_score', 50),
                "sector_sentiment": sector_outlook.get('sentiment_score', 0),
                "news_confidence": sector_outlook.get('confidence', 0.5)
            },
            "analysis_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        try:
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'comprehensive_score' in key:
                        try:
                            score = float(value)
                            result["comprehensive_score"] = max(0, min(100, score))
                        except:
                            pass
                    elif 'investment_rating' in key:
                        if value in ["매우추천", "추천", "보통", "주의", "비추천"]:
                            result["investment_rating"] = value
                    elif 'risk_level' in key:
                        if value in ["저위험", "중위험", "고위험"]:
                            result["risk_level"] = value
                    elif 'expected_return' in key:
                        if value in ["저수익", "중수익", "고수익"]:
                            result["expected_return"] = value
                    elif 'time_horizon' in key:
                        if value in ["단기", "중기", "장기"]:
                            result["time_horizon"] = value
                    elif 'investment_thesis' in key:
                        result["investment_thesis"] = value
                    elif any(factor_key in key for factor_key in [
                        'key_drivers', 'risk_factors', 'financial_highlights', 'market_opportunities'
                    ]):
                        factors = self._parse_array_field(value)
                        if 'key_drivers' in key:
                            result["key_drivers"] = factors[:3]
                        elif 'risk_factors' in key:
                            result["risk_factors"] = factors[:2]
                        elif 'financial_highlights' in key:
                            result["financial_highlights"] = factors[:2]
                        elif 'market_opportunities' in key:
                            result["market_opportunities"] = factors[:2]
            
        except Exception as e:
            print(f"⚠️ 종합 분석 파싱 실패: {e}")
        
        return result
    
    def _parse_array_field(self, value: str) -> List[str]:
        """배열 형태 필드 파싱"""
        try:
            if '[' in value and ']' in value:
                clean_value = value.replace('[', '').replace(']', '').replace('"', '')
                items = [item.strip() for item in clean_value.split(',')]
                return [item for item in items if item]
            else:
                return [value] if value else []
        except:
            return [value] if value else []
    
    def _fallback_synthesis(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        financial_analysis: Dict[str, Any],
        sector_outlook: Dict[str, Any]
    ) -> Dict[str, Any]:
        """폴백 종합 분석 (규칙 기반)"""
        
        # 간단한 점수 계산
        financial_score = financial_analysis.get('financial_score', 50)
        sector_sentiment = sector_outlook.get('sentiment_score', 0)
        
        # 가중 평균 (재무 40%, 뉴스 60%)
        comprehensive_score = (financial_score * 0.4) + ((sector_sentiment + 1) * 50 * 0.6)
        comprehensive_score = max(0, min(100, comprehensive_score))
        
        # 등급 결정
        if comprehensive_score >= 80:
            rating = "매우추천"
        elif comprehensive_score >= 65:
            rating = "추천"
        elif comprehensive_score >= 35:
            rating = "보통"
        elif comprehensive_score >= 20:
            rating = "주의"
        else:
            rating = "비추천"
        
        return {
            "stock_code": stock.get('code', ''),
            "stock_name": stock.get('name', ''),
            "sector": sector,
            "investment_profile": investment_profile,
            "comprehensive_score": int(comprehensive_score),
            "investment_rating": rating,
            "risk_level": "중위험",
            "expected_return": "중수익",
            "time_horizon": "중기",
            "key_drivers": ["재무 안정성", "섹터 전망"],
            "risk_factors": ["시장 변동성"],
            "financial_highlights": financial_analysis.get('strengths', ["재무 데이터 분석 결과"]),
            "market_opportunities": [sector_outlook.get('summary', '섹터 전망 분석')],
            "investment_thesis": f"{stock.get('name', '')}는 재무적 기초({financial_score}점)와 시장 전망을 종합할 때 {rating} 수준의 투자처로 평가됩니다.",
            "analysis_components": {
                "financial_score": financial_score,
                "sector_sentiment": sector_sentiment,
                "news_confidence": sector_outlook.get('confidence', 0.5)
            },
            "analysis_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    
    def _get_fallback_analysis(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str
    ) -> Dict[str, Any]:
        """완전 폴백 분석 (오류 시)"""
        
        return {
            "stock_code": stock.get('code', ''),
            "stock_name": stock.get('name', ''),
            "sector": sector,
            "investment_profile": investment_profile,
            "comprehensive_score": 50,
            "investment_rating": "보통",
            "risk_level": "중위험",
            "expected_return": "중수익",
            "time_horizon": "중기",
            "key_drivers": ["추가 분석 필요"],
            "risk_factors": ["데이터 부족"],
            "financial_highlights": [],
            "market_opportunities": [],
            "investment_thesis": f"{stock.get('name', '')}에 대한 상세 분석을 위해 더 많은 데이터가 필요합니다.",
            "analysis_components": {
                "financial_score": 50,
                "sector_sentiment": 0,
                "news_confidence": 0.3
            },
            "analysis_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    
    async def analyze_multiple_stocks(
        self,
        stocks: List[Dict[str, Any]],
        sectors: List[str],
        investment_profile: str,
        sector_outlooks: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """다중 종목 종합 분석"""
        
        print(f"🔍 {len(stocks)}개 종목 종합 분석 시작...")
        
        results = {}
        
        # 섹터 전망이 없으면 먼저 분석
        if not sector_outlooks:
            unique_sectors = list(set(sectors))
            sector_outlooks = await self.sector_analyzer.analyze_multiple_sectors(
                unique_sectors
            )
        
        # 배치별 처리
        batch_size = 2  # 종합 분석은 리소스가 많이 드므로 작은 배치
        
        for i in range(0, len(stocks), batch_size):
            batch_stocks = stocks[i:i+batch_size]
            batch_sectors = sectors[i:i+batch_size]
            
            # 배치 내 동시 실행
            tasks = []
            for stock, sector in zip(batch_stocks, batch_sectors):
                task = self.comprehensive_stock_analysis(
                    stock=stock,
                    sector=sector,
                    investment_profile=investment_profile,
                    sector_outlook=sector_outlooks.get(sector, {})
                )
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for stock, result in zip(batch_stocks, batch_results):
                stock_code = stock.get('code', '')
                if isinstance(result, Exception):
                    print(f"❌ {stock.get('name', '')} 종합 분석 실패: {result}")
                    results[stock_code] = self._get_fallback_analysis(
                        stock, batch_sectors[batch_stocks.index(stock)], investment_profile
                    )
                else:
                    results[stock_code] = result
            
            # 배치 간 딜레이 (더 긴 대기)
            if i + batch_size < len(stocks):
                await asyncio.sleep(3)
        
        print(f"✅ 종합 분석 완료: {len(results)}개 종목")
        return results


# 전역 인스턴스
comprehensive_analysis_service = ComprehensiveAnalysisService()
