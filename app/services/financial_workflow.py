from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from datetime import datetime
import json
from app.services.rag_service import rag_service
from app.services.financial_agent import (
    FinancialDataTool, 
    FinancialKnowledgeTool, 
    FinancialNewsTool, 
    FinancialAnalysisTool
)
from app.config import settings

class FinancialWorkflowState(TypedDict):
    """금융 워크플로우 상태 정의"""
    messages: Annotated[List[BaseMessage], "대화 메시지들"]
    user_query: str
    query_type: str  # "data", "analysis", "news", "knowledge", "general"
    financial_data: Dict[str, Any]
    analysis_result: str
    news_data: List[Dict[str, Any]]
    knowledge_context: str
    final_response: str
    error: str
    next_step: str

class FinancialWorkflowService:
    """LangGraph를 활용한 금융 워크플로우 서비스"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = self._create_tools()
        self.workflow = self._create_workflow()
    
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
            # API 키가 없을 때는 더미 LLM 반환 (테스트용)
            print("⚠️ API 키가 설정되지 않았습니다. 워크플로우 테스트 모드로 실행됩니다.")
            return None
    
    def _create_tools(self):
        """도구들 생성"""
        return [
            FinancialDataTool(),
            FinancialKnowledgeTool(),
            FinancialNewsTool(),
            FinancialAnalysisTool()
        ]
    
    def _create_workflow(self):
        """LangGraph 워크플로우 생성"""
        if self.llm is None:
            # API 키가 없을 때는 더미 워크플로우 반환
            return None
            
        workflow = StateGraph(FinancialWorkflowState)
        
        # 노드들 추가
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("get_financial_data", self._get_financial_data)
        workflow.add_node("search_knowledge", self._search_knowledge)
        workflow.add_node("get_news", self._get_news)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # 엣지들 추가
        workflow.set_entry_point("classify_query")
        
        # 쿼리 분류 후 라우팅
        workflow.add_conditional_edges(
            "classify_query",
            self._route_after_classification,
            {
                "data": "get_financial_data",
                "analysis": "analyze_data", 
                "news": "get_news",
                "knowledge": "search_knowledge",
                "general": "generate_response",
                "error": "handle_error"
            }
        )
        
        # 데이터 조회 후 분석으로
        workflow.add_edge("get_financial_data", "analyze_data")
        
        # 분석 후 응답 생성
        workflow.add_edge("analyze_data", "generate_response")
        
        # 뉴스 조회 후 응답 생성
        workflow.add_edge("get_news", "generate_response")
        
        # 지식 검색 후 응답 생성
        workflow.add_edge("search_knowledge", "generate_response")
        
        # 응답 생성 후 종료
        workflow.add_edge("generate_response", END)
        
        # 에러 처리 후 종료
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """사용자 쿼리 분류"""
        query = state["user_query"].lower()
        
        # 키워드 기반 분류
        if any(keyword in query for keyword in ["주가", "가격", "현재가", "시세", "005930", "삼성전자"]):
            query_type = "data"
        elif any(keyword in query for keyword in ["분석", "전망", "투자", "추천", "의견"]):
            query_type = "analysis"
        elif any(keyword in query for keyword in ["뉴스", "소식", "이슈", "공시"]):
            query_type = "news"
        elif any(keyword in query for keyword in ["뜻", "이해", "설명", "기본", "원리"]):
            query_type = "knowledge"
        else:
            query_type = "general"
        
        state["query_type"] = query_type
        state["next_step"] = query_type
        
        return state
    
    def _route_after_classification(self, state: FinancialWorkflowState) -> str:
        """분류 후 라우팅"""
        return state["query_type"]
    
    def _get_financial_data(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """금융 데이터 조회"""
        try:
            query = state["user_query"]
            
            # 심볼 추출 로직
            symbol = self._extract_symbol(query)
            if not symbol:
                state["error"] = "주식 심볼을 찾을 수 없습니다."
                state["next_step"] = "error"
                return state
            
            # 데이터 조회
            data = rag_service.get_financial_data(symbol)
            if "error" in data:
                state["error"] = data["error"]
                state["next_step"] = "error"
                return state
            
            state["financial_data"] = data
            state["next_step"] = "analyze"
            
        except Exception as e:
            state["error"] = f"데이터 조회 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _analyze_data(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """데이터 분석"""
        try:
            if "financial_data" not in state or not state["financial_data"]:
                state["error"] = "분석할 데이터가 없습니다."
                state["next_step"] = "error"
                return state
            
            data = state["financial_data"]
            
            # 기본 분석 로직
            analysis_parts = []
            
            # 가격 변화 분석
            if data.get('price_change_percent', 0) > 0:
                analysis_parts.append(f"📈 긍정적 신호: 전일 대비 {data['price_change_percent']:.2f}% 상승")
            else:
                analysis_parts.append(f"📉 부정적 신호: 전일 대비 {data['price_change_percent']:.2f}% 하락")
            
            # 거래량 분석
            volume = data.get('volume', 0)
            if volume > 1000000:
                analysis_parts.append(f"🔥 높은 관심도: 거래량 {volume:,}주 (평소 대비 높음)")
            else:
                analysis_parts.append(f"📊 보통 거래량: {volume:,}주")
            
            # PER 분석
            pe_ratio = data.get('pe_ratio')
            if isinstance(pe_ratio, (int, float)):
                if pe_ratio < 15:
                    analysis_parts.append(f"💰 저평가: PER {pe_ratio:.1f} (투자 매력도 높음)")
                elif pe_ratio > 25:
                    analysis_parts.append(f"⚠️ 고평가: PER {pe_ratio:.1f} (투자 주의 필요)")
                else:
                    analysis_parts.append(f"📊 적정가: PER {pe_ratio:.1f}")
            
            # 섹터 정보
            sector = data.get('sector', 'Unknown')
            analysis_parts.append(f"🏢 섹터: {sector}")
            
            state["analysis_result"] = "\n".join(analysis_parts)
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"분석 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _get_news(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """뉴스 조회"""
        try:
            query = state["user_query"]
            news = rag_service.get_financial_news(query)
            state["news_data"] = news
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"뉴스 조회 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _search_knowledge(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """지식 검색"""
        try:
            query = state["user_query"]
            context = rag_service.get_context_for_query(query)
            state["knowledge_context"] = context
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"지식 검색 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _generate_response(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """최종 응답 생성"""
        try:
            query_type = state.get("query_type", "general")
            user_query = state["user_query"]
            
            response_parts = []
            
            if query_type == "data" and "financial_data" in state:
                data = state["financial_data"]
                response_parts.append(f"📊 {data['company_name']} ({data.get('symbol', 'N/A')}) 실시간 정보")
                response_parts.append(f"현재가: {data['current_price']:,}원")
                response_parts.append(f"전일대비: {data['price_change']:+,}원 ({data['price_change_percent']:+.2f}%)")
                response_parts.append(f"거래량: {data['volume']:,}주")
                
            elif query_type == "analysis" and "analysis_result" in state:
                response_parts.append("🔍 투자 분석 결과:")
                response_parts.append(state["analysis_result"])
                
            elif query_type == "news" and "news_data" in state:
                news = state["news_data"]
                if news:
                    response_parts.append("📰 최신 뉴스:")
                    for i, article in enumerate(news[:3], 1):
                        response_parts.append(f"{i}. {article['title']}")
                        response_parts.append(f"   {article['summary']}")
                else:
                    response_parts.append("관련 뉴스를 찾을 수 없습니다.")
                    
            elif query_type == "knowledge" and "knowledge_context" in state:
                response_parts.append("📚 금융 지식:")
                response_parts.append(state["knowledge_context"])
                
            else:
                # 일반적인 질문에 대한 응답
                response_parts.append("안녕하세요! 금융 전문가 챗봇입니다.")
                response_parts.append("주식 정보, 투자 분석, 금융 뉴스, 금융 지식에 대해 도움을 드릴 수 있습니다.")
                response_parts.append("구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다.")
            
            # 주의사항 추가
            if query_type in ["data", "analysis"]:
                response_parts.append("\n⚠️ 주의사항: 이 정보는 참고용이며, 투자 결정은 신중히 하시기 바랍니다.")
            
            state["final_response"] = "\n".join(response_parts)
            state["next_step"] = "end"
            
        except Exception as e:
            state["error"] = f"응답 생성 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _handle_error(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """에러 처리"""
        error_msg = state.get("error", "알 수 없는 오류가 발생했습니다.")
        state["final_response"] = f"죄송합니다. {error_msg}"
        state["next_step"] = "end"
        return state
    
    def _extract_symbol(self, query: str) -> str:
        """쿼리에서 주식 심볼 추출"""
        query_lower = query.lower()
        
        # 한국 주식 심볼 매핑 (한글은 원본 유지, 영문은 소문자)
        symbol_mapping = {
            "삼성전자": "005930.KS",
            "samsung": "005930.KS",
            "sk하이닉스": "000660.KS",
            "sk hynix": "000660.KS",
            "naver": "035420.KS",
            "네이버": "035420.KS",
            "삼성바이오로직스": "207940.KS",
            "samsung biologics": "207940.KS",
            "삼성sdi": "006400.KS",
            "samsung sdi": "006400.KS"
        }
        
        # 원본 쿼리와 소문자 쿼리 모두에서 검색
        for keyword, symbol in symbol_mapping.items():
            if keyword in query or keyword in query_lower:
                return symbol
        
        # 직접적인 심볼 패턴 검색
        import re
        symbol_pattern = r'\b\d{6}\.KS\b'
        match = re.search(symbol_pattern, query)
        if match:
            return match.group()
        
        return ""
    
    def process_query(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자 쿼리 처리"""
        try:
            if self.workflow is None:
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
            
            # 초기 상태 설정
            initial_state = FinancialWorkflowState(
                messages=[HumanMessage(content=user_query)],
                user_query=user_query,
                query_type="",
                financial_data={},
                analysis_result="",
                news_data=[],
                knowledge_context="",
                final_response="",
                error="",
                next_step=""
            )
            
            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            return {
                "success": True,
                "reply_text": result["final_response"],
                "action_type": "display_info",
                "action_data": {
                    "query_type": result.get("query_type", "general"),
                    "financial_data": result.get("financial_data", {}),
                    "analysis_result": result.get("analysis_result", ""),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "reply_text": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                "action_type": "display_info",
                "action_data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }

# 전역 워크플로우 서비스 인스턴스
financial_workflow = FinancialWorkflowService()
