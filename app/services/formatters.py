"""
공용 포맷터 모듈
financial_agent에서 추출한 유용한 포맷팅 로직들을 공용으로 사용
"""

from typing import Dict, Any, List


class FinancialDataFormatter:
    """금융 데이터 포맷터"""
    
    @staticmethod
    def format_stock_data(data: Dict[str, Any], symbol: str = "") -> str:
        """주식 데이터를 포맷팅"""
        if "error" in data:
            return f"오류: {data['error']}"
        
        return f"""
주식 정보 ({data['company_name']} - {symbol}):
- 현재가: {data['current_price']:,}원
- 전일대비: {data['price_change']:+,}원 ({data['price_change_percent']:+.2f}%)
- 거래량: {data['volume']:,}주
- 고가: {data['high']:,}원
- 저가: {data['low']:,}원
- 시가: {data['open']:,}원
- 시가총액: {data['market_cap']:,}원
- PER: {data['pe_ratio']}
- 배당수익률: {data['dividend_yield']}
- 섹터: {data['sector']}
- 조회시간: {data['timestamp']}
        """


class NewsFormatter:
    """뉴스 포맷터"""
    
    @staticmethod
    def format_news_list(news_list: List[Dict[str, Any]]) -> str:
        """뉴스 리스트를 포맷팅"""
        if not news_list:
            return "관련 뉴스를 찾을 수 없습니다."
        
        news_text = "📰 최신 뉴스 요약:\n\n"
        overall_sentiment = 0
        total_impact = 0
        positive_count = 0
        negative_count = 0
        
        for i, article in enumerate(news_list, 1):
            news_text += f"{i}. **{article['title']}**\n"
            news_text += f"   📝 {article['summary']}\n"
            news_text += f"   📅 {article['published']}\n"
            news_text += f"   🔗 {article['url']}\n"
            
            # 영향도 분석 정보 추가
            if 'impact_analysis' in article:
                impact = article['impact_analysis']
                news_text += f"   📊 영향도: {impact['impact_direction']} ({impact['impact_score']}점)\n"
                news_text += f"   🎯 시장 영향: {impact['market_impact']}\n"
                
                # 전체 감정 분석을 위한 데이터 수집
                if impact['impact_direction'] == '긍정적':
                    positive_count += 1
                    overall_sentiment += impact['impact_score']
                elif impact['impact_direction'] == '부정적':
                    negative_count += 1
                    overall_sentiment -= impact['impact_score']
                
                total_impact += impact['impact_score']
            
            news_text += "\n"
        
        # 전체 뉴스 분석 및 인사이트 생성
        news_text += "🔍 **뉴스 분석 및 시장 전망:**\n"
        
        # 전체 감정 분석
        if positive_count > negative_count:
            overall_sentiment_text = "긍정적"
            sentiment_emoji = "📈"
        elif negative_count > positive_count:
            overall_sentiment_text = "부정적"
            sentiment_emoji = "📉"
        else:
            overall_sentiment_text = "중립적"
            sentiment_emoji = "➡️"
        
        avg_impact = total_impact / len(news_list) if news_list else 0
        
        news_text += f"• {sentiment_emoji} **전체 시장 감정**: {overall_sentiment_text}\n"
        news_text += f"• 📊 **평균 영향도**: {avg_impact:.1f}점\n"
        news_text += f"• 📈 **긍정적 뉴스**: {positive_count}개\n"
        news_text += f"• 📉 **부정적 뉴스**: {negative_count}개\n\n"
        
        # 투자 인사이트 생성
        news_text += "💡 **투자 인사이트:**\n"
        if overall_sentiment_text == "긍정적":
            if avg_impact >= 70:
                news_text += "• 강한 긍정적 신호로 주가 상승 가능성 높음\n"
                news_text += "• 단기적으로 매수 관심 증가 예상\n"
            else:
                news_text += "• 중간 정도의 긍정적 영향으로 주가에 부분적 상승 기대\n"
        elif overall_sentiment_text == "부정적":
            if avg_impact >= 70:
                news_text += "• 강한 부정적 신호로 주가 하락 위험 높음\n"
                news_text += "• 단기적으로 매도 압력 증가 예상\n"
            else:
                news_text += "• 중간 정도의 부정적 영향으로 주가에 부분적 하락 기대\n"
        else:
            news_text += "• 중립적 뉴스로 주가에 큰 영향 없을 것으로 예상\n"
        
        news_text += "• 투자 결정 시 다른 시장 요인들도 함께 고려 필요\n"
        news_text += "• 단일 뉴스에 의존한 투자보다는 종합적 분석 권장\n"
        
        return news_text


class AnalysisFormatter:
    """분석 포맷터"""
    
    @staticmethod
    def format_stock_analysis(data: Dict[str, Any], symbol: str = "") -> str:
        """주식 분석 결과를 포맷팅"""
        if "error" in data:
            return f"오류: {data['error']}"
        
        # 기본 분석
        analysis = []
        
        # 가격 변화 분석
        if data['price_change_percent'] > 5:
            analysis.append("• 강한 상승세를 보이고 있습니다.")
        elif data['price_change_percent'] > 0:
            analysis.append("• 소폭 상승세를 보이고 있습니다.")
        elif data['price_change_percent'] < -5:
            analysis.append("• 강한 하락세를 보이고 있습니다.")
        elif data['price_change_percent'] < 0:
            analysis.append("• 소폭 하락세를 보이고 있습니다.")
        else:
            analysis.append("• 가격이 안정적입니다.")
        
        # 거래량 분석
        if data['volume'] > 1000000:  # 100만주 이상
            analysis.append("• 거래량이 활발합니다.")
        else:
            analysis.append("• 거래량이 평범한 수준입니다.")
        
        # PER 분석
        if isinstance(data['pe_ratio'], (int, float)) and data['pe_ratio'] > 0:
            if data['pe_ratio'] < 15:
                analysis.append("• PER이 낮아 상대적으로 저평가된 상태입니다.")
            elif data['pe_ratio'] > 30:
                analysis.append("• PER이 높아 상대적으로 고평가된 상태일 수 있습니다.")
            else:
                analysis.append("• PER이 적정 수준입니다.")
        
        return f"""
📊 **{data['company_name']} ({symbol}) 분석 결과**

**기본 정보:**
- 현재가: {data['current_price']:,}원
- 전일대비: {data['price_change']:+,}원 ({data['price_change_percent']:+.2f}%)
- 거래량: {data['volume']:,}주
- 시가총액: {data['market_cap']:,}원

**분석 결과:**
{chr(10).join(analysis)}

**투자 고려사항:**
• 기술적 분석과 기본적 분석을 함께 고려하세요
• 시장 상황과 업종 동향을 파악하세요
• 리스크 관리와 분산투자를 권장합니다
        """


# 전역 포맷터 인스턴스들
stock_data_formatter = FinancialDataFormatter()
news_formatter = NewsFormatter()
analysis_formatter = AnalysisFormatter()

