"""금융 워크플로우 - LangGraph 기반 분기 처리"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

from app.config import settings
from app.services.workflow_components.query_classifier_service import query_classifier
from app.services.workflow_components.financial_data_service import financial_data_service
from app.services.workflow_components.analysis_service import analysis_service
from app.services.workflow_components.news_service import news_service
from app.services.workflow_components.response_generator_service import response_generator
from app.services.workflow_components.visualization_service import visualization_service
from app.services.rag_service import rag_service

# 간소화된 지능형 워크플로우 (선택적 사용)
try:
    from app.services.langgraph_enhanced import simplified_intelligent_workflow
    INTELLIGENT_WORKFLOW_AVAILABLE = True
except ImportError:
    INTELLIGENT_WORKFLOW_AVAILABLE = False


class FinancialWorkflowState(TypedDict):
    """금융 워크플로우 상태 정의"""
    messages: Annotated[List[BaseMessage], "대화 메시지들"]
    user_query: str
    query_type: str  # "data", "analysis", "news", "knowledge", "visualization", "general"
    financial_data: Dict[str, Any]
    analysis_result: str
    news_data: List[Dict[str, Any]]
    knowledge_context: str
    chart_data: Optional[Dict[str, Any]]  # visualization용
    final_response: str
    error: str
    next_step: str


class FinancialWorkflowService:
    """LangGraph를 활용한 금융 워크플로우 서비스 - 분기 처리 전담"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.workflow = self._create_workflow()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        # Google Gemini 우선 사용
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
        else:
            # API 키가 없을 때는 더미 LLM 반환 (테스트용)
            print("⚠️ API 키가 설정되지 않았습니다. 워크플로우 테스트 모드로 실행됩니다.")
            return None
    
    def _create_workflow(self):
        """LangGraph 워크플로우 생성 - 분기 처리만 담당"""
        if self.llm is None:
            # API 키가 없을 때는 더미 워크플로우 반환
            return None
            
        workflow = StateGraph(FinancialWorkflowState)
        
        # 노드들 추가 - 각 노드는 해당 서비스를 호출만 함
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("get_financial_data", self._get_financial_data)
        workflow.add_node("search_knowledge", self._search_knowledge)
        workflow.add_node("get_news", self._get_news)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("create_visualization", self._create_visualization)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)
        
        # 엣지들 추가 - 분기 처리 로직
        workflow.set_entry_point("classify_query")
        
        # 쿼리 분류 후 라우팅
        workflow.add_conditional_edges(
            "classify_query",
            self._route_after_classification,
            {
                "data": "get_financial_data",
                "analysis": "get_financial_data",  # analysis도 먼저 데이터 조회
                "news": "get_news",
                "knowledge": "search_knowledge",
                "visualization": "get_financial_data",  # 시각화도 먼저 데이터 조회
                "general": "generate_response",
                "error": "handle_error"
            }
        )
        
        # 데이터 조회 후 조건부 라우팅
        workflow.add_conditional_edges(
            "get_financial_data",
            self._route_after_data,
            {
                "analyze": "analyze_data",
                "visualization": "create_visualization",
                "error": "handle_error"
            }
        )
        
        # 분석 후 응답 생성
        workflow.add_edge("analyze_data", "generate_response")
        
        # 뉴스 조회 후 응답 생성
        workflow.add_edge("get_news", "generate_response")
        
        # 지식 검색 후 응답 생성
        workflow.add_edge("search_knowledge", "generate_response")
        
        # 시각화 후 응답 생성
        workflow.add_edge("create_visualization", "generate_response")
        
        # 응답 생성 후 종료
        workflow.add_edge("generate_response", END)
        
        # 에러 처리 후 종료
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """쿼리 분류 - query_classifier_service 호출"""
        query = state["user_query"]
        query_type = query_classifier.classify(query)
        
        state["query_type"] = query_type
        state["next_step"] = query_type
        
        return state
    
    def _route_after_classification(self, state: FinancialWorkflowState) -> str:
        """분류 후 라우팅"""
        return state["query_type"]
    
    def _route_after_data(self, state: FinancialWorkflowState) -> str:
        """데이터 조회 후 라우팅"""
        if "error" in state and state["error"]:
            return "error"
        elif state.get("query_type") == "visualization":
            return "visualization"
        else:
            return "analyze"
    
    def _get_financial_data(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """금융 데이터 조회 - financial_data_service 호출"""
        try:
            query = state["user_query"]
            data = financial_data_service.get_financial_data(query)
            
            if "error" in data:
                state["error"] = data["error"]
            else:
                state["financial_data"] = data
            
        except Exception as e:
            from app.utils.common_utils import ErrorHandler
            state["error"] = ErrorHandler.handle_workflow_error(e, "데이터 조회")
        
        return state
    
    def _analyze_data(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """데이터 분석 - analysis_service 호출"""
        try:
            if "financial_data" not in state or not state["financial_data"]:
                state["error"] = "분석할 데이터가 없습니다."
                state["next_step"] = "error"
                return state
            
            data = state["financial_data"]
            analysis_result = analysis_service.analyze_financial_data(data)
            
            state["analysis_result"] = analysis_result
            state["next_step"] = "generate_response"
            
        except Exception as e:
            from app.utils.common_utils import ErrorHandler
            state["error"] = ErrorHandler.handle_workflow_error(e, "분석")
            state["next_step"] = "error"
        
        return state
    
    def _get_news(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """뉴스 조회 - news_service 호출"""
        try:
            query = state["user_query"]
            news = news_service.get_financial_news(query)
            state["news_data"] = news
            state["next_step"] = "generate_response"
            
        except Exception as e:
            from app.utils.common_utils import ErrorHandler
            state["error"] = ErrorHandler.handle_workflow_error(e, "뉴스 조회")
            state["next_step"] = "error"
        
        return state
    
    def _search_knowledge(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """지식 검색 - rag_service 호출"""
        try:
            query = state["user_query"]
            context = rag_service.get_context_for_query(query)
            state["knowledge_context"] = context
            state["next_step"] = "generate_response"
            
        except Exception as e:
            from app.utils.common_utils import ErrorHandler
            state["error"] = ErrorHandler.handle_workflow_error(e, "지식 검색")
            state["next_step"] = "error"
        
        return state
    
    def _create_visualization(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """시각화 생성 - visualization_service 호출"""
        try:
            query = state["user_query"]
            financial_data = state.get("financial_data", {})
            
            # 이미 조회된 금융 데이터를 사용하여 차트 데이터 생성
            state["chart_data"] = {
                "query": query,
                "data": financial_data
            }
            
        except Exception as e:
            state["error"] = f"시각화 생성 중 오류: {str(e)}"
        
        return state
    
    def _generate_response(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """최종 응답 생성 - response_generator 호출"""
        try:
            query_type = state.get("query_type", "general")
            
            # 쿼리 타입에 따라 적절한 응답 생성
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
                # 시각화 응답은 dict 형태로 반환됨 (text + chart)
                viz_response = response_generator.generate_visualization_response(
                    state["chart_data"]["query"],
                    state["chart_data"]["data"]
                )
                # chart_data를 state에 저장 (chatbot_service에서 사용)
                state["chart_data"] = viz_response
                final_response = viz_response.get("text", "차트가 생성되었습니다.")
                
            else:
                # 일반적인 질문에 대한 응답
                final_response = response_generator.generate_general_response()
            
            # 빈 응답 방지 폴백
            if not final_response or len(final_response.strip()) < 10:
                final_response = "죄송합니다. 요청하신 정보를 처리할 수 없습니다. 다른 질문으로 시도해보세요."
            
            state["final_response"] = final_response
            state["next_step"] = "end"
            
        except Exception as e:
            state["error"] = f"응답 생성 중 오류: {str(e)}"
            state["next_step"] = "error"
        
        return state
    
    def _handle_error(self, state: FinancialWorkflowState) -> FinancialWorkflowState:
        """에러 처리 - response_generator 호출"""
        error_msg = state.get("error", "알 수 없는 오류가 발생했습니다.")
        state["final_response"] = response_generator.generate_error_response(error_msg)
        state["next_step"] = "end"
        return state
    
    def process_query(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자 쿼리 처리 - 메인 진입점 (자동 워크플로우 선택)"""
        try:
            # API 키 확인
            if self.workflow is None:
                return self._create_api_key_missing_response(user_id)
            
            # 복잡도에 따른 자동 워크플로우 선택
            use_intelligent = self._should_use_intelligent_workflow(user_query)
            
            if use_intelligent and INTELLIGENT_WORKFLOW_AVAILABLE:
                return self._process_with_intelligent_workflow(user_query, user_id)
            else:
                # 기본 워크플로우 실행
                result = self._execute_workflow(user_query)
                return self._create_success_response(result, user_id)
            
        except Exception as e:
            return self._create_error_response(e, user_id)
    
    def _should_use_intelligent_workflow(self, user_message: str) -> bool:
        """지능형 워크플로우 사용 여부 자동 결정"""
        # 복잡한 질문 키워드들
        complex_keywords = [
            "종합", "비교", "분석", "예측", "추천", "의견", "고려",
            "여러", "다양한", "상세", "심화", "고급", "전문적"
        ]
        
        # 멀티 서비스가 필요한 키워드들
        multi_service_keywords = [
            "뉴스", "차트", "분석", "지식", "설명", "현재가", "예측"
        ]
        
        # 질문 복잡도 점수 계산
        complexity_score = 0
        service_count = 0
        
        message_lower = user_message.lower()
        
        # 복잡도 키워드 체크
        for keyword in complex_keywords:
            if keyword in message_lower:
                complexity_score += 2
        
        # 멀티 서비스 키워드 체크
        for keyword in multi_service_keywords:
            if keyword in message_lower:
                service_count += 1
        
        # 문장 길이 고려
        if len(user_message) > 30:
            complexity_score += 1
        
        # 여러 문장이나 질문이 있는 경우
        if user_message.count("?") > 1 or user_message.count("그리고") > 0:
            complexity_score += 2
        
        # 지능형 워크플로우 사용 조건
        use_intelligent = (
            complexity_score >= 3 or  # 복잡도 점수가 3 이상
            service_count >= 3 or    # 3개 이상의 서비스가 필요
            len(user_message) > 50   # 긴 질문
        )
        
        if use_intelligent:
            print(f"🧠 지능형 워크플로우 자동 선택: 복잡도={complexity_score}, 서비스={service_count}")
        else:
            print(f"⚡ 기본 워크플로우 자동 선택: 복잡도={complexity_score}, 서비스={service_count}")
        
        return use_intelligent
    
    def _process_with_intelligent_workflow(self, user_query: str, user_id: Optional[str]) -> Dict[str, Any]:
        """지능형 멀티 서비스 워크플로우로 처리"""
        try:
            print(f"🧠 지능형 멀티 서비스 워크플로우 사용")
            
            result = simplified_intelligent_workflow.process_query(
                query=user_query,
                user_id=int(user_id) if user_id else 1,
                session_id=f"intelligent_{user_id or 'default'}"
            )
            
            # 응답 형식을 기존 형식에 맞게 변환
            return {
                "success": "error" not in result,
                "reply_text": result.get("response", ""),
                "action_type": "intelligent_analysis",
                "action_data": {
                    "query_complexity": result.get("query_complexity", ""),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "services_used": result.get("services_used", []),
                    "fallback_used": result.get("fallback_used", []),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "workflow_type": "intelligent_multi_service"
                },
                "chart_image": result.get("chart_data", {}).get("chart_base64") if result.get("chart_data") else None
            }
            
        except Exception as e:
            print(f"❌ 지능형 워크플로우 실패, 기본 워크플로우로 폴백: {e}")
            # 폴백: 기본 워크플로우 사용
            result = self._execute_workflow(user_query)
            return self._create_success_response(result, user_id)
    
    def _create_api_key_missing_response(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """API 키가 없을 때의 응답 생성"""
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
    
    def _execute_workflow(self, user_query: str) -> FinancialWorkflowState:
        """워크플로우 실행"""
        initial_state = FinancialWorkflowState(
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
            next_step=""
        )
        
        return self.workflow.invoke(initial_state)
    
    def _create_success_response(self, result: FinancialWorkflowState, user_id: Optional[str] = None) -> Dict[str, Any]:
        """성공 응답 생성"""
        chart_data = result.get("chart_data", None)
        action_data = {
            "query_type": result.get("query_type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        # visualization 쿼리인 경우 차트 포함
        if chart_data and isinstance(chart_data, dict) and "chart" in chart_data:
            action_data["chart"] = chart_data["chart"]
            action_data["chart_type"] = chart_data.get("chart_type", "unknown")
        
        return {
            "success": True,
            "reply_text": result["final_response"],
            "action_type": "show_chart" if chart_data else "display_info",
            "action_data": action_data
        }
    
    def _create_error_response(self, error: Exception, user_id: Optional[str] = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "success": False,
            "reply_text": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(error)}",
            "action_type": "display_info",
            "action_data": {
                "error": str(error),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
        }


# 전역 워크플로우 서비스 인스턴스
financial_workflow = FinancialWorkflowService()

