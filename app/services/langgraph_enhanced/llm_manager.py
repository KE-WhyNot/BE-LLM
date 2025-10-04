"""
LLM 관리자 (Gemini 2.0 Flash 전용)
깔끔하게 Gemini만 사용하도록 단순화
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class LLMManager:
    """LLM 관리자 (Gemini 전용)"""
    
    def __init__(self):
        self.llm_cache = {}
        self.default_model = "gemini-2.0-flash-exp"
    
    def get_llm(self, 
                model_name: Optional[str] = None, 
                temperature: float = 0.7, 
                **kwargs) -> ChatGoogleGenerativeAI:
        """
        Gemini LLM 인스턴스 반환 (캐싱 포함)
        """
        # 모델명이 없으면 기본 모델 사용
        if model_name is None:
            model_name = self.default_model
        
        # 캐시에서 확인
        cache_key = f"{model_name}_{temperature}_{hash(str(kwargs))}"
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]
        
        # API 키 확인
        google_api_key = settings.google_api_key
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
        
        # Gemini LLM 인스턴스 생성
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=google_api_key,
            **kwargs
        )
        
        # 캐시에 저장
        self.llm_cache[cache_key] = llm
        
        print(f"🤖 Gemini LLM 로드: {model_name} (temperature: {temperature})")
        return llm
    
    def get_default_llm(self, temperature: float = 0.7, **kwargs) -> ChatGoogleGenerativeAI:
        """기본 Gemini LLM 반환"""
        return self.get_llm(model_name=None, temperature=temperature, **kwargs)
    
    def clear_cache(self):
        """LLM 캐시 초기화"""
        self.llm_cache.clear()
        print("🧹 LLM 캐시가 초기화되었습니다.")


# 전역 LLM 관리자 인스턴스
llm_manager = LLMManager()


def get_gemini_llm(model_name: Optional[str] = None, 
                   temperature: float = 0.7, 
                   **kwargs) -> ChatGoogleGenerativeAI:
    """Gemini LLM 인스턴스 반환 (편의 함수)"""
    return llm_manager.get_llm(model_name, temperature, **kwargs)


def get_default_gemini_llm(temperature: float = 0.7, **kwargs) -> ChatGoogleGenerativeAI:
    """기본 Gemini LLM 반환 (편의 함수)"""
    return llm_manager.get_default_llm(temperature, **kwargs)
