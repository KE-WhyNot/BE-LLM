"""
LangGraph 워크플로우 라우터
모든 분기 처리를 중앙에서 관리
"""

from typing import Dict, Any, TypedDict, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from .agents import (
    QueryAnalyzerAgent,
    DataAgent,
    NewsAgent,
    AnalysisAgent,
    KnowledgeAgent,
    VisualizationAgent,
    ResponseAgent
)
from .llm_manager import LLMManager


class WorkflowState(TypedDict):
    """워크플로우 상태 정의"""
    messages: List[Any]
    user_query: str
    query_analysis: Dict[str, Any]
    financial_data: Dict[str, Any]
    analysis_result: str
    news_data: List[Dict[str, Any]]
    knowledge_context: str
    chart_data: Optional[Dict[str, Any]]
    final_response: str
    error: str
    next_agent: str
    agent_history: List[str]


class WorkflowRouter:
    """워크플로우 라우터 - 모든 분기 처리 중앙 관리"""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        
        # 에이전트 초기화
        self.agents = {
            "query_analyzer": QueryAnalyzerAgent(),
            "data_agent": DataAgent(),
            "news_agent": NewsAgent(),
            "analysis_agent": AnalysisAgent(),
            "knowledge_agent": KnowledgeAgent(),
            "visualization_agent": VisualizationAgent(),
            "response_agent": ResponseAgent(),
        }
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """워크플로우 구축"""
        workflow = StateGraph(WorkflowState)
        
        # 에이전트 노드 추가
        workflow.add_node("query_analyzer", self._query_analyzer_node)
        workflow.add_node("data_agent", self._data_agent_node)
        workflow.add_node("analysis_agent", self._analysis_agent_node)
        workflow.add_node("news_agent", self._news_agent_node)
        workflow.add_node("knowledge_agent", self._knowledge_agent_node)
        workflow.add_node("visualization_agent", self._visualization_agent_node)
        workflow.add_node("response_agent", self._response_agent_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # 시작점 설정
        workflow.set_entry_point("query_analyzer")
        
        # 에이전트 간 연결
        workflow.add_conditional_edges(
            "query_analyzer",
            self._route_after_query_analysis,
            {
                "data_agent": "data_agent",
                "analysis_agent": "analysis_agent", 
                "news_agent": "news_agent",
                "knowledge_agent": "knowledge_agent",
                "visualization_agent": "visualization_agent",
                "response_agent": "response_agent",
                "error": "error_handler"
            }
        )
        
        # 데이터 에이전트 후 라우팅
        workflow.add_conditional_edges(
            "data_agent",
            self._route_after_data,
            {
                "response_agent": "response_agent",
                "end": END
            }
        )
        
        # 다른 에이전트들은 모두 응답 에이전트로
        workflow.add_edge("analysis_agent", "response_agent")
        workflow.add_edge("news_agent", "response_agent")
        workflow.add_edge("knowledge_agent", "response_agent")
        workflow.add_edge("visualization_agent", "response_agent")
        
        # 응답 생성 후 종료
        workflow.add_edge("response_agent", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    def _query_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """쿼리 분석 노드"""
        try:
            user_query = state["user_query"]
            analyzer = self.agents["query_analyzer"]
            
            query_analysis = analyzer.process(user_query)
            state["query_analysis"] = query_analysis
            state["next_agent"] = query_analysis.get("next_agent", "response_agent")
            
            print(f"🔍 쿼리 분석 완료: {query_analysis['primary_intent']} (신뢰도: {query_analysis['confidence']:.2f})")
            print(f"   근거: {query_analysis['reasoning']}")
            print(f"   다음 에이전트: {state['next_agent']}")
            
        except Exception as e:
            print(f"❌ 쿼리 분석 에이전트 오류: {e}")
            state["error"] = f"쿼리 분석 중 오류: {str(e)}"
            state["next_agent"] = "error_handler"
        
        return state
    
    def _data_agent_node(self, state: WorkflowState) -> WorkflowState:
        """데이터 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            data_agent = self.agents["data_agent"]
            
            result = data_agent.process(user_query, query_analysis)
            
            if result['success']:
                state["financial_data"] = result['data']
                
                # 간단한 주가 요청이면 바로 응답 생성
                if result.get('is_simple_request', False):
                    state["final_response"] = result['simple_response']
                    print(f"⚡ 간단한 주가 응답 생성 완료")
                else:
                    print(f"📊 데이터 조회 완료")
            else:
                state["error"] = result.get('error', '데이터 조회 실패')
            
        except Exception as e:
            print(f"❌ 데이터 에이전트 오류: {e}")
            state["error"] = f"데이터 에이전트 오류: {str(e)}"
        
        return state
    
    def _analysis_agent_node(self, state: WorkflowState) -> WorkflowState:
        """분석 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            analysis_agent = self.agents["analysis_agent"]
            
            result = analysis_agent.process(user_query, query_analysis)
            
            if result['success']:
                state["analysis_result"] = result['analysis_result']
                if result.get('financial_data'):
                    state["financial_data"] = result['financial_data']
                print(f"📈 투자 분석 완료: {result.get('stock_symbol', '일반')}")
            else:
                state["error"] = result.get('error', '투자 분석 실패')
            
        except Exception as e:
            print(f"❌ 분석 에이전트 오류: {e}")
            state["error"] = f"분석 에이전트 오류: {str(e)}"
        
        return state
    
    def _news_agent_node(self, state: WorkflowState) -> WorkflowState:
        """뉴스 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            news_agent = self.agents["news_agent"]
            
            result = news_agent.process(user_query, query_analysis)
            
            if result['success']:
                state["news_data"] = result['news_data']
                state["news_analysis"] = result['analysis_result']
                print(f"📰 뉴스 수집 및 분석 완료: {len(result['news_data'])}건")
            else:
                state["error"] = result.get('error', '뉴스 수집 실패')
            
        except Exception as e:
            print(f"❌ 뉴스 에이전트 오류: {e}")
            state["error"] = f"뉴스 에이전트 오류: {str(e)}"
        
        return state
    
    def _knowledge_agent_node(self, state: WorkflowState) -> WorkflowState:
        """지식 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            knowledge_agent = self.agents["knowledge_agent"]
            
            result = knowledge_agent.process(user_query, query_analysis)
            
            if result['success']:
                state["knowledge_context"] = result['explanation_result']
                print(f"📚 지식 교육 완료: {result.get('concept', '일반')}")
            else:
                state["error"] = result.get('error', '지식 설명 실패')
            
        except Exception as e:
            print(f"❌ 지식 에이전트 오류: {e}")
            state["error"] = f"지식 에이전트 오류: {str(e)}"
        
        return state
    
    def _visualization_agent_node(self, state: WorkflowState) -> WorkflowState:
        """시각화 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            visualization_agent = self.agents["visualization_agent"]
            
            result = visualization_agent.process(user_query, query_analysis)
            
            if result['success']:
                state["chart_data"] = result['chart_data']
                state["chart_analysis"] = result['analysis_result']
                if result.get('chart_image'):
                    state["chart_image"] = result['chart_image']
                print(f"📊 차트 생성 및 분석 완료")
            else:
                state["error"] = result.get('error', '차트 생성 실패')
            
        except Exception as e:
            print(f"❌ 시각화 에이전트 오류: {e}")
            state["error"] = f"시각화 에이전트 오류: {str(e)}"
        
        return state
    
    def _response_agent_node(self, state: WorkflowState) -> WorkflowState:
        """응답 에이전트 노드"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            response_agent = self.agents["response_agent"]
            
            # 수집된 데이터 통합
            collected_data = {
                'financial_data': state.get('financial_data', {}),
                'analysis_result': state.get('analysis_result', ''),
                'news_data': state.get('news_data', []),
                'news_analysis': state.get('news_analysis', ''),
                'knowledge_explanation': state.get('knowledge_context', ''),
                'chart_data': state.get('chart_data', {}),
                'chart_analysis': state.get('chart_analysis', '')
            }
            
            result = response_agent.process(user_query, query_analysis, collected_data)
            
            if result['success']:
                state["final_response"] = result['final_response']
                print(f"💬 최종 응답 생성 완료")
            else:
                state["error"] = result.get('error', '응답 생성 실패')
            
        except Exception as e:
            print(f"❌ 응답 에이전트 오류: {e}")
            state["error"] = f"응답 에이전트 오류: {str(e)}"
        
        return state
    
    def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """에러 핸들러 노드"""
        error_msg = state.get("error", "알 수 없는 오류가 발생했습니다.")
        state["final_response"] = f"죄송합니다. {error_msg} 다른 질문으로 시도해보세요."
        return state
    
    def _route_after_query_analysis(self, state: WorkflowState) -> str:
        """쿼리 분석 후 라우팅"""
        return state.get("next_agent", "response_agent")
    
    def _route_after_data(self, state: WorkflowState) -> str:
        """데이터 에이전트 후 라우팅"""
        # 간단한 주가 요청이고 이미 응답이 생성된 경우 바로 종료
        if state.get("final_response"):
            return "end"
        else:
            return "response_agent"
    
    def _build_response_context(self, state: WorkflowState) -> str:
        """응답 컨텍스트 구축"""
        context_parts = []
        
        if state.get("financial_data"):
            context_parts.append(f"📊 금융 데이터: {state['financial_data']}")
        
        if state.get("analysis_result"):
            context_parts.append(f"📈 분석 결과: {state['analysis_result']}")
        
        if state.get("news_data"):
            news_summary = "\n".join([f"- {news['title']}" for news in state['news_data'][:3]])
            context_parts.append(f"📰 뉴스 정보:\n{news_summary}")
        
        if state.get("knowledge_context"):
            context_parts.append(f"📚 지식 정보: {state['knowledge_context']}")
        
        if state.get("chart_data"):
            context_parts.append("📊 차트가 생성되었습니다.")
        
        return "\n\n".join(context_parts) if context_parts else "수집된 정보가 없습니다."
    
    def process_query(self, user_query: str, user_id: str = None) -> Dict[str, Any]:
        """사용자 쿼리 처리"""
        try:
            # 초기 상태 설정
            initial_state = WorkflowState(
                messages=[HumanMessage(content=user_query)],
                user_query=user_query,
                query_analysis={},
                financial_data={},
                analysis_result="",
                news_data=[],
                knowledge_context="",
                chart_data=None,
                final_response="",
                error="",
                next_agent="",
                agent_history=[]
            )
            
            # 워크플로우 실행
            result = self.workflow.invoke(initial_state)
            
            # 응답 형식 변환
            return {
                "success": "error" not in result,
                "reply_text": result.get("final_response", ""),
                "action_type": "llm_agent_analysis",
                "action_data": {
                    "query_analysis": result.get("query_analysis", {}),
                    "agent_history": result.get("agent_history", []),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "workflow_type": "clean_agent_system"
                },
                "chart_image": result.get("chart_data", {}).get("chart_base64") if result.get("chart_data") else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "reply_text": f"시스템 오류가 발생했습니다: {str(e)}",
                "action_type": "error",
                "action_data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id
                }
            }
