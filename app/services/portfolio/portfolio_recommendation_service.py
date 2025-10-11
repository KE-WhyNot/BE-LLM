"""포트폴리오 추천 서비스 - 실제 주식 종목 기반"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from app.utils.portfolio_stock_loader import portfolio_stock_loader
from app.schemas.portfolio_schema import (
    InvestmentProfileRequest,
    StockRecommendation,
    PortfolioRecommendationResult
)


class PortfolioRecommendationService:
    """실제 주식 종목 기반 포트폴리오 추천 서비스"""
    
    def __init__(self):
        # 투자 성향별 자산 배분 규칙
        self.asset_allocation_rules = {
            "안정형": {"예적금": 80, "주식": 20},
            "안정추구형": {"예적금": 60, "주식": 40},
            "위험중립형": {"예적금": 50, "주식": 50},
            "적극투자형": {"예적금": 30, "주식": 70},
            "공격투자형": {"예적금": 20, "주식": 80}
        }
        
        self.stock_loader = portfolio_stock_loader
    
    def recommend_portfolio(
        self, 
        profile: InvestmentProfileRequest
    ) -> PortfolioRecommendationResult:
        """투자 프로필을 기반으로 포트폴리오 추천"""
        
        # 1. 예적금 vs 주식 비율 결정
        allocation = self.asset_allocation_rules.get(
            profile.investmentProfile,
            self.asset_allocation_rules["위험중립형"]
        )
        savings_pct = allocation["예적금"]
        stocks_pct = allocation["주식"]
        
        # 2. 관심 섹터 기반 주식 선정
        recommended_stocks = self._select_stocks(
            profile.interestedSectors,
            profile.investmentProfile,
            profile.lossTolerance,
            profile.financialKnowledge,
            stocks_pct
        )
        
        # 3. 추천 결과 생성
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        result = PortfolioRecommendationResult(
            portfolioId=profile.profileId,
            userId=profile.userId,
            recommendedStocks=recommended_stocks,
            allocationSavings=savings_pct,
            createdAt=now,
            updatedAt=now
        )
        
        return result
    
    def _select_stocks(
        self,
        interested_sectors: List[str],
        investment_profile: str,
        loss_tolerance: str,
        financial_knowledge: str,
        total_stock_pct: int
    ) -> List[StockRecommendation]:
        """관심 섹터와 투자 성향을 고려하여 주식 선정"""
        
        recommendations = []
        
        # 관심 섹터가 없는 경우 기본 섹터 사용
        if not interested_sectors:
            interested_sectors = self._get_default_sectors(investment_profile)
        
        # 섹터 수에 따라 분산 투자
        num_sectors = len(interested_sectors)
        
        # 각 섹터에서 1-2개 종목 선정
        stocks_per_sector = max(1, min(2, 5 // num_sectors))
        
        selected_stocks = []
        for sector in interested_sectors:
            sector_stocks = self.stock_loader.get_best_stocks_for_profile(
                sector, 
                investment_profile,
                limit=stocks_per_sector
            )
            for stock in sector_stocks:
                selected_stocks.append({
                    'stock': stock,
                    'sector': sector
                })
        
        # 최대 5개 종목으로 제한
        selected_stocks = selected_stocks[:5]
        
        if not selected_stocks:
            # 종목이 없으면 에러 방지를 위해 기본 종목 반환
            return self._get_default_recommendations(total_stock_pct)
        
        # 종목별 비율 계산
        num_stocks = len(selected_stocks)
        base_allocation = total_stock_pct // num_stocks
        remainder = total_stock_pct % num_stocks
        
        # 추천 종목 리스트 생성
        for idx, item in enumerate(selected_stocks):
            stock = item['stock']
            sector = item['sector']
            
            # 비율 배분 (나머지는 첫 번째 종목에 추가)
            allocation = base_allocation + (remainder if idx == 0 else 0)
            
            # 추천 이유 생성
            reason = self._generate_recommendation_reason(
                stock, 
                sector,
                investment_profile,
                loss_tolerance,
                financial_knowledge
            )
            
            recommendation = StockRecommendation(
                stockId=stock['code'],
                stockName=stock['name'],
                allocationPct=allocation,
                sectorName=sector,
                reason=reason
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_recommendation_reason(
        self,
        stock: Dict[str, Any],
        sector: str,
        investment_profile: str,
        loss_tolerance: str,
        financial_knowledge: str
    ) -> str:
        """종목 추천 이유 생성"""
        
        characteristics = stock.get('characteristics', [])
        name = stock['name']
        market_cap = stock.get('market_cap', 0)
        
        reason_parts = []
        
        # 섹터 언급
        reason_parts.append(f"{sector} 섹터의 {name}은(는)")
        
        # 특성 기반 설명
        if '시가총액 상위' in characteristics:
            reason_parts.append("시가총액 상위 기업으로 시장에서 안정적인 위치를 차지하고 있으며")
        
        if '안정' in characteristics:
            reason_parts.append("안정적인 수익 구조를 가지고 있어")
            if investment_profile in ["안정형", "안정추구형"]:
                reason_parts.append("귀하의 안정 지향적 투자 성향에 적합합니다.")
            else:
                reason_parts.append("포트폴리오의 안정성을 높여줍니다.")
        
        elif '고변동' in characteristics:
            if investment_profile in ["적극투자형", "공격투자형"]:
                reason_parts.append("높은 변동성으로 수익 기회가 크며, 귀하의 공격적인 투자 성향에 부합합니다.")
            else:
                reason_parts.append("성장 가능성이 높아 포트폴리오의 수익성을 높여줍니다.")
        
        if '배당주' in characteristics:
            reason_parts.append("꾸준한 배당 수익도 기대할 수 있습니다.")
        
        # 기본 설명이 없는 경우
        if len(reason_parts) <= 1:
            if market_cap > 10000000000000:  # 10조 이상
                reason_parts.append("대형주로서 안정적인 투자처입니다.")
            elif market_cap > 1000000000000:  # 1조 이상
                reason_parts.append("중견 기업으로 성장 가능성과 안정성을 갖추고 있습니다.")
            else:
                reason_parts.append("성장 잠재력이 있는 종목입니다.")
        
        return " ".join(reason_parts)
    
    def _get_default_sectors(self, investment_profile: str) -> List[str]:
        """투자 성향별 기본 섹터 반환"""
        
        if investment_profile in ["안정형", "안정추구형"]:
            # 안정형: 안정적인 섹터 우선
            return ["전기·전자", "기타금융", "IT 서비스"]
        elif investment_profile == "위험중립형":
            # 중립형: 균형잡힌 섹터
            return ["전기·전자", "제약", "기타금융"]
        else:  # 적극투자형, 공격투자형
            # 공격형: 성장 가능성 높은 섹터
            return ["전기·전자", "IT 서비스", "제약"]
    
    def _get_default_recommendations(self, total_stock_pct: int) -> List[StockRecommendation]:
        """기본 추천 종목 (fallback)"""
        
        # 안정적인 대형주 위주로 기본 추천
        default_stocks = [
            {
                'code': '005930',
                'name': '삼성전자',
                'sector': '전기·전자',
                'pct': 40,
                'reason': '국내 대표 기업으로 안정적인 수익 구조와 글로벌 경쟁력을 보유하고 있습니다.'
            },
            {
                'code': '035420',
                'name': 'NAVER',
                'sector': 'IT 서비스',
                'pct': 30,
                'reason': '국내 최대 IT 기업으로 다양한 사업 포트폴리오와 성장 가능성을 갖추고 있습니다.'
            },
            {
                'code': '105560',
                'name': 'KB금융',
                'sector': '기타금융',
                'pct': 30,
                'reason': '금융 섹터의 대표 기업으로 안정적인 배당 수익을 기대할 수 있습니다.'
            }
        ]
        
        # 비율 조정
        scale = total_stock_pct / 100
        recommendations = []
        
        for stock in default_stocks:
            recommendations.append(StockRecommendation(
                stockId=stock['code'],
                stockName=stock['name'],
                allocationPct=int(stock['pct'] * scale),
                sectorName=stock['sector'],
                reason=stock['reason']
            ))
        
        return recommendations


# 전역 인스턴스
portfolio_recommendation_service = PortfolioRecommendationService()

