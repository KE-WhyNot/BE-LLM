from pydantic import BaseModel
from typing import Optional, Any

# 프론트엔드에서 백엔드로 보내는 요청 형식
class ChatRequest(BaseModel):
    user_id: Optional[int] = None # 로그인 안한 사용자일 수도 있음
    session_id: str # 사용자 대화 세션을 구분하기 위한 ID
    message: str

# 백엔드에서 프론트엔드로 보내는 응답 형식
class ChatResponse(BaseModel):
    reply_text: str # 챗봇의 답변 메시지 (예: "거래내역 화면으로 이동합니다.")
    
    # 프론트엔드가 어떤 행동을 해야할지 알려주는 신호
    # 'navigate': 페이지 이동, 'display_info': 정보 표시, 'show_chart': 차트 표시 등
    action_type: str 
    
    # 행동에 필요한 추가 데이터
    action_data: Optional[Any] = None 
    # 예: {'path': '/transactions'} 또는 {'summary': '삼성전자 뉴스 요약...'}
    
    # 차트 이미지 (base64 인코딩, visualization 쿼리 시 사용)
    chart_image: Optional[str] = None
    # 예: "iVBORw0KGgoAAAANSUhEUgAA..." (프론트엔드에서 <img src="data:image/png;base64,{chart_image}" />로 표시)
    
    # Pinecone 검색 결과 (Colab 노트북 방식으로 표시)
    pinecone_results: Optional[list] = None
    # 예: [{"id": "doc1", "score": 0.85, "metadata": {"text": "...", "source": "..."}}]