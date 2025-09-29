#!/usr/bin/env python3
"""
Google API 키 테스트 스크립트
"""
import os
from app.config import settings

def test_google_api():
    """Google API 키 테스트"""
    print("🔍 Google API 키 테스트를 시작합니다...")
    
    # 환경 변수 확인
    print(f"환경 변수 GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY', 'Not set')}")
    print(f"설정에서 google_api_key: {settings.google_api_key}")
    
    # Google Generative AI 테스트
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        print("📱 ChatGoogleGenerativeAI 초기화 테스트...")
        
        # API 키가 없으면 더미 모델 사용
        if not settings.google_api_key or settings.google_api_key == "your_google_api_key_here":
            print("⚠️ Google API 키가 설정되지 않았습니다.")
            print("💡 테스트를 위해 더미 응답을 반환합니다.")
            return "Google API 키가 필요합니다. .env 파일에 GOOGLE_API_KEY를 설정해주세요."
        
        # 실제 Google API 테스트
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            google_api_key=settings.google_api_key
        )
        
        print("✅ ChatGoogleGenerativeAI 초기화 성공!")
        
        # 간단한 테스트
        response = llm.invoke("안녕하세요")
        print(f"🤖 응답: {response.content}")
        
        return "Google API 테스트 성공!"
        
    except Exception as e:
        print(f"❌ Google API 테스트 실패: {e}")
        return f"오류: {str(e)}"

if __name__ == "__main__":
    result = test_google_api()
    print(f"\n결과: {result}")
