"""응답 생성 서비스 (동적 프롬프팅 지원)"""

from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.utils.formatters import stock_data_formatter, news_formatter, analysis_formatter
from app.services.workflow_components.visualization_service import visualization_service
# prompt_manager는 agents/에서 개별 관리


class ResponseGeneratorService:
    """최종 응답을 생성하는 서비스 (동적 프롬프팅)"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화 (최적화된 파라미터)"""
        # 최적화된 LLM 매니저 사용
        from app.services.langgraph_enhanced.llm_manager import get_gemini_llm
        
        if settings.google_api_key:
            return get_gemini_llm(purpose="response")
        return None
    
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
    
    def generate_knowledge_response(self, knowledge_context: str, user_query: str = "") -> str:
        """지식 검색 응답 생성 - LLM을 사용하여 컨텍스트 기반 답변 생성
        
        Args:
            knowledge_context: 검색된 지식 컨텍스트
            user_query: 사용자 질문
            
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
            
            # LLM을 사용하여 컨텍스트 기반 답변 생성
            if user_query and self.llm:
                prompt = f"""당신은 금융 전문가입니다. 사용자의 질문에 대해 제공된 컨텍스트를 바탕으로 명확하고 이해하기 쉽게 설명해주세요.

사용자 질문: {user_query}

참고 자료:
{knowledge_context}

위 참고 자료를 바탕으로 사용자의 질문에 답변해주세요. 다음 형식을 따라주세요:

1. **용어/개념 정의**: 핵심 개념을 명확하게 설명
2. **구체적 예시**: 실생활이나 투자에서의 활용 예시
3. **추가 팁**: 관련된 유용한 정보나 주의사항

답변은 친절하고 이해하기 쉽게 작성하되, 전문성을 유지해주세요.
"""
                
                try:
                    llm_response = self.llm.invoke(prompt)
                    return f"📚 **금융 지식 답변**\n\n{llm_response.content}"
                except Exception as e:
                    print(f"⚠️ LLM 응답 생성 실패, 폴백 사용: {e}")
                    # LLM 실패 시 폴백: 컨텍스트 직접 반환
                    return f"📚 **금융 지식 검색 결과**\n\n{knowledge_context[:1000]}"
            
            # user_query가 없거나 LLM이 없으면 컨텍스트 직접 반환
            response = f"📚 **금융 지식 검색 결과**\n\n{knowledge_context[:1000]}"
            
            # 추가 학습 리소스 제안
            response += "\n\n" + self._get_learning_resources_tip()
            
            return response
            
        except Exception as e:
            return f"❌ 지식 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def generate_general_response(self, user_query: str = "", rag_context: str = "") -> str:
        """일반적인 응답 생성 - RAG 컨텍스트가 있으면 활용
        
        Args:
            user_query: 사용자 질문
            rag_context: Pinecone RAG 검색 결과 컨텍스트
            
        Returns:
            str: 응답 텍스트
        """
        # RAG 컨텍스트가 있고 사용자 질문이 있으면 LLM을 사용한 답변 생성
        if user_query and rag_context and rag_context.strip() and self.llm:
            try:
                prompt = f"""당신은 친절한 금융 전문가 AI 어시스턴트입니다. 사용자의 질문에 대해 제공된 참고 자료를 활용하여 도움이 되는 답변을 생성해주세요.

사용자 질문: {user_query}

참고 자료:
{rag_context}

위 참고 자료가 질문과 관련이 있다면 이를 바탕으로 답변하고, 관련이 없다면 일반적인 금융 지식으로 답변해주세요.

답변 형식:
- 질문에 직접적으로 답변
- 필요시 추가 설명이나 예시 제공
- 더 구체적인 질문을 유도하는 팁 제공

답변은 친절하고 이해하기 쉽게 작성해주세요.
"""
                
                llm_response = self.llm.invoke(prompt)
                return llm_response.content
                
            except Exception as e:
                print(f"⚠️ General 응답 LLM 생성 실패: {e}")
                # LLM 실패 시 기본 응답
                pass
        
        # 기본 응답 (RAG 컨텍스트가 없거나 LLM이 없을 때)
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
    
    async def generate_news_analysis_response(self, news_data: List[Dict[str, Any]], user_query: str, news_query_used: str = None) -> str:
        """뉴스 분석 응답 생성 (특히 오늘 하루 뉴스 분석용)
        
        Args:
            news_data: 뉴스 데이터 리스트
            user_query: 사용자 원본 쿼리
            news_query_used: 실제 사용된 뉴스 검색 쿼리
            
        Returns:
            str: 분석된 뉴스 응답
        """
        try:
            if not news_data:
                return "📰 죄송합니다. 관련 뉴스를 찾을 수 없습니다.\n\n**다시 시도해보세요:**\n- 더 일반적인 키워드 사용: \"삼성전자\", \"반도체\", \"한국 증시\" 등\n- 다른 종목이나 주제로 검색해보세요\n- 잠시 후 다시 시도해주세요"
            
            # 오늘 하루 뉴스 분석인지 확인
            is_today_analysis = news_query_used == "오늘 하루 시장 뉴스" or "오늘" in user_query or "하루" in user_query
            
            if is_today_analysis:
                return await self._generate_today_market_analysis(news_data)
            else:
                return await self._generate_specific_news_analysis(news_data, user_query)
                
        except Exception as e:
            print(f"❌ 뉴스 분석 응답 생성 중 오류: {e}")
            return f"📰 뉴스 분석 중 오류가 발생했습니다: {str(e)}"
    
    async def _generate_today_market_analysis(self, news_data: List[Dict[str, Any]]) -> str:
        """오늘 하루 시장 뉴스 종합 분석 생성"""
        try:
            # LLM을 사용한 종합 분석
            if self.llm:
                news_summary = "\n".join([
                    f"{i+1}. {news['title']}\n   {news.get('summary', news.get('description', ''))[:100]}..."
                    for i, news in enumerate(news_data[:8])  # 상위 8개만 사용
                ])
                
                prompt = f"""당신은 전문 금융 애널리스트입니다. 오늘 하루의 주요 시장 뉴스들을 분석하여 종합적인 시장 동향을 제공해주세요.

## 📰 오늘의 주요 뉴스들
{news_summary}

## 📊 분석 요청사항
다음 관점에서 종합 분석을 제공해주세요:

1. **🎯 주요 이슈**: 오늘 가장 주목할 만한 이슈 3가지
2. **📈 시장 영향**: 각 이슈가 주식시장에 미칠 영향
3. **🏢 섹터별 동향**: 주요 섹터(반도체, 자동차, 바이오 등)별 동향
4. **💡 투자 인사이트**: 투자자 관점에서의 해석 및 조언
5. **⚠️ 주의사항**: 투자 시 주의해야 할 리스크 요소

## 📝 응답 형식
**📅 오늘의 시장 분석 (2025년 1월 7일)**

### 🎯 주요 이슈
• 이슈 1: [내용]
• 이슈 2: [내용]  
• 이슈 3: [내용]

### 📈 시장 영향
• 긍정적 요인: [내용]
• 부정적 요인: [내용]

### 🏢 섹터별 동향
• 반도체: [내용]
• 자동차: [내용]
• 바이오: [내용]

### 💡 투자 인사이트
[종합적인 투자 관점에서의 해석]

### ⚠️ 주의사항
[투자 시 주의할 점들]

**면책조항**: 이 분석은 참고용이며, 투자 권유가 아닙니다. 투자 결정은 신중히 하시기 바랍니다."""

                response = self.llm.invoke(prompt)
                return response.content
            else:
                # LLM이 없는 경우 기본 분석
                return self._generate_basic_news_summary(news_data, is_today_analysis=True)
                
        except Exception as e:
            print(f"❌ 오늘 시장 분석 생성 중 오류: {e}")
            return self._generate_basic_news_summary(news_data, is_today_analysis=True)
    
    async def _generate_specific_news_analysis(self, news_data: List[Dict[str, Any]], user_query: str) -> str:
        """특정 주제 뉴스 분석 생성"""
        try:
            if self.llm:
                news_summary = "\n".join([
                    f"{i+1}. {news['title']}\n   {news.get('summary', news.get('description', ''))[:150]}..."
                    for i, news in enumerate(news_data[:5])
                ])
                
                prompt = f"""당신은 전문 금융 애널리스트입니다. "{user_query}"에 대한 최신 뉴스들을 분석하여 상세한 분석을 제공해주세요.

## 📰 관련 뉴스들
{news_summary}

## 📊 분석 요청사항
다음 관점에서 분석을 제공해주세요:

1. **📈 핵심 내용**: 주요 뉴스 내용 요약
2. **💼 기업/섹터 영향**: 관련 기업이나 섹터에 미치는 영향
3. **📊 투자 관점**: 투자자 관점에서의 해석
4. **🔮 전망**: 향후 전망 및 시사점

## 📝 응답 형식
**📰 {user_query} 관련 뉴스 분석**

### 📈 핵심 내용
[주요 뉴스 내용 요약]

### 💼 기업/섹터 영향  
[관련 기업이나 섹터에 미치는 영향]

### 📊 투자 관점
[투자자 관점에서의 해석]

### 🔮 전망
[향후 전망 및 시사점]

**면책조항**: 이 분석은 참고용이며, 투자 권유가 아닙니다."""

                response = self.llm.invoke(prompt)
                return response.content
            else:
                return self._generate_basic_news_summary(news_data, is_today_analysis=False)
                
        except Exception as e:
            print(f"❌ 특정 뉴스 분석 생성 중 오류: {e}")
            return self._generate_basic_news_summary(news_data, is_today_analysis=False)
    
    def _generate_basic_news_summary(self, news_data: List[Dict[str, Any]], is_today_analysis: bool = False) -> str:
        """기본 뉴스 요약 생성 (LLM 없을 때)"""
        if is_today_analysis:
            title = "📅 오늘의 주요 시장 뉴스"
        else:
            title = "📰 관련 뉴스"
        
        response = f"{title}\n\n"
        
        for i, news in enumerate(news_data[:5], 1):
            response += f"**{i}. {news['title']}**\n"
            if news.get('summary'):
                response += f"{news['summary'][:200]}...\n"
            elif news.get('description'):
                response += f"{news['description'][:200]}...\n"
            if news.get('url'):
                response += f"🔗 [원문 보기]({news['url']})\n"
            response += "\n"
        
        return response

    async def generate_response(self, state: Dict[str, Any]) -> str:
        """통합 응답 생성 (동적 워크플로우용)
        
        Args:
            state: 워크플로우 상태 딕셔너리
            
        Returns:
            str: 최종 응답 텍스트
        """
        try:
            query_type = state.get("query_type", "general")
            user_query = state.get("user_query", "")
            
            # 쿼리 타입에 따른 응답 생성
            if query_type in ["visualization", "contextual_visualization"]:
                response = self._generate_visualization_response(state)
            elif query_type in ["analysis", "detailed_analysis", "guided_analysis"]:
                response = self._generate_analysis_response(state)
            elif query_type in ["news", "contextual_news"]:
                response = await self._generate_news_response(state)
            elif query_type in ["knowledge", "contextual_knowledge"]:
                response = self._generate_knowledge_response(state)
            elif query_type in ["data", "data_optimized"]:
                response = self._generate_data_response(state.get("financial_data", {}))
            else:
                response = self._generate_general_response(state)
            
            return response
            
        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _generate_visualization_response(self, state: Dict[str, Any]) -> str:
        """시각화 응답 생성"""
        financial_data = state.get("financial_data", {})
        chart_data = state.get("chart_data", {})
        
        if not financial_data:
            return "❌ 차트를 생성할 데이터가 없습니다."
        
        # 기본 주가 정보
        response = self.generate_data_response(financial_data)
        
        # 차트 정보 추가
        if chart_data:
            response += "\n\n📊 **차트 정보:**"
            response += "\n• 캔들스틱 차트와 거래량이 함께 표시됩니다"
            response += "\n• 상단: 가격 변동 (빨간색: 상승, 파란색: 하락)"
            response += "\n• 하단: 거래량 (평균 거래량 라인 포함)"
        
        return response
    
    def _generate_analysis_response(self, state: Dict[str, Any]) -> str:
        """분석 응답 생성"""
        analysis_result = state.get("analysis_result", "")
        financial_data = state.get("financial_data", {})
        
        if not analysis_result:
            return "❌ 분석 결과를 생성할 수 없습니다."
        
        response = analysis_result
        
        # 추가 데이터 정보
        if financial_data:
            response += "\n\n📈 **추가 데이터 정보:**"
            response += f"\n• 종목: {financial_data.get('symbol', 'N/A')}"
            response += f"\n• 현재가: {financial_data.get('current_price', 'N/A')}"
        
        return response
    
    async def _generate_news_response(self, state: Dict[str, Any]) -> str:
        """뉴스 응답 생성 (새로운 분석 방식 사용)"""
        news_data = state.get("news_data", [])
        user_query = state.get("user_query", "")
        news_query_used = state.get("news_query_used", user_query)
        
        if not news_data:
            return "📰 죄송합니다. 관련 뉴스를 찾을 수 없습니다."
        
        return await self.generate_news_analysis_response(news_data, user_query, news_query_used)
    
    def _generate_knowledge_response(self, state: Dict[str, Any]) -> str:
        """지식 응답 생성"""
        knowledge_context = state.get("knowledge_context", "")
        user_query = state.get("user_query", "")
        
        if not knowledge_context:
            return f"❌ '{user_query}'에 대한 정보를 찾을 수 없습니다."
        
        response = f"📚 **{user_query}에 대한 설명:**\n\n"
        response += knowledge_context
        
        # 추가 도움말
        response += "\n\n💡 **더 알고 싶으시다면:**"
        response += "\n• 구체적인 예시를 들어 설명해드릴 수 있습니다"
        response += "\n• 관련된 다른 금융 용어도 궁금하시면 물어보세요"
        
        return response
    
    def _generate_general_response(self, state: Dict[str, Any]) -> str:
        """일반 응답 생성"""
        user_query = state.get("user_query", "")
        
        response = f"안녕하세요! '{user_query}'에 대해 도움을 드리겠습니다.\n\n"
        response += "다음과 같은 정보를 제공할 수 있습니다:\n"
        response += "• 📊 주식 가격 및 차트 정보\n"
        response += "• 📈 투자 분석 및 인사이트\n"
        response += "• 📰 관련 뉴스 및 시장 동향\n"
        response += "• 📚 금융 용어 및 개념 설명\n\n"
        response += "더 구체적인 질문을 해주시면 정확한 정보를 제공해드리겠습니다!"
        
        return response
    
    def generate_unified_response(self, 
                                   query: str,
                                   query_type: str,
                                   financial_data: Optional[Dict[str, Any]] = None,
                                   news_data: Optional[List[Dict[str, Any]]] = None,
                                   analysis_result: Optional[str] = None,
                                   knowledge_context: Optional[str] = None,
                                   chart_data: Optional[Dict[str, Any]] = None,
                                   user_context: Optional[Dict[str, Any]] = None) -> str:
        """✨ LLM 기반 통합 응답 생성 (동적 프롬프팅)
        
        모든 데이터를 종합하여 일관되고 자연스러운 응답을 생성합니다.
        
        Args:
            query: 사용자 질문
            query_type: 쿼리 유형 (data, analysis, news, knowledge, visualization, general)
            financial_data: 금융 데이터 (선택)
            news_data: 뉴스 데이터 (선택)
            analysis_result: 분석 결과 (선택)
            knowledge_context: 지식 컨텍스트 (선택)
            chart_data: 차트 데이터 (선택)
            user_context: 사용자 프로필 (선택)
            
        Returns:
            str: AI 생성 통합 응답
        """
        if not self.llm:
            # LLM이 없으면 기존 메서드로 폴백
            return self._generate_fallback_response(query_type, financial_data, news_data, knowledge_context)
        
        try:
            # ✨ 쿼리 유형별 동적 프롬프트 생성
            if query_type == "analysis" and financial_data:
                messages = prompt_manager.generate_analysis_prompt(
                    financial_data=financial_data,
                    user_query=query,
                    user_context=user_context
                )
            elif query_type == "news" and news_data:
                messages = prompt_manager.generate_news_prompt(
                    news_data=news_data,
                    user_query=query
                )
            elif query_type == "knowledge" and knowledge_context:
                messages = prompt_manager.generate_knowledge_prompt(
                    knowledge_context=knowledge_context,
                    user_query=query
                )
            elif query_type == "visualization" and chart_data:
                messages = prompt_manager.generate_visualization_prompt(
                    user_query=query
                )
            else:
                # 일반 응답
                return self._generate_general_response({"user_query": query})
            
            # LLM 호출
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"❌ 통합 응답 생성 오류: {e}")
            # 오류 시 기존 메서드로 폴백
            return self._generate_fallback_response(query_type, financial_data, news_data, knowledge_context)
    
    def _generate_fallback_response(self, 
                                     query_type: str,
                                     financial_data: Optional[Dict[str, Any]] = None,
                                     news_data: Optional[List[Dict[str, Any]]] = None,
                                     knowledge_context: Optional[str] = None) -> str:
        """폴백 응답 생성"""
        if query_type == "data" and financial_data:
            return self.generate_data_response(financial_data)
        elif query_type == "analysis" and financial_data:
            return self.generate_analysis_response(financial_data)
        elif query_type == "news" and news_data:
            return self.generate_news_response(news_data)
        elif query_type == "knowledge" and knowledge_context:
            state = {"user_query": "", "knowledge_context": knowledge_context}
            return self.generate_response(state)
        else:
            return "죄송합니다. 요청을 처리할 수 없습니다."


# 전역 서비스 인스턴스
response_generator = ResponseGeneratorService()
