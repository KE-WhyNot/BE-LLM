from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type, Dict, Any, List
import json
import os
from datetime import datetime
from app.services.rag_service import rag_service
from app.config import settings

class FinancialDataTool:
    """금융 데이터 조회 도구"""
    
    name = "get_financial_data"
    description = "주식 심볼을 입력받아 실시간 주식 데이터를 조회합니다. 예: '005930.KS' (삼성전자)"
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, symbol: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """주식 데이터 조회"""
        try:
            data = self.rag_service.get_financial_data(symbol)
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
        except Exception as e:
            return f"데이터 조회 중 오류 발생: {str(e)}"

class FinancialKnowledgeTool:
    """금융 지식 검색 도구"""
    
    name = "search_financial_knowledge"
    description = "금융 관련 질문에 대한 지식 베이스에서 관련 정보를 검색합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """금융 지식 검색"""
        try:
            context = self.rag_service.get_context_for_query(query)
            return context if context else "관련 정보를 찾을 수 없습니다."
        except Exception as e:
            return f"지식 검색 중 오류 발생: {str(e)}"

class FinancialNewsTool:
    """금융 뉴스 조회 도구 - 통합된 뉴스 분석 및 인사이트 제공"""
    
    name = "get_financial_news"
    description = "특정 종목이나 키워드에 대한 최신 금융 뉴스를 조회하고, 분석 및 투자 인사이트를 제공합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """금융 뉴스 조회 및 분석"""
        try:
            news = self.rag_service.get_financial_news(query)
            if not news:
                return "관련 뉴스를 찾을 수 없습니다."
            
            news_text = "📰 최신 뉴스 요약:\n\n"
            overall_sentiment = 0
            total_impact = 0
            positive_count = 0
            negative_count = 0
            
            for i, article in enumerate(news, 1):
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
            
            avg_impact = total_impact / len(news) if news else 0
            
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
        except Exception as e:
            return f"뉴스 조회 중 오류 발생: {str(e)}"

class FinancialAnalysisTool:
    """금융 분석 도구"""
    
    name = "analyze_financial_data"
    description = "주식 데이터를 분석하여 투자 인사이트를 제공합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, symbol: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """주식 데이터 분석"""
        try:
            data = self.rag_service.get_financial_data(symbol)
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
        except Exception as e:
            return f"분석 중 오류 발생: {str(e)}"

class FinancialAgent:
    """금융 전문가 에이전트"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=5
        )
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.openai_api_key
            )
        elif settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.1,
                google_api_key=settings.google_api_key
            )
        else:
            print("⚠️ API 키가 설정되지 않았습니다. 기본 응답 모드로 실행됩니다.")
            return None
    
    def _create_tools(self):
        """도구들 생성"""
        return [
            FinancialDataTool(),
            FinancialKnowledgeTool(),
            FinancialNewsTool(),
            FinancialAnalysisTool()
        ]
    
    def _create_agent(self):
        """에이전트 생성"""
        if self.llm is None:
            return None
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 금융 전문가 AI 어시스턴트입니다. 
            
다음 도구들을 사용하여 사용자의 질문에 답변하세요:
- get_financial_data: 주식 데이터 조회
- search_financial_knowledge: 금융 지식 검색  
- get_financial_news: 뉴스 조회 및 분석
- analyze_financial_data: 주식 데이터 분석

항상 정확하고 도움이 되는 정보를 제공하며, 투자 조언을 할 때는 리스크를 명시하세요."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def chat(self, message: str, user_id: int = 1) -> Dict[str, Any]:
        """채팅 처리"""
        try:
            if self.agent is None:
                return {
                    "success": False,
                    "reply_text": "API 키가 설정되지 않아 서비스를 이용할 수 없습니다.",
                    "action_type": "error",
                    "action_data": {}
                }
            
            response = self.agent.invoke({
                "input": message,
                "chat_history": self.memory.chat_memory.messages
            })
            
            return {
                "success": True,
                "reply_text": response["output"],
                "action_type": "text",
                "action_data": {}
            }
            
        except Exception as e:
            return {
                "success": False,
                "reply_text": f"처리 중 오류가 발생했습니다: {str(e)}",
                "action_type": "error",
                "action_data": {}
            }
