"""
개인화된 투자 포트폴리오 제안 서비스
사용자 프로필과 시장 데이터를 종합하여 맞춤형 자산 배분 및 투자 포트폴리오를 제안
"""

from typing import Dict, Any, List
import json
from datetime import datetime

class PortfolioAdvisor:
    """개인화된 투자 포트폴리오 제안 서비스"""
    
    def __init__(self):
        # 투자 유형별 자산 배분 규칙 (엄격히 준수)
        self.asset_allocation_rules = {
            "안정형": {"예적금": 80, "투자": 20},
            "안정추구형": {"예적금": 60, "투자": 40},
            "위험중립형": {"예적금": 50, "투자": 50},
            "적극투자형": {"예적금": 30, "투자": 70},
            "공격투자형": {"예적금": 20, "투자": 80}
        }
        
        # 섹터별 위험도 분류
        self.sector_risk_levels = {
            "고위험": ["반도체", "AI", "바이오", "게임", "암호화폐", "2차전지"],
            "중위험": ["신재생에너지", "로봇", "우주항공", "항공주"],
            "저위험": ["은행", "보험", "통신", "유틸리티", "소비재"]
        }
        
        # 기본 포트폴리오 템플릿 (분산투자용)
        self.default_sectors = ["반도체", "AI", "2차전지", "은행", "항공주"]
    
    def analyze_portfolio(self, user_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 프로필과 시장 데이터를 분석하여 개인화된 포트폴리오 제안
        
        Args:
            user_data: 사용자 개인 프로필
            market_data: 실시간 시장 데이터
            
        Returns:
            포트폴리오 제안 결과 (JSON 형식)
        """
        try:
            # 1단계: 총자본 배분
            asset_allocation = self._calculate_asset_allocation(user_data)
            
            # 2단계: 투자 포트폴리오 구성
            investment_portfolio = self._calculate_investment_portfolio(user_data, market_data)
            
            # 3단계: 근거 생성
            rationale = self._generate_rationale(user_data, market_data, asset_allocation, investment_portfolio)
            
            return {
                "assetAllocation": {
                    "labels": ["예적금", "투자"],
                    "proportions": [asset_allocation["예적금"], asset_allocation["투자"]]
                },
                "investmentPortfolio": {
                    "labels": investment_portfolio["labels"],
                    "proportions": investment_portfolio["proportions"]
                },
                "rationale": rationale
            }
            
        except Exception as e:
            return {
                "error": f"포트폴리오 분석 중 오류 발생: {str(e)}"
            }
    
    def _calculate_asset_allocation(self, user_data: Dict[str, Any]) -> Dict[str, int]:
        """1단계: 총자본 배분 계산 (엄격한 규칙 적용)"""
        investment_type = user_data.get("investment_type", "위험중립형")
        
        # 투자 유형에 따른 배분 비율 가져오기 (엄격히 준수)
        allocation_ratio = self.asset_allocation_rules.get(investment_type, self.asset_allocation_rules["위험중립형"])
        
        return {
            "예적금": allocation_ratio["예적금"],
            "투자": allocation_ratio["투자"]
        }
    
    def _calculate_investment_portfolio(self, user_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """2단계: 투자 포트폴리오 구성 (최소 3개 섹터, 분산투자)"""
        investment_type = user_data.get("investment_type", "위험중립형")
        interested_sectors = user_data.get("interested_sectors", [])
        sector_outlook = market_data.get("sector_outlook", {})
        
        # 사용자 관심 섹터 우선 고려
        portfolio_sectors = interested_sectors.copy()
        
        # 시장 전망이 좋은 섹터 추가 (사용자 관심사가 아닌 경우)
        positive_sectors = []
        for sector, outlook in sector_outlook.items():
            if sector not in portfolio_sectors and self._is_positive_outlook(outlook):
                positive_sectors.append(sector)
        
        # 분산 투자를 위한 추가 섹터 선택 (최소 3개 보장)
        if len(portfolio_sectors) < 3:
            # 기본 섹터에서 추가
            for sector in self.default_sectors:
                if sector not in portfolio_sectors and len(portfolio_sectors) < 5:
                    portfolio_sectors.append(sector)
        
        # 최대 5개 섹터로 제한
        portfolio_sectors = portfolio_sectors[:5]
        
        # 비율 계산
        proportions = self._calculate_sector_proportions(
            portfolio_sectors, investment_type, sector_outlook, interested_sectors
        )
        
        return {
            "labels": portfolio_sectors,
            "proportions": proportions
        }
    
    def _calculate_sector_proportions(self, sectors: List[str], investment_type: str, 
                                    sector_outlook: Dict[str, str], interested_sectors: List[str]) -> List[int]:
        """섹터별 투자 비율 계산 (분산투자 + 위험관리)"""
        if not sectors:
            return []
        
        # 기본 비율 (균등 분배)
        base_proportion = 100 // len(sectors)
        proportions = [base_proportion] * len(sectors)
        
        # 사용자 관심사 가중치 적용
        for i, sector in enumerate(sectors):
            if sector in interested_sectors:
                proportions[i] += 15  # 관심사 +15%
        
        # 시장 전망에 따른 조정
        for i, sector in enumerate(sectors):
            outlook = sector_outlook.get(sector, "")
            if self._is_positive_outlook(outlook):
                proportions[i] += 10  # 긍정적 전망 +10%
            elif self._is_negative_outlook(outlook):
                proportions[i] -= 10  # 부정적 전망 -10%
        
        # 투자 유형에 따른 위험도 조정
        if investment_type in ["안정형", "안정추구형"]:
            for i, sector in enumerate(sectors):
                if sector in self.sector_risk_levels["고위험"]:
                    proportions[i] -= 15  # 고위험 섹터 비중 감소
                elif sector in self.sector_risk_levels["저위험"]:
                    proportions[i] += 10   # 저위험 섹터 비중 증가
        
        # 비율 정규화 (총합이 100이 되도록)
        total = sum(proportions)
        if total > 0:
            proportions = [max(5, int(p * 100 / total)) for p in proportions]  # 최소 5% 보장
        
        # 총합이 100이 되도록 조정
        current_total = sum(proportions)
        if current_total != 100:
            diff = 100 - current_total
            if diff > 0:
                # 가장 큰 비중에 차이만큼 추가
                max_idx = proportions.index(max(proportions))
                proportions[max_idx] += diff
            else:
                # 가장 작은 비중에서 차이만큼 차감
                min_idx = proportions.index(min(proportions))
                proportions[min_idx] = max(5, proportions[min_idx] + diff)
        
        return proportions
    
    def _is_positive_outlook(self, outlook: str) -> bool:
        """시장 전망이 긍정적인지 판단"""
        positive_keywords = ["긍정", "상승", "성장", "개선", "호재", "증가", "확대", "기대", "회복", "안정"]
        return any(keyword in outlook for keyword in positive_keywords)
    
    def _is_negative_outlook(self, outlook: str) -> bool:
        """시장 전망이 부정적인지 판단"""
        negative_keywords = ["부정", "하락", "위험", "악재", "악화", "감소", "축소", "우려", "둔화", "변동성"]
        return any(keyword in outlook for keyword in negative_keywords)
    
    def _generate_rationale(self, user_data: Dict[str, Any], market_data: Dict[str, Any], 
                          asset_allocation: Dict[str, int], investment_portfolio: Dict[str, Any]) -> str:
        """3단계: 포트폴리오 근거 생성 (전문가 조언 스타일)"""
        investment_type = user_data.get("investment_type", "위험중립형")
        age = user_data.get("age", 30)
        investment_purpose = user_data.get("investment_purpose", "")
        interested_sectors = user_data.get("interested_sectors", [])
        market_summary = market_data.get("market_summary", "")
        sector_outlook = market_data.get("sector_outlook", {})
        
        rationale_parts = []
        
        # 1단계 근거 (자산 배분)
        rationale_parts.append(f"{investment_type} 성향과 {age}세의 나이, '{investment_purpose}' 목적을 고려하여, ")
        rationale_parts.append(f"안정적인 예적금 비중을 {asset_allocation['예적금']}%로, ")
        rationale_parts.append(f"성장 가능성이 높은 투자 비중을 {asset_allocation['투자']}%로 설정했습니다. ")
        
        # 2단계 근거 (투자 포트폴리오)
        rationale_parts.append("투자 포트폴리오는 ")
        
        # 사용자 관심사 반영
        if interested_sectors:
            rationale_parts.append(f"귀하의 관심 섹터인 {', '.join(interested_sectors)}를 중심으로 ")
        
        # 시장 상황 반영
        rationale_parts.append("현재 시장 상황을 종합적으로 분석하여 구성했습니다. ")
        
        # 구체적인 섹터별 근거
        for i, (sector, proportion) in enumerate(zip(investment_portfolio["labels"], investment_portfolio["proportions"])):
            outlook = sector_outlook.get(sector, "")
            if outlook:
                rationale_parts.append(f"{sector} 섹터는 {outlook} ")
                rationale_parts.append(f"따라서 {proportion}%의 비중을 할당했습니다. ")
            else:
                rationale_parts.append(f"{sector} 섹터는 {proportion}%의 비중으로 ")
                rationale_parts.append("분산투자 효과를 극대화하도록 구성했습니다. ")
        
        # 시장 전망 인용
        if market_summary:
            rationale_parts.append(f"현재 시장 상황은 '{market_summary}' ")
            rationale_parts.append("이러한 환경에서 위험을 분산하면서도 성장 가능성을 확보하는 포트폴리오를 제안합니다.")
        
        return "".join(rationale_parts)

# 전역 인스턴스
portfolio_advisor = PortfolioAdvisor()
