import asyncio
import sys
from app.services.chatbot_service import chatbot_service
from app.schemas.chat_schema import ChatRequest

def get_user_input():
    """사용자 입력을 받는 함수"""
    try:
        return input("You: ")
    except (EOFError, KeyboardInterrupt):
        return "exit"

async def main():
    """금융 전문가 챗봇 대화형 테스트"""
    print("=" * 60)
    print("🤖 금융 전문가 챗봇 (개선된 버전)")
    print("=" * 60)
    print("\n💡 사용 가능한 질문 예시:")
    print("  - 삼성전자 주가 알려줘")
    print("  - 005930 현재가")
    print("  - 삼성전자 분석해줘")
    print("  - 삼성전자 뉴스")
    print("  - 배당주의 의미는")
    print("  - 투자 전략 추천해줘")
    print("\n종료하려면 'exit' 또는 'quit'를 입력하세요.\n")
    
    session_id = "test_session_001" # 테스트용 세션 ID

    while True:
        user_input = get_user_input()
        
        if user_input.lower() in ['exit', 'quit', '종료']:
            print("\n👋 테스트를 종료합니다. 감사합니다!")
            break
        
        if not user_input.strip():
            continue
        
        request = ChatRequest(
            message=user_input,
            user_id=1, # 테스트용 사용자 ID (정수)
            session_id=session_id
        )
        
        # chatbot_service의 process_chat_request 함수를 비동기로 호출
        response = await chatbot_service.process_chat_request(request)
        
        print(f"\n🤖 Assistant: {response.reply_text}\n")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())