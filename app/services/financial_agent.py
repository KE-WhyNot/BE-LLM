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
    """금융 뉴스 조회 도구"""
    
    name = "get_financial_news"
    description = "특정 종목이나 키워드에 대한 최신 금융 뉴스를 조회합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """금융 뉴스 조회"""
        try:
            news = self.rag_service.get_financial_news(query)
            if not news:
                return "관련 뉴스를 찾을 수 없습니다."
            
            news_text = "최신 금융 뉴스:\n"
            for i, article in enumerate(news, 1):
                news_text += f"{i}. {article['title']}\n"
                news_text += f"   요약: {article['summary']}\n"
                news_text += f"   발행일: {article['published']}\n\n"
            
            return news_text
        except Exception as e:
            return f"뉴스 조회 중 오류 발생: {str(e)}"

class NewsAnalysisTool:
    """뉴스 URL 분석 도구"""
    
    name = "analyze_news_url"
    description = "뉴스 URL을 입력받아 내용을 스크래핑하고, 요약하며, 주식에 미치는 영향을 분석합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """뉴스 URL 분석"""
        try:
            # 1. 뉴스 내용 스크래핑
            print(f"📰 뉴스 URL 분석 중: {url}")
            news_data = self.rag_service.get_news_content_from_url(url)
            
            if not news_data.get("success", False):
                return f"❌ 뉴스 내용을 가져올 수 없습니다: {news_data.get('error', '알 수 없는 오류')}"
            
            title = news_data.get("title", "")
            content = news_data.get("content", "")
            author = news_data.get("author", "")
            published_date = news_data.get("published_date", "")
            
            if not content or len(content.strip()) < 50:
                return "❌ 뉴스 내용이 충분하지 않아 분석할 수 없습니다."
            
            # 2. 뉴스 요약
            print("📝 뉴스 요약 생성 중...")
            summary = self.rag_service.summarize_news_content(content, title)
            
            # 3. 주식 영향 분석
            print("📊 주식 영향 분석 중...")
            impact_analysis = self.rag_service.analyze_news_impact(content, title)
            
            # 4. 결과 종합
            result = f"""
📰 **뉴스 분석 결과**

**제목:** {title}
**작성자:** {author}
**발행일:** {published_date}
**URL:** {url}

**📝 뉴스 요약:**
{summary}

**📊 주식 영향 분석:**
- **감정 분석:** {impact_analysis.get('sentiment', '분석 불가')}
- **영향 수준:** {impact_analysis.get('impact_level', '알 수 없음')}
- **영향 점수:** {impact_analysis.get('impact_score', 0):.2f}
- **긍정 키워드:** {impact_analysis.get('positive_keywords_found', 0)}개
- **부정 키워드:** {impact_analysis.get('negative_keywords_found', 0)}개

**💡 투자 시사점:**
{self._generate_investment_insights(impact_analysis, summary)}
"""
            
            return result
            
        except Exception as e:
            return f"뉴스 분석 중 오류 발생: {str(e)}"
    
    def _generate_investment_insights(self, impact_analysis: Dict[str, Any], summary: str) -> str:
        """투자 시사점 생성"""
        sentiment = impact_analysis.get('sentiment', '중립')
        impact_level = impact_analysis.get('impact_level', '낮음')
        
        insights = []
        
        if sentiment == "긍정적":
            if impact_level == "높음":
                insights.append("• 강한 긍정적 신호로 주가 상승 가능성 높음")
                insights.append("• 단기적으로 매수 관심 증가 예상")
            elif impact_level == "중간":
                insights.append("• 중간 정도의 긍정적 영향으로 주가에 부분적 상승 기대")
            else:
                insights.append("• 약한 긍정적 신호로 주가에 미미한 영향 예상")
        elif sentiment == "부정적":
            if impact_level == "높음":
                insights.append("• 강한 부정적 신호로 주가 하락 위험 높음")
                insights.append("• 단기적으로 매도 압력 증가 예상")
            elif impact_level == "중간":
                insights.append("• 중간 정도의 부정적 영향으로 주가에 부분적 하락 기대")
            else:
                insights.append("• 약한 부정적 신호로 주가에 미미한 영향 예상")
        else:
            insights.append("• 중립적 뉴스로 주가에 큰 영향 없을 것으로 예상")
        
        # 추가 투자 조언
        insights.append("• 투자 결정 시 다른 시장 요인들도 함께 고려 필요")
        insights.append("• 단일 뉴스에 의존한 투자보다는 종합적 분석 권장")
        
        return "\n".join(insights)

class AutoNewsAnalysisTool:
    """자동 뉴스 검색 및 분석 도구"""
    
    name = "get_news_analysis"
    description = "특정 키워드나 종목에 대한 최신 뉴스를 자동으로 검색하고, 각 뉴스의 내용을 분석하여 주식에 미치는 영향을 종합적으로 평가합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """자동 뉴스 검색 및 분석"""
        try:
            print(f"🔍 '{query}' 관련 뉴스 자동 분석을 시작합니다...")
            
            # 1. 뉴스 검색
            print("📰 최신 뉴스 검색 중...")
            news_list = self.rag_service.get_financial_news(query, max_results=3)
            
            if not news_list:
                return f"❌ '{query}' 관련 뉴스를 찾을 수 없습니다."
            
            # 2. 각 뉴스 분석
            analysis_results = []
            overall_sentiment = 0
            total_impact = 0
            
            for i, news in enumerate(news_list, 1):
                print(f"📊 뉴스 {i} 분석 중: {news.get('title', '')[:50]}...")
                
                # 뉴스 URL에서 내용 스크래핑
                url = news.get('url', '')
                if url:
                    news_data = self.rag_service.get_news_content_from_url(url)
                    
                    if news_data.get("success", False):
                        content = news_data.get("content", "")
                        title = news_data.get("title", news.get('title', ''))
                        
                        if content and len(content) > 50:
                            # 뉴스 요약
                            summary = self.rag_service.summarize_news_content(content, title)
                            
                            # 영향 분석
                            impact_analysis = self.rag_service.analyze_news_impact(content, title)
                            
                            analysis_results.append({
                                "title": title,
                                "summary": summary,
                                "sentiment": impact_analysis.get('sentiment', '중립'),
                                "impact_score": impact_analysis.get('impact_score', 0),
                                "impact_level": impact_analysis.get('impact_level', '낮음'),
                                "url": url
                            })
                            
                            # 전체 감정 점수 누적
                            sentiment_score = impact_analysis.get('impact_score', 0)
                            overall_sentiment += sentiment_score
                            total_impact += 1
                        else:
                            # 내용이 부족한 경우 기본 정보만 사용
                            analysis_results.append({
                                "title": news.get('title', ''),
                                "summary": news.get('summary', ''),
                                "sentiment": "분석 불가",
                                "impact_score": 0,
                                "impact_level": "알 수 없음",
                                "url": url
                            })
                    else:
                        # 스크래핑 실패 시 기본 정보만 사용
                        analysis_results.append({
                            "title": news.get('title', ''),
                            "summary": news.get('summary', ''),
                            "sentiment": "분석 불가",
                            "impact_score": 0,
                            "impact_level": "알 수 없음",
                            "url": url
                        })
            
            # 3. 종합 분석 결과 생성
            if total_impact > 0:
                avg_sentiment = overall_sentiment / total_impact
                if avg_sentiment > 0.3:
                    overall_sentiment_text = "긍정적"
                elif avg_sentiment < -0.3:
                    overall_sentiment_text = "부정적"
                else:
                    overall_sentiment_text = "중립"
            else:
                overall_sentiment_text = "분석 불가"
                avg_sentiment = 0
            
            # 4. 결과 종합
            result = f"""
📰 **'{query}' 관련 뉴스 종합 분석**

**📊 전체 시장 감정:** {overall_sentiment_text} (평균 점수: {avg_sentiment:.2f})
**📈 분석된 뉴스 수:** {len(analysis_results)}개

"""
            
            # 각 뉴스 분석 결과
            for i, analysis in enumerate(analysis_results, 1):
                result += f"""
**📰 뉴스 {i}: {analysis['title'][:60]}...**
- **감정:** {analysis['sentiment']}
- **영향 수준:** {analysis['impact_level']}
- **요약:** {analysis['summary'][:150]}...
- **링크:** {analysis['url']}

"""
            
            # 종합 투자 조언
            result += f"""
**💡 종합 투자 시사점:**

{self._generate_comprehensive_insights(overall_sentiment_text, avg_sentiment, len(analysis_results))}

**⚠️ 투자 주의사항:**
• 단일 뉴스에 의존한 투자보다는 종합적 분석 권장
• 시장 변동성과 리스크를 항상 고려하세요
• 투자 결정 전 전문가 상담을 권장합니다
"""
            
            return result
            
        except Exception as e:
            return f"뉴스 자동 분석 중 오류 발생: {str(e)}"
    
    def _generate_comprehensive_insights(self, sentiment: str, avg_score: float, news_count: int) -> str:
        """종합 투자 시사점 생성"""
        insights = []
        
        if sentiment == "긍정적":
            if avg_score > 0.7:
                insights.append("• 매우 강한 긍정적 신호로 주가 상승 가능성 매우 높음")
                insights.append("• 단기적으로 강한 매수 관심 증가 예상")
            elif avg_score > 0.4:
                insights.append("• 강한 긍정적 신호로 주가 상승 가능성 높음")
                insights.append("• 단기적으로 매수 관심 증가 예상")
            else:
                insights.append("• 약한 긍정적 신호로 주가에 부분적 상승 기대")
        elif sentiment == "부정적":
            if avg_score < -0.7:
                insights.append("• 매우 강한 부정적 신호로 주가 하락 위험 매우 높음")
                insights.append("• 단기적으로 강한 매도 압력 증가 예상")
            elif avg_score < -0.4:
                insights.append("• 강한 부정적 신호로 주가 하락 위험 높음")
                insights.append("• 단기적으로 매도 압력 증가 예상")
            else:
                insights.append("• 약한 부정적 신호로 주가에 부분적 하락 기대")
        else:
            insights.append("• 중립적 뉴스로 주가에 큰 영향 없을 것으로 예상")
        
        # 뉴스 수에 따른 신뢰도
        if news_count >= 3:
            insights.append(f"• {news_count}개의 뉴스 분석으로 신뢰도 높음")
        elif news_count >= 2:
            insights.append(f"• {news_count}개의 뉴스 분석으로 중간 신뢰도")
        else:
            insights.append(f"• {news_count}개의 뉴스 분석으로 제한적 신뢰도")
        
        return "\n".join(insights)

class FinancialAnalysisTool:
    """금융 분석 도구"""
    
    name = "analyze_financial_data"
    description = "주식 데이터를 분석하여 투자 인사이트를 제공합니다."
    
    def __init__(self):
        self.rag_service = rag_service
    
    def __call__(self, symbol: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """금융 데이터 분석"""
        try:
            data = self.rag_service.get_financial_data(symbol)
            if "error" in data:
                return f"오류: {data['error']}"
            
            # 기본 분석 로직
            analysis = []
            
            # 가격 변화 분석
            if data['price_change_percent'] > 0:
                analysis.append(f"📈 긍정적: 전일 대비 {data['price_change_percent']:.2f}% 상승")
            else:
                analysis.append(f"📉 부정적: 전일 대비 {data['price_change_percent']:.2f}% 하락")
            
            # 거래량 분석
            if data['volume'] > 1000000:  # 100만주 이상
                analysis.append(f"🔥 높은 거래량: {data['volume']:,}주 (관심도 높음)")
            else:
                analysis.append(f"📊 보통 거래량: {data['volume']:,}주")
            
            # PER 분석
            if isinstance(data['pe_ratio'], (int, float)):
                if data['pe_ratio'] < 15:
                    analysis.append(f"💰 저평가: PER {data['pe_ratio']:.1f} (매력적)")
                elif data['pe_ratio'] > 25:
                    analysis.append(f"⚠️ 고평가: PER {data['pe_ratio']:.1f} (주의 필요)")
                else:
                    analysis.append(f"📊 적정가: PER {data['pe_ratio']:.1f}")
            
            # 섹터 정보
            analysis.append(f"🏢 섹터: {data['sector']}")
            
            return f"""
{data['company_name']} ({symbol}) 분석 결과:

{chr(10).join(analysis)}

⚠️ 주의사항: 이 분석은 참고용이며, 투자 결정은 신중히 하시기 바랍니다.
            """
        except Exception as e:
            return f"분석 중 오류 발생: {str(e)}"

class FinancialExpertAgent:
    """금융 전문가 에이전트"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = self._create_tools()
        self.memory = ConversationBufferWindowMemory(
            k=5,  # 최근 5개 대화 기억
            memory_key="chat_history",
            return_messages=True
        )
        self.agent_executor = self._create_agent()
    
    def _initialize_llm(self):
        """LLM 초기화 (OpenAI 또는 Google Gemini)"""
        if settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.openai_api_key
            )
        elif settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.1,
                google_api_key=settings.google_api_key
            )
        else:
            # API 키가 없을 때는 더미 LLM 반환 (테스트용)
            print("⚠️ API 키가 설정되지 않았습니다. 테스트 모드로 실행됩니다.")
            return None
    
    def _create_tools(self):
        """도구들 생성"""
        return [
            Tool(
                name=FinancialDataTool().name,
                description=FinancialDataTool().description,
                func=FinancialDataTool()
            ),
            Tool(
                name=FinancialKnowledgeTool().name,
                description=FinancialKnowledgeTool().description,
                func=FinancialKnowledgeTool()
            ),
            Tool(
                name=FinancialNewsTool().name,
                description=FinancialNewsTool().description,
                func=FinancialNewsTool()
            ),
            Tool(
                name=FinancialAnalysisTool().name,
                description=FinancialAnalysisTool().description,
                func=FinancialAnalysisTool()
            ),
            Tool(
                name=NewsAnalysisTool().name,
                description=NewsAnalysisTool().description,
                func=NewsAnalysisTool()
            ),
            Tool(
                name=AutoNewsAnalysisTool().name,
                description=AutoNewsAnalysisTool().description,
                func=AutoNewsAnalysisTool()
            )
        ]
    
    def _create_agent(self):
        """에이전트 생성"""
        if self.llm is None:
            # API 키가 없을 때는 더미 에이전트 반환
            return None
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 한국의 금융 전문가입니다. 다음 원칙을 따라 답변해주세요:

1. 정확성: 정확한 금융 정보를 제공하고, 불확실한 정보는 명시하세요.
2. 신중함: 투자 조언은 신중하게 하고, 리스크를 항상 언급하세요.
3. 이해하기 쉬움: 복잡한 금융 개념을 일반인이 이해할 수 있도록 설명하세요.
4. 실용성: 실제 투자에 도움이 되는 구체적인 정보를 제공하세요.
5. 한국어: 모든 답변은 한국어로 해주세요.

사용 가능한 도구들:
- get_financial_data: 실시간 주식 데이터 조회
- search_financial_knowledge: 금융 지식 검색
- get_financial_news: 금융 뉴스 조회
- analyze_financial_data: 주식 데이터 분석
- analyze_news_url: 뉴스 URL 분석 (내용 스크래핑, 요약, 주식 영향 분석)
- get_news_analysis: 자동 뉴스 검색 및 종합 분석 (최근 동향, 뉴스 분석 요청 시 사용)

사용자의 질문에 가장 적합한 도구를 선택하여 정확하고 도움이 되는 답변을 제공하세요."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def chat(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자와 대화"""
        try:
            if self.agent_executor is None:
                # API 키가 없을 때는 기본 응답
                return {
                    "success": True,
                    "reply_text": "안녕하세요! 금융 전문가 챗봇입니다. API 키를 설정하면 더 정확한 분석을 제공할 수 있습니다.",
                    "action_type": "display_info",
                    "action_data": {
                        "message": "API 키가 설정되지 않았습니다.",
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id
                    }
                }
            
            # 에이전트 실행
            response = self.agent_executor.invoke({"input": message})
            
            return {
                "success": True,
                "reply_text": response["output"],
                "action_type": "display_info",
                "action_data": {
                    "message": response["output"],
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            }
        except Exception as e:
            error_message = f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"
            return {
                "success": False,
                "reply_text": error_message,
                "action_type": "display_info",
                "action_data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """대화 기록 조회"""
        history = []
        if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
            for message in self.memory.chat_memory.messages:
                if isinstance(message, HumanMessage):
                    history.append({"role": "user", "content": message.content})
                elif isinstance(message, AIMessage):
                    history.append({"role": "assistant", "content": message.content})
        return history
    
    def clear_memory(self):
        """대화 기록 초기화"""
        self.memory.clear()

# 전역 에이전트 인스턴스
financial_agent = FinancialExpertAgent()
