"""
신뢰도 계산기
단일 책임: 서비스 결과의 신뢰도를 계산하는 역할만 담당
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import get_enhanced_settings
from .query_complexity_analyzer import ComplexityAnalysis


class ConfidenceCalculator:
    """신뢰도 계산기"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.quality_weights = self._load_quality_weights()
        self.service_weights = self._load_service_weights()
    
    def _load_quality_weights(self) -> Dict[str, float]:
        """품질 가중치 로드"""
        return {
            "data_completeness": 0.3,    # 데이터 완성도
            "response_length": 0.2,      # 응답 길이
            "service_success_rate": 0.3, # 서비스 성공률
            "error_count": 0.2           # 에러 수
        }
    
    def _load_service_weights(self) -> Dict[str, float]:
        """서비스 가중치 로드"""
        return {
            "financial_data": 0.4,
            "analysis": 0.3,
            "news": 0.15,
            "knowledge": 0.1,
            "visualization": 0.05
        }
    
    def calculate_confidence(self, 
                           service_results: Dict[str, Any], 
                           complexity_analysis: ComplexityAnalysis) -> float:
        """신뢰도 계산"""
        try:
            # 기본 신뢰도 계산
            base_confidence = self._calculate_base_confidence(service_results)
            
            # 복잡도 보정
            complexity_factor = self._calculate_complexity_factor(complexity_analysis)
            
            # 서비스 품질 보정
            quality_factor = self._calculate_quality_factor(service_results)
            
            # 최종 신뢰도 계산
            final_confidence = base_confidence * complexity_factor * quality_factor
            
            # 0.0 ~ 1.0 범위로 제한
            return max(0.0, min(1.0, final_confidence))
            
        except Exception as e:
            # 계산 실패 시 기본값 반환
            return 0.5
    
    def _calculate_base_confidence(self, service_results: Dict[str, Any]) -> float:
        """기본 신뢰도 계산"""
        if not service_results:
            return 0.0
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for service_name, result in service_results.items():
            service_weight = self.service_weights.get(service_name, 0.1)
            
            if result.get("success", False):
                # 성공한 서비스는 높은 신뢰도
                service_confidence = 0.8
            else:
                # 실패한 서비스는 낮은 신뢰도
                service_confidence = 0.2
            
            weighted_confidence += service_confidence * service_weight
            total_weight += service_weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_confidence / total_weight
    
    def _calculate_complexity_factor(self, complexity_analysis: ComplexityAnalysis) -> float:
        """복잡도 보정 계수 계산"""
        complexity_level = complexity_analysis.level.value
        complexity_score = complexity_analysis.score
        
        # 복잡도별 기본 계수
        base_factors = {
            "simple": 1.0,
            "moderate": 0.9,
            "complex": 0.8,
            "multi_faceted": 0.7
        }
        
        base_factor = base_factors.get(complexity_level, 0.8)
        
        # 복잡도 점수에 따른 보정
        if complexity_score > 10:
            score_factor = 0.8  # 매우 복잡하면 신뢰도 감소
        elif complexity_score > 5:
            score_factor = 0.9  # 복잡하면 약간 감소
        else:
            score_factor = 1.0  # 단순하면 그대로
        
        return base_factor * score_factor
    
    def _calculate_quality_factor(self, service_results: Dict[str, Any]) -> float:
        """품질 보정 계수 계산"""
        if not service_results:
            return 0.5
        
        # 데이터 완성도 평가
        data_completeness = self._evaluate_data_completeness(service_results)
        
        # 응답 길이 평가
        response_length_score = self._evaluate_response_length(service_results)
        
        # 서비스 성공률
        success_rate = self._calculate_success_rate(service_results)
        
        # 에러 수 평가
        error_score = self._evaluate_error_count(service_results)
        
        # 가중 평균 계산
        quality_score = (
            data_completeness * self.quality_weights["data_completeness"] +
            response_length_score * self.quality_weights["response_length"] +
            success_rate * self.quality_weights["service_success_rate"] +
            error_score * self.quality_weights["error_count"]
        )
        
        return quality_score
    
    def _evaluate_data_completeness(self, service_results: Dict[str, Any]) -> float:
        """데이터 완성도 평가"""
        if not service_results:
            return 0.0
        
        total_score = 0.0
        service_count = len(service_results)
        
        for service_name, result in service_results.items():
            if not result.get("success", False):
                continue
            
            data = result.get("data", {})
            
            # 서비스별 완성도 평가
            if service_name == "financial_data":
                if isinstance(data, dict) and "data" in data:
                    financial_data = data["data"]
                    if isinstance(financial_data, dict) and financial_data:
                        total_score += 1.0
                    else:
                        total_score += 0.3
                else:
                    total_score += 0.1
            
            elif service_name == "analysis":
                if isinstance(data, str) and len(data) > 50:
                    total_score += 1.0
                elif isinstance(data, dict) and "analysis" in data:
                    total_score += 0.8
                else:
                    total_score += 0.3
            
            elif service_name == "news":
                if isinstance(data, list) and len(data) > 0:
                    total_score += 1.0
                else:
                    total_score += 0.2
            
            elif service_name == "knowledge":
                if isinstance(data, str) and len(data) > 20:
                    total_score += 1.0
                elif isinstance(data, dict) and "context" in data:
                    total_score += 0.8
                else:
                    total_score += 0.3
            
            elif service_name == "visualization":
                if isinstance(data, dict) and "chart_base64" in data:
                    total_score += 1.0
                else:
                    total_score += 0.1
        
        return total_score / service_count if service_count > 0 else 0.0
    
    def _evaluate_response_length(self, service_results: Dict[str, Any]) -> float:
        """응답 길이 평가"""
        total_length = 0
        response_count = 0
        
        for result in service_results.values():
            if result.get("success", False):
                data = result.get("data", "")
                
                if isinstance(data, str):
                    total_length += len(data)
                    response_count += 1
                elif isinstance(data, dict) and "analysis" in data:
                    total_length += len(data["analysis"])
                    response_count += 1
        
        if response_count == 0:
            return 0.0
        
        avg_length = total_length / response_count
        
        # 길이에 따른 점수 (100자 이상이면 높은 점수)
        if avg_length >= 200:
            return 1.0
        elif avg_length >= 100:
            return 0.8
        elif avg_length >= 50:
            return 0.6
        elif avg_length >= 20:
            return 0.4
        else:
            return 0.2
    
    def _calculate_success_rate(self, service_results: Dict[str, Any]) -> float:
        """서비스 성공률 계산"""
        if not service_results:
            return 0.0
        
        successful_services = sum(1 for result in service_results.values() 
                                if result.get("success", False))
        total_services = len(service_results)
        
        return successful_services / total_services
    
    def _evaluate_error_count(self, service_results: Dict[str, Any]) -> float:
        """에러 수 평가 (에러가 적을수록 높은 점수)"""
        error_count = sum(1 for result in service_results.values() 
                         if not result.get("success", False))
        
        total_services = len(service_results)
        if total_services == 0:
            return 1.0
        
        error_rate = error_count / total_services
        
        # 에러율에 따른 점수 (에러가 적을수록 높은 점수)
        if error_rate == 0:
            return 1.0
        elif error_rate <= 0.2:
            return 0.8
        elif error_rate <= 0.4:
            return 0.6
        elif error_rate <= 0.6:
            return 0.4
        else:
            return 0.2
