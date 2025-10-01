"""
성능 모니터링 및 A/B 테스트 시스템
LangGraph 워크플로우 최적화를 위한 성능 추적
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import statistics
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """쿼리 타입 열거형"""
    DATA = "data"
    ANALYSIS = "analysis"
    NEWS = "news"
    KNOWLEDGE = "knowledge"
    VISUALIZATION = "visualization"
    GENERAL = "general"


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 클래스"""
    query: str
    query_type: str
    processing_time: float
    success: bool
    timestamp: datetime
    user_context: Dict[str, Any]
    response_quality: Optional[float] = None


class PerformanceMonitor:
    """성능 모니터링 및 A/B 테스트 시스템"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        self.optimization_suggestions: List[str] = []
    
    def record_metric(self, 
                     query: str,
                     query_type: str,
                     processing_time: float,
                     success: bool,
                     user_context: Dict[str, Any] = None,
                     response_quality: float = None):
        """성능 메트릭 기록"""
        metric = PerformanceMetric(
            query=query,
            query_type=query_type,
            processing_time=processing_time,
            success=success,
            timestamp=datetime.now(),
            user_context=user_context or {},
            response_quality=response_quality
        )
        
        self.metrics.append(metric)
        self._analyze_performance()
    
    def _analyze_performance(self):
        """성능 분석 및 최적화 제안"""
        if len(self.metrics) < 10:  # 최소 데이터 필요
            return
        
        recent_metrics = self._get_recent_metrics(hours=24)
        
        # 처리 시간 분석
        processing_times = [m.processing_time for m in recent_metrics]
        avg_processing_time = statistics.mean(processing_times)
        
        # 성공률 분석
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        
        # 쿼리 타입별 성능 분석
        type_performance = self._analyze_by_query_type(recent_metrics)
        
        # 최적화 제안 생성
        suggestions = []
        
        if avg_processing_time > 5.0:
            suggestions.append("평균 처리 시간이 5초를 초과합니다. 캐싱 전략을 고려하세요.")
        
        if success_rate < 0.9:
            suggestions.append(f"성공률이 {success_rate:.1%}입니다. 에러 핸들링을 개선하세요.")
        
        # 느린 쿼리 타입 식별
        slow_types = [qt for qt, perf in type_performance.items() if perf['avg_time'] > 3.0]
        if slow_types:
            suggestions.append(f"다음 쿼리 타입이 느립니다: {', '.join(slow_types)}")
        
        self.optimization_suggestions = suggestions
    
    def _get_recent_metrics(self, hours: int = 24) -> List[PerformanceMetric]:
        """최근 N시간 메트릭 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics if m.timestamp >= cutoff_time]
    
    def _analyze_by_query_type(self, metrics: List[PerformanceMetric]) -> Dict[str, Dict[str, Any]]:
        """쿼리 타입별 성능 분석"""
        type_groups = {}
        
        for metric in metrics:
            query_type = metric.query_type
            if query_type not in type_groups:
                type_groups[query_type] = []
            type_groups[query_type].append(metric)
        
        performance_by_type = {}
        for query_type, type_metrics in type_groups.items():
            processing_times = [m.processing_time for m in type_metrics]
            success_count = sum(1 for m in type_metrics if m.success)
            
            performance_by_type[query_type] = {
                'avg_time': statistics.mean(processing_times),
                'max_time': max(processing_times),
                'min_time': min(processing_times),
                'success_rate': success_count / len(type_metrics),
                'count': len(type_metrics)
            }
        
        return performance_by_type
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 조회"""
        if not self.metrics:
            return {"message": "성능 데이터가 없습니다."}
        
        recent_metrics = self._get_recent_metrics(hours=24)
        
        if not recent_metrics:
            return {"message": "최근 24시간 데이터가 없습니다."}
        
        processing_times = [m.processing_time for m in recent_metrics]
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        
        return {
            "total_queries": len(recent_metrics),
            "avg_processing_time": statistics.mean(processing_times),
            "max_processing_time": max(processing_times),
            "min_processing_time": min(processing_times),
            "success_rate": success_rate,
            "optimization_suggestions": self.optimization_suggestions,
            "performance_by_type": self._analyze_by_query_type(recent_metrics)
        }
    
    def start_ab_test(self, 
                     test_name: str,
                     variant_a: Dict[str, Any],
                     variant_b: Dict[str, Any],
                     traffic_split: float = 0.5) -> str:
        """A/B 테스트 시작"""
        test_id = f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.ab_tests[test_id] = {
            "test_name": test_name,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "traffic_split": traffic_split,
            "start_time": datetime.now(),
            "results": {"a": [], "b": []}
        }
        
        return test_id
    
    def record_ab_test_result(self, 
                             test_id: str,
                             variant: str,
                             result: Dict[str, Any]):
        """A/B 테스트 결과 기록"""
        if test_id in self.ab_tests:
            self.ab_tests[test_id]["results"][variant].append({
                "result": result,
                "timestamp": datetime.now()
            })
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """A/B 테스트 결과 조회"""
        if test_id not in self.ab_tests:
            return {"error": "테스트를 찾을 수 없습니다."}
        
        test = self.ab_tests[test_id]
        results_a = test["results"]["a"]
        results_b = test["results"]["b"]
        
        return {
            "test_name": test["test_name"],
            "start_time": test["start_time"],
            "variant_a_results": len(results_a),
            "variant_b_results": len(results_b),
            "traffic_split": test["traffic_split"],
            "status": "running" if len(results_a) + len(results_b) < 100 else "completed"
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """최적화 권장사항 조회"""
        recommendations = []
        
        recent_metrics = self._get_recent_metrics(hours=24)
        if not recent_metrics:
            return recommendations
        
        # 처리 시간 기반 권장사항
        avg_time = statistics.mean([m.processing_time for m in recent_metrics])
        if avg_time > 3.0:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "처리 시간 최적화",
                "description": f"평균 처리 시간이 {avg_time:.2f}초입니다. 캐싱이나 병렬 처리를 고려하세요.",
                "suggestions": [
                    "Redis 캐싱 도입",
                    "비동기 처리 구현",
                    "데이터베이스 쿼리 최적화"
                ]
            })
        
        # 성공률 기반 권장사항
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        if success_rate < 0.95:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "에러 처리 개선",
                "description": f"성공률이 {success_rate:.1%}입니다. 에러 핸들링을 강화하세요.",
                "suggestions": [
                    "재시도 로직 추가",
                    "폴백 메커니즘 구현",
                    "에러 로깅 강화"
                ]
            })
        
        # 쿼리 타입별 권장사항
        type_performance = self._analyze_by_query_type(recent_metrics)
        for query_type, perf in type_performance.items():
            if perf['avg_time'] > 2.0:
                recommendations.append({
                    "type": "query_optimization",
                    "priority": "medium",
                    "title": f"{query_type} 쿼리 최적화",
                    "description": f"{query_type} 타입의 평균 처리 시간이 {perf['avg_time']:.2f}초입니다.",
                    "suggestions": [
                        f"{query_type} 전용 캐싱 전략",
                        "프롬프트 최적화",
                        "병렬 처리 도입"
                    ]
                })
        
        return recommendations
    
    def export_metrics(self, filepath: str):
        """메트릭 데이터 내보내기"""
        data = {
            "metrics": [
                {
                    "query": m.query,
                    "query_type": m.query_type,
                    "processing_time": m.processing_time,
                    "success": m.success,
                    "timestamp": m.timestamp.isoformat(),
                    "user_context": m.user_context,
                    "response_quality": m.response_quality
                }
                for m in self.metrics
            ],
            "ab_tests": self.ab_tests,
            "optimization_suggestions": self.optimization_suggestions
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 전역 성능 모니터 인스턴스
performance_monitor = PerformanceMonitor()
