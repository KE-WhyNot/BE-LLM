"""
간소화된 지능형 워크플로우
클린코드 원칙에 따라 단순하고 명확한 구조로 재구성
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import get_enhanced_settings, get_model_config
from .error_handler import handle_enhanced_error, safe_execute_enhanced
from .components import (
    QueryComplexityAnalyzer, 
    ServicePlanner, 
    ServiceExecutor, 
    ResultCombiner, 
    ConfidenceCalculator
)
# Lazy import로 순환 참조 방지
# from app.services.workflow_components import ...
# from app.services.rag_service import ...


class SimplifiedIntelligentWorkflow:
    """간소화된 지능형 워크플로우"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.model_config = get_model_config()
        
        # 컴포넌트 초기화
        self.complexity_analyzer = QueryComplexityAnalyzer()
        self.service_planner = ServicePlanner()
        self.service_executor = ServiceExecutor()
        self.result_combiner = ResultCombiner()
        self.confidence_calculator = ConfidenceCalculator()
        
        # 서비스 매핑 (Lazy import로 순환 참조 방지)
        self._service_mapping = None
    
    @property
    def service_mapping(self):
        """서비스 매핑을 lazy하게 로드"""
        if self._service_mapping is None:
            from app.services.workflow_components import (
                financial_data_service,
                analysis_service,
                news_service,
                response_generator,
                visualization_service
            )
            from app.services.rag_service import rag_service
            
            self._service_mapping = {
                "financial_data": financial_data_service,
                "analysis": analysis_service,
                "news": news_service,
                "knowledge": rag_service,
                "visualization": visualization_service,
                "response": response_generator
            }
        return self._service_mapping
    
    def process_query(self, 
                     query: str, 
                     user_id: int = 1, 
                     session_id: str = "default") -> Dict[str, Any]:
        """쿼리 처리 - 메인 진입점"""
        start_time = datetime.now()
        
        try:
            # 1. 쿼리 복잡도 분석
            complexity_analysis = self.complexity_analyzer.analyze_complexity(query)
            
            # 2. 서비스 실행 계획 수립
            service_plan = self.service_planner.create_service_plan(
                complexity_analysis.required_services,
                complexity_analysis.level.value,
                {"user_id": user_id, "session_id": session_id}
            )
            
            # 3. 서비스 실행
            service_results = self._execute_services(query, service_plan)
            
            # 4. 결과 조합
            combined_result = self.result_combiner.combine_results(
                query, service_results, complexity_analysis
            )
            
            # 5. 신뢰도 계산
            confidence_score = self.confidence_calculator.calculate_confidence(
                service_results, complexity_analysis
            )
            
            # 6. 응답 생성
            final_response = self._generate_final_response(
                query, combined_result, confidence_score, complexity_analysis
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "response": final_response,
                "query_complexity": complexity_analysis.level.value,
                "confidence_score": confidence_score,
                "services_used": list(service_results.keys()),
                "processing_time": processing_time,
                "workflow_type": "simplified_intelligent",
                "chart_data": self._extract_chart_data(service_results)
            }
            
        except Exception as e:
            error_result = handle_enhanced_error(
                e, 
                context={"query": query, "user_id": user_id, "session_id": session_id},
                operation="simplified_intelligent_workflow"
            )
            
            return {
                "success": False,
                "error": error_result["error_message"],
                "workflow_type": "simplified_intelligent",
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _execute_services(self, 
                         query: str, 
                         service_plan) -> Dict[str, Any]:
        """서비스 실행"""
        service_results = {}
        
        if service_plan.strategy.value == "sequential":
            # 순차 실행
            for group in service_plan.service_groups:
                for service_name in group:
                    result = self._execute_single_service(query, service_name)
                    if result["success"]:
                        service_results[service_name] = result
        
        elif service_plan.strategy.value == "parallel":
            # 병렬 실행
            with ThreadPoolExecutor(max_workers=self.settings.max_parallel_services) as executor:
                futures = {}
                for group in service_plan.service_groups:
                    for service_name in group:
                        future = executor.submit(self._execute_single_service, query, service_name)
                        futures[future] = service_name
                
                for future in as_completed(futures, timeout=self.settings.service_timeout):
                    service_name = futures[future]
                    try:
                        result = future.result()
                        if result["success"]:
                            service_results[service_name] = result
                    except Exception as e:
                        print(f"❌ {service_name} 서비스 실행 실패: {e}")
        
        else:  # hybrid
            # 혼합 실행: 그룹별로 순차, 그룹 내에서는 병렬
            for group in service_plan.service_groups:
                if len(group) == 1:
                    # 단일 서비스는 순차 실행
                    result = self._execute_single_service(query, group[0])
                    if result["success"]:
                        service_results[group[0]] = result
                else:
                    # 여러 서비스는 병렬 실행
                    with ThreadPoolExecutor(max_workers=len(group)) as executor:
                        futures = {
                            executor.submit(self._execute_single_service, query, service): service
                            for service in group
                        }
                        
                        for future in as_completed(futures, timeout=self.settings.service_timeout):
                            service_name = futures[future]
                            try:
                                result = future.result()
                                if result["success"]:
                                    service_results[service_name] = result
                            except Exception as e:
                                print(f"❌ {service_name} 서비스 실행 실패: {e}")
        
        return service_results
    
    def _execute_single_service(self, query: str, service_name: str) -> Dict[str, Any]:
        """단일 서비스 실행"""
        try:
            if service_name not in self.service_mapping:
                return {"success": False, "error": f"Unknown service: {service_name}"}
            
            service = self.service_mapping[service_name]
            
            # 서비스별 실행 로직
            if service_name == "financial_data":
                result = service.get_financial_data(query)
            elif service_name == "analysis":
                result = service.analyze_data(query)
            elif service_name == "news":
                result = service.get_news(query)
            elif service_name == "knowledge":
                result = service.get_context_for_query(query)
            elif service_name == "visualization":
                # 시각화는 금융 데이터가 필요하므로 별도 처리
                financial_data = self.service_mapping["financial_data"].get_financial_data(query)
                if financial_data.get("success"):
                    result = service.create_chart("candlestick_volume", financial_data.get("data", {}))
                else:
                    result = {"success": False, "error": "No financial data for visualization"}
            else:
                result = {"success": False, "error": f"Unsupported service: {service_name}"}
            
            return {
                "success": True,
                "service": service_name,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_chart_data(self, service_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """차트 데이터 추출"""
        visualization_result = service_results.get("visualization")
        if visualization_result and visualization_result.get("success"):
            chart_data = visualization_result.get("data")
            if chart_data and "chart_base64" in chart_data:
                return {
                    "chart_base64": chart_data["chart_base64"],
                    "chart_type": "candlestick_volume"
                }
        return None
    
    def _generate_final_response(self, 
                               query: str, 
                               combined_result: Dict[str, Any], 
                               confidence_score: float,
                               complexity_analysis) -> str:
        """최종 응답 생성"""
        try:
            if confidence_score < self.settings.fallback_confidence_threshold:
                # 신뢰도가 낮으면 폴백 응답
                return self._generate_fallback_response(query, complexity_analysis)
            
            # 신뢰도가 높으면 조합된 결과 사용
            return combined_result.get("response", "응답을 생성할 수 없습니다.")
            
        except Exception as e:
            return self._generate_fallback_response(query, complexity_analysis)
    
    def _generate_fallback_response(self, query: str, complexity_analysis) -> str:
        """폴백 응답 생성"""
        complexity_level = complexity_analysis.level.value
        
        if complexity_level == "simple":
            return f"'{query}'에 대한 간단한 답변을 제공할 수 없습니다. 다시 시도해주세요."
        elif complexity_level == "moderate":
            return f"'{query}'에 대한 분석을 완료할 수 없습니다. 다른 질문을 시도해보세요."
        else:
            return f"'{query}'에 대한 종합적인 분석을 제공할 수 없습니다. 질문을 단순화하여 다시 시도해주세요."


# 전역 인스턴스
simplified_intelligent_workflow = SimplifiedIntelligentWorkflow()
