"""
쿼리 복잡도 분석기
단일 책임: 쿼리의 복잡도를 분석하고 분류하는 역할만 담당
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from ..config import get_complexity_config
from ..error_handler import safe_execute_enhanced, ErrorType, ErrorSeverity, EnhancedError


class ComplexityLevel(Enum):
    """복잡도 레벨"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MULTI_FACETED = "multi_faceted"


@dataclass
class ComplexityAnalysis:
    """복잡도 분석 결과"""
    level: ComplexityLevel
    score: int
    factors: List[str]
    required_services: List[str]
    estimated_time: float


class QueryComplexityAnalyzer:
    """쿼리 복잡도 분석기"""
    
    def __init__(self):
        self.config = get_complexity_config()
        self.complexity_keywords = self._load_complexity_keywords()
        self.service_keywords = self._load_service_keywords()
    
    def _load_complexity_keywords(self) -> Dict[str, List[str]]:
        """복잡도 키워드 로드"""
        return {
            "high": [
                "종합", "비교", "분석", "예측", "추천", "의견", "고려",
                "여러", "다양한", "상세", "심화", "고급", "전문적",
                "모든", "전체", "포괄", "통합", "조합"
            ],
            "medium": [
                "설명", "알려줘", "뭐야", "어떻게", "왜", "언제",
                "현재", "최근", "오늘", "이번"
            ],
            "low": [
                "간단", "빠르게", "요약", "핵심", "정리"
            ]
        }
    
    def _load_service_keywords(self) -> Dict[str, List[str]]:
        """서비스 키워드 로드"""
        return {
            "financial_data": ["주가", "가격", "현재가", "시세", "차트", "그래프"],
            "analysis": ["분석", "기술적", "펀더멘털", "예측", "추세"],
            "news": ["뉴스", "소식", "이슈", "최근", "오늘"],
            "knowledge": ["뭐야", "의미", "정의", "개념", "설명"],
            "visualization": ["차트", "그래프", "시각화", "캔들", "그림"]
        }
    
    def analyze_complexity(self, query: str) -> ComplexityAnalysis:
        """쿼리 복잡도 분석"""
        try:
            # 복잡도 점수 계산
            complexity_score = self._calculate_complexity_score(query)
            
            # 복잡도 레벨 결정
            complexity_level = self._determine_complexity_level(complexity_score)
            
            # 복잡도 요인 분석
            complexity_factors = self._identify_complexity_factors(query)
            
            # 필요한 서비스 식별
            required_services = self._identify_required_services(query)
            
            # 예상 처리 시간 계산
            estimated_time = self._estimate_processing_time(complexity_level, len(required_services))
            
            return ComplexityAnalysis(
                level=complexity_level,
                score=complexity_score,
                factors=complexity_factors,
                required_services=required_services,
                estimated_time=estimated_time
            )
            
        except Exception as e:
            # 에러 발생 시 기본값 반환
            return ComplexityAnalysis(
                level=ComplexityLevel.SIMPLE,
                score=0,
                factors=["분석 실패"],
                required_services=["financial_data"],
                estimated_time=1.0
            )
    
    def _calculate_complexity_score(self, query: str) -> int:
        """복잡도 점수 계산"""
        score = 0
        query_lower = query.lower()
        
        # 고복잡도 키워드 체크
        for keyword in self.complexity_keywords["high"]:
            if keyword in query_lower:
                score += 3
        
        # 중복잡도 키워드 체크
        for keyword in self.complexity_keywords["medium"]:
            if keyword in query_lower:
                score += 1
        
        # 저복잡도 키워드 체크 (점수 감소)
        for keyword in self.complexity_keywords["low"]:
            if keyword in query_lower:
                score = max(0, score - 1)
        
        # 문장 길이 고려
        if len(query) > self.config["query_length"]:
            score += 2
        elif len(query) > self.config["query_length"] // 2:
            score += 1
        
        # 여러 문장이나 질문 수 고려
        question_count = query.count("?")
        if question_count > 1:
            score += 2
        elif question_count == 1:
            score += 1
        
        # 연결어 고려
        connector_words = ["그리고", "또한", "또는", "그런데", "하지만"]
        for connector in connector_words:
            if connector in query_lower:
                score += 1
        
        return score
    
    def _determine_complexity_level(self, score: int) -> ComplexityLevel:
        """복잡도 레벨 결정"""
        threshold = self.config["threshold"]
        
        if score >= threshold * 2:
            return ComplexityLevel.MULTI_FACETED
        elif score >= threshold:
            return ComplexityLevel.COMPLEX
        elif score >= threshold // 2:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
    def _identify_complexity_factors(self, query: str) -> List[str]:
        """복잡도 요인 식별"""
        factors = []
        query_lower = query.lower()
        
        if len(query) > self.config["query_length"]:
            factors.append("긴 질문")
        
        question_count = query.count("?")
        if question_count > 1:
            factors.append("다중 질문")
        
        high_complexity_count = sum(1 for keyword in self.complexity_keywords["high"] 
                                  if keyword in query_lower)
        if high_complexity_count > 0:
            factors.append(f"고복잡도 키워드 {high_complexity_count}개")
        
        connector_count = sum(1 for connector in ["그리고", "또한", "또는"] 
                            if connector in query_lower)
        if connector_count > 0:
            factors.append(f"연결어 {connector_count}개")
        
        return factors
    
    def _identify_required_services(self, query: str) -> List[str]:
        """필요한 서비스 식별"""
        required_services = []
        query_lower = query.lower()
        
        for service, keywords in self.service_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                required_services.append(service)
        
        # 기본 서비스가 없으면 financial_data 추가
        if not required_services:
            required_services.append("financial_data")
        
        return required_services
    
    def _estimate_processing_time(self, complexity_level: ComplexityLevel, service_count: int) -> float:
        """예상 처리 시간 계산 (초)"""
        base_times = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MODERATE: 2.0,
            ComplexityLevel.COMPLEX: 4.0,
            ComplexityLevel.MULTI_FACETED: 8.0
        }
        
        base_time = base_times.get(complexity_level, 2.0)
        service_multiplier = 1 + (service_count - 1) * 0.5
        
        return base_time * service_multiplier
