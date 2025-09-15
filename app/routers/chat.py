from fastapi import APIRouter
from app.schemas.chat_schema import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat_request(request: ChatRequest):
    """
    사용자의 채팅 메시지를 받아 적절한 응답을 반환합니다.
    (현재는 임시 로직으로, 나중에 실제 챗봇 서비스로 대체됩니다.)
    """
    message = request.message
    
    if "삼성전자" in message:
        # 정보 요약 챗봇(RAG) 기능의 임시 응답
        return ChatResponse(
            reply_text=f"'{message}'에 대한 최신 동향을 요약해 드릴게요.",
            action_type="display_info",
            action_data={"summary": "삼성전자 관련 뉴스 요약 내용입니다..."}
        )
    else:
        # 기능 수행(네비게이션) 챗봇의 임시 응답
        return ChatResponse(
            reply_text="거래내역 화면으로 이동합니다.",
            action_type="navigate",
            action_data={"path": "/transactions"}
        )