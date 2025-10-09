"""
공통 유틸리티 함수들

중복 코드를 제거하고 재사용 가능한 공통 기능들을 제공
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
import json
import hashlib


class ConfigManager:
    """설정 관리 유틸리티"""
    
    @staticmethod
    def get_embedding_model() -> str:
        """임베딩 모델 경로 반환 (환경변수에서 로드)"""
        from app.config import settings
        return settings.embedding_model
    
    @staticmethod
    def get_chunk_settings() -> Dict[str, int]:
        """문서 청크 설정 반환"""
        from app.config import settings
        return {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap
        }
    
    @staticmethod
    def get_rag_settings() -> Dict[str, Any]:
        """RAG 설정 반환"""
        from app.config import settings
        return {
            "max_search_results": settings.max_search_results,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap
        }
    
    @staticmethod
    def get_data_agent_settings() -> Dict[str, Any]:
        """Data-Agent 설정 반환"""
        from app.config import settings
        return {
            "news_collection_interval": settings.news_collection_interval,
            "confidence_threshold": settings.confidence_threshold,
            "max_news_results": settings.max_news_results
        }


class PerformanceMonitor:
    """성능 모니터링 유틸리티"""
    
    @staticmethod
    def time_function(func: Callable) -> Callable:
        """함수 실행 시간 측정 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                print(f"⏱️ {func.__name__} 실행 시간: {execution_time:.3f}초")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"❌ {func.__name__} 실행 실패 (시간: {execution_time:.3f}초): {e}")
                raise
        return wrapper
    
    @staticmethod
    def log_performance(func_name: str, execution_time: float, success: bool = True):
        """성능 로그 기록"""
        status = "성공" if success else "실패"
        logging.info(f"성능: {func_name} - {execution_time:.3f}초 - {status}")


class ErrorHandler:
    """에러 처리 유틸리티"""
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """API 에러 처리"""
        error_info = {
            "error": True,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # 특정 에러 타입별 처리
        if "timeout" in str(error).lower():
            error_info["suggestion"] = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        elif "connection" in str(error).lower():
            error_info["suggestion"] = "네트워크 연결을 확인해주세요."
        elif "not found" in str(error).lower():
            error_info["suggestion"] = "요청한 데이터를 찾을 수 없습니다."
        else:
            error_info["suggestion"] = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        return error_info
    
    @staticmethod
    def handle_validation_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """검증 에러 처리"""
        return {
            "error": True,
            "error_type": "ValidationError",
            "error_message": str(error),
            "context": context,
            "suggestion": "입력 데이터를 확인해주세요.",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def handle_workflow_error(error: Exception, operation: str = "") -> str:
        """워크플로우 에러 처리 - 상태 업데이트용"""
        return f"{operation} 중 오류: {str(error)}"
    
    @staticmethod
    def safe_execute(func, *args, **kwargs) -> Tuple[bool, Any]:
        """안전한 함수 실행"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            return False, str(e)


class CacheManager:
    """캐시 관리 유틸리티"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        캐시 매니저 초기화
        
        Args:
            default_ttl: 기본 TTL (초)
        """
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self.cache:
            data, expiry = self.cache[key]
            if datetime.now() < expiry:
                return data
            else:
                # 만료된 캐시 제거
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장"""
        if ttl is None:
            ttl = self.default_ttl
        
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """캐시에서 값 삭제"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """모든 캐시 삭제"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if now >= expiry
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


class DataValidator:
    """데이터 검증 유틸리티"""
    
    @staticmethod
    def validate_stock_symbol(symbol: str) -> bool:
        """주식 심볼 유효성 검증"""
        import re
        
        # 한국 주식 패턴 (6자리.KS)
        korean_pattern = r'^\d{6}\.KS$'
        if re.match(korean_pattern, symbol):
            return True
        
        # 미국 주식 패턴 (대문자 1-5자)
        us_pattern = r'^[A-Z]{1,5}$'
        if re.match(us_pattern, symbol):
            return True
        
        # 지수 패턴 (^로 시작)
        index_pattern = r'^\^[A-Z0-9]+$'
        if re.match(index_pattern, symbol):
            return True
        
        return False
    
    @staticmethod
    def validate_query(query: str) -> Dict[str, Any]:
        """사용자 쿼리 검증"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not query or not query.strip():
            result["valid"] = False
            result["errors"].append("쿼리가 비어있습니다.")
            return result
        
        if len(query) > 500:
            result["warnings"].append("쿼리가 너무 깁니다. 500자 이하로 입력해주세요.")
        
        # 금융 관련 키워드가 있는지 확인
        finance_keywords = ["주가", "주식", "투자", "분석", "뉴스", "시장", "경제"]
        if not any(keyword in query for keyword in finance_keywords):
            result["warnings"].append("금융 관련 질문이 아닐 수 있습니다.")
        
        return result


class LoggingManager:
    """로깅 관리 유틸리티"""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
        """로깅 설정"""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                *([logging.FileHandler(log_file)] if log_file else [])
            ]
        )
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """로거 인스턴스 반환"""
        return logging.getLogger(name)


class SecurityUtils:
    """보안 유틸리티"""
    
    @staticmethod
    def hash_string(text: str) -> str:
        """문자열 해시화"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """입력 데이터 정리"""
        # HTML 태그 제거
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 제거 (일부 허용)
        clean_text = re.sub(r'[<>"\']', '', clean_text)
        
        return clean_text.strip()
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> bool:
        """API 키 유효성 검증"""
        if not api_key:
            return False
        
        # 기본적인 길이 및 형식 검증
        if len(api_key) < 20:
            return False
        
        return True


class DataFormatter:
    """데이터 포맷팅 유틸리티"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "KRW") -> str:
        """통화 포맷팅"""
        if currency == "KRW":
            return f"{amount:,.0f}원"
        elif currency == "USD":
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """퍼센트 포맷팅"""
        return f"{value:+.2f}%"
    
    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """숫자 포맷팅"""
        return f"{value:,.{decimals}f}"
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """타임스탬프 포맷팅"""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")


# 전역 인스턴스들
cache_manager = CacheManager()
logger = LoggingManager.get_logger(__name__)


# 편의 함수들
def get_config_manager() -> ConfigManager:
    """설정 매니저 인스턴스 반환"""
    return ConfigManager()


def get_performance_monitor() -> PerformanceMonitor:
    """성능 모니터 인스턴스 반환"""
    return PerformanceMonitor()


def get_error_handler() -> ErrorHandler:
    """에러 핸들러 인스턴스 반환"""
    return ErrorHandler()


def get_data_validator() -> DataValidator:
    """데이터 검증기 인스턴스 반환"""
    return DataValidator()


def get_security_utils() -> SecurityUtils:
    """보안 유틸리티 인스턴스 반환"""
    return SecurityUtils()


def get_data_formatter() -> DataFormatter:
    """데이터 포맷터 인스턴스 반환"""
    return DataFormatter()


if __name__ == "__main__":
    # 테스트 실행
    print("=== 공통 유틸리티 테스트 ===")
    
    # 설정 매니저 테스트
    config_manager = get_config_manager()
    print(f"임베딩 모델: {config_manager.get_embedding_model()}")
    print(f"청크 설정: {config_manager.get_chunk_settings()}")
    
    # 캐시 매니저 테스트
    cache_manager.set("test_key", "test_value", ttl=60)
    print(f"캐시 테스트: {cache_manager.get('test_key')}")
    
    # 데이터 검증기 테스트
    validator = get_data_validator()
    print(f"심볼 검증 (005930.KS): {validator.validate_stock_symbol('005930.KS')}")
    print(f"심볼 검증 (INVALID): {validator.validate_stock_symbol('INVALID')}")
    
    # 데이터 포맷터 테스트
    formatter = get_data_formatter()
    print(f"통화 포맷: {formatter.format_currency(75000)}")
    print(f"퍼센트 포맷: {formatter.format_percentage(2.5)}")
    
    print("=== 테스트 완료 ===")

