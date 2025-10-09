"""
에이전트 모듈
각 에이전트의 프롬프트와 로직을 분리하여 관리

전문 에이전트 (7개):
- QueryAnalyzerAgent: 쿼리 분석
- DataAgent: 데이터 조회
- AnalysisAgent: 투자 분석
- NewsAgent: 뉴스 수집
- KnowledgeAgent: 지식 교육
- VisualizationAgent: 차트 생성
- ResponseAgent: 최종 응답

메타 에이전트 (4개):
- ServicePlannerAgent: 서비스 전략 계획
- ParallelExecutor: 병렬 실행
- ConfidenceCalculatorAgent: 신뢰도 계산
- ResultCombinerAgent: 결과 통합

유틸리티 에이전트 (1개):
- FallbackAgent: 풀백 처리
"""

from .base_agent import BaseAgent
from .query_analyzer import QueryAnalyzerAgent
from .investment_intent_detector import InvestmentIntentDetector
from .data_agent import DataAgent
from .news_agent import NewsAgent
from .analysis_agent import AnalysisAgent
from .knowledge_agent import KnowledgeAgent
from .visualization_agent import VisualizationAgent
from .response_agent import ResponseAgent

# 메타 에이전트
from .service_planner import ServicePlannerAgent
from .parallel_executor import ParallelExecutor, parallel_executor
from .result_combiner import ResultCombinerAgent
from .confidence_calculator import ConfidenceCalculatorAgent, confidence_calculator

# 유틸리티 에이전트
from .fallback_agent import (
    FallbackAgent, 
    NewsSourceFallback,
    get_fallback_agent, 
    get_news_source_fallback
)

__all__ = [
    # 기본
    'BaseAgent',
    
    # 전문 에이전트
    'QueryAnalyzerAgent',
    'InvestmentIntentDetector',
    'DataAgent',
    'NewsAgent',
    'AnalysisAgent',
    'KnowledgeAgent',
    'VisualizationAgent',
    'ResponseAgent',
    
    # 메타 에이전트
    'ServicePlannerAgent',
    'ParallelExecutor',
    'parallel_executor',
    'ResultCombinerAgent',
    'ConfidenceCalculatorAgent',
    'confidence_calculator',
    
    # 유틸리티 에이전트
    'FallbackAgent',
    'NewsSourceFallback',
    'get_fallback_agent',
    'get_news_source_fallback'
]
