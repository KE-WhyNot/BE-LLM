from typing import Dict, Any, Optional
from datetime import datetime
from app.services.chatbot.financial_workflow import financial_workflow
from app.services.monitoring_service import monitoring_service
from app.services.pinecone_rag_service import pinecone_rag_service
from app.schemas.chat_schema import ChatRequest, ChatResponse

class FinancialChatbotService:
    """금융 전문가 챗봇 서비스"""
    
    def __init__(self):
        self.financial_workflow = financial_workflow
        self.monitoring_service = monitoring_service
        self.pinecone_rag_service = pinecone_rag_service
        self._initialize_services()
    
    def _initialize_services(self):
        """서비스 초기화"""
        try:
            # Pinecone RAG 서비스 초기화
            self.pinecone_rag_service.initialize()
            print("금융 전문가 챗봇 서비스가 초기화되었습니다.")
        except Exception as e:
            print(f"서비스 초기화 중 오류: {e}")
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """채팅 요청 처리"""
        try:
            # 모니터링 시작
            start_time = datetime.now()
            
            # 사용자 메시지 분석
            user_message = request.message.strip()
            if not user_message:
                return self._create_error_response("메시지를 입력해주세요.")
            
            # LangGraph 워크플로우로 일원화 라우팅 (자동 워크플로우 선택)
            result = self.financial_workflow.process_query(
                user_message,
                user_id=request.user_id
            )
            
            # 응답 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 모니터링 로그
            self.monitoring_service.trace_query(
                user_message,
                result["reply_text"],
                {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "processing_time": processing_time,
                    "success": result["success"],
                    "query_type": result.get("action_data", {}).get("query_type", "unknown")
                }
            )
            
            # 응답 생성
            if result["success"]:
                # 차트 이미지가 있는지 확인
                chart_image = None
                if "chart" in result.get("action_data", {}):
                    chart_image = result["action_data"]["chart"]
                
                # Pinecone RAG는 에이전트 내부에서만 사용 (KnowledgeAgent, AnalysisAgent)
                # 최종 응답에는 포함하지 않음
                pinecone_results = None
                
                return ChatResponse(
                    reply_text=result["reply_text"],
                    action_type=result["action_type"],
                    action_data=result["action_data"],
                    chart_image=chart_image,
                    pinecone_results=pinecone_results
                )
            else:
                return self._create_error_response(result["reply_text"])
                
        except Exception as e:
            error_msg = f"처리 중 오류가 발생했습니다: {str(e)}"
            
            # 에러 로깅
            self.monitoring_service.log_error(
                "chatbot_service_error",
                str(e),
                {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "message": request.message
                }
            )
            
            return self._create_error_response(error_msg)
    
    
    
    def _create_error_response(self, error_message: str) -> ChatResponse:
        """에러 응답 생성"""
        return ChatResponse(
            reply_text=error_message,
            action_type="display_info",
            action_data={
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_conversation_history(self, session_id: str) -> list:
        """대화 기록 조회"""
        try:
            # 워크플로우 경로로 일원화되어 별도 대화 기록 저장소가 없습니다.
            return []
        except Exception as e:
            print(f"대화 기록 조회 실패: {e}")
            return []
    
    def clear_conversation_history(self, session_id: str):
        """대화 기록 초기화"""
        try:
            # 워크플로우 경로에서는 초기화할 대화 기록이 없습니다.
            return None
        except Exception as e:
            print(f"대화 기록 초기화 실패: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        try:
            return self.monitoring_service.get_performance_metrics()
        except Exception as e:
            return {"error": f"메트릭 조회 실패: {e}"}
    
    def generate_performance_report(self) -> str:
        """성능 리포트 생성"""
        try:
            return self.monitoring_service.generate_performance_report()
        except Exception as e:
            return f"리포트 생성 실패: {e}"
    
    def update_knowledge_base(self, new_documents: list):
        """지식 베이스 업데이트"""
        try:
            self.knowledge_base_service.update_knowledge_base(new_documents)
        except Exception as e:
            print(f"지식 베이스 업데이트 실패: {e}")
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """지식 베이스 통계 조회"""
        try:
            return self.knowledge_base_service.get_knowledge_base_stats()
        except Exception as e:
            return {"error": f"통계 조회 실패: {e}"}

# 전역 챗봇 서비스 인스턴스
chatbot_service = FinancialChatbotService()

