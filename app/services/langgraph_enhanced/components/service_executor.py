"""
서비스 실행기
단일 책임: 서비스 실행 및 결과 관리만 담당
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import time

from ..config import get_enhanced_settings
from ..error_handler import safe_execute_enhanced


class ServiceExecutor:
    """서비스 실행기"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.execution_stats = {}
    
    def execute_service(self, 
                       service_func: Callable, 
                       service_name: str,
                       *args, 
                       **kwargs) -> Dict[str, Any]:
        """서비스 실행"""
        start_time = time.time()
        
        try:
            # 타임아웃 설정하여 서비스 실행
            success, result = safe_execute_enhanced(
                service_func,
                *args,
                operation=f"execute_{service_name}",
                context={"service_name": service_name, "args": args, "kwargs": kwargs},
                **kwargs
            )
            
            execution_time = time.time() - start_time
            
            # 실행 통계 업데이트
            self._update_execution_stats(service_name, execution_time, success)
            
            return {
                "success": success,
                "result": result,
                "execution_time": execution_time,
                "service_name": service_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_execution_stats(service_name, execution_time, False)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "service_name": service_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_execution_stats(self, service_name: str, execution_time: float, success: bool):
        """실행 통계 업데이트"""
        if service_name not in self.execution_stats:
            self.execution_stats[service_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
        
        stats = self.execution_stats[service_name]
        stats["total_executions"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total_executions"]
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """실행 통계 반환"""
        return self.execution_stats.copy()
    
    def reset_execution_stats(self):
        """실행 통계 초기화"""
        self.execution_stats.clear()
