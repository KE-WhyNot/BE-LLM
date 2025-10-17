"""고도화된 포트폴리오 추천 서비스 - 뉴스 분석 + 기업 규모 선호도 반영"""

import time
import unicodedata
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.utils.portfolio_stock_loader import portfolio_stock_loader
from app.services.portfolio.sector_analysis_service import sector_analysis_service
from app.services.portfolio.comprehensive_analysis_service import comprehensive_analysis_service
from app.schemas.portfolio_schema import (
    InvestmentProfileRequest,
    StockRecommendation,
    PortfolioRecommendationResult
)
from app.services.portfolio.allocation_utils import now_utc_z, normalize_integer_allocations
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class EnhancedPortfolioService:
    """뉴스 분석과 기업 규모 선호도를 반영한 고도화된 포트폴리오 추천 서비스"""
    
    def __init__(self):
        # 투자 성향별 자산 배분 규칙
        self.asset_allocation_rules = {
            "안정형": {"예적금": 80, "주식": 20},
            "안정추구형": {"예적금": 60, "주식": 40},
            "위험중립형": {"예적금": 50, "주식": 50},
            "적극투자형": {"예적금": 30, "주식": 70},
            "공격투자형": {"예적금": 20, "주식": 80}
        }
        
        # 투자 성향별 기업 규모 선호도
        self.company_size_preferences = {
            "안정형": {"대기업": 0.9, "중견기업": 0.6, "중소기업": 0.3},
            "안정추구형": {"대기업": 0.8, "중견기업": 0.7, "중소기업": 0.4},
            "위험중립형": {"대기업": 0.7, "중견기업": 0.7, "중소기업": 0.6},
            "적극투자형": {"대기업": 0.6, "중견기업": 0.8, "중소기업": 0.7},
            "공격투자형": {"대기업": 0.5, "중견기업": 0.8, "중소기업": 0.9}
        }
        
        self.stock_loader = portfolio_stock_loader
        self.sector_analyzer = sector_analysis_service
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """LLM 초기화 (동적 추천 이유 생성용)"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.4,  # 더 창의적인 추천 이유를 위해 온도 상승
                google_api_key=settings.google_api_key
            )
        return None
    
    async def recommend_enhanced_portfolio(
        self, 
        profile: InvestmentProfileRequest,
        use_news_analysis: bool = True,
        use_financial_analysis: bool = True
    ) -> PortfolioRecommendationResult:
        """최고도화된 포트폴리오 추천 (뉴스 + 재무제표 종합 분석)"""
        
        total_start_time = time.time()
        
        print(f"🚀 최고도화된 포트폴리오 추천 시작 (사용자: {profile.userId})")
        print(f"📊 분석 범위: 뉴스({use_news_analysis}) + 재무제표({use_financial_analysis})")
        
        # 1. 기본 자산 배분 결정
        step1_start = time.time()
        allocation = self.asset_allocation_rules.get(
            profile.investmentProfile,
            self.asset_allocation_rules["위험중립형"]
        )
        base_savings_pct = allocation["예적금"]
        base_stocks_pct = allocation["주식"]
        step1_time = time.time() - step1_start
        print(f"⏱️ [단계 1] 기본 자산 배분 결정: {step1_time:.3f}초")
        
        # 2. 관심 섹터 기본 설정
        step2_start = time.time()
        interested_sectors = profile.interestedSectors
        if not interested_sectors:
            print("⚠️ 사용자 관심 섹터 없음, 투자 성향 기반 기본 섹터 사용")
            interested_sectors = self._get_default_sectors(profile.investmentProfile)
        step2_time = time.time() - step2_start
        print(f"⏱️ [단계 2] 관심 섹터 설정: {step2_time:.3f}초")
        
        # 3. 기업 규모 선호도 결정
        step3_start = time.time()
        company_size_preference = self.company_size_preferences.get(
            profile.investmentProfile,
            self.company_size_preferences["위험중립형"]
        )
        
        # 추가 조정: 금융 지식도와 손실 허용도 반영
        company_size_preference = self._adjust_size_preference_by_knowledge(
            company_size_preference,
            profile.financialKnowledge,
            profile.lossTolerance
        )
        step3_time = time.time() - step3_start
        print(f"⏱️ [단계 3] 기업 규모 선호도 결정: {step3_time:.3f}초")
        
        # 4. 종목 선정 (종합 분석 기반) - 가장 시간이 많이 걸리는 단계
        step4_start = time.time()
        # 종목 배분은 주식 내에서 100% 기준으로 정규화 (원그래프 용)
        recommended_stocks = await self._select_comprehensive_stocks(
            interested_sectors,
            profile.investmentProfile,
            company_size_preference,
            100,
            use_news_analysis,
            use_financial_analysis
        )
        step4_time = time.time() - step4_start
        print(f"⏱️ [단계 4] 종목 선정 (종합 분석): {step4_time:.3f}초")
        
        # 5. 최종 예적금 비율 계산 (주식 원그래프와 독립적으로 규칙 기반 유지)
        step5_start = time.time()
        # 주식 배분은 항상 100으로 정규화되어 반환되며, 예적금 비율은 규칙값 사용
        final_savings_pct = base_savings_pct
        step5_time = time.time() - step5_start
        print(f"⏱️ [단계 5] 최종 비율 계산: {step5_time:.3f}초")
        
        # 6. 결과 생성
        step6_start = time.time()
        now = now_utc_z()
        
        # 디버깅: recommended_stocks 상태 확인
        print(f"🔍 [디버깅] recommended_stocks 타입: {type(recommended_stocks)}")
        print(f"🔍 [디버깅] recommended_stocks 개수: {len(recommended_stocks) if recommended_stocks else 0}")
        if recommended_stocks:
            print(f"🔍 [디버깅] 첫 번째 종목: {recommended_stocks[0].stockName if recommended_stocks[0] else 'None'}")
        
        result = PortfolioRecommendationResult(
            portfolioId=profile.profileId,
            userId=profile.userId,
            recommendedStocks=recommended_stocks,
            allocationSavings=final_savings_pct,
            createdAt=now,
            updatedAt=now
        )
        
        # 디버깅: 결과 객체 상태 확인
        print(f"🔍 [디버깅] result.recommendedStocks 개수: {len(result.recommendedStocks) if result.recommendedStocks else 0}")
        print(f"🔍 [디버깅] result.allocationSavings: {result.allocationSavings}")
        
        step6_time = time.time() - step6_start
        print(f"⏱️ [단계 6] 결과 생성: {step6_time:.3f}초")
        
        total_time = time.time() - total_start_time
        
        analysis_type = []
        if use_news_analysis: analysis_type.append("뉴스")
        if use_financial_analysis: analysis_type.append("재무제표")
        analysis_desc = " + ".join(analysis_type) if analysis_type else "기본"
        
        print(f"✅ 최고도화된 포트폴리오 추천 완료 ({analysis_desc}): {len(recommended_stocks)}개 종목, 예적금 {final_savings_pct}%")
        print(f"📊 총 소요 시간: {total_time:.3f}초")
        print(f"📈 단계 4(종목 선정)가 전체의 {(step4_time/total_time)*100:.1f}% 차지")
        
        return result
    
    def _calculate_sector_allocations(
        self,
        sectors: List[str],
        base_stock_pct: int,
        sector_outlooks: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """섹터별 비중 배분 (뉴스 전망 반영)"""
        
        # 기본 균등 배분
        base_allocation = base_stock_pct // len(sectors)
        remainder = base_stock_pct % len(sectors)
        
        allocations = {}
        adjustments = {}
        
        # 각 섹터의 뉴스 기반 조정값 계산
        for sector in sectors:
            allocations[sector] = base_allocation
            
            outlook = sector_outlooks.get(sector, {})
            weight_adjustment = outlook.get('weight_adjustment', 0)
            confidence = outlook.get('confidence', 0.5)
            
            # 신뢰도가 높을수록 조정값을 더 적극 반영
            final_adjustment = weight_adjustment * confidence
            adjustments[sector] = final_adjustment
        
        # 조정값 적용
        for sector in sectors:
            adjustment = adjustments[sector]
            allocations[sector] = max(1, allocations[sector] + int(adjustment))
        
        # 나머지 배분 (첫 번째 섹터에 추가)
        if remainder > 0:
            first_sector = sectors[0]
            allocations[first_sector] += remainder
        
        # 총합이 100%를 넘지 않도록 조정
        total = sum(allocations.values())
        if total > base_stock_pct:
            # 초과분을 비례적으로 차감
            excess = total - base_stock_pct
            for sector in sectors:
                reduction = int((allocations[sector] / total) * excess)
                allocations[sector] = max(1, allocations[sector] - reduction)
        
        # 최종 검증
        final_total = sum(allocations.values())
        if final_total != base_stock_pct:
            # 차이를 가장 큰 섹터에서 조정
            max_sector = max(allocations.keys(), key=lambda k: allocations[k])
            allocations[max_sector] += (base_stock_pct - final_total)
            allocations[max_sector] = max(1, allocations[max_sector])
        
        return allocations
    
    def _adjust_size_preference_by_knowledge(
        self,
        base_preference: Dict[str, float],
        financial_knowledge: str,
        loss_tolerance: str
    ) -> Dict[str, float]:
        """금융 지식도와 손실 허용도에 따른 기업 규모 선호도 조정"""
        
        adjusted_preference = base_preference.copy()
        
        # 금융 지식도에 따른 조정
        knowledge_adjustments = {
            "매우 낮음": {"대기업": 0.1, "중견기업": -0.05, "중소기업": -0.1},
            "낮음": {"대기업": 0.05, "중견기업": 0.0, "중소기업": -0.05},
            "보통": {"대기업": 0.0, "중견기업": 0.0, "중소기업": 0.0},
            "높음": {"대기업": -0.05, "중견기업": 0.05, "중소기업": 0.05},
            "매우 높음": {"대기업": -0.1, "중견기업": 0.05, "중소기업": 0.1}
        }
        
        # 손실 허용도에 따른 조정
        tolerance_adjustments = {
            "10": {"대기업": 0.1, "중견기업": -0.05, "중소기업": -0.1},
            "30": {"대기업": 0.05, "중견기업": 0.0, "중소기업": -0.05},
            "50": {"대기업": 0.0, "중견기업": 0.0, "중소기업": 0.0},
            "70": {"대기업": -0.05, "중견기업": 0.05, "중소기업": 0.05},
            "100": {"대기업": -0.1, "중견기업": 0.05, "중소기업": 0.1}
        }
        
        # 조정값 적용
        knowledge_adj = knowledge_adjustments.get(financial_knowledge, {})
        tolerance_adj = tolerance_adjustments.get(loss_tolerance, {})
        
        for size in adjusted_preference:
            adj_value = knowledge_adj.get(size, 0) + tolerance_adj.get(size, 0)
            adjusted_preference[size] = max(0.1, min(1.0, adjusted_preference[size] + adj_value))
        
        return adjusted_preference
    
    async def _select_comprehensive_stocks(
        self,
        interested_sectors: List[str],
        investment_profile: str,
        company_size_preference: Dict[str, float],
        total_stock_pct: int,
        use_news_analysis: bool,
        use_financial_analysis: bool
    ) -> List[StockRecommendation]:
        """최고도화된 종목 선정 (뉴스 + 재무제표 종합 분석)"""
        
        recommendations = []
        
        # 1. 각 섹터에서 후보 종목 선정
        all_candidate_stocks = []
        for sector in interested_sectors:
            sector_stocks = self.stock_loader.get_best_stocks_for_profile(
                sector=sector,
                investment_profile=investment_profile,
                limit=3,  # 섹터당 최대 3개 후보
                company_size_preference=company_size_preference
            )
            
            for stock in sector_stocks:
                all_candidate_stocks.append({
                    'stock': stock,
                    'sector': sector
                })
        
        if not all_candidate_stocks:
            return []
        
        # 2. 종합 분석 수행 (뉴스 + 재무제표)
        if use_news_analysis or use_financial_analysis:
            print(f"🔍 {len(all_candidate_stocks)}개 후보 종목 종합 분석 중...")
            
            # 종합 분석 실행
            stocks_for_analysis = [item['stock'] for item in all_candidate_stocks]
            sectors_for_analysis = [item['sector'] for item in all_candidate_stocks]
            
            try:
                comprehensive_results = await comprehensive_analysis_service.analyze_multiple_stocks(
                    stocks=stocks_for_analysis,
                    sectors=sectors_for_analysis,
                    investment_profile=investment_profile
                )
                
                # 종합 점수 기반 정렬
                scored_candidates = []
                for item in all_candidate_stocks:
                    stock_code = item['stock']['code']
                    analysis = comprehensive_results.get(stock_code, {})
                    comprehensive_score = analysis.get('comprehensive_score', 50)
                    
                    scored_candidates.append({
                        **item,
                        'analysis': analysis,
                        'comprehensive_score': comprehensive_score
                    })
                
                # 점수순 정렬
                scored_candidates.sort(key=lambda x: x['comprehensive_score'], reverse=True)
                
                # 상위 종목 선택 (최대 5개)
                selected_candidates = scored_candidates[:5]
                
            except Exception as e:
                print(f"⚠️ 종합 분석 실패, 기본 선정 방식 사용: {e}")
                selected_candidates = [
                    {**item, 'analysis': {}, 'comprehensive_score': 50} 
                    for item in all_candidate_stocks[:5]
                ]
        else:
            # 기본 방식: 단순 선정
            selected_candidates = [
                {**item, 'analysis': {}, 'comprehensive_score': 50} 
                for item in all_candidate_stocks[:5]
            ]
        
        # 3. 비중 배분 (종합 점수 기반, 정수 정규화)
        if selected_candidates:
            total_score = sum(item['comprehensive_score'] for item in selected_candidates)
            scores = [item['comprehensive_score'] for item in selected_candidates]
            # 점수가 모두 0인 경우 균등 분배
            allocations = normalize_integer_allocations(scores if total_score > 0 else [1]*len(scores), total_stock_pct, min_each=1)

            for (item, allocation_pct) in zip(selected_candidates, allocations):
                stock = item['stock']
                analysis = item['analysis']
                sector = item['sector']

                reason = await self._generate_comprehensive_reason(
                    stock=stock,
                    sector=sector,
                    investment_profile=investment_profile,
                    analysis=analysis,
                    use_news_analysis=use_news_analysis,
                    use_financial_analysis=use_financial_analysis
                )

                recommendation = StockRecommendation(
                    stockId=stock['code'],
                    stockName=stock['name'],
                    allocationPct=allocation_pct,
                    sectorName=sector,
                    reason=reason
                )
                recommendations.append(recommendation)
        
        # 4. 비중 총합 검증 (이미 normalize로 맞춰졌지만, 안전망)
        current_total = sum(rec.allocationPct for rec in recommendations)
        if recommendations and current_total != total_stock_pct:
            # 차이를 가장 큰 비중 종목에서 보정
            target = max(recommendations, key=lambda x: x.allocationPct)
            target.allocationPct = max(1, target.allocationPct + (total_stock_pct - current_total))
        
        return recommendations
    
    def _generate_enhanced_reason(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        sector_outlook: Dict[str, Any],
        company_size_preference: Dict[str, float]
    ) -> str:
        """고도화된 추천 이유 생성 (시장 전망 상세 반영)"""
        
        name = stock['name']
        analysis = stock.get('analysis', {})
        
        reason_parts = []
        
        # 1. 기본 소개 + 특성 기반 분류
        investment_grade = analysis.get('investment_grade', '균형형')
        risk_level = analysis.get('risk_level', '중위험')
        company_size = analysis.get('company_size', '중견기업')
        
        reason_parts.append(f"{sector} 섹터의 {name}은(는)")
        reason_parts.append(f"{investment_grade} {company_size}으로")
        
        # 2. 상세한 시장 전망 반영
        if sector_outlook and sector_outlook.get('confidence', 0) > 0.5:
            market_impact = sector_outlook.get('market_impact', '')
            time_horizon = sector_outlook.get('time_horizon', '중기')
            summary = sector_outlook.get('summary', '')
            
            # 시장 전망 요약
            if market_impact:
                reason_parts.append(f"현재 시장 분석에 따르면 {market_impact}")
            
            # 투자 시점 고려
            if time_horizon == "단기":
                reason_parts.append("단기적으로")
            elif time_horizon == "장기":
                reason_parts.append("장기적 관점에서")
            else:
                reason_parts.append("중기적으로")
            
            # 전망 요약 직접 인용
            if summary:
                reason_parts.append(f'"{summary}"')
        
        # 3. 개인 투자 성향과의 매칭
        characteristics = analysis.get('characteristics', [])
        
        if investment_profile in ["안정형", "안정추구형"]:
            if '안정' in characteristics or risk_level == "저위험":
                reason_parts.append("이는 귀하의 안정 추구 투자 성향과 잘 부합하며,")
            else:
                reason_parts.append("포트폴리오의 분산 효과를 위해 선정되었으며,")
                
        elif investment_profile in ["적극투자형", "공격투자형"]:
            if '고변동' in characteristics or analysis.get('growth_potential', 0) > 0:
                reason_parts.append("높은 성장 잠재력으로 귀하의 적극적 투자 성향에 적합하며,")
            else:
                reason_parts.append("포트폴리오의 안정성 확보를 위해 포함되었으며,")
        else:
            reason_parts.append("균형잡힌 위험-수익 프로필을 가지고 있어")
        
        # 4. 구체적 투자 메리트
        if '배당주' in characteristics:
            reason_parts.append("안정적인 배당 수익과 함께")
        
        if '시가총액 상위' in characteristics:
            reason_parts.append("시장 선도 기업으로서의 지위를")
        
        # 5. 마무리 - 기대 효과
        if risk_level == "저위험":
            reason_parts.append("안전한 자산 보전 효과를 기대할 수 있습니다.")
        elif risk_level == "고위험":
            reason_parts.append("높은 수익 창출 가능성을 제공합니다.")
        else:
            reason_parts.append("안정성과 수익성의 균형을 추구할 수 있습니다.")
        
        # 최종 문장 정리
        full_reason = " ".join(reason_parts)
        
        # 문장 길이 제한 (너무 길면 요약)
        if len(full_reason) > 300:
            # 핵심 부분만 추출
            core_parts = reason_parts[:3] + reason_parts[-2:]
            full_reason = " ".join(core_parts)
        
        return full_reason
    
    async def _generate_comprehensive_reason(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        analysis: Dict[str, Any],
        use_news_analysis: bool = True,
        use_financial_analysis: bool = True
    ) -> str:
        """뉴스 + 재무제표 종합 추천 이유 생성 (LLM 기반 동적 생성)"""
        
        stock_name = stock.get('name', '')
        stock_code = stock.get('code', '')
        comprehensive_score = analysis.get('comprehensive_score', 50)
        
        # LLM을 사용해서 동적 추천 이유 생성
        if self.llm:
            try:
                # 실제 데이터 기반 동적 추천 이유 생성
                dynamic_reason = await self._generate_dynamic_reason_with_llm(
                    stock, sector, investment_profile, analysis, 
                    use_news_analysis, use_financial_analysis
                )
                return dynamic_reason
            except Exception as e:
                print(f"⚠️ LLM 추천 이유 생성 실패: {e}")
        
        # 폴백: 기존 템플릿 방식
        return self._generate_fallback_reason(
            stock, sector, investment_profile, analysis,
            use_news_analysis, use_financial_analysis
        )
    
    def _get_stock_characteristics(self, stock_name: str, sector: str, stock_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """종목별 특성 정보 반환 (우량주, 배당주, 성장주 등)"""
        
        characteristics = {
            "type": "일반주",
            "features": [],
            "market_position": "중견기업",
            "dividend_type": "일반",
            "advantages": [],
            "disadvantages": [],
            "risk_level": "중위험"
        }
        
        # stock_data에서 characteristics 확인 (portfolio_stocks.yaml에서 로드된 데이터)
        stock_characteristics = []
        if stock_data and 'characteristics' in stock_data:
            stock_characteristics = stock_data['characteristics']
        
        # 우선배당주 특성 세부 분석
        if "우선배당주" in stock_characteristics or "우" in stock_name:
            characteristics["type"] = "우선배당주"
            characteristics["dividend_type"] = "우선배당"
            
            # 우선배당주 고유 장점
            characteristics["advantages"].extend([
                "배당 우선권 보장",
                "안정적인 배당 수익",
                "일반주 대비 안정성",
                "하방 리스크 제한적"
            ])
            
            # 우선배당주 고유 단점
            characteristics["disadvantages"].extend([
                "의결권 제한",
                "시세차익 제한적",
                "유동성 상대적 부족",
                "상승 탄력성 낮음"
            ])
            
            characteristics["risk_level"] = "저위험"
            characteristics["market_position"] = "모기업 연동"
            
            # 일반주 대비 특성
            if "안정" in stock_characteristics:
                characteristics["features"].extend(["안정형 우선배당", "배당 연속성"])
            if "고변동" in stock_characteristics:
                characteristics["features"].extend(["변동형 우선배당", "수익 탄력성"])
                characteristics["risk_level"] = "중위험"
        
        # 일반주 특성
        else:
            # 대형 우량주
            if stock_name in ["삼성전자", "SK하이닉스", "NAVER", "카카오"] or "시가총액 상위" in stock_characteristics:
                characteristics["type"] = "대형 우량주"
                characteristics["features"].extend(["시장 선도", "안정성"])
                characteristics["market_position"] = "업계 1위"
                characteristics["advantages"].extend(["시장 지배력", "브랜드 파워", "재무 안정성"])
                
            # 배당주 특성
            if "배당주" in stock_characteristics:
                characteristics["features"].append("배당 우량주")
                characteristics["advantages"].extend(["꾸준한 배당", "현금흐름 안정"])
                
            # 성장주 특성
            if stock_name in ["SK하이닉스", "카카오"] or "성장" in ' '.join(stock_characteristics):
                characteristics["features"].append("성장주")
                characteristics["advantages"].extend(["성장 잠재력", "기술 혁신"])
                characteristics["disadvantages"].extend(["변동성", "밸류에이션 부담"])
                characteristics["risk_level"] = "중위험"
            
        # 섹터별 특성
        if sector == "전기·전자":
            characteristics["features"].extend(["기술 혁신", "글로벌 경쟁력"])
            if characteristics["type"] != "우선배당주":
                characteristics["disadvantages"].extend(["업황 민감", "기술 경쟁"])
        elif sector == "IT 서비스":
            characteristics["features"].extend(["플랫폼 사업", "디지털 전환"])
            if characteristics["type"] != "우선배당주":
                characteristics["disadvantages"].extend(["규제 리스크", "경쟁 심화"])
        elif sector == "기타금융":
            characteristics["features"].extend(["금리 민감", "경기 연동"])
            characteristics["advantages"].extend(["금리 상승 수혜", "안정적 사업모델"])
            
        # 개별 종목 특성
        if stock_name == "삼성전자":
            characteristics["features"].extend(["반도체 강자", "배당 우량주"])
            characteristics["advantages"].extend(["글로벌 점유율 1위", "기술력"])
        elif stock_name == "SK하이닉스":
            characteristics["features"].extend(["메모리 반도체", "성장주"])
            characteristics["advantages"].extend(["HBM 선도", "AI 수혜"])
        elif stock_name == "NAVER":
            characteristics["features"].extend(["검색 포털", "클라우드"])
            characteristics["advantages"].extend(["국내 검색 독점", "해외 확장"])
        elif stock_name == "카카오":
            characteristics["features"].extend(["모바일 플랫폼", "핀테크"])
            characteristics["advantages"].extend(["생활 플랫폼", "간편결제"])
            
        return characteristics
    
    async def _generate_dynamic_reason_with_llm(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        analysis: Dict[str, Any],
        use_news_analysis: bool,
        use_financial_analysis: bool
    ) -> str:
        """LLM 기반 동적 추천 이유 생성 (실제 뉴스 + 재무 데이터 활용)"""
        
        stock_name = stock.get('name', '')
        stock_code = stock.get('code', '')
        
        # 종목 특성 정보 (우선배당주 등)
        stock_chars = self._get_stock_characteristics(stock_name, sector, stock)
        
        # 실제 뉴스 헤드라인과 재무 수치를 더 구체적으로 추출
        raw_financial = analysis.get('raw_financial_data', {})
        raw_news = analysis.get('raw_news_data', {})
        
        # 🔥 뉴스 헤드라인 직접 추출 (더 구체적)
        actual_news_headlines = []
        sector_outlook = ""
        market_drivers = []
        if raw_news:
            headlines = raw_news.get('headlines', [])
            if headlines:
                actual_news_headlines = headlines[:3]  # 최신 3개 헤드라인
            
            # 뉴스 분석 결과
            news_sentiment = raw_news.get('sentiment_analysis', {})
            sector_outlook = raw_news.get('sector_outlook', '') or raw_news.get('sector_summary', '')
            market_drivers = raw_news.get('market_drivers', []) or raw_news.get('key_factors', [])
        
        # 💰 실제 재무 수치 직접 추출 (순수 데이터만)
        actual_financial_metrics = []
        financial_health_status = None
        
        if raw_financial:
            # 핵심 재무 지표들 (숫자만)
            revenue_growth = raw_financial.get('revenue_growth', '')
            profit_margin = raw_financial.get('profit_margin', '')
            debt_ratio = raw_financial.get('debt_ratio', '')
            roe = raw_financial.get('roe', '')
            current_ratio = raw_financial.get('current_ratio', '')
            
            # 실제 수치가 있는 것만 포함
            if revenue_growth:
                actual_financial_metrics.append(f"매출성장률 {revenue_growth}")
            if profit_margin:
                actual_financial_metrics.append(f"영업이익률 {profit_margin}")
            if roe:
                actual_financial_metrics.append(f"ROE {roe}")
            if debt_ratio:
                actual_financial_metrics.append(f"부채비율 {debt_ratio}")
            if current_ratio:
                actual_financial_metrics.append(f"유동비율 {current_ratio}")
            
            # 재무 건전성 상태 (별도 변수로)
            financial_health_status = raw_financial.get('financial_health', '')
        
        # 📈 투자자 성향별 맞춤 분석 포인트
        investor_focus = self._get_investor_focus_points(investment_profile)
        
        # 🎯 종합 점수와 세부 평가
        comprehensive_score = analysis.get('comprehensive_score', 50)
        news_score = analysis.get('news_score', 50)
        financial_score = analysis.get('financial_score', 50)
        
        # 재무 상태를 자연스러운 표현으로 변환
        financial_status_text = ""
        if financial_health_status:
            health_map = {
                "우수": "견고한 재무구조를 갖추고 있으며",
                "양호": "안정적인 재무상태를 유지하고 있고", 
                "보통": "무난한 재무지표를 보이고 있으나",
                "주의": "재무 개선이 필요한 상황이며",
                "위험": "재무 리스크를 안고 있어"
            }
            financial_status_text = health_map.get(financial_health_status, "")
        
        # 더 구체적이고 동적인 프롬프트 생성
        prompt = f"""당신은 전문 포트폴리오 매니저입니다. 아래 데이터를 바탕으로 {stock_name}에 대한 {investment_profile} 투자자를 위한 추천 이유를 **자연스럽고 전문적인 문장**으로 작성하세요.

【투자자 프로필】
성향: {investment_profile}
관심 섹터: {sector}
투자 목표: {investor_focus}

【재무 지표】
{chr(10).join([f"• {metric}" for metric in actual_financial_metrics[:4]]) if actual_financial_metrics else '• 분석 중'}
{f"• 전반적으로 {financial_status_text}" if financial_status_text else ''}

【시장 동향 및 전망 (Neo4j 기반 분석)】
• 최신 동향: {chr(10).join([f"  - {headline}" for headline in actual_news_headlines[:2]]) if actual_news_headlines else '분석 중'}
• 핵심 동력: {', '.join(market_drivers) if market_drivers else '분석 중'}
• 섹터 전망: {sector_outlook if sector_outlook else '분석 중'}

【AI 평가】
재무 {financial_score}점 | 뉴스 {news_score}점 | 종합 {comprehensive_score}점

【종목 특징】
{stock_chars["type"]} | 강점: {', '.join(stock_chars["advantages"][:2])} | 유의: {', '.join(stock_chars["disadvantages"][:1])}

【작성 규칙】
1. '시장 동향 및 전망' 데이터를 활용하여, "~한 동향으로 인해 ~가 예상됩니다." 와 같은 구체적인 문장을 포함하세요.
2. 위 데이터를 자연스럽게 녹인 2-3문장 작성
3. "재무 건전성: 보통", "매출 성장률 8%" 같은 딱딱한 표현 금지  
4. {investment_profile} 투자자에게 의미있는 핵심만 전달
5. 읽기 쉽고 전문적인 문체 사용
6. 구체적 조언 제공 (뻔한 말 금지)

추천 이유:"""

        try:
            response = await self.llm.ainvoke(prompt)
            reason = response.content.strip()
            
            # 응답 품질 검증 및 정제
            reason = self._refine_llm_response(reason, stock_name, investment_profile)
            
            return reason
            
        except Exception as e:
            print(f"⚠️ LLM 추천 이유 생성 중 오류: {e}")
            return self._generate_fallback_reason(
                stock, sector, investment_profile, analysis,
                use_news_analysis, use_financial_analysis
            )
    
    def _get_investor_focus_points(self, investment_profile: str) -> str:
        """투자자 성향별 중점 관심사 반환"""
        focus_map = {
            "안정형": "배당 수익, 원금 보전, 낮은 변동성",
            "안정추구형": "꾸준한 수익, 브랜드 가치, 안정적 성장",
            "위험중립형": "균형 잡힌 성장, 적정 밸류에이션, 중장기 전망",
            "적극투자형": "성장 잠재력, 업계 경쟁력, 혁신 기술",
            "공격투자형": "고성장 기대, 시장 확대, 파괴적 혁신"
        }
        return focus_map.get(investment_profile, "균형 잡힌 투자")
    
    def _refine_llm_response(self, response: str, stock_name: str, investment_profile: str) -> str:
        """LLM 응답 품질 검증 및 정제"""
        
        # 기본 정제
        refined = response.strip()
        
        # 불필요한 접두어 제거
        prefixes_to_remove = [
            "투자 추천 이유:", "추천 이유:", "🎯 투자 추천 이유:", 
            "분석 결과:", "결론:", "투자 의견:"
        ]
        for prefix in prefixes_to_remove:
            if refined.startswith(prefix):
                refined = refined[len(prefix):].strip()
        
        # 길이 제한 (너무 긴 경우 핵심 문장만 추출)
        if len(refined) > 400:
            sentences = refined.split('. ')
            if len(sentences) >= 3:
                # 첫 번째와 마지막 문장 유지
                refined = sentences[0] + '. ' + sentences[-1]
                if not refined.endswith('.'):
                    refined += '.'
            else:
                refined = refined[:400] + '...'
        
        # 품질 검증: 종목명과 투자자 성향이 언급되었는지 확인
        has_stock_name = stock_name in refined
        has_profile_context = any(keyword in refined for keyword in [
            "안정", "성장", "배당", "수익", "위험", "변동성", "투자"
        ])
        
        # 품질이 낮은 경우 보완
        if not has_stock_name or not has_profile_context:
            print(f"⚠️ LLM 응답 품질 낮음, 보완 처리: 종목명({has_stock_name}) 맥락({has_profile_context})")
            # 기본 정보 추가
            if not has_stock_name:
                refined = f"{stock_name}은(는) " + refined
        
        return self._normalize_korean_text(refined)
    
    def _get_investor_specific_examples(
        self, 
        investment_profile: str, 
        stock_name: str, 
        sector: str,
        financial_metrics: List[str],
        news_headlines: List[str],
        comprehensive_score: int
    ) -> str:
        """투자자 성향별 맞춤형 분석 예시 생성"""
        
        # 실제 데이터가 있는 경우 활용
        sample_metric = financial_metrics[0] if financial_metrics else "매출 성장률 +15.2%"
        sample_headline = news_headlines[0] if news_headlines else f"[{sector}] 업계 전망 개선세"
        
        examples = {
            "안정형": f"""
💡 안정형 투자자 분석 예시:
"삼성전자우는 배당수익률 2.8%와 부채비율 15.3%로 안정적 현금흐름을 제공하며, 최근 '메모리 반도체 수급 개선' 뉴스로 배당 지속성이 더욱 견고해졌으나, 반도체 업황 변동성에 대한 주의가 필요합니다."

📊 안정형 중점 분석 요소:
• 배당 수익률과 지속성 → 현재 데이터: {sample_metric}
• 재무 안정성 (부채비율, 현금 보유) 
• 시장 변동성 대응 능력
• 업계 뉴스가 배당에 미치는 영향 → 현재 뉴스: {sample_headline}
""",
            
            "안정추구형": f"""
💡 안정추구형 투자자 분석 예시:
"NAVER는 ROE 12.4%와 매출성장률 8.7%로 꾸준한 성장세를 보이며, 최근 '클라우드 사업 확장' 발표로 중장기 성장 동력을 확보했으나, 플랫폼 규제 리스크를 지속 모니터링해야 합니다."

📊 안정추구형 중점 분석 요소:
• 안정적 성장률 (ROE, 매출성장) → 현재 데이터: {sample_metric}
• 브랜드 가치와 시장 지위
• 중장기 비즈니스 모델 지속성
• 성장 관련 뉴스 분석 → 현재 뉴스: {sample_headline}
""",
            
            "위험중립형": f"""
💡 위험중립형 투자자 분석 예시:
"SK하이닉스는 PER 18.5배, PBR 1.2배로 적정 밸류에이션을 유지하며, 최근 'HBM 수주 확대' 뉴스로 AI 반도체 수혜주로 재조명받고 있으나, 메모리 업황 사이클을 고려한 진입 타이밍이 중요합니다."

📊 위험중립형 중점 분석 요소:
• 밸류에이션 지표 (PER, PBR) → 현재 데이터: {sample_metric}  
• 업종 내 상대적 경쟁력
• 중장기 성장 vs 단기 리스크 균형
• 업황 사이클 분석 → 현재 뉴스: {sample_headline}
""",
            
            "적극투자형": f"""
💡 적극투자형 투자자 분석 예시:
"카카오는 매출성장률 22.3%와 신사업 투자 확대로 높은 성장 잠재력을 보이며, 최근 'AI 서비스 출시' 뉴스로 테크 혁신 리더십을 강화하고 있으나, 높은 PER 30배에 따른 밸류에이션 부담을 감안해야 합니다."

📊 적극투자형 중점 분석 요소:
• 고성장 지표 (매출/영업이익 증가율) → 현재 데이터: {sample_metric}
• 신사업 진출과 혁신 투자
• 시장 확장 가능성과 경쟁우위
• 성장 관련 뉴스 모멘텀 → 현재 뉴스: {sample_headline}
""",
            
            "공격투자형": f"""
💡 공격투자형 투자자 분석 예시:
"셀트리온은 매출성장률 45.7%와 글로벌 바이오시밀러 시장 진출로 파괴적 성장을 추진하며, 최근 'FDA 신약 승인' 뉴스로 시장 판도 변화를 주도할 잠재력을 보이나, 높은 R&D 투자와 규제 리스크에 대한 높은 리스크 허용도가 필요합니다."

📊 공격투자형 중점 분석 요소:  
• 파괴적 성장률 (50%+ 성장) → 현재 데이터: {sample_metric}
• 시장 혁신과 게임 체인저 가능성
• 글로벌 시장 진출 성과
• 혁신 관련 뉴스 임팩트 → 현재 뉴스: {sample_headline}
"""
        }
        
        return examples.get(investment_profile, examples["위험중립형"])
    
    def _get_investment_priorities(self, investment_profile: str) -> str:
        """투자자 성향별 우선순위"""
        priorities = {
            "안정형": "배당수익(40%) > 원금보전(35%) > 안정성(25%)",
            "안정추구형": "안정성장(45%) > 배당수익(30%) > 브랜드가치(25%)",
            "위험중립형": "균형성장(40%) > 밸류에이션(35%) > 리스크관리(25%)",
            "적극투자형": "성장잠재력(50%) > 혁신기술(30%) > 시장확장(20%)",
            "공격투자형": "파괴적혁신(60%) > 시장지배력(25%) > 고성장(15%)"
        }
        return priorities.get(investment_profile, "균형 투자")
    
    def _get_investor_risk_focus(self, investment_profile: str) -> str:
        """투자자 성향별 리스크 관점"""
        risk_focus = {
            "안정형": "배당 중단/감소 리스크와 원금 손실 가능성",
            "안정추구형": "꾸준한 성장 둔화와 브랜드 가치 하락",  
            "위험중립형": "업황 사이클과 밸류에이션 과열",
            "적극투자형": "성장 모멘텀 실종과 경쟁 열세",
            "공격투자형": "혁신 실패와 시장 판도 변화"
        }
        return risk_focus.get(investment_profile, "일반적인 시장 리스크")
    
    def _generate_fallback_reason(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        analysis: Dict[str, Any],
        use_news_analysis: bool,
        use_financial_analysis: bool
    ) -> str:
        """폴백용 템플릿 기반 추천 이유 생성"""
        
        stock_name = stock.get('name', '')
        investment_rating = analysis.get('investment_rating', '보통')
        risk_level = analysis.get('risk_level', '중위험')
        
        # 조사 처리
        def get_josa(word):
            if not word:
                return "은"
            last_char = word[-1]
            if '가' <= last_char <= '힣':
                code = ord(last_char) - ord('가')
                jong = code % 28
                return "은" if jong != 0 else "는"
            elif last_char.lower() in 'aeiou' or last_char in '13679':
                return "는"  
            else:
                return "은"
        
        josa = get_josa(stock_name)
        
        # 기본 템플릿 추천 이유
        stock_chars = self._get_stock_characteristics(stock_name, sector, stock)
        stock_type = stock_chars["type"]
        
        base = (
            f"{sector} 섹터의 {stock_name}{josa} 우선배당주로서 안정적인 배당 수익을 제공하는 {investment_rating} 등급의 투자처입니다."
            if stock_type == "우선배당주"
            else f"{sector} 섹터의 {stock_name}{josa} {investment_rating} 등급의 {risk_level} 투자처로 평가됩니다."
        )
        return self._normalize_korean_text(base)
    
    def _get_default_sectors(self, investment_profile: str) -> List[str]:
        """투자 성향에 따라 기본 관심 섹터를 반환"""
        if investment_profile in ["안정형", "안정추구형"]:
            # 안정적이고 배당률이 높은 섹터
            return ["기타금융", "화학"]
        elif investment_profile == "위험중립형":
            # 시장 대표 섹터
            return ["전기·전자", "IT 서비스", "운송장비·부품"]
        elif investment_profile in ["적극투자형", "공격투자형"]:
            # 성장성이 높은 기술주 중심 섹터
            return ["전기·전자", "IT 서비스", "제약"]
        return ["전기·전자", "IT 서비스"] # 기본값

    def _normalize_korean_text(self, text: str) -> str:
        """한글 텍스트 정규화 및 깨짐 문자 제거"""
        if not text:
            return ""
        # NFC 정규화로 문자열을 표준 형태로 변환
        normalized = unicodedata.normalize("NFC", text)
        # 흔한 깨짐 문자() 제거 및 공백 정리
        normalized = normalized.replace("", "")
        normalized = " ".join(normalized.split())
        return normalized.strip()


# 전역 인스턴스
enhanced_portfolio_service = EnhancedPortfolioService()
