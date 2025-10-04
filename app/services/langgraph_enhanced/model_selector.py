"""
모델 선택기
작업 유형에 따라 최적의 모델을 선택하는 역할
"""

from typing import Dict, Any, Optional
from enum import Enum
import os

from .config import get_model_config
from .error_handler import safe_execute_enhanced


class TaskType(Enum):
    """작업 유형"""
    SIMPLE_QUERY = "simple_query"           # 단순 질문
    COMPLEX_ANALYSIS = "complex_analysis"    # 복잡한 분석
    CODE_GENERATION = "code_generation"      # 코드 생성
    KOREAN_FINANCE = "korean_finance"        # 한국 금융 분석
    MULTI_LANGUAGE = "multi_language"        # 다국어 처리
    CREATIVE_WRITING = "creative_writing"    # 창의적 글쓰기


class ModelSelector:
    """모델 선택기"""
    
    def __init__(self):
        self.model_config = get_model_config()
        self.model_performance = self._load_model_performance_data()
    
    def _load_model_performance_data(self) -> Dict[str, Dict[str, float]]:
        """모델별 성능 데이터 로드 (Gemini 전용)"""
        return {
            "gemini-2.0-flash-exp": {
                "speed": 0.9,           # 매우 빠름
                "cost": 0.9,            # 매우 저렴
                "korean": 0.95,         # 한국어 특화
                "accuracy": 0.85,       # 정확도
                "stability": 0.8        # 안정성
            }
        }
    
    def select_optimal_model(self, 
                           task_type: TaskType, 
                           query: str,
                           user_context: Optional[Dict[str, Any]] = None) -> str:
        """작업 유형에 따라 최적의 모델 선택"""
        try:
            # 작업별 모델 선호도 계산
            model_scores = self._calculate_model_scores(task_type, query, user_context)
            
            # 최고 점수 모델 선택
            optimal_model = max(model_scores, key=model_scores.get)
            
            # 모델명을 실제 모델 ID로 변환
            return self._map_to_actual_model(optimal_model)
            
        except Exception as e:
            # 에러 발생 시 기본 모델 반환
            return self.model_config["primary"]
    
    def _calculate_model_scores(self, 
                              task_type: TaskType, 
                              query: str,
                              user_context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """모델별 점수 계산"""
        scores = {}
        
        for model, performance in self.model_performance.items():
            base_score = 0.0
            
            # 작업 유형별 가중치
            if task_type == TaskType.SIMPLE_QUERY:
                # 단순 질문: 속도와 비용 중시
                base_score = (performance["speed"] * 0.4 + 
                            performance["cost"] * 0.4 + 
                            performance["accuracy"] * 0.2)
            
            elif task_type == TaskType.COMPLEX_ANALYSIS:
                # 복잡한 분석: 정확도와 한국어 처리 중시
                base_score = (performance["accuracy"] * 0.4 + 
                            performance["korean"] * 0.3 + 
                            performance["stability"] * 0.3)
            
            elif task_type == TaskType.KOREAN_FINANCE:
                # 한국 금융: 한국어 처리와 정확도 중시
                base_score = (performance["korean"] * 0.5 + 
                            performance["accuracy"] * 0.3 + 
                            performance["speed"] * 0.2)
            
            elif task_type == TaskType.CODE_GENERATION:
                # 코드 생성: 정확도와 속도 중시
                base_score = (performance["accuracy"] * 0.5 + 
                            performance["speed"] * 0.3 + 
                            performance["stability"] * 0.2)
            
            else:
                # 기본: 균형 잡힌 점수
                base_score = (performance["accuracy"] * 0.3 + 
                            performance["speed"] * 0.3 + 
                            performance["cost"] * 0.2 + 
                            performance["korean"] * 0.2)
            
            # 쿼리 길이에 따른 보정
            query_length_factor = self._calculate_query_length_factor(query)
            base_score *= query_length_factor
            
            # 사용자 컨텍스트에 따른 보정
            context_factor = self._calculate_context_factor(user_context)
            base_score *= context_factor
            
            scores[model] = base_score
        
        return scores
    
    def _calculate_query_length_factor(self, query: str) -> float:
        """쿼리 길이에 따른 보정 계수"""
        length = len(query)
        
        if length < 50:
            return 1.0  # 짧은 질문: 모든 모델 동일
        elif length < 200:
            return 1.0  # 중간 질문: 모든 모델 동일
        else:
            # 긴 질문: Gemini의 긴 컨텍스트 활용도가 높음
            return 1.1 if "gemini" in query.lower() else 1.0
    
    def _calculate_context_factor(self, user_context: Optional[Dict[str, Any]]) -> float:
        """사용자 컨텍스트에 따른 보정 계수"""
        if not user_context:
            return 1.0
        
        # 한국 사용자인 경우 Gemini 선호
        if user_context.get("language", "").lower() in ["ko", "korean"]:
            return 1.1
        
        # 복잡한 분석 요청인 경우 GPT-4o 선호
        if user_context.get("complexity", "simple") == "complex":
            return 1.0
        
        return 1.0
    
    def _map_to_actual_model(self, model_name: str) -> str:
        """모델명을 실제 모델 ID로 매핑 (Gemini 전용)"""
        # Gemini만 사용하므로 항상 Gemini 모델 반환
        return self.model_config["gemini"]
    
    def get_model_recommendation(self, task_type: TaskType) -> Dict[str, Any]:
        """작업 유형별 모델 추천 정보 (Gemini 전용)"""
        recommendations = {
            TaskType.SIMPLE_QUERY: {
                "recommended": "gemini-2.0-flash-exp",
                "reason": "빠른 속도와 저렴한 비용"
            },
            TaskType.COMPLEX_ANALYSIS: {
                "recommended": "gemini-2.0-flash-exp", 
                "reason": "긴 컨텍스트와 한국어 특화"
            },
            TaskType.KOREAN_FINANCE: {
                "recommended": "gemini-2.0-flash-exp",
                "reason": "한국어 금융 용어 특화"
            },
            TaskType.CODE_GENERATION: {
                "recommended": "gemini-2.0-flash-exp",
                "reason": "코드 생성과 한국어 특화"
            }
        }
        
        return recommendations.get(task_type, {
            "recommended": "gemini-2.0-flash-exp",
            "reason": "균형 잡힌 성능과 한국어 특화"
        })


# 전역 모델 선택기 인스턴스
model_selector = ModelSelector()


def select_model_for_task(task_type: TaskType, 
                         query: str,
                         user_context: Optional[Dict[str, Any]] = None) -> str:
    """작업에 최적화된 모델 선택"""
    return model_selector.select_optimal_model(task_type, query, user_context)


def get_task_type_from_query(query: str) -> TaskType:
    """쿼리에서 작업 유형 추출"""
    query_lower = query.lower()
    
    # 한국 금융 관련 키워드
    korean_finance_keywords = ["주가", "시세", "현재가", "PER", "PBR", "배당", "상장", "KOSPI", "KOSDAQ"]
    if any(keyword in query_lower for keyword in korean_finance_keywords):
        return TaskType.KOREAN_FINANCE
    
    # 복잡한 분석 키워드
    complex_keywords = ["분석", "비교", "예측", "종합", "다면적", "고려"]
    if any(keyword in query_lower for keyword in complex_keywords):
        return TaskType.COMPLEX_ANALYSIS
    
    # 코드 생성 키워드
    code_keywords = ["코드", "함수", "클래스", "스크립트", "프로그램"]
    if any(keyword in query_lower for keyword in code_keywords):
        return TaskType.CODE_GENERATION
    
    # 기본적으로 단순 질문으로 분류
    return TaskType.SIMPLE_QUERY
