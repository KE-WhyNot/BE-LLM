from pydantic import BaseModel
from typing import Optional, Any

# 프론트엔드에서 백엔드로 보내는 요청 형식
class ChatRequest(BaseModel):
    user_id: Optional[int] = None # 로그인 안한 사용자일 수도 있음
    session_id: str # 사용자 대화 세션을 구분하기 위한 ID
    message: str

# 백엔드에서 프론트엔드로 보내는 응답 형식
class ChatResponse(BaseModel):
    reply_text: str # 챗봇의 답변 메시지
    
    action_type: str # 프론트엔드 액션 타입 (예: "intelligent_agent_system", "display_info")
    
    action_data: Optional[Any] = None # 액션에 필요한 추가 데이터 (query_analysis, service_plan, confidence_evaluation 등)
    
    chart_image: Optional[str] = None # 차트 이미지 (base64 인코딩)
    
    success: bool = True # 요청 성공 여부
    
    error_message: Optional[str] = None # 에러 메시지 (에러 발생 시)
    
    @staticmethod
    def create_success(
        reply_text: str,
        action_type: str,
        action_data: Optional[Any] = None,
        chart_image: Optional[str] = None
    ):
        """성공 응답 생성"""
        return ChatResponse(
            reply_text=reply_text,
            action_type=action_type,
            action_data=action_data,
            chart_image=chart_image,
            success=True,
            error_message=None
        )
    
    @staticmethod
    def create_error(error_message: str):
        """에러 응답 생성"""
        return ChatResponse(
            reply_text=error_message,
            action_type="display_info",
            action_data={"error": True},
            chart_image=None,
            success=False,
            error_message=error_message
        )