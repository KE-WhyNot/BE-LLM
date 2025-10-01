"""
향상된 LangGraph 기반 금융 워크플로우
동적 프롬프트 생성 및 AI Agent 최적화
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

from app.config import settings
from app.services.workflow_components.query_classifier_service import query_classifier
from app.services.workflow_components.financial_data_service import financial_data_service
from app.services.langgraph_enhanced.ai_analysis_service import ai_analysis_service
from app.services.workflow_components.news_service import news_service
from app.services.workflow_components.response_generator_service import response_generator
from app.services.workflow_components.visualization_service import visualization_service
from app.services.rag_service import rag_service
from app.services.langgraph_enhanced.prompt_generator import prompt_generator


class EnhancedFinancialWorkflowState(TypedDict):
    """향상된 금융 워크플로우 상태 정의"""
    messages: Annotated[List[BaseMessage], "대화 메시지들"]
    user_query: str
    query_type: str
    financial_data: Dict[str, Any]
    analysis_result: str
    news_data: List[Dict[str, Any]]
    knowledge_context: str
    chart_data: Optional[Dict[str, Any]]
    final_response: str
    error: str
    next_step: str
    user_context: Dict[str, Any]  # 사용자 컨텍스트 추가
    performance_metrics: Dict[str, Any]  # 성능 메트릭 추가


class EnhancedFinancialWorkflowService:
    """향상된 LangGraph 기반 금융 워크플로우 서비스"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.workflow = self._create_enhanced_workflow()
        self.performance_tracker = {}
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=settings.google_api_key
            )
        elif settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.openai_api_key
            )
        return None
    
    def _create_enhanced_workflow(self):
        """향상된 워크플로우 생성"""
        if self.llm is None:
            return None
        
        workflow = StateGraph(EnhancedFinancialWorkflowState)
        
        # 노드들 추가
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("get_financial_data", self._get_financial_data)
        workflow.add_node("search_knowledge", self._search_knowledge)
        workflow.add_node("get_news", self._get_news)
        workflow.add_node("ai_analyze_data", self._ai_analyze_data)
        workflow.add_node("create_visualization", self._create_visualization)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("optimize_performance", self._optimize_performance)
        
        # 엣지들 추가
        workflow.set_entry_point("classify_query")
        
        # 쿼리 분류 후 라우팅
        workflow.add_conditional_edges(
            "classify_query",
            self._route_after_classification,
            {
                "data": "get_financial_data",
                "analysis": "get_financial_data",
                "news": "get_news",
                "knowledge": "search_knowledge",
                "visualization": "get_financial_data",
                "general": "generate_response",
                "error": "handle_error"
            }
        )
        
        # 데이터 조회 후 조건부 라우팅
        workflow.add_conditional_edges(
            "get_financial_data",
            self._route_after_data,
            {
                "analyze": "ai_analyze_data",
                "visualization": "create_visualization",
                "error": "handle_error"
            }
        )
        
        # AI 분석 후 응답 생성
        workflow.add_edge("ai_analyze_data", "generate_response")
        
        # 뉴스 조회 후 응답 생성
        workflow.add_edge("get_news", "generate_response")
        
        # 지식 검색 후 응답 생성
        workflow.add_edge("search_knowledge", "generate_response")
        
        # 시각화 후 응답 생성
        workflow.add_edge("create_visualization", "generate_response")
        
        # 성능 최적화
        workflow.add_edge("generate_response", "optimize_performance")
        workflow.add_edge("optimize_performance", END)
        
        # 에러 처리 후 종료
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """향상된 쿼리 분류"""
        start_time = datetime.now()
        
        query = state["user_query"]
        query_type = query_classifier.classify(query)
        
        # 사용자 컨텍스트 추출
        user_context = self._extract_user_context(state)
        
        state["query_type"] = query_type
        state["user_context"] = user_context
        state["next_step"] = query_type
        
        # 성능 메트릭 기록
        processing_time = (datetime.now() - start_time).total_seconds()
        state["performance_metrics"] = {
            "classification_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        return state
    
    def _extract_user_context(self, state: EnhancedFinancialWorkflowState) -> Dict[str, Any]:
        """사용자 컨텍스트 추출"""
        # 대화 히스토리에서 사용자 프로필 추출
        messages = state.get("messages", [])
        
        # 기본 컨텍스트
        context = {
            "user_profile": "일반 투자자",
            "investment_experience": "중급",
            "interests": ["기술주"],
            "risk_tolerance": "보통",
            "conversation_history": [msg.content for msg in messages[-5:]]  # 최근 5개 메시지
        }
        
        # 대화 히스토리 분석으로 컨텍스트 개선
        if messages:
            recent_queries = [msg.content for msg in messages[-3:]]
            context["recent_interests"] = self._analyze_user_interests(recent_queries)
        
        return context
    
    def _analyze_user_interests(self, queries: List[str]) -> List[str]:
        """사용자 관심사 분석"""
        interests = []
        
        for query in queries:
            query_lower = query.lower()
            if any(tech in query_lower for tech in ["삼성", "네이버", "카카오", "기술"]):
                interests.append("기술주")
            if any(finance in query_lower for finance in ["은행", "금융", "보험"]):
                interests.append("금융주")
            if any(bio in query_lower for bio in ["바이오", "제약", "의료"]):
                interests.append("바이오주")
        
        return list(set(interests)) if interests else ["기술주"]
    
    def _route_after_classification(self, state: EnhancedFinancialWorkflowState) -> str:
        """분류 후 라우팅"""
        return state["query_type"]
    
    def _route_after_data(self, state: EnhancedFinancialWorkflowState) -> str:
        """데이터 조회 후 라우팅"""
        if "error" in state and state["error"]:
            return "error"
        elif state.get("query_type") == "visualization":
            return "visualization"
        else:
            return "analyze"
    
    def _get_financial_data(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """금융 데이터 조회"""
        try:
            query = state["user_query"]
            data = financial_data_service.get_financial_data(query)
            
            if "error" in data:
                state["error"] = data["error"]
            else:
                state["financial_data"] = data
            
        except Exception as e:
            state["error"] = f"데이터 조회 중 오류: {str(e)}"
        
        return state
    
    def _ai_analyze_data(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """AI Agent 기반 데이터 분석"""
        try:
            if "financial_data" not in state or not state["financial_data"]:
                state["error"] = "분석할 데이터가 없습니다."
                return state
            
            query = state["user_query"]
            financial_data = state["financial_data"]
            user_context = state.get("user_context", {})
            
            # AI 분석 실행
            analysis_result = ai_analysis_service.analyze_data(
                query=query,
                financial_data=financial_data,
                user_context=user_context
            )
            
            state["analysis_result"] = analysis_result
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"AI 분석 중 오류: {str(e)}"
        
        return state
    
    def _get_news(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """뉴스 조회"""
        try:
            query = state["user_query"]
            news_data = news_service.get_financial_news(query)
            state["news_data"] = news_data
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"뉴스 조회 중 오류: {str(e)}"
        
        return state
    
    def _search_knowledge(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """지식 검색"""
        try:
            query = state["user_query"]
            context = rag_service.get_context_for_query(query)
            state["knowledge_context"] = context
            state["next_step"] = "generate_response"
            
        except Exception as e:
            state["error"] = f"지식 검색 중 오류: {str(e)}"
        
        return state
    
    def _create_visualization(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """시각화 생성"""
        try:
            query = state["user_query"]
            financial_data = state.get("financial_data", {})
            
            state["chart_data"] = {
                "query": query,
                "data": financial_data
            }
            
        except Exception as e:
            state["error"] = f"시각화 생성 중 오류: {str(e)}"
        
        return state
    
    def _generate_response(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """최종 응답 생성"""
        try:
            query_type = state.get("query_type", "general")
            
            if query_type == "data" and "financial_data" in state:
                final_response = response_generator.generate_data_response(
                    state["financial_data"]
                )
            elif query_type == "analysis" and "financial_data" in state:
                final_response = response_generator.generate_analysis_response(
                    state["financial_data"]
                )
            elif query_type == "news" and "news_data" in state:
                final_response = response_generator.generate_news_response(
                    state["news_data"]
                )
            elif query_type == "knowledge" and "knowledge_context" in state:
                final_response = response_generator.generate_knowledge_response(
                    state["knowledge_context"]
                )
            elif query_type == "visualization" and "chart_data" in state:
                viz_response = response_generator.generate_visualization_response(
                    state["chart_data"]["query"],
                    state["chart_data"]["data"]
                )
                state["chart_data"] = viz_response
                final_response = viz_response.get("text", "차트가 생성되었습니다.")
            else:
                final_response = response_generator.generate_general_response()
            
            if not final_response or len(final_response.strip()) < 10:
                final_response = "죄송합니다. 요청하신 정보를 처리할 수 없습니다. 다른 질문으로 시도해보세요."
            
            state["final_response"] = final_response
            state["next_step"] = "optimize_performance"
            
        except Exception as e:
            state["error"] = f"응답 생성 중 오류: {str(e)}"
        
        return state
    
    def _optimize_performance(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """성능 최적화"""
        try:
            # 성능 메트릭 수집
            metrics = state.get("performance_metrics", {})
            metrics["total_processing_time"] = (datetime.now() - datetime.fromisoformat(metrics.get("timestamp", datetime.now().isoformat()))).total_seconds()
            
            # A/B 테스트를 위한 메트릭 저장
            self.performance_tracker[state["user_query"]] = {
                "query_type": state["query_type"],
                "processing_time": metrics.get("total_processing_time", 0),
                "success": "error" not in state,
                "timestamp": datetime.now().isoformat()
            }
            
            state["performance_metrics"] = metrics
            
        except Exception as e:
            print(f"성능 최적화 중 오류: {e}")
        
        return state
    
    def _handle_error(self, state: EnhancedFinancialWorkflowState) -> EnhancedFinancialWorkflowState:
        """에러 처리"""
        error_message = state.get("error", "알 수 없는 오류가 발생했습니다.")
        state["final_response"] = response_generator.generate_error_response(error_message)
        state["next_step"] = "end"
        return state
    
    def process_query(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """향상된 쿼리 처리"""
        try:
            if self.workflow is None:
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
            initial_state = EnhancedFinancialWorkflowState(
                messages=[HumanMessage(content=user_query)],
                user_query=user_query,
                query_type="",
                financial_data={},
                analysis_result="",
                news_data=[],
                knowledge_context="",
                chart_data=None,
                final_response="",
                error="",
                next_step="",
                user_context={},
                performance_metrics={}
            )
            
            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            # 차트 데이터 추출
            chart_data = result.get("chart_data", None)
            action_data_with_chart = {
                "query_type": result.get("query_type", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "performance_metrics": result.get("performance_metrics", {})
            }
            
            # visualization 쿼리인 경우 차트 포함
            if chart_data and isinstance(chart_data, dict) and "chart" in chart_data:
                action_data_with_chart["chart"] = chart_data["chart"]
                action_data_with_chart["chart_type"] = chart_data.get("chart_type", "unknown")
            
            return {
                "success": True,
                "reply_text": result["final_response"],
                "action_type": "show_chart" if chart_data else "display_info",
                "action_data": action_data_with_chart
            }
            
        except Exception as e:
            return {
                "success": False,
                "reply_text": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                "action_type": "display_info",
                "action_data": {
                    "error": True,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        return self.performance_tracker


# 향상된 워크플로우 서비스 인스턴스
enhanced_financial_workflow = EnhancedFinancialWorkflowService()
