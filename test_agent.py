import asyncio
from app.services.enhanced_chatbot_service import EnhancedFinancialChatbotService
from app.schemas.chat_schema import ChatRequest

# 향상된 챗봇 서비스 인스턴스 생성
chatbot_service = EnhancedFinancialChatbotService()

async def main():
    """챗봇 서비스의 LangGraph 워크플로우를 테스트하는 CLI 스크립트"""
    print("금융 전문가 챗봇 테스트를 시작합니다. (종료: 'exit')")
    
    session_id = "test_session_001" # 테스트용 세션 ID

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("테스트를 종료합니다.")
            break
        
        request = ChatRequest(
            message=user_input,
            user_id=1, # 테스트용 사용자 ID (정수)
            session_id=session_id
        )
        
        # chatbot_service의 process_chat_request 함수를 비동기로 호출
        response = await chatbot_service.process_chat_request(request)
        
        print(f"Assistant: {response.reply_text}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())