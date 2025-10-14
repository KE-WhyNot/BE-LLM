"""뉴스 + 재무제표 종합 분석 서비스"""

import asyncio
import time
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
                model="gemini-2.0-flash",
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
        analysis_start = time.time()
        
        print(f"🔍 {stock_name} 종합 분석 시작...")
        
        try:
            # 1. 재무제표 분석 (동시 실행을 위해 태스크 생성)
            financial_start = time.time()
            financial_task = self.financial_analyzer.get_financial_analysis(
                stock_code, 
                stock_name, 
                investment_profile
            )
            
            # 2. 섹터 전망이 없으면 개별 분석
            if not sector_outlook:
                sector_start = time.time()
                sector_task = self.sector_analyzer.analyze_sector_outlook(sector)
                sector_outlook, financial_analysis = await asyncio.gather(
                    sector_task, financial_task
                )
                sector_time = time.time() - sector_start
                print(f"  📈 섹터 분석: {sector_time:.3f}초")
            else:
                financial_analysis = await financial_task
            
            financial_time = time.time() - financial_start
            print(f"  💰 재무 분석: {financial_time:.3f}초")
            
            # 3. 종합 분석 실행
            synthesis_start = time.time()
            comprehensive_result = await self._synthesize_analysis(
                stock=stock,
                sector=sector,
                investment_profile=investment_profile,
                financial_analysis=financial_analysis,
                sector_outlook=sector_outlook
            )
            synthesis_time = time.time() - synthesis_start
            print(f"  🧠 종합 분석: {synthesis_time:.3f}초")
            
            total_time = time.time() - analysis_start
            print(f"✅ {stock_name} 분석 완료: {total_time:.3f}초")
            
            return comprehensive_result
            
        except Exception as e:
            total_time = time.time() - analysis_start
            print(f"❌ {stock_name} 종합 분석 실패 ({total_time:.3f}초): {e}")
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
            "analysis_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            # 🔥 실제 데이터 원본 (LLM 동적 생성용) - 대폭 강화
            "raw_financial_data": self._extract_detailed_financial_data(financial_analysis),
            "raw_news_data": self._extract_detailed_news_data(sector_outlook)
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
                # 빈 값이나 의미없는 값들 필터링
                filtered_items = []
                for item in items:
                    clean_item = item.strip()
                    if (clean_item and 
                        clean_item not in ['', ' ', '값', '데이터', 'null', 'None', '추가 분석 필요', '[', ']', '[]'] and
                        len(clean_item) > 1 and
                        not clean_item.startswith('[') and
                        not clean_item.endswith(']')):
                        filtered_items.append(clean_item)
                return filtered_items
            else:
                # 단일 값도 의미있는 내용인지 확인
                if value and value not in ['', ' ', '값', '데이터', 'null', 'None', '추가 분석 필요']:
                    return [value]
                return []
        except:
            return []
    
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
        
        multi_analysis_start = time.time()
        print(f"🔍 {len(stocks)}개 종목 종합 분석 시작...")
        
        results = {}
        
        # 섹터 전망이 없으면 먼저 분석
        if not sector_outlooks:
            sector_analysis_start = time.time()
            unique_sectors = list(set(sectors))
            sector_outlooks = await self.sector_analyzer.analyze_multiple_sectors(
                unique_sectors
            )
            sector_analysis_time = time.time() - sector_analysis_start
            print(f"🏢 다중 섹터 분석: {sector_analysis_time:.3f}초 ({len(unique_sectors)}개 섹터)")
        
        # 배치별 처리
        batch_size = 2  # 종합 분석은 리소스가 많이 드므로 작은 배치
        batch_count = (len(stocks) + batch_size - 1) // batch_size
        
        print(f"📦 배치 처리 시작: {batch_count}개 배치 (배치당 {batch_size}개 종목)")
        
        for i in range(0, len(stocks), batch_size):
            batch_start = time.time()
            batch_stocks = stocks[i:i+batch_size]
            batch_sectors = sectors[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            print(f"  🔄 배치 {batch_num}/{batch_count} 처리 중... ({len(batch_stocks)}개 종목)")
            
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
            
            batch_time = time.time() - batch_start
            print(f"  ✅ 배치 {batch_num} 완료: {batch_time:.3f}초")
            
            # 배치 간 딜레이 (더 긴 대기)
            if i + batch_size < len(stocks):
                print(f"  ⏳ 배치 간 대기: 3초...")
                await asyncio.sleep(3)
        
        total_time = time.time() - multi_analysis_start
        avg_time_per_stock = total_time / len(stocks) if stocks else 0
        
        print(f"✅ 종합 분석 완료: {len(results)}개 종목, 총 {total_time:.3f}초")
        print(f"📊 종목당 평균 분석 시간: {avg_time_per_stock:.3f}초")
        
        return results
    
    def _extract_detailed_financial_data(self, financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """재무 분석에서 더 구체적인 데이터 추출"""
        
        key_metrics = financial_analysis.get('key_metrics', {})
        analysis_summary = financial_analysis.get('analysis_summary', '')
        
        # 구체적 재무 지표 추출 및 정제
        extracted_metrics = {}
        
        # ROE 추출 (여러 표현 방식 지원)
        roe_value = self._extract_metric_value(key_metrics, ['ROE', 'roe', '자기자본이익률', '자기자본수익률'])
        if roe_value:
            extracted_metrics['roe'] = roe_value
        
        # 매출 성장률 추출
        revenue_growth = self._extract_metric_value(key_metrics, ['매출성장률', '매출증가율', 'revenue_growth', '성장률'])
        if revenue_growth:
            extracted_metrics['revenue_growth'] = revenue_growth
        
        # 영업이익률 추출
        profit_margin = self._extract_metric_value(key_metrics, ['영업이익률', '영업마진', 'operating_margin', 'profit_margin'])
        if profit_margin:
            extracted_metrics['profit_margin'] = profit_margin
        
        # 부채비율 추출
        debt_ratio = self._extract_metric_value(key_metrics, ['부채비율', 'debt_ratio', '부채율'])
        if debt_ratio:
            extracted_metrics['debt_ratio'] = debt_ratio
        
        # 유동비율 추출
        current_ratio = self._extract_metric_value(key_metrics, ['유동비율', 'current_ratio', '유동성비율'])
        if current_ratio:
            extracted_metrics['current_ratio'] = current_ratio
        
        # PER, PBR 추출
        per = self._extract_metric_value(key_metrics, ['PER', 'per', '주가수익비율'])
        if per:
            extracted_metrics['per'] = per
            
        pbr = self._extract_metric_value(key_metrics, ['PBR', 'pbr', '주가순자산비율'])
        if pbr:
            extracted_metrics['pbr'] = pbr
        
        # 재무 건전성 평가 (분석 요약에서 추출)
        financial_health = self._extract_financial_health_assessment(analysis_summary, financial_analysis)
        
        return {
            "key_metrics": extracted_metrics,
            "financial_score": financial_analysis.get('financial_score', 50),
            "strengths": financial_analysis.get('strengths', []),
            "weaknesses": financial_analysis.get('weaknesses', []),
            "analysis_summary": analysis_summary,
            "financial_health": financial_health,
            "revenue_growth": extracted_metrics.get('revenue_growth', ''),
            "profit_margin": extracted_metrics.get('profit_margin', ''),
            "debt_ratio": extracted_metrics.get('debt_ratio', ''),
            "roe": extracted_metrics.get('roe', ''),
            "current_ratio": extracted_metrics.get('current_ratio', ''),
            "per": extracted_metrics.get('per', ''),
            "pbr": extracted_metrics.get('pbr', '')
        }
    
    def _extract_detailed_news_data(self, sector_outlook: Dict[str, Any]) -> Dict[str, Any]:
        """섹터 뉴스에서 더 구체적인 데이터 추출"""
        
        # 기존 데이터
        sector_summary = sector_outlook.get('summary', '')
        market_impact = sector_outlook.get('market_impact', '')
        key_factors = sector_outlook.get('key_factors', [])
        
        # 🔥 뉴스 헤드라인 시뮬레이션 (실제 구현 시 뉴스 서비스에서 가져와야 함)
        headlines = self._extract_or_simulate_headlines(sector_outlook, sector_summary, key_factors)
        
        # 감정 분석 세부 정보
        sentiment_analysis = {
            "overall_sentiment": sector_outlook.get('sentiment_score', 0),
            "positive_signals": self._extract_positive_signals(sector_summary, key_factors),
            "negative_signals": self._extract_negative_signals(sector_summary, key_factors),
            "neutral_signals": self._extract_neutral_signals(sector_summary, key_factors)
        }
        
        # 시장 전망 세부화
        market_drivers = self._extract_market_drivers(sector_summary, key_factors, market_impact)
        
        return {
            "headlines": headlines,  # 🔥 실제 헤드라인
            "sector_summary": sector_summary,
            "market_impact": market_impact,
            "sentiment_score": sector_outlook.get('sentiment_score', 0),
            "key_factors": key_factors,
            "news_count": sector_outlook.get('news_count', 0),
            "sentiment_analysis": sentiment_analysis,
            "sector_outlook": sector_summary,
            "market_drivers": market_drivers
        }
    
    def _extract_metric_value(self, metrics: Dict[str, Any], possible_keys: List[str]) -> str:
        """다양한 키에서 지표 값 추출"""
        for key in possible_keys:
            for metric_key, value in metrics.items():
                if key.lower() in metric_key.lower():
                    if value and str(value).strip() not in ['', 'null', 'None', 'N/A']:
                        # 단위 포함해서 반환
                        return str(value)
        return ''
    
    def _extract_financial_health_assessment(self, analysis_summary: str, financial_data: Dict[str, Any]) -> str:
        """재무 건전성 평가 추출"""
        
        financial_score = financial_data.get('financial_score', 50)
        
        # 점수 기반 기본 평가
        if financial_score >= 80:
            base_health = "매우 우수"
        elif financial_score >= 70:
            base_health = "우수"
        elif financial_score >= 60:
            base_health = "양호"
        elif financial_score >= 40:
            base_health = "보통"
        else:
            base_health = "주의 필요"
        
        # 분석 요약에서 구체적 평가 추출
        health_keywords = {
            "우수": ["우수", "양호", "건전", "안정", "탄탄"],
            "주의": ["우려", "부담", "위험", "악화", "취약"],
            "개선": ["개선", "회복", "향상", "성장"]
        }
        
        detailed_assessment = []
        for category, keywords in health_keywords.items():
            for keyword in keywords:
                if keyword in analysis_summary:
                    detailed_assessment.append(f"{category}: {keyword} 상황")
                    break
        
        if detailed_assessment:
            return f"{base_health} ({', '.join(detailed_assessment[:2])})"
        else:
            return base_health
    
    def _extract_or_simulate_headlines(self, sector_outlook: Dict[str, Any], sector_summary: str, key_factors: List[str]) -> List[str]:
        """뉴스 헤드라인 추출 또는 시뮬레이션"""
        
        # TODO: 실제 구현에서는 뉴스 서비스에서 실제 헤드라인을 가져와야 함
        # 현재는 분석 결과를 바탕으로 시뮬레이션
        
        headlines = []
        sector = sector_outlook.get('sector', '')
        sentiment_score = sector_outlook.get('sentiment_score', 0)
        
        # 핵심 요인 기반 헤드라인 생성
        if key_factors:
            for factor in key_factors[:3]:
                if sentiment_score > 0.2:
                    headline = f"[{sector}] {factor}로 업계 전망 개선세"
                elif sentiment_score < -0.2:
                    headline = f"[{sector}] {factor} 우려에 업계 주목"
                else:
                    headline = f"[{sector}] {factor} 관련 업계 동향 주시"
                headlines.append(headline)
        
        # 섹터 요약 기반 헤드라인 추가
        if sector_summary and len(headlines) < 3:
            summary_words = sector_summary.split()[:3]
            if summary_words:
                keyword = ' '.join(summary_words)
                headline = f"[시장분석] {sector} {keyword} 전망"
                headlines.append(headline)
        
        # 최소 1개는 보장
        if not headlines:
            headlines = [f"[{sector}] 시장 동향 및 투자 전망"]
        
        return headlines[:3]  # 최대 3개
    
    def _extract_positive_signals(self, summary: str, factors: List[str]) -> List[str]:
        """긍정적 신호 추출"""
        positive_words = ["성장", "증가", "상승", "개선", "회복", "확대", "호조", "기대"]
        signals = []
        
        text = summary + ' ' + ' '.join(factors)
        for word in positive_words:
            if word in text:
                signals.append(f"{word} 신호")
        
        return signals[:3]
    
    def _extract_negative_signals(self, summary: str, factors: List[str]) -> List[str]:
        """부정적 신호 추출"""
        negative_words = ["하락", "감소", "우려", "위험", "악화", "축소", "둔화", "부진"]
        signals = []
        
        text = summary + ' ' + ' '.join(factors)
        for word in negative_words:
            if word in text:
                signals.append(f"{word} 우려")
        
        return signals[:3]
    
    def _extract_neutral_signals(self, summary: str, factors: List[str]) -> List[str]:
        """중립적 신호 추출"""
        neutral_words = ["안정", "유지", "보합", "관망", "모니터링", "지켜봄"]
        signals = []
        
        text = summary + ' ' + ' '.join(factors)
        for word in neutral_words:
            if word in text:
                signals.append(f"{word} 상황")
        
        return signals[:2]
    
    def _extract_market_drivers(self, summary: str, factors: List[str], market_impact: str) -> List[str]:
        """시장 동력 요인 추출"""
        
        drivers = []
        
        # 핵심 요인에서 추출
        if factors:
            drivers.extend(factors[:2])
        
        # 시장 파장에서 추출
        if market_impact:
            # 간단한 키워드 추출
            driver_keywords = ["정책", "기술", "수요", "공급", "투자", "규제", "금리", "환율"]
            for keyword in driver_keywords:
                if keyword in market_impact:
                    drivers.append(f"{keyword} 변화")
        
        # 요약에서 추가 추출
        if summary and len(drivers) < 3:
            summary_drivers = self._extract_drivers_from_summary(summary)
            drivers.extend(summary_drivers)
        
        return list(set(drivers))[:3]  # 중복 제거 후 최대 3개
    
    def _extract_drivers_from_summary(self, summary: str) -> List[str]:
        """요약에서 동력 요인 추출"""
        
        driver_patterns = [
            "실적", "수익", "매출", "성장", "전망", "계획", "투자", "개발", 
            "출시", "확장", "진출", "협력", "인수", "합병"
        ]
        
        drivers = []
        for pattern in driver_patterns:
            if pattern in summary:
                drivers.append(f"{pattern} 동향")
                if len(drivers) >= 2:  # 최대 2개만
                    break
        
        return drivers


# 전역 인스턴스
comprehensive_analysis_service = ComprehensiveAnalysisService()
