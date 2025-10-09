from fastapi import APIRouter, HTTPException
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chatbot.chatbot_service import chatbot_service
from typing import Dict, Any

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat_request(request: ChatRequest):
    """
    금융 전문가 챗봇과의 대화를 처리합니다.
    RAG, LangChain, LangGraph, LangSmith를 활용한 고급 금융 분석을 제공합니다.
    복잡도에 따라 자동으로 최적의 워크플로우를 선택합니다.
    """
    try:
        response = await chatbot_service.process_chat_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/chat/history/{session_id}")
async def get_conversation_history(session_id: str):
    """대화 기록을 조회합니다."""
    try:
        history = chatbot_service.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/chat/history/{session_id}")
async def clear_conversation_history(session_id: str):
    """대화 기록을 초기화합니다."""
    try:
        chatbot_service.clear_conversation_history(session_id)
        return {"message": "대화 기록이 초기화되었습니다.", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 초기화 중 오류가 발생했습니다: {str(e)}")

@router.get("/chat/metrics")
async def get_performance_metrics():
    """챗봇 성능 메트릭을 조회합니다."""
    try:
        metrics = chatbot_service.get_performance_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메트릭 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/chat/report")
async def get_performance_report():
    """성능 리포트를 생성합니다."""
    try:
        report = chatbot_service.generate_performance_report()
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/chat/knowledge-base/stats")
async def get_knowledge_base_stats():
    """지식 베이스 통계를 조회합니다."""
    try:
        stats = chatbot_service.get_knowledge_base_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/chat/knowledge-base/update")
async def update_knowledge_base(documents: list):
    """지식 베이스를 업데이트합니다."""
    try:
        chatbot_service.update_knowledge_base(documents)
        return {"message": "지식 베이스가 업데이트되었습니다.", "document_count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지식 베이스 업데이트 중 오류가 발생했습니다: {str(e)}")