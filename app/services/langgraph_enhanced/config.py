"""
LangGraph Enhanced 설정 관리
모든 하드코딩된 값들을 환경변수로 관리
"""

from typing import Optional, Dict, Any, List
import os


class LangGraphEnhancedSettings:
    """LangGraph Enhanced 전용 설정"""
    
    def __init__(self):
        # 모델 설정 (Gemini 2.0 Flash 전용)
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.primary_model = os.getenv("PRIMARY_MODEL", "gemini-2.0-flash-exp")
        self.fallback_model = os.getenv("FALLBACK_MODEL", "gemini-2.0-flash-exp")
        
        # 워크플로우 설정
        self.max_parallel_services = int(os.getenv("MAX_PARALLEL_SERVICES", "3"))
        self.service_timeout = int(os.getenv("SERVICE_TIMEOUT", "30"))
        self.max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "2"))
        
        # 복잡도 판단 임계값
        self.complexity_threshold = int(os.getenv("COMPLEXITY_THRESHOLD", "3"))
        self.service_count_threshold = int(os.getenv("SERVICE_COUNT_THRESHOLD", "3"))
        self.query_length_threshold = int(os.getenv("QUERY_LENGTH_THRESHOLD", "50"))
        
        # 성능 모니터링
        self.enable_performance_tracking = os.getenv("ENABLE_PERFORMANCE_TRACKING", "true").lower() == "true"
        self.enable_langsmith_tracing = os.getenv("ENABLE_LANGSMITH_TRACING", "true").lower() == "true"
        
        # 프롬프트 설정
        self.max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "4000"))
        self.context_window_size = int(os.getenv("CONTEXT_WINDOW_SIZE", "5"))
        
        # 폴백 설정
        self.enable_fallback = os.getenv("ENABLE_FALLBACK", "true").lower() == "true"
        self.fallback_confidence_threshold = float(os.getenv("FALLBACK_CONFIDENCE_THRESHOLD", "0.3"))


# 전역 설정 인스턴스
enhanced_settings = LangGraphEnhancedSettings()


def get_enhanced_settings() -> LangGraphEnhancedSettings:
    """설정 인스턴스 반환"""
    return enhanced_settings


def get_model_config() -> Dict[str, str]:
    """모델 설정 반환 (Gemini 전용)"""
    return {
        "primary": enhanced_settings.primary_model,
        "gemini": enhanced_settings.gemini_model,
        "fallback": enhanced_settings.fallback_model
    }


def get_complexity_config() -> Dict[str, int]:
    """복잡도 판단 설정 반환"""
    return {
        "threshold": enhanced_settings.complexity_threshold,
        "service_count": enhanced_settings.service_count_threshold,
        "query_length": enhanced_settings.query_length_threshold
    }


def get_performance_config() -> Dict[str, Any]:
    """성능 설정 반환"""
    return {
        "max_parallel": enhanced_settings.max_parallel_services,
        "timeout": enhanced_settings.service_timeout,
        "max_retry": enhanced_settings.max_retry_attempts,
        "enable_tracking": enhanced_settings.enable_performance_tracking,
        "enable_langsmith": enhanced_settings.enable_langsmith_tracing
    }
