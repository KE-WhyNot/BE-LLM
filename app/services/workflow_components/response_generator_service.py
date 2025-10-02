"""응답 생성 서비스"""

from typing import Dict, Any, List
from app.utils.formatters import stock_data_formatter, news_formatter, analysis_formatter
from app.services.workflow_components.visualization_service import visualization_service


class ResponseGeneratorService:
    """최종 응답을 생성하는 서비스"""
    
    def __init__(self):
        pass
    
    def generate_data_response(self, financial_data: Dict[str, Any]) -> str:
        """주식 데이터 조회 응답 생성
        
        Args:
            financial_data: 금융 데이터
            
        Returns:
            str: 응답 텍스트
        """
        try:
            if not financial_data or "error" in financial_data:
                return """❌ 죄송합니다. 주식 데이터를 가져올 수 없습니다.

**가능한 원인:**
- 종목명 또는 종목 코드가 정확하지 않을 수 있습니다
- 해당 종목이 장 마감 후거나 거래가 없을 수 있습니다
- 네트워크 연결 문제가 발생했을 수 있습니다

**다시 시도해보세요:**
- 정확한 종목명 사용: "삼성전자", "SK하이닉스", "네이버" 등
- 종목 코드 사용: "005930.KS", "000660.KS" 등
"""
            
            symbol = financial_data.get('symbol', 'N/A')
            company_name = financial_data.get('company_name', 'N/A')
            
            # 기본 데이터 포맷팅
            response = stock_data_formatter.format_stock_data(financial_data, symbol)
            
            # 추가 인사이트 생성
            response += "\n\n" + self._generate_data_insights(financial_data, company_name)
            
            # 주의사항
            response += "\n\n" + self._get_investment_disclaimer()
            
            return response
            
        except Exception as e:
            return f"❌ 응답 생성 중 오류가 발생했습니다: {str(e)}\n\n다시 시도하거나 다른 종목으로 질문해주세요."
    
    def generate_analysis_response(self, financial_data: Dict[str, Any]) -> str:
        """주식 분석 응답 생성
        
        Args:
            financial_data: 금융 데이터
            
        Returns:
            str: 응답 텍스트
        """
        try:
            if not financial_data or "error" in financial_data:
                return """❌ 죄송합니다. 분석할 주식 데이터를 가져올 수 없습니다.

**가능한 원인:**
- 종목명이 정확하지 않거나 존재하지 않는 종목일 수 있습니다
- 해당 종목의 데이터가 일시적으로 제공되지 않을 수 있습니다

**해결 방법:**
1. 종목명을 정확하게 입력해주세요 (예: "삼성전자", "SK하이닉스")
2. 잠시 후 다시 시도해주세요
"""
            
            symbol = financial_data.get('symbol', 'N/A')
            company_name = financial_data.get('company_name', 'N/A')
            
            # 기본 분석 포맷팅
            response = analysis_formatter.format_stock_analysis(financial_data, symbol)
            
            # 상세 투자 분석 추가
            response += "\n\n" + self._generate_detailed_investment_analysis(financial_data, company_name)
            
            # 투자 주의사항
            response += "\n\n" + self._get_detailed_investment_disclaimer()
            
            return response
            
        except Exception as e:
            return f"❌ 응답 생성 중 오류가 발생했습니다: {str(e)}\n\n잠시 후 다시 시도해주세요."
    
    def generate_news_response(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 조회 응답 생성
        
        Args:
            news_data: 뉴스 리스트
            
        Returns:
            str: 응답 텍스트
        """
        try:
            if not news_data:
                return """📰 죄송합니다. 관련 뉴스를 찾을 수 없습니다.

**가능한 원인:**
- 해당 종목에 대한 최근 뉴스가 없을 수 있습니다
- 검색 키워드가 너무 구체적이거나 정확하지 않을 수 있습니다
- 일시적인 뉴스 피드 문제일 수 있습니다

**다시 시도해보세요:**
- 더 일반적인 키워드 사용: "삼성전자", "반도체", "한국 증시" 등
- 다른 종목이나 주제로 검색해보세요
- 잠시 후 다시 시도해주세요
"""
            
            # 뉴스 포맷팅
            response = news_formatter.format_news_list(news_data)
            
            # 뉴스 활용 팁 추가
            response += "\n\n" + self._get_news_usage_tips()
            
            return response
            
        except Exception as e:
            return f"❌ 뉴스 응답 생성 중 오류가 발생했습니다: {str(e)}\n\n잠시 후 다시 시도해주세요."
    
    def generate_knowledge_response(self, knowledge_context: str) -> str:
        """지식 검색 응답 생성
        
        Args:
            knowledge_context: 검색된 지식 컨텍스트
            
        Returns:
            str: 응답 텍스트
        """
        try:
            if not knowledge_context or not knowledge_context.strip():
                return """📚 죄송합니다. 관련 금융 지식을 찾을 수 없습니다.

**도움말:**
저희 챗봇은 다음과 같은 금융 지식에 대해 답변할 수 있습니다:

📊 **금융 용어:**
- PER, PBR, ROE 등 재무 지표
- 배당수익률, 시가총액 등

💼 **투자 전략:**
- 분산투자, 장기투자, 가치투자
- 리스크 관리 방법

📈 **시장 분석:**
- 기본적 분석 vs 기술적 분석
- KOSPI, KOSDAQ 이해하기

**예시 질문:**
- "PER이 뭐야?"
- "분산투자란 무엇인가요?"
- "ROE는 어떻게 계산하나요?"
- "기술적 분석이란?"
"""
            
            # 지식 컨텍스트 포맷팅
            response = f"📚 **금융 지식 검색 결과**\n\n{knowledge_context}"
            
            # 추가 학습 리소스 제안
            response += "\n\n" + self._get_learning_resources_tip()
            
            return response
            
        except Exception as e:
            return f"❌ 지식 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def generate_general_response(self) -> str:
        """일반적인 응답 생성
        
        Returns:
            str: 응답 텍스트
        """
        return """👋 **안녕하세요! 금융 전문가 AI 챗봇입니다.**

저는 다음과 같은 분야에서 도움을 드릴 수 있습니다:

📊 **1. 주식 정보 조회**
- 실시간 주가, 거래량, 시가총액 확인
- 예: "삼성전자 주가 알려줘", "SK하이닉스 현재가는?"

📈 **2. 투자 분석**
- 기술적/기본적 분석, PER/PBR 분석
- 투자 의견 및 매수/매도 추천
- 예: "네이버 투자해도 될까?", "카카오 분석해줘"

📰 **3. 금융 뉴스**
- 최신 시장 뉴스 및 종목별 뉴스
- 뉴스 영향도 분석 및 시장 전망
- 예: "삼성전자 뉴스 알려줘", "최근 반도체 뉴스는?"

📚 **4. 금융 지식**
- 금융 용어 설명, 투자 전략 안내
- 재무 지표 이해하기
- 예: "PER이 뭐야?", "분산투자란?", "ROE 설명해줘"

💡 **사용 팁:**
- 구체적인 종목명이나 질문을 해주시면 더 정확한 답변을 드립니다
- 궁금한 점이 있으시면 언제든지 물어보세요!

**무엇을 도와드릴까요?** 😊
"""
    
    def generate_visualization_response(self, query: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """시각화 응답 생성
        
        Args:
            query: 사용자 질문
            financial_data: 금융 데이터
            
        Returns:
            Dict: 차트 이미지와 설명을 포함한 응답
        """
        try:
            if not financial_data or "error" in financial_data:
                return {
                    "text": """❌ 죄송합니다. 차트를 생성할 데이터가 없습니다.

**가능한 원인:**
- 종목명이 정확하지 않을 수 있습니다
- 해당 종목의 데이터를 찾을 수 없습니다

**해결 방법:**
- 정확한 종목명으로 다시 시도해주세요 (예: "삼성전자 차트")
- 종목 코드로 시도해보세요 (예: "005930.KS 차트")
""",
                    "chart": None
                }
            
            # AI가 적절한 차트 타입 결정
            chart_type = visualization_service.determine_chart_type(query, financial_data)
            
            # 차트 생성
            chart_base64 = visualization_service.create_chart(chart_type, financial_data)
            
            # 차트 타입에 따른 설명 생성
            company_name = financial_data.get('company_name', 'Unknown')
            symbol = financial_data.get('symbol', 'Unknown')
            
            chart_descriptions = {
                'price_history': f"📈 {company_name} ({symbol})의 주가 추이 차트입니다.",
                'financial_metrics': f"📊 {company_name}의 주요 재무 지표(PER, PBR, ROE)를 한눈에 비교한 차트입니다.",
                'comparison': "📊 여러 종목의 성과를 비교한 차트입니다. (정규화: 시작일 = 100)",
                'candlestick': f"🕯️ {company_name}의 캔들스틱 차트입니다. 빨간색은 상승, 파란색은 하락을 나타냅니다.",
                'volume_analysis': f"📊 {company_name}의 주가와 거래량을 함께 분석한 차트입니다.",
            }
            
            description = chart_descriptions.get(chart_type, "📊 차트가 생성되었습니다.")
            
            return {
                "text": f"""{description}

**차트 활용 팁:**
• 주가 추이를 통해 상승/하락 패턴을 파악하세요
• 거래량이 늘어나면 관심도가 높다는 신호입니다
• 캔들스틱에서 연속된 빨간색/파란색은 추세를 나타냅니다

💡 **추가 요청:**
- "재무 지표 차트" - PER, PBR, ROE 비교
- "캔들 차트" - 캔들스틱 차트
- "거래량 분석" - 거래량 포함 차트
- "삼성전자 vs SK하이닉스" - 종목 비교
""",
                "chart": chart_base64,
                "chart_type": chart_type
            }
            
        except Exception as e:
            return {
                "text": f"❌ 차트 생성 중 오류가 발생했습니다: {str(e)}\n\n다시 시도하거나 다른 종목으로 질문해주세요.",
                "chart": None
            }
    
    def generate_error_response(self, error_message: str) -> str:
        """에러 응답 생성
        
        Args:
            error_message: 에러 메시지
            
        Returns:
            str: 응답 텍스트
        """
        return f"""❌ **죄송합니다. 오류가 발생했습니다.**

**오류 내용:** {error_message}

**해결 방법:**
1. 질문을 다시 한 번 확인해주세요
2. 종목명이나 키워드를 정확하게 입력했는지 확인해주세요
3. 잠시 후 다시 시도해주세요
4. 문제가 계속되면 다른 질문으로 시도해보세요

**도움이 필요하신가요?**
- "도움말" 또는 "사용법"을 입력하시면 사용 가능한 기능을 안내해드립니다.
"""
    
    # ===== 헬퍼 메서드 =====
    
    def _generate_data_insights(self, data: Dict[str, Any], company_name: str) -> str:
        """주식 데이터에 대한 추가 인사이트 생성"""
        insights = ["📊 **데이터 인사이트:**"]
        
        price_change_pct = data.get('price_change_percent', 0)
        volume = data.get('volume', 0)
        pe_ratio = data.get('pe_ratio', 'N/A')
        
        # 가격 변동 인사이트
        if price_change_pct > 5:
            insights.append(f"• {company_name}의 주가가 전일 대비 {price_change_pct:.2f}% 급등했습니다. 거래량과 뉴스를 확인해보세요.")
        elif price_change_pct > 2:
            insights.append(f"• {company_name}의 주가가 상승세를 보이고 있습니다 (+{price_change_pct:.2f}%).")
        elif price_change_pct < -5:
            insights.append(f"• {company_name}의 주가가 전일 대비 {abs(price_change_pct):.2f}% 급락했습니다. 시장 상황을 확인해보세요.")
        elif price_change_pct < -2:
            insights.append(f"• {company_name}의 주가가 하락세를 보이고 있습니다 ({price_change_pct:.2f}%).")
        else:
            insights.append(f"• {company_name}의 주가는 전일과 비슷한 수준을 유지하고 있습니다.")
        
        # 거래량 인사이트
        if volume > 10000000:
            insights.append(f"• 거래량이 {volume:,}주로 매우 활발합니다. 높은 시장 관심도를 보이고 있습니다.")
        elif volume > 5000000:
            insights.append(f"• 거래량이 {volume:,}주로 활발한 편입니다.")
        elif volume > 0:
            insights.append(f"• 거래량은 {volume:,}주입니다.")
        
        # PER 인사이트
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            if pe_ratio < 10:
                insights.append(f"• PER {pe_ratio:.2f}로 저평가 구간입니다. 가치투자 관점에서 매력적일 수 있습니다.")
            elif pe_ratio < 15:
                insights.append(f"• PER {pe_ratio:.2f}로 적정 수준입니다.")
            elif pe_ratio < 25:
                insights.append(f"• PER {pe_ratio:.2f}로 약간 높은 편이지만 성장성이 반영된 것일 수 있습니다.")
            else:
                insights.append(f"• PER {pe_ratio:.2f}로 고평가 구간입니다. 투자 시 신중한 판단이 필요합니다.")
        
        # PBR 인사이트
        pbr = data.get('pbr', 'N/A')
        if isinstance(pbr, (int, float)) and pbr > 0:
            if pbr < 1:
                insights.append(f"• PBR {pbr:.2f}로 순자산보다 주가가 낮습니다. 저평가 가능성이 있습니다.")
            elif pbr < 2:
                insights.append(f"• PBR {pbr:.2f}로 적정 수준입니다.")
            else:
                insights.append(f"• PBR {pbr:.2f}로 프리미엄이 반영되어 있습니다. 성장성에 대한 기대가 높습니다.")
        
        # ROE 인사이트
        roe = data.get('roe', 'Unknown')
        if isinstance(roe, (int, float)) and roe > 0:
            if roe > 20:
                insights.append(f"• ROE {roe:.2f}%로 매우 우수한 자본 효율성을 보이고 있습니다.")
            elif roe > 15:
                insights.append(f"• ROE {roe:.2f}%로 양호한 수준입니다.")
            elif roe > 10:
                insights.append(f"• ROE {roe:.2f}%로 보통 수준입니다.")
            else:
                insights.append(f"• ROE {roe:.2f}%로 자본 효율성 개선이 필요해 보입니다.")
        
        # 부채비율 인사이트
        debt_to_equity = data.get('debt_to_equity', 'Unknown')
        if isinstance(debt_to_equity, (int, float)):
            if debt_to_equity < 100:
                insights.append(f"• 부채비율 {debt_to_equity:.1f}%로 재무구조가 건전합니다.")
            elif debt_to_equity < 200:
                insights.append(f"• 부채비율 {debt_to_equity:.1f}%로 적정 수준입니다.")
            else:
                insights.append(f"• 부채비율 {debt_to_equity:.1f}%로 다소 높은 편입니다. 재무 안정성을 확인해보세요.")
        
        return "\n".join(insights)
    
    def _generate_detailed_investment_analysis(self, data: Dict[str, Any], company_name: str) -> str:
        """상세 투자 분석 생성"""
        analysis = ["💡 **상세 투자 분석:**"]
        
        price_change_pct = data.get('price_change_percent', 0)
        volume = data.get('volume', 0)
        pe_ratio = data.get('pe_ratio', 'N/A')
        pbr = data.get('pbr', 'N/A')
        roe = data.get('roe', 'Unknown')
        debt_to_equity = data.get('debt_to_equity', 'Unknown')
        sector = data.get('sector', 'Unknown')
        
        # 종합 투자 의견
        positive_signals = 0
        negative_signals = 0
        
        # 가격 변동 신호
        if price_change_pct > 2:
            positive_signals += 1
        elif price_change_pct < -2:
            negative_signals += 1
        
        # 거래량 신호
        if volume > 5000000:
            positive_signals += 1
        
        # PER 신호
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            if pe_ratio < 15:
                positive_signals += 1
            elif pe_ratio > 30:
                negative_signals += 1
        
        # PBR 신호
        if isinstance(pbr, (int, float)) and pbr > 0:
            if pbr < 1:
                positive_signals += 1
            elif pbr > 3:
                negative_signals += 1
        
        # ROE 신호
        if isinstance(roe, (int, float)) and roe > 0:
            if roe > 15:
                positive_signals += 1
            elif roe < 5:
                negative_signals += 1
        
        # 부채비율 신호
        if isinstance(debt_to_equity, (int, float)):
            if debt_to_equity < 100:
                positive_signals += 1
            elif debt_to_equity > 200:
                negative_signals += 1
        
        # 투자 의견 생성
        if positive_signals > negative_signals:
            analysis.append(f"• **종합 의견:** {company_name}는 현재 긍정적인 신호가 많습니다. 매수 관심을 가져볼 만합니다.")
        elif negative_signals > positive_signals:
            analysis.append(f"• **종합 의견:** {company_name}는 현재 부정적인 신호가 보입니다. 신중한 접근이 필요합니다.")
        else:
            analysis.append(f"• **종합 의견:** {company_name}는 현재 혼조세를 보이고 있습니다. 추가 정보 확인이 필요합니다.")
        
        # 섹터 정보
        if sector != 'Unknown':
            analysis.append(f"• **섹터:** {sector} - 해당 섹터의 전반적인 시장 동향도 함께 확인해보세요.")
        
        # 추가 확인 사항
        analysis.append("\n**투자 전 확인사항:**")
        analysis.append("• 최근 뉴스 및 공시사항 확인")
        analysis.append("• 경쟁사와의 비교 분석")
        analysis.append("• 업종 전체의 시장 동향")
        analysis.append("• 본인의 투자 목표 및 리스크 허용 수준")
        
        return "\n".join(analysis)
    
    def _get_investment_disclaimer(self) -> str:
        """투자 주의사항"""
        return """⚠️ **투자 주의사항:**
이 정보는 참고용이며, 투자 결정은 신중히 하시기 바랍니다.
과거 실적이 미래 수익을 보장하지 않으며, 투자에는 원금 손실 위험이 있습니다."""
    
    def _get_detailed_investment_disclaimer(self) -> str:
        """상세 투자 주의사항"""
        return """⚠️ **중요 고지사항:**

**이 분석은 참고용 정보입니다:**
- 실시간 데이터 및 기본적인 지표를 기반으로 한 분석입니다
- 전문적인 투자 자문이나 권유가 아닙니다
- 개별 투자자의 재무 상황을 고려하지 않았습니다

**투자 전 반드시 확인하세요:**
1. 본인의 투자 목표 및 리스크 허용 수준
2. 해당 기업의 재무제표 및 사업보고서
3. 최근 공시사항 및 뉴스
4. 전문가의 투자 의견 (필요 시)

**투자 책임은 본인에게 있습니다.** 신중한 판단 부탁드립니다."""
    
    def _get_news_usage_tips(self) -> str:
        """뉴스 활용 팁"""
        return """💡 **뉴스 활용 팁:**

**뉴스를 읽을 때 주의할 점:**
• 여러 뉴스 소스를 비교하여 객관적으로 판단하세요
• 뉴스의 발행 날짜와 시의성을 확인하세요
• 긍정적/부정적 뉴스가 주가에 미치는 영향은 단기적일 수 있습니다
• 루머와 확인된 정보를 구분하세요

**다음 단계:**
• 관심 종목의 공식 공시를 확인하세요
• 장기적인 관점에서 기업의 펀더멘털을 분석하세요
• 뉴스 기반 단기 매매는 고위험이므로 신중하세요"""
    
    def _get_learning_resources_tip(self) -> str:
        """학습 리소스 팁"""
        return """📖 **더 알아보기:**

**추가로 궁금한 점이 있으신가요?**
• 관련 용어나 개념에 대해 더 질문해주세요
• 실제 종목에 적용해보고 싶다면 종목명과 함께 질문해주세요
• "예시" 또는 "예제"를 요청하시면 구체적인 사례를 들어 설명해드립니다

**연관 질문 추천:**
• 다른 재무 지표에 대해서도 궁금하신가요?
• 실전 투자 전략에 대해 알아보시겠어요?
• 특정 시장이나 섹터에 대해 더 알고 싶으신가요?"""


# 전역 서비스 인스턴스
response_generator = ResponseGeneratorService()
