"""데이터 분석 서비스"""

from typing import Dict, Any


class AnalysisService:
    """금융 데이터 분석을 담당하는 서비스"""
    
    def __init__(self):
        pass
    
    def analyze_financial_data(self, data: Dict[str, Any]) -> str:
        """금융 데이터를 분석하여 인사이트 생성
        
        Args:
            data: 금융 데이터 딕셔너리
            
        Returns:
            str: 분석 결과 텍스트
        """
        try:
            if not data or "error" in data:
                return "분석할 데이터가 없습니다."
            
            analysis_parts = []
            
            # 가격 변화 분석
            price_change_percent = data.get('price_change_percent', 0)
            if price_change_percent > 0:
                analysis_parts.append(
                    f"📈 긍정적 신호: 전일 대비 {price_change_percent:.2f}% 상승"
                )
            else:
                analysis_parts.append(
                    f"📉 부정적 신호: 전일 대비 {price_change_percent:.2f}% 하락"
                )
            
            # 거래량 분석
            volume = data.get('volume', 0)
            if volume > 1000000:
                analysis_parts.append(
                    f"🔥 높은 관심도: 거래량 {volume:,}주 (평소 대비 높음)"
                )
            else:
                analysis_parts.append(f"📊 보통 거래량: {volume:,}주")
            
            # PER 분석
            pe_ratio = data.get('pe_ratio')
            if isinstance(pe_ratio, (int, float)):
                if pe_ratio < 15:
                    analysis_parts.append(
                        f"💰 저평가: PER {pe_ratio:.1f} (투자 매력도 높음)"
                    )
                elif pe_ratio > 25:
                    analysis_parts.append(
                        f"⚠️ 고평가: PER {pe_ratio:.1f} (투자 주의 필요)"
                    )
                else:
                    analysis_parts.append(f"📊 적정가: PER {pe_ratio:.1f}")
            
            # 섹터 정보
            sector = data.get('sector', 'Unknown')
            analysis_parts.append(f"🏢 섹터: {sector}")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            return f"분석 중 오류: {str(e)}"
    
    def get_investment_recommendation(self, data: Dict[str, Any]) -> str:
        """투자 추천 의견 생성
        
        Args:
            data: 금융 데이터 딕셔너리
            
        Returns:
            str: 투자 추천 의견
        """
        try:
            if not data or "error" in data:
                return "추천 의견을 생성할 수 없습니다."
            
            score = 0
            reasons = []
            
            # 가격 변화 점수
            price_change_percent = data.get('price_change_percent', 0)
            if price_change_percent > 3:
                score += 2
                reasons.append("강한 상승 추세")
            elif price_change_percent > 0:
                score += 1
                reasons.append("상승 추세")
            elif price_change_percent < -3:
                score -= 2
                reasons.append("하락 추세")
            elif price_change_percent < 0:
                score -= 1
                reasons.append("약한 하락")
            
            # PER 점수
            pe_ratio = data.get('pe_ratio')
            if isinstance(pe_ratio, (int, float)):
                if pe_ratio < 15:
                    score += 2
                    reasons.append("저평가 구간")
                elif pe_ratio < 20:
                    score += 1
                    reasons.append("적정 평가")
                elif pe_ratio > 30:
                    score -= 2
                    reasons.append("고평가 구간")
            
            # 거래량 점수
            volume = data.get('volume', 0)
            if volume > 1000000:
                score += 1
                reasons.append("높은 거래량")
            
            # 최종 추천
            if score >= 3:
                recommendation = "💚 매수 추천"
            elif score >= 1:
                recommendation = "💛 보유 추천"
            elif score >= -1:
                recommendation = "🤍 중립"
            else:
                recommendation = "💔 관망 추천"
            
            result = f"{recommendation}\n\n주요 근거:\n- " + "\n- ".join(reasons)
            result += "\n\n⚠️ 주의: 이는 참고 의견이며, 최종 투자 결정은 본인의 판단에 따라야 합니다."
            
            return result
            
        except Exception as e:
            return f"추천 의견 생성 중 오류: {str(e)}"


# 전역 서비스 인스턴스
analysis_service = AnalysisService()

