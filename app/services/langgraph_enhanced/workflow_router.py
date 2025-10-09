"""
LangGraph 워크플로우 라우터
모든 분기 처리를 중앙에서 관리
메타 에이전트 시스템으로 최적화된 병렬 실행
"""

from typing import Dict, Any, TypedDict, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langsmith import traceable

from .agents import (
    QueryAnalyzerAgent,
    DataAgent,
    NewsAgent,
    AnalysisAgent,
    KnowledgeAgent,
    VisualizationAgent,
    ResponseAgent,
    # 메타 에이전트
    ServicePlannerAgent,
    ParallelExecutor,
    ResultCombinerAgent,
    ConfidenceCalculatorAgent
)
from .llm_manager import LLMManager


class WorkflowState(TypedDict):
    """워크플로우 상태 정의 (메타 에이전트 필드 추가)"""
    messages: List[Any]
    user_query: str
    query_analysis: Dict[str, Any]
    service_plan: Dict[str, Any]  # ✨ 서비스 전략 계획
    parallel_results: Dict[str, Any]  # ✨ 병렬 실행 결과
    combined_result: Dict[str, Any]  # ✨ 통합 결과
    confidence_evaluation: Dict[str, Any]  # ✨ 신뢰도 평가
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
        
        # 전문 에이전트 초기화
        self.agents = {
            "query_analyzer": QueryAnalyzerAgent(),
            "data_agent": DataAgent(),
            "news_agent": NewsAgent(),
            "analysis_agent": AnalysisAgent(),
            "knowledge_agent": KnowledgeAgent(),
            "visualization_agent": VisualizationAgent(),
            "response_agent": ResponseAgent(),
        }
        
        # 메타 에이전트 초기화 ✨ NEW
        self.service_planner = ServicePlannerAgent()
        self.parallel_executor = ParallelExecutor()
        self.result_combiner = ResultCombinerAgent()
        self.confidence_calculator = ConfidenceCalculatorAgent()
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """워크플로우 구축 (메타 에이전트 통합)"""
        workflow = StateGraph(WorkflowState)
        
        # 전문 에이전트 노드 추가
        workflow.add_node("query_analyzer", self._query_analyzer_node)
        workflow.add_node("service_planner", self._service_planner_node)  # ✨ NEW
        workflow.add_node("parallel_executor", self._parallel_executor_node)  # ✨ NEW
        workflow.add_node("data_agent", self._data_agent_node)
        workflow.add_node("analysis_agent", self._analysis_agent_node)
        workflow.add_node("news_agent", self._news_agent_node)
        workflow.add_node("knowledge_agent", self._knowledge_agent_node)
        workflow.add_node("visualization_agent", self._visualization_agent_node)
        workflow.add_node("result_combiner", self._result_combiner_node)  # ✨ NEW
        workflow.add_node("confidence_calculator", self._confidence_calculator_node)  # ✨ NEW
        workflow.add_node("response_agent", self._response_agent_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # 시작점 설정
        workflow.set_entry_point("query_analyzer")
        
        # 쿼리 분석 → 서비스 계획
        workflow.add_edge("query_analyzer", "service_planner")
        
        # 서비스 계획 → 조건부 라우팅 (복잡도 기반)
        workflow.add_conditional_edges(
            "service_planner",
            self._route_after_planning,
            {
                "parallel": "parallel_executor",  # 병렬 실행 필요
                "data_agent": "data_agent",       # 단순 데이터 조회
                "analysis_agent": "analysis_agent",
                "news_agent": "news_agent",
                "knowledge_agent": "knowledge_agent",
                "visualization_agent": "visualization_agent",
                "response_agent": "response_agent",
                "error": "error_handler"
            }
        )
        
        # 병렬 실행 → 결과 통합
        workflow.add_edge("parallel_executor", "result_combiner")
        
        # 데이터 에이전트 후 라우팅
        workflow.add_conditional_edges(
            "data_agent",
            self._route_after_data,
            {
                "analysis_agent": "analysis_agent",  # ← 투자 질문 시 analysis_agent로!
                "response_agent": "response_agent",
                "result_combiner": "result_combiner",
                "end": END
            }
        )
        
        # 다른 전문 에이전트들 → 결과 통합
        workflow.add_edge("analysis_agent", "result_combiner")
        workflow.add_edge("news_agent", "result_combiner")
        workflow.add_edge("knowledge_agent", "result_combiner")
        workflow.add_edge("visualization_agent", "result_combiner")
        
        # 결과 통합 → 신뢰도 계산
        workflow.add_edge("result_combiner", "confidence_calculator")
        
        # 신뢰도 계산 → 최종 응답
        workflow.add_edge("confidence_calculator", "response_agent")
        
        # 응답 생성 후 종료
        workflow.add_edge("response_agent", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    @traceable(name="query_analyzer_step")
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
    
    @traceable(name="service_planner_step")
    def _service_planner_node(self, state: WorkflowState) -> WorkflowState:
        """서비스 계획 노드 - 복잡도 분석 및 실행 전략 수립"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            
            # 서비스 플래너로 실행 전략 수립
            planner_result = self.service_planner.process(user_query, query_analysis)
            
            if planner_result.get('success') and 'strategy' in planner_result:
                strategy = planner_result['strategy']
                
                # workflow_router가 기대하는 형식으로 변환
                service_plan = {
                    'execution_mode': self._determine_execution_mode(strategy),
                    'agents_to_execute': self._extract_agents_to_execute(strategy, query_analysis),
                    'complexity': query_analysis.get('complexity', 'simple'),
                    'next_agent': self._determine_next_agent(strategy, query_analysis),
                    'strategy': strategy  # 원본 전략 보관
                }
            else:
                # 실패 시 query_analysis 기반으로 폴백
                service_plan = {
                    'execution_mode': 'single',
                    'agents_to_execute': [],
                    'complexity': 'simple',
                    'next_agent': query_analysis.get('next_agent', 'response_agent'),
                    'strategy': {}
                }
            
            state["service_plan"] = service_plan
            
            print(f"🎯 서비스 계획 수립 완료:")
            print(f"   복잡도: {service_plan.get('complexity', 'N/A')}")
            print(f"   실행 모드: {service_plan.get('execution_mode', 'N/A')}")
            print(f"   다음 에이전트: {service_plan.get('next_agent', 'N/A')}")
            agents_list = service_plan.get('agents_to_execute', [])
            if agents_list:
                print(f"   병렬 실행 에이전트: {', '.join(agents_list)}")
            
        except Exception as e:
            print(f"❌ 서비스 플래너 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"서비스 계획 수립 중 오류: {str(e)}"
            # 폴백: query_analysis 기반 단순 계획
            query_analysis = state.get("query_analysis", {})
            state["service_plan"] = {
                "execution_mode": "single",
                "next_agent": query_analysis.get("next_agent", "response_agent"),
                "agents_to_execute": [],
                "complexity": "simple"
            }
        
        return state
    
    def _determine_execution_mode(self, strategy: Dict[str, Any]) -> str:
        """전략에서 실행 모드 결정"""
        execution_strategy = strategy.get('execution_strategy', 'sequential')
        parallel_groups = strategy.get('parallel_groups', [])
        
        # parallel_groups가 있고 2개 이상의 에이전트를 동시 실행하면 parallel
        if parallel_groups and len(parallel_groups) > 0:
            # 첫 번째 그룹에 2개 이상의 에이전트가 있으면 병렬
            if isinstance(parallel_groups[0], list) and len(parallel_groups[0]) > 1:
                return 'parallel'
        
        return 'single'
    
    def _extract_agents_to_execute(self, strategy: Dict[str, Any], query_analysis: Dict[str, Any]) -> List[str]:
        """실행할 에이전트 목록 추출"""
        parallel_groups = strategy.get('parallel_groups', [])
        
        # 병렬 그룹에서 에이전트 추출
        agents = []
        if parallel_groups and len(parallel_groups) > 0:
            # 첫 번째 병렬 그룹의 에이전트들
            first_group = parallel_groups[0]
            if isinstance(first_group, list):
                # 'data', 'news' -> 'data_agent', 'news_agent'
                agents = [f"{agent}_agent" if not agent.endswith('_agent') else agent 
                         for agent in first_group]
        
        # 만약 추출된 에이전트가 없으면 query_analysis에서 추출
        if not agents:
            primary_intent = query_analysis.get('primary_intent', 'general')
            if primary_intent in ['data', 'analysis', 'news', 'knowledge', 'visualization']:
                agents = [f"{primary_intent}_agent"]
        
        return agents
    
    def _determine_next_agent(self, strategy: Dict[str, Any], query_analysis: Dict[str, Any]) -> str:
        """다음 실행할 에이전트 결정 (단일 실행 모드용)"""
        execution_order = strategy.get('execution_order', [])
        
        if execution_order and len(execution_order) > 0:
            first_agent = execution_order[0]
            # 'data' -> 'data_agent'
            if not first_agent.endswith('_agent'):
                first_agent = f"{first_agent}_agent"
            return first_agent
        
        # 폴백: query_analysis에서 가져오기
        return query_analysis.get('next_agent', 'response_agent')
    
    def _parallel_executor_node(self, state: WorkflowState) -> WorkflowState:
        """병렬 실행 노드 - 여러 에이전트 동시 실행"""
        try:
            user_query = state["user_query"]
            query_analysis = state["query_analysis"]
            service_plan = state["service_plan"]
            
            # 병렬 실행할 에이전트 목록
            agents_to_execute = service_plan.get("agents_to_execute", [])
            
            print(f"⚡ 병렬 실행 시작: {', '.join(agents_to_execute)}")
            
            # 병렬 실행 - execute_parallel_sync 메서드 사용 (동기식)
            parallel_results = self.parallel_executor.execute_parallel_sync(
                agents_to_execute,
                self.agents,
                user_query,
                query_analysis
            )
            
            state["parallel_results"] = parallel_results
            
            # 병렬 실행 결과를 state에 반영
            for agent_name, result in parallel_results.items():
                if result.get('success'):
                    if agent_name == "data_agent":
                        state["financial_data"] = result.get('data', {})
                    elif agent_name == "analysis_agent":
                        state["analysis_result"] = result.get('analysis_result', '')
                    elif agent_name == "news_agent":
                        state["news_data"] = result.get('news_data', [])
                        state["news_analysis"] = result.get('analysis_result', '')
                    elif agent_name == "knowledge_agent":
                        state["knowledge_context"] = result.get('explanation_result', '')
                    elif agent_name == "visualization_agent":
                        state["chart_data"] = result.get('chart_data', {})
            
            print(f"✅ 병렬 실행 완료: {len(parallel_results)}개 에이전트")
            
        except Exception as e:
            print(f"❌ 병렬 실행 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"병렬 실행 중 오류: {str(e)}"
            state["parallel_results"] = {}
        
        return state
    
    @traceable(name="result_combiner_step")
    def _result_combiner_node(self, state: WorkflowState) -> WorkflowState:
        """결과 통합 노드 - LLM 기반 지능형 결과 통합"""
        try:
            user_query = state["user_query"]
            
            # 에이전트별로 결과 구조화
            agent_results = {}
            
            # 데이터 에이전트 결과
            if state.get('financial_data'):
                agent_results['data_agent'] = {
                    'success': True,
                    'financial_data': state['financial_data']
                }
            
            # 분석 에이전트 결과
            if state.get('analysis_result'):
                news_data_in_state = state.get('news_data', [])
                print(f"🔍 analysis_agent 결과 생성: news_data={len(news_data_in_state)}개")
                agent_results['analysis_agent'] = {
                    'success': True,
                    'analysis_result': state['analysis_result'],
                    # analysis_agent가 수집한 뉴스도 포함 ✨
                    'news_data': news_data_in_state
                }
            
            # 뉴스 에이전트 결과
            if state.get('news_data') or state.get('news_analysis'):
                agent_results['news_agent'] = {
                    'success': True,
                    'news_data': state.get('news_data', []),
                    'news_analysis': state.get('news_analysis', '')
                }
            
            # 지식 에이전트 결과
            if state.get('knowledge_context'):
                agent_results['knowledge_agent'] = {
                    'success': True,
                    'explanation_result': state['knowledge_context']
                }
            
            # 시각화 에이전트 결과
            if state.get('chart_data'):
                agent_results['visualization_agent'] = {
                    'success': True,
                    'chart_data': state['chart_data'],
                    'chart_analysis': state.get('chart_analysis', '')
                }
            
            print(f"🔗 결과 통합 시작... (에이전트: {list(agent_results.keys())})")
            
            # process 메서드 사용
            combined_result = self.result_combiner.process(
                user_query,
                agent_results,
                state.get('query_analysis', {})
            )
            
            state["combined_result"] = combined_result
            
            print(f"✅ 결과 통합 완료")
            
        except Exception as e:
            print(f"❌ 결과 통합 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"결과 통합 중 오류: {str(e)}"
            state["combined_result"] = {"combined_response": "결과 통합 중 오류가 발생했습니다."}
        
        return state
    
    @traceable(name="confidence_calculator_step")
    def _confidence_calculator_node(self, state: WorkflowState) -> WorkflowState:
        """신뢰도 계산 노드 - 응답 품질 평가"""
        try:
            user_query = state["user_query"]
            combined_result = state.get("combined_result", {})
            
            # process 메서드 사용
            confidence_evaluation = self.confidence_calculator.process(
                user_query,
                combined_result,
                state.get("parallel_results", {})
            )
            
            state["confidence_evaluation"] = confidence_evaluation
            
            print(f"🎯 신뢰도 평가 완료:")
            print(f"   전체 신뢰도: {confidence_evaluation.get('overall_confidence', 0):.2f}")
            print(f"   데이터 품질: {confidence_evaluation.get('data_quality', 0):.2f}")
            print(f"   응답 완성도: {confidence_evaluation.get('response_completeness', 0):.2f}")
            
        except Exception as e:
            print(f"❌ 신뢰도 계산 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"신뢰도 계산 중 오류: {str(e)}"
            state["confidence_evaluation"] = {"overall_confidence": 0.5}
        
        return state
    
    # ========== 공통 에이전트 실행 함수 (중복 제거) ==========
    
    def _execute_agent(self, agent_name: str, state: WorkflowState, 
                      success_handler=None) -> WorkflowState:
        """공통 에이전트 실행 로직"""
        try:
            agent = self.agents[agent_name]
            result = agent.process(state["user_query"], state["query_analysis"])
            
            if result['success']:
                if success_handler:
                    success_handler(state, result)
            else:
                state["error"] = result.get('error', f'{agent_name} 실패')
                
        except Exception as e:
            print(f"❌ {agent_name} 오류: {e}")
            state["error"] = f"{agent_name} 오류: {str(e)}"
        
        return state
    
    @traceable(name="data_agent_step")
    def _data_agent_node(self, state: WorkflowState) -> WorkflowState:
        """데이터 에이전트 노드"""
        def handle_success(s, r):
            s["financial_data"] = r['data']
            if r.get('is_simple_request'):
                s["final_response"] = r['simple_response']
                print(f"⚡ 간단한 주가 응답 생성 완료")
                # LangSmith에 간단한 응답 경로 기록
                from langsmith import get_current_run_tree
                run_tree = get_current_run_tree()
                if run_tree:
                    run_tree.add_metadata({"response_type": "simple_stock_price", "bypassed_response_agent": True})
            else:
                print(f"📊 데이터 조회 완료")
        return self._execute_agent("data_agent", state, handle_success)
    
    def _analysis_agent_node(self, state: WorkflowState) -> WorkflowState:
        """분석 에이전트 노드 (async 처리 - RAG + 뉴스 통합)"""
        try:
            import asyncio
            import concurrent.futures
            
            agent = self.agents["analysis_agent"]
            
            # 동기 함수에서 비동기 함수 실행
            # 이미 실행 중인 이벤트 루프가 있으므로 새 스레드에서 실행
            def run_async_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        agent.process(state["user_query"], state["query_analysis"])
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_in_thread)
                result = future.result(timeout=60)  # 60초 타임아웃
            
            if result['success']:
                state["analysis_result"] = result['analysis_result']
                if result.get('financial_data'):
                    state["financial_data"] = result['financial_data']
                # 뉴스 데이터 저장 ✨
                if result.get('news_data'):
                    state["news_data"] = result['news_data']
                    print(f"🔍 _analysis_agent_node: news_data 저장 → {len(result['news_data'])}개")
                else:
                    print(f"🔍 _analysis_agent_node: result에 news_data 없음")
                print(f"📈 통합 투자 분석 완료: {result.get('stock_symbol', '일반')}")
                print(f"   - RAG 컨텍스트: {result.get('rag_context_length', 0)} 글자")
                print(f"   - 뉴스: {result.get('news_count', 0)}건")
            else:
                state["error"] = result.get('error', 'analysis_agent 실패')
                
        except Exception as e:
            print(f"❌ analysis_agent 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"analysis_agent 오류: {str(e)}"
        
        return state
    
    def _news_agent_node(self, state: WorkflowState) -> WorkflowState:
        """뉴스 에이전트 노드 (async 처리 - sync wrapper)"""
        def handle_success(s, r):
            s["news_data"] = r['news_data']
            s["news_analysis"] = r['analysis_result']
            print(f"📰 뉴스 수집 및 분석 완료: {len(r['news_data'])}건")
        
        # NewsAgent가 async이므로 동기적으로 실행
        try:
            import asyncio
            agent = self.agents["news_agent"]
            
            # 현재 이벤트 루프가 실행 중인지 확인
            try:
                loop = asyncio.get_running_loop()
                # 이미 루프가 실행 중이면 run_until_complete 사용 불가
                # 대신 동기 방식으로 처리
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        agent.process(state["user_query"], state["query_analysis"])
                    )
                    result = future.result(timeout=60)  # 60초 타임아웃
            except RuntimeError:
                # 루프가 실행 중이지 않으면 새로 만들어서 실행
                result = asyncio.run(
                    agent.process(state["user_query"], state["query_analysis"])
                )
                
            if result['success']:
                handle_success(state, result)
            else:
                state["error"] = result.get('error', 'news_agent 실패')
                
        except Exception as e:
            print(f"❌ news_agent 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"news_agent 오류: {str(e)}"
        
        return state
    
    def _knowledge_agent_node(self, state: WorkflowState) -> WorkflowState:
        """지식 에이전트 노드"""
        def handle_success(s, r):
            s["knowledge_context"] = r['explanation_result']
            print(f"📚 지식 교육 완료: {r.get('concept', '일반')}")
        return self._execute_agent("knowledge_agent", state, handle_success)
    
    def _visualization_agent_node(self, state: WorkflowState) -> WorkflowState:
        """시각화 에이전트 노드"""
        def handle_success(s, r):
            s["chart_data"] = r['chart_data']
            s["chart_analysis"] = r['analysis_result']
            if r.get('chart_image'):
                s["chart_image"] = r['chart_image']
            print(f"📊 차트 생성 및 분석 완료")
        return self._execute_agent("visualization_agent", state, handle_success)
    
    @traceable(name="response_agent_step")
    def _response_agent_node(self, state: WorkflowState) -> WorkflowState:
        """응답 에이전트 노드"""
        try:
            # 디버그: state 키 확인
            print(f"🔍 response_agent_node state 키: {list(state.keys())}")
            print(f"   financial_data 있음: {'financial_data' in state}")
            if 'financial_data' in state:
                fd = state['financial_data']
                print(f"   financial_data 타입: {type(fd)}, 비어있음: {not fd if isinstance(fd, dict) else 'N/A'}")
            
            # 메타 에이전트의 통합 결과가 있으면 우선 사용
            combined_result = state.get("combined_result", {})
            print(f"   combined_result 있음: {bool(combined_result)}")
            print(f"   combined_response 있음: {bool(combined_result.get('combined_response'))}")
            
            if combined_result.get("combined_response"):
                state["final_response"] = combined_result["combined_response"]
                print(f"💬 메타 에이전트 통합 응답 사용")
                return state
            
            # 통합 결과가 없으면 기존 방식으로 응답 생성
            collected_data = {
                'financial_data': state.get('financial_data', {}),
                'analysis_result': state.get('analysis_result', ''),
                'news_data': state.get('news_data', []),
                'news_analysis': state.get('news_analysis', ''),
                'knowledge_explanation': state.get('knowledge_context', ''),
                'chart_data': state.get('chart_data', {}),
                'chart_analysis': state.get('chart_analysis', '')
            }
            
            print(f"📦 collected_data 구성 완료:")
            print(f"   - financial_data: {bool(collected_data['financial_data'])}")
            print(f"   - analysis_result: {bool(collected_data['analysis_result'])}")
            print(f"   - news_data: {len(collected_data.get('news_data', []))}")
            
            result = self.agents["response_agent"].process(
                state["user_query"], 
                state["query_analysis"], 
                collected_data
            )
            
            if result['success']:
                state["final_response"] = result['final_response']
                print(f"💬 기본 응답 생성 완료")
            else:
                state["error"] = result.get('error', '응답 생성 실패')
                
        except Exception as e:
            print(f"❌ 응답 에이전트 오류: {e}")
            import traceback
            traceback.print_exc()
            state["error"] = f"응답 에이전트 오류: {str(e)}"
        
        return state
    
    def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """에러 핸들러 노드"""
        error_msg = state.get("error", "알 수 없는 오류가 발생했습니다.")
        state["final_response"] = f"죄송합니다. {error_msg} 다른 질문으로 시도해보세요."
        return state
    
    # ========== 라우팅 함수들 ==========
    
    def _route_after_planning(self, state: WorkflowState) -> str:
        """서비스 계획 후 라우팅"""
        service_plan = state.get("service_plan", {})
        execution_mode = service_plan.get("execution_mode", "single")
        
        # 에러가 있으면 에러 핸들러로
        if state.get("error"):
            return "error"
        
        # 병렬 실행 모드 - 여러 에이전트 동시 실행
        if execution_mode == "parallel":
            agents_to_execute = service_plan.get("agents_to_execute", [])
            if len(agents_to_execute) > 1:
                return "parallel"
        
        # 단일 에이전트 실행 모드
        next_agent = service_plan.get("next_agent", "response_agent")
        
        # 병렬 실행 에이전트 목록이 있으면 첫 번째 실행
        agents_to_execute = service_plan.get("agents_to_execute", [])
        if agents_to_execute and len(agents_to_execute) > 0:
            # 병렬 실행할 에이전트가 1개만 있어도 그것을 실행
            next_agent = agents_to_execute[0]
        
        return next_agent
    
    def _route_after_query_analysis(self, state: WorkflowState) -> str:
        """쿼리 분석 후 라우팅"""
        return state.get("next_agent", "response_agent")
    
    def _route_after_data(self, state: WorkflowState) -> str:
        """데이터 에이전트 후 라우팅 (투자 질문 감지)"""
        service_plan = state.get("service_plan", {})
        execution_mode = service_plan.get("execution_mode", "single")
        query_analysis = state.get("query_analysis", {})
        
        # 💡 투자 질문 감지 (최우선 체크!)
        is_investment_question = query_analysis.get('is_investment_question', False)
        
        if is_investment_question:
            # 투자 질문이면 무조건 analysis_agent로!
            print(f"💡 투자 질문 감지! 심층 분석을 위해 analysis_agent로 라우팅")
            state['final_response'] = None  # 혹시 설정되었다면 리셋
            return "analysis_agent"
        
        # 간단한 주가 요청이고 이미 응답이 생성된 경우
        if state.get("final_response"):
            # 투자 질문 아니면 그대로 종료
            return "end"
        
        # 병렬 실행 모드였다면 결과 통합으로
        if execution_mode == "parallel":
            return "result_combiner"
        
        # 일반 모드는 응답 생성으로
        return "response_agent"
    
    @traceable(name="intelligent_workflow", run_type="chain", metadata={"workflow_type": "meta_agent_enhanced"})
    def process_query(self, user_query: str, user_id: str = None) -> Dict[str, Any]:
        """사용자 쿼리 처리"""
        try:
            # 초기 상태 설정
            initial_state = WorkflowState(
                messages=[HumanMessage(content=user_query)],
                user_query=user_query,
                query_analysis={},
                service_plan={},  # ✨ 메타 에이전트 필드
                parallel_results={},  # ✨ 메타 에이전트 필드
                combined_result={},  # ✨ 메타 에이전트 필드
                confidence_evaluation={},  # ✨ 메타 에이전트 필드
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
            
            # 디버그: result 타입 확인
            print(f"\n🔍 workflow.invoke 결과 타입: {type(result)}")
            print(f"🔍 result 키: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            if isinstance(result, dict):
                print(f"🔍 final_response: '{result.get('final_response', 'NONE')[:100]}'")
                print(f"🔍 combined_result 있음: {bool(result.get('combined_result'))}")
            
            # 응답 형식 변환
            return {
                "success": "error" not in result or not result.get("error"),
                "reply_text": result.get("final_response", ""),
                "action_type": "intelligent_agent_system",
                "action_data": {
                    "query_analysis": result.get("query_analysis", {}),
                    "service_plan": result.get("service_plan", {}),
                    "confidence_evaluation": result.get("confidence_evaluation", {}),
                    "agent_history": result.get("agent_history", []),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "workflow_type": "meta_agent_enhanced"
                },
                "chart_image": result.get("chart_data", {}).get("chart_base64") if result.get("chart_data") else None
            }
            
        except Exception as e:
            print(f"❌ 워크플로우 실행 오류: {e}")
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

            # 응답 형식 변환
            return {
                "success": "error" not in result or not result.get("error"),
                "reply_text": result.get("final_response", ""),
                "action_type": "intelligent_agent_system",
                "action_data": {
                    "query_analysis": result.get("query_analysis", {}),
                    "service_plan": result.get("service_plan", {}),
                    "confidence_evaluation": result.get("confidence_evaluation", {}),
                    "agent_history": result.get("agent_history", []),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "workflow_type": "meta_agent_enhanced"
                },
                "chart_image": result.get("chart_data", {}).get("chart_base64") if result.get("chart_data") else None
            }
            
        except Exception as e:
            print(f"❌ 워크플로우 실행 오류: {e}")
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
