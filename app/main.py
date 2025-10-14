from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, portfolio
from app.config import settings

app = FastAPI(
    title="금융 전문가 챗봇 API",
    description="RAG, LangChain, LangGraph, LangSmith를 활용한 고급 금융 분석 챗봇",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(chat.router, prefix="/api/v1")
app.include_router(portfolio.router)

@app.get("/")
def read_root():
    """서버 상태 확인"""
    return {
        "message": "금융 전문가 챗봇 서비스가 실행 중입니다",
        "version": "1.0.0",
        "features": [
            "RAG 기반 금융 지식 검색",
            "LangChain 에이전트",
            "LangGraph 워크플로우",
            "LangSmith 모니터링",
            "실시간 주식 데이터",
            "금융 분석 및 전망"
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "history": "/api/v1/chat/history/{session_id}",
            "metrics": "/api/v1/chat/metrics",
            "report": "/api/v1/chat/report",
            "knowledge_base": "/api/v1/chat/knowledge-base/stats",
            "portfolio": "/api/v1/portfolio",
            "portfolio_enhanced": "/api/v1/portfolio/enhanced",
            "sectors": "/api/v1/portfolio/sectors"
        }
    }

@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "pinecone_rag_service": "active",
            "langchain_agent": "active", 
            "langgraph_workflow": "active",
            "langsmith_monitoring": "active" if settings.langsmith_api_key else "inactive"
        }
    }