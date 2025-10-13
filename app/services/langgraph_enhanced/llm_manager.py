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
        self.default_model = "gemini-2.0-flash"  # 정식 2.0 버전, 높은 할당량
    
    def get_llm(self, 
                model_name: Optional[str] = None, 
                temperature: float = 0.7,
                purpose: str = "general",
                **kwargs) -> ChatGoogleGenerativeAI:
        """
        Gemini LLM 인스턴스 반환 (용도별 최적화된 파라미터)
        """
        # 모델명이 없으면 기본 모델 사용
        if model_name is None:
            model_name = self.default_model
        
        # 용도별 최적화된 파라미터 설정
        optimized_params = self._get_optimized_params(purpose, temperature, **kwargs)
        
        # 캐시에서 확인
        cache_key = f"{model_name}_{purpose}_{optimized_params['temperature']}_{hash(str(optimized_params))}"
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]
        
        # API 키 확인
        google_api_key = settings.google_api_key
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
        
        # Gemini LLM 인스턴스 생성
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            **optimized_params
        )
        
        # 캐시에 저장
        self.llm_cache[cache_key] = llm
        
        print(f"🤖 Gemini LLM 로드: {model_name} ({purpose}, temperature: {optimized_params['temperature']})")
        return llm
    
    def _get_optimized_params(self, purpose: str, temperature: float, **kwargs) -> dict:
        """용도별 최적화된 LLM 파라미터 반환"""
        base_params = {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
            **kwargs
        }
        
        # 용도별 최적화
        if purpose == "classification":
            return {
                **base_params,
                "temperature": 0.1,  # 분류는 일관성 중요
                "max_output_tokens": 512,  # 구조화된 응답을 위해 충분한 토큰
                "top_p": 0.8
            }
        elif purpose == "analysis":
            return {
                **base_params,
                "temperature": 0.3,  # 분석은 균형잡힌 창의성
                "max_output_tokens": 4096,  # 상세한 분석 필요
                "top_p": 0.9
            }
        elif purpose == "news":
            return {
                **base_params,
                "temperature": 0.2,  # 뉴스는 객관성 중요
                "max_output_tokens": 2048,
                "top_p": 0.85
            }
        elif purpose == "knowledge":
            return {
                **base_params,
                "temperature": 0.4,  # 교육적 설명은 적당한 창의성
                "max_output_tokens": 3072,
                "top_p": 0.9
            }
        elif purpose == "response":
            return {
                **base_params,
                "temperature": 0.7,  # 응답은 자연스러움 중요
                "max_output_tokens": 2048,
                "top_p": 0.9
            }
        else:  # general
            return base_params
    
    def get_default_llm(self, temperature: float = 0.7, purpose: str = "general", **kwargs) -> ChatGoogleGenerativeAI:
        """기본 Gemini LLM 반환"""
        return self.get_llm(model_name=None, temperature=temperature, purpose=purpose, **kwargs)
    
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
