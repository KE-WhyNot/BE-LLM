"""고도화된 포트폴리오 추천 서비스 - 뉴스 분석 + 기업 규모 선호도 반영"""

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
    
    async def recommend_enhanced_portfolio(
        self, 
        profile: InvestmentProfileRequest,
        use_news_analysis: bool = True,
        use_financial_analysis: bool = True
    ) -> PortfolioRecommendationResult:
        """최고도화된 포트폴리오 추천 (뉴스 + 재무제표 종합 분석)"""
        
        print(f"🚀 최고도화된 포트폴리오 추천 시작 (사용자: {profile.userId})")
        print(f"📊 분석 범위: 뉴스({use_news_analysis}) + 재무제표({use_financial_analysis})")
        
        # 1. 기본 자산 배분 결정
        allocation = self.asset_allocation_rules.get(
            profile.investmentProfile,
            self.asset_allocation_rules["위험중립형"]
        )
        base_savings_pct = allocation["예적금"]
        base_stocks_pct = allocation["주식"]
        
        # 2. 관심 섹터 기본 설정
        interested_sectors = profile.interestedSectors
        if not interested_sectors:
            interested_sectors = self._get_default_sectors(profile.investmentProfile)
        
        # 3. 기업 규모 선호도 결정
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
        
        # 4. 종목 선정 (종합 분석 기반)
        recommended_stocks = await self._select_comprehensive_stocks(
            interested_sectors,
            profile.investmentProfile,
            company_size_preference,
            base_stocks_pct,
            use_news_analysis,
            use_financial_analysis
        )
        
        # 5. 최종 예적금 비율 계산
        total_stock_allocation = sum(stock.allocationPct for stock in recommended_stocks)  
        final_savings_pct = 100 - total_stock_allocation
        
        # 6. 결과 생성
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        result = PortfolioRecommendationResult(
            portfolioId=profile.profileId,
            userId=profile.userId,
            recommendedStocks=recommended_stocks,
            allocationSavings=final_savings_pct,
            createdAt=now,
            updatedAt=now
        )
        
        analysis_type = []
        if use_news_analysis: analysis_type.append("뉴스")
        if use_financial_analysis: analysis_type.append("재무제표")
        analysis_desc = " + ".join(analysis_type) if analysis_type else "기본"
        
        print(f"✅ 최고도화된 포트폴리오 추천 완료 ({analysis_desc}): {len(recommended_stocks)}개 종목, 예적금 {final_savings_pct}%")
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
        
        # 3. 비중 배분 (종합 점수 기반)
        if selected_candidates:
            total_score = sum(item['comprehensive_score'] for item in selected_candidates)
            
            for item in selected_candidates:
                stock = item['stock']
                analysis = item['analysis']
                score = item['comprehensive_score']
                sector = item['sector']
                
                # 점수 비례 배분
                if total_score > 0:
                    allocation_pct = int((score / total_score) * total_stock_pct)
                else:
                    allocation_pct = total_stock_pct // len(selected_candidates)
                
                # 최소 1% 보장
                allocation_pct = max(1, allocation_pct)
                
                # 종합 추천 이유 생성
                reason = self._generate_comprehensive_reason(
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
        
        # 4. 비중 총합 조정 (100% 맞추기)
        current_total = sum(rec.allocationPct for rec in recommendations)
        if current_total != total_stock_pct and recommendations:
            # 가장 높은 비중 종목에서 조정
            max_recommendation = max(recommendations, key=lambda x: x.allocationPct)
            adjustment = total_stock_pct - current_total
            max_recommendation.allocationPct = max(1, max_recommendation.allocationPct + adjustment)
        
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
    
    def _generate_comprehensive_reason(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        analysis: Dict[str, Any],
        use_news_analysis: bool = True,
        use_financial_analysis: bool = True
    ) -> str:
        """뉴스 + 재무제표 종합 추천 이유 생성"""
        
        stock_name = stock.get('name', '')
        comprehensive_score = analysis.get('comprehensive_score', 50)
        
        reason_parts = []
        
        # 1. 기본 소개 + 종합 평가
        investment_rating = analysis.get('investment_rating', '보통')
        risk_level = analysis.get('risk_level', '중위험')
        
        reason_parts.append(f"{sector} 섹터의 {stock_name}은(는)")
        reason_parts.append(f"종합 분석 결과 '{investment_rating}' 등급의 {risk_level} 투자처로,")
        
        # 2. 재무제표 근거 (활용 시)
        if use_financial_analysis and analysis:
            financial_highlights = analysis.get('financial_highlights', [])
            key_metrics = analysis.get('key_metrics', {})
            
            if financial_highlights:
                reason_parts.append(f"재무적으로 {', '.join(financial_highlights[:2])}의 강점을 보이며,")
            
            # 핵심 재무지표 언급
            if key_metrics:
                metric_mentions = []
                for metric, value in list(key_metrics.items())[:2]:  # 상위 2개 지표만
                    if value and value != "값" and value != "데이터":
                        metric_mentions.append(f"{metric} {value}")
                
                if metric_mentions:
                    reason_parts.append(f"({', '.join(metric_mentions)})")
        
        # 3. 시장 전망 및 뉴스 근거 (활용 시)
        if use_news_analysis and analysis:
            market_opportunities = analysis.get('market_opportunities', [])
            investment_thesis = analysis.get('investment_thesis', '')
            time_horizon = analysis.get('time_horizon', '중기')
            
            # 시장 기회 언급
            if market_opportunities:
                reason_parts.append(f"{time_horizon}적으로 {market_opportunities[0]}의 기회가 기대되며,")
            
            # 투자 논리 직접 인용 (핵심!)
            if investment_thesis:
                # 너무 길면 요약
                if len(investment_thesis) > 100:
                    thesis_parts = investment_thesis.split('.')
                    short_thesis = thesis_parts[0] + '.' if thesis_parts else investment_thesis[:100]
                    reason_parts.append(f'"{short_thesis}"')
                else:
                    reason_parts.append(f'"{investment_thesis}"')
        
        # 4. 개인 투자 성향 매칭
        expected_return = analysis.get('expected_return', '중수익')
        
        if investment_profile in ["안정형", "안정추구형"]:
            if risk_level == "저위험":
                reason_parts.append("귀하의 안정 추구 성향에 매우 적합한 안전한 투자처입니다.")
            else:
                reason_parts.append("포트폴리오 다각화를 위해 신중하게 선정된 종목입니다.")
                
        elif investment_profile in ["적극투자형", "공격투자형"]:
            if expected_return in ["고수익", "중수익"]:
                reason_parts.append(f"{expected_return} 가능성으로 귀하의 적극적 투자 성향에 부합합니다.")
            else:
                reason_parts.append("포트폴리오의 안정성 확보를 위해 포함되었습니다.")
        else:
            reason_parts.append(f"{expected_return}과 적정 위험 수준의 균형잡힌 투자 옵션입니다.")
        
        # 5. 리스크 요인 (중요한 경우 언급)
        risk_factors = analysis.get('risk_factors', [])
        if risk_factors and comprehensive_score < 70:
            main_risk = risk_factors[0]
            reason_parts.append(f"다만 {main_risk} 요인을 주의 깊게 모니터링할 필요가 있습니다.")
        
        # 최종 문장 구성
        full_reason = " ".join(reason_parts)
        
        # 길이 제한 (400자 내외)
        if len(full_reason) > 400:
            # 핵심 부분만 유지 (소개 + 핵심 근거 + 결론)
            core_parts = reason_parts[:2] + reason_parts[-2:]
            full_reason = " ".join(core_parts)
        
        return full_reason
    
    def _get_default_sectors(self, investment_profile: str) -> List[str]:
        """투자 성향별 기본 섹터 반환"""
        
        if investment_profile in ["안정형", "안정추구형"]:
            return ["전기·전자", "기타금융", "IT 서비스"]
        elif investment_profile == "위험중립형":
            return ["전기·전자", "제약", "기타금융"]
        else:  # 적극투자형, 공격투자형
            return ["전기·전자", "IT 서비스", "제약"]


# 전역 인스턴스
enhanced_portfolio_service = EnhancedPortfolioService()
