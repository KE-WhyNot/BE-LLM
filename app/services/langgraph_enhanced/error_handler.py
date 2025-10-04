"""
LangGraph Enhanced 에러 처리 유틸리티
구체적이고 일관된 에러 처리 로직 제공
"""

from typing import Dict, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime
import logging
import traceback


class ErrorType(Enum):
    """에러 타입 정의"""
    VALIDATION_ERROR = "validation_error"
    MODEL_ERROR = "model_error"
    SERVICE_ERROR = "service_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnhancedError(Exception):
    """향상된 에러 클래스"""
    
    def __init__(self, 
                 message: str,
                 error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 details: Optional[Dict[str, Any]] = None,
                 recoverable: bool = True):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()
        super().__init__(self.message)


class EnhancedErrorHandler:
    """향상된 에러 핸들러"""
    
    def __init__(self, logger_name: str = "langgraph_enhanced"):
        self.logger = logging.getLogger(logger_name)
        self.error_stats = {}
    
    def handle_error(self, 
                    error: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    operation: str = "") -> Dict[str, Any]:
        """에러 처리 및 로깅"""
        
        # 에러 정보 추출
        error_info = self._extract_error_info(error, context, operation)
        
        # 에러 로깅
        self._log_error(error_info)
        
        # 통계 업데이트
        self._update_error_stats(error_info)
        
        # 사용자 친화적 메시지 생성
        user_message = self._generate_user_message(error_info)
        
        return {
            "success": False,
            "error_type": error_info["error_type"],
            "error_message": user_message,
            "technical_details": error_info.get("details", {}),
            "recoverable": error_info.get("recoverable", True),
            "timestamp": error_info["timestamp"]
        }
    
    def _extract_error_info(self, 
                           error: Exception, 
                           context: Optional[Dict[str, Any]], 
                           operation: str) -> Dict[str, Any]:
        """에러 정보 추출"""
        
        if isinstance(error, EnhancedError):
            return {
                "error_type": error.error_type.value,
                "severity": error.severity.value,
                "message": error.message,
                "details": error.details,
                "recoverable": error.recoverable,
                "timestamp": error.timestamp,
                "operation": operation,
                "context": context or {}
            }
        
        # 일반 Exception을 EnhancedError로 변환
        error_type = self._classify_error(error)
        severity = self._determine_severity(error_type)
        
        return {
            "error_type": error_type.value,
            "severity": severity.value,
            "message": str(error),
            "details": {
                "exception_type": type(error).__name__,
                "traceback": traceback.format_exc()
            },
            "recoverable": self._is_recoverable(error_type),
            "timestamp": datetime.now(),
            "operation": operation,
            "context": context or {}
        }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """에러 타입 분류"""
        error_name = type(error).__name__.lower()
        
        if "validation" in error_name or "value" in error_name:
            return ErrorType.VALIDATION_ERROR
        elif "timeout" in error_name or "time" in error_name:
            return ErrorType.TIMEOUT_ERROR
        elif "network" in error_name or "connection" in error_name:
            return ErrorType.NETWORK_ERROR
        elif "config" in error_name or "setting" in error_name:
            return ErrorType.CONFIGURATION_ERROR
        elif any(keyword in error_name for keyword in ["openai", "gemini", "model", "llm"]):
            return ErrorType.MODEL_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _determine_severity(self, error_type: ErrorType) -> ErrorSeverity:
        """에러 심각도 결정"""
        severity_map = {
            ErrorType.VALIDATION_ERROR: ErrorSeverity.LOW,
            ErrorType.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            ErrorType.MODEL_ERROR: ErrorSeverity.HIGH,
            ErrorType.SERVICE_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    def _is_recoverable(self, error_type: ErrorType) -> bool:
        """에러 복구 가능 여부"""
        recoverable_types = {
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR,
            ErrorType.VALIDATION_ERROR
        }
        return error_type in recoverable_types
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """에러 로깅"""
        log_message = (
            f"Error in {error_info.get('operation', 'unknown operation')}: "
            f"{error_info['message']} "
            f"[Type: {error_info['error_type']}, Severity: {error_info['severity']}]"
        )
        
        if error_info["severity"] == ErrorSeverity.CRITICAL.value:
            self.logger.critical(log_message, extra=error_info)
        elif error_info["severity"] == ErrorSeverity.HIGH.value:
            self.logger.error(log_message, extra=error_info)
        elif error_info["severity"] == ErrorSeverity.MEDIUM.value:
            self.logger.warning(log_message, extra=error_info)
        else:
            self.logger.info(log_message, extra=error_info)
    
    def _update_error_stats(self, error_info: Dict[str, Any]) -> None:
        """에러 통계 업데이트"""
        error_type = error_info["error_type"]
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1
    
    def _generate_user_message(self, error_info: Dict[str, Any]) -> str:
        """사용자 친화적 에러 메시지 생성"""
        error_type = error_info["error_type"]
        
        user_messages = {
            ErrorType.VALIDATION_ERROR.value: "입력한 정보를 다시 확인해주세요.",
            ErrorType.MODEL_ERROR.value: "AI 모델 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            ErrorType.SERVICE_ERROR.value: "서비스 처리 중 오류가 발생했습니다.",
            ErrorType.TIMEOUT_ERROR.value: "처리 시간이 초과되었습니다. 다시 시도해주세요.",
            ErrorType.CONFIGURATION_ERROR.value: "시스템 설정에 문제가 있습니다. 관리자에게 문의하세요.",
            ErrorType.NETWORK_ERROR.value: "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요.",
            ErrorType.UNKNOWN_ERROR.value: "예상치 못한 오류가 발생했습니다. 다시 시도해주세요."
        }
        
        return user_messages.get(error_type, "알 수 없는 오류가 발생했습니다.")
    
    def safe_execute(self, 
                    func: Callable, 
                    *args, 
                    operation: str = "",
                    context: Optional[Dict[str, Any]] = None,
                    **kwargs) -> Tuple[bool, Any]:
        """안전한 함수 실행"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            error_result = self.handle_error(e, context, operation)
            return False, error_result
    
    def get_error_stats(self) -> Dict[str, int]:
        """에러 통계 반환"""
        return self.error_stats.copy()
    
    def reset_error_stats(self) -> None:
        """에러 통계 초기화"""
        self.error_stats.clear()


# 전역 에러 핸들러 인스턴스
enhanced_error_handler = EnhancedErrorHandler()


def handle_enhanced_error(error: Exception, 
                         context: Optional[Dict[str, Any]] = None,
                         operation: str = "") -> Dict[str, Any]:
    """전역 에러 처리 함수"""
    return enhanced_error_handler.handle_error(error, context, operation)


def safe_execute_enhanced(func: Callable, 
                         *args, 
                         operation: str = "",
                         context: Optional[Dict[str, Any]] = None,
                         **kwargs) -> Tuple[bool, Any]:
    """전역 안전 실행 함수"""
    return enhanced_error_handler.safe_execute(func, *args, operation=operation, context=context, **kwargs)
