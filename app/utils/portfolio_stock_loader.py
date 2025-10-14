"""포트폴리오 주식 데이터 로더"""

import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path


class PortfolioStockLoader:
    """포트폴리오 추천용 주식 데이터 로더"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 기본 경로: config/portfolio_stocks.yaml
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "portfolio_stocks.yaml"
        
        self.config_path = Path(config_path)
        self.stocks_data: List[Dict[str, Any]] = []
        self._load_config()
    
    def _load_config(self):
        """YAML 파일에서 주식 데이터 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.stocks_data = data.get('stocks', [])
        except Exception as e:
            print(f"주식 데이터 로드 실패: {e}")
            self.stocks_data = []
    
    def get_stocks_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """섹터별 주식 목록 반환"""
        return [stock for stock in self.stocks_data if stock.get('sector') == sector]
    
    def get_stocks_by_sectors(self, sectors: List[str]) -> List[Dict[str, Any]]:
        """여러 섹터의 주식 목록 반환"""
        return [stock for stock in self.stocks_data if stock.get('sector') in sectors]
    
    def get_stock_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """종목 코드로 주식 정보 반환"""
        for stock in self.stocks_data:
            if stock.get('code') == code:
                return stock
        return None
    
    def get_stable_stocks(self, sector: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """안정적인 주식 목록 반환 (시가총액 상위 + 안정 특성)"""
        stable_stocks = []
        
        for stock in self.stocks_data:
            # 섹터 필터
            if sector and stock.get('sector') != sector:
                continue
            
            characteristics = stock.get('characteristics', [])
            # 안정 특성 또는 시가총액 상위 주식
            if '안정' in characteristics or '시가총액 상위' in characteristics:
                stable_stocks.append(stock)
        
        # 시가총액 기준 정렬
        stable_stocks.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        if limit:
            return stable_stocks[:limit]
        return stable_stocks
    
    def get_high_return_stocks(self, sector: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """고수익 주식 목록 반환 (고변동 특성)"""
        high_return_stocks = []
        
        for stock in self.stocks_data:
            # 섹터 필터
            if sector and stock.get('sector') != sector:
                continue
            
            characteristics = stock.get('characteristics', [])
            # 고변동 특성
            if '고변동' in characteristics:
                high_return_stocks.append(stock)
        
        # 시가총액 기준 정렬 (큰 것부터)
        high_return_stocks.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        if limit:
            return high_return_stocks[:limit]
        return high_return_stocks
    
    def get_dividend_stocks(self, sector: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """배당주 목록 반환"""
        dividend_stocks = []
        
        for stock in self.stocks_data:
            # 섹터 필터
            if sector and stock.get('sector') != sector:
                continue
            
            characteristics = stock.get('characteristics', [])
            # 배당주 특성
            if '배당주' in characteristics:
                dividend_stocks.append(stock)
        
        # 시가총액 기준 정렬
        dividend_stocks.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        if limit:
            return dividend_stocks[:limit]
        return dividend_stocks
    
    def get_all_sectors(self) -> List[str]:
        """모든 섹터 목록 반환"""
        sectors = set()
        for stock in self.stocks_data:
            sector = stock.get('sector')
            if sector:
                sectors.add(sector)
        return sorted(list(sectors))
    
    def classify_by_market_cap(self, market_cap: int) -> str:
        """시가총액 기준 기업 규모 분류 (기본)"""
        if market_cap >= 10_000_000_000_000:  # 10조 이상
            return "대기업"
        elif market_cap >= 1_000_000_000_000:  # 1조 이상
            return "중견기업"
        else:
            return "중소기업"
    
    def classify_stock_comprehensive(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """주식 특성을 종합적으로 분석하여 분류"""
        characteristics = stock.get('characteristics', [])
        market_cap = stock.get('market_cap', 0)
        
        # 기본 규모 분류
        size_by_cap = self.classify_by_market_cap(market_cap)
        
        # 특성 기반 조정
        stability_score = 0  # -2(매우 불안정) ~ +2(매우 안정)
        growth_potential = 0  # -2(저성장) ~ +2(고성장)
        
        if '시가총액 상위' in characteristics:
            stability_score += 1
            
        if '안정' in characteristics:
            stability_score += 2
            growth_potential -= 1  # 안정적이지만 성장성은 제한적
            
        if '고변동' in characteristics:
            stability_score -= 1
            growth_potential += 2  # 변동성 높지만 성장 가능성 큼
            
        if '배당주' in characteristics:
            stability_score += 1
            
        # 종합 등급 결정
        if stability_score >= 2:
            investment_grade = "안정형"
        elif stability_score >= 0:
            investment_grade = "균형형"  
        else:
            investment_grade = "성장형"
            
        # 위험도 평가
        if stability_score >= 1 and '고변동' not in characteristics:
            risk_level = "저위험"
        elif '고변동' in characteristics and stability_score < 0:
            risk_level = "고위험"
        else:
            risk_level = "중위험"
            
        return {
            "company_size": size_by_cap,
            "investment_grade": investment_grade,
            "risk_level": risk_level,
            "stability_score": stability_score,
            "growth_potential": growth_potential,
            "characteristics": characteristics,
            "recommended_for": self._get_recommended_profiles(investment_grade, risk_level)
        }
    
    def _get_recommended_profiles(self, investment_grade: str, risk_level: str) -> List[str]:
        """투자 등급과 위험도에 따른 추천 투자 성향"""
        if investment_grade == "안정형" and risk_level == "저위험":
            return ["안정형", "안정추구형"]
        elif investment_grade == "균형형" and risk_level == "중위험":
            return ["안정추구형", "위험중립형", "적극투자형"]
        elif investment_grade == "성장형" and risk_level == "고위험":
            return ["적극투자형", "공격투자형"]
        else:
            return ["위험중립형"]
    
    def get_stocks_by_company_size(
        self, 
        sector: str = None, 
        company_size: str = "대기업"
    ) -> List[Dict[str, Any]]:
        """기업 규모별 주식 목록 반환"""
        
        stocks = self.stocks_data if not sector else self.get_stocks_by_sector(sector)
        
        filtered_stocks = []
        for stock in stocks:
            stock_size = self.classify_by_market_cap(stock.get('market_cap', 0))
            if stock_size == company_size:
                filtered_stocks.append(stock)
        
        # 시가총액 기준 정렬
        filtered_stocks.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        return filtered_stocks
    
    def get_best_stocks_for_profile(
        self, 
        sector: str, 
        investment_profile: str,
        limit: int = 2,
        company_size_preference: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """투자 성향에 맞는 섹터별 최적 주식 선정 (종합 특성 분석 기반)"""
        
        sector_stocks = self.get_stocks_by_sector(sector)
        
        if not sector_stocks:
            return []
        
        # 각 주식을 종합 분석
        analyzed_stocks = []
        for stock in sector_stocks:
            analysis = self.classify_stock_comprehensive(stock)
            stock_with_analysis = stock.copy()
            stock_with_analysis['analysis'] = analysis
            analyzed_stocks.append(stock_with_analysis)
        
        # 투자 성향에 맞는 주식 필터링 및 점수 부여
        scored_stocks = []
        
        for stock in analyzed_stocks:
            analysis = stock['analysis']
            recommended_profiles = analysis['recommended_for']
            
            # 기본 매칭 점수
            if investment_profile in recommended_profiles:
                base_score = 3
            elif self._is_compatible_profile(investment_profile, recommended_profiles):
                base_score = 2
            else:
                base_score = 1
            
            # 특성별 추가 점수
            characteristics = analysis['characteristics']
            
            # 투자 성향별 특성 선호도 반영
            preference_bonus = 0
            if investment_profile in ["안정형", "안정추구형"]:
                if '안정' in characteristics:
                    preference_bonus += 2
                if '배당주' in characteristics:
                    preference_bonus += 1
                if '고변동' in characteristics:
                    preference_bonus -= 1
                    
            elif investment_profile in ["적극투자형", "공격투자형"]:
                if '고변동' in characteristics:
                    preference_bonus += 2
                if '시가총액 상위' in characteristics:
                    preference_bonus += 1
                if analysis['growth_potential'] > 0:
                    preference_bonus += 1
                    
            else:  # 위험중립형
                if '시가총액 상위' in characteristics:
                    preference_bonus += 1
                if '배당주' in characteristics:
                    preference_bonus += 1
            
            # 시가총액 점수 (안정성 반영)
            market_cap_score = min(2, stock.get('market_cap', 0) / 10_000_000_000_000)
            
            final_score = base_score + preference_bonus + market_cap_score
            
            scored_stocks.append({
                'stock': stock,
                'score': final_score,
                'analysis': analysis
            })
        
        # 점수 기준 정렬
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        # 기업 규모 선호도 추가 적용
        if company_size_preference:
            scored_stocks = self._apply_size_preference_to_scored_stocks(
                scored_stocks, 
                company_size_preference
            )
        
        return [item['stock'] for item in scored_stocks[:limit]]
    
    def _is_compatible_profile(self, user_profile: str, recommended_profiles: List[str]) -> bool:
        """투자 성향 호환성 확인"""
        profile_compatibility = {
            "안정형": ["안정추구형"],
            "안정추구형": ["안정형", "위험중립형"],
            "위험중립형": ["안정추구형", "적극투자형"],
            "적극투자형": ["위험중립형", "공격투자형"],
            "공격투자형": ["적극투자형"]
        }
        
        compatible = profile_compatibility.get(user_profile, [])
        return any(profile in recommended_profiles for profile in compatible)
    
    def _apply_size_preference_to_scored_stocks(
        self, 
        scored_stocks: List[Dict[str, Any]], 
        size_preference: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """점수 기반 주식에 기업 규모 선호도 적용"""
        
        for item in scored_stocks:
            company_size = item['analysis']['company_size']
            preference_multiplier = size_preference.get(company_size, 1.0)
            item['score'] *= preference_multiplier
        
        # 점수 재정렬
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        return scored_stocks
    
    def _apply_company_size_preference(
        self, 
        stocks: List[Dict[str, Any]], 
        size_preference: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """기업 규모 선호도를 적용하여 주식 필터링"""
        
        # 각 주식에 점수 부여
        scored_stocks = []
        
        for stock in stocks:
            company_size = self.classify_by_market_cap(stock.get('market_cap', 0))
            preference_score = size_preference.get(company_size, 0.5)
            
            # 기본 점수 + 선호도 가중치
            base_score = stock.get('market_cap', 0) / 1_000_000_000_000  # 조 단위로 정규화
            final_score = base_score * preference_score
            
            scored_stocks.append({
                'stock': stock,
                'score': final_score,
                'company_size': company_size
            })
        
        # 점수 기준 정렬
        scored_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['stock'] for item in scored_stocks]
    
    def reload_config(self):
        """설정 파일 재로드"""
        self._load_config()


# 전역 인스턴스
portfolio_stock_loader = PortfolioStockLoader()

