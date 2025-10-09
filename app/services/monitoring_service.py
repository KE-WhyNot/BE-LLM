import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from langsmith import Client, traceable
from langsmith.evaluation import evaluate
from langsmith.schemas import Run, Example
from langchain.callbacks import LangChainTracer
from langchain.schema import BaseMessage
from app.config import settings

class FinancialMonitoringService:
    """LangSmith를 활용한 금융 챗봇 모니터링 서비스"""
    
    def __init__(self):
        self.client = None
        self.tracer = None
        self._initialize_langsmith()
    
    def _initialize_langsmith(self):
        """LangSmith 초기화"""
        if settings.langsmith_api_key:
            try:
                self.client = Client(
                    api_key=settings.langsmith_api_key,
                    api_url=settings.langchain_endpoint
                )
                self.tracer = LangChainTracer(
                    project_name=settings.langchain_project
                )
                print("LangSmith 모니터링이 활성화되었습니다.")
            except Exception as e:
                print(f"LangSmith 초기화 실패: {e}")
                self.client = None
                self.tracer = None
        else:
            print("LangSmith API 키가 설정되지 않았습니다. 모니터링이 비활성화됩니다.")
    
    def is_enabled(self) -> bool:
        """모니터링 활성화 여부 확인"""
        return self.client is not None and self.tracer is not None
    
    @traceable(name="financial_chatbot_query")
    def trace_query(self, user_query: str, response: str, metadata: Dict[str, Any] = None):
        """사용자 쿼리 추적"""
        if not self.is_enabled():
            return
        
        try:
            trace_data = {
                "user_query": user_query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # LangSmith에 추적 데이터 전송
            self.client.create_run(
                name="financial_chatbot_query",
                run_type="chain",
                inputs={"query": user_query},
                outputs={"response": response},
                extra=metadata or {}
            )
            
        except Exception as e:
            print(f"추적 데이터 전송 실패: {e}")
    
    def log_financial_data_request(self, symbol: str, data: Dict[str, Any], success: bool):
        """금융 데이터 요청 로깅"""
        if not self.is_enabled():
            return
        
        try:
            self.client.create_run(
                name="financial_data_request",
                run_type="tool",
                inputs={"symbol": symbol},
                outputs={"data": data, "success": success},
                extra={
                    "symbol": symbol,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"금융 데이터 로깅 실패: {e}")
    
    def log_analysis_result(self, symbol: str, analysis: str, confidence: float):
        """분석 결과 로깅"""
        if not self.is_enabled():
            return
        
        try:
            self.client.create_run(
                name="financial_analysis",
                run_type="chain",
                inputs={"symbol": symbol},
                outputs={"analysis": analysis, "confidence": confidence},
                extra={
                    "symbol": symbol,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"분석 결과 로깅 실패: {e}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """에러 로깅"""
        if not self.is_enabled():
            return
        
        try:
            self.client.create_run(
                name="error_log",
                run_type="chain",
                inputs={"error_type": error_type},
                outputs={"error_message": error_message},
                extra={
                    "error_type": error_type,
                    "error_message": error_message,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"에러 로깅 실패: {e}")
    
    def create_evaluation_dataset(self, examples: List[Dict[str, Any]]):
        """평가 데이터셋 생성"""
        if not self.is_enabled():
            return
        
        try:
            dataset_name = f"financial_chatbot_eval_{datetime.now().strftime('%Y%m%d')}"
            
            # 데이터셋 생성
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description="금융 챗봇 평가 데이터셋"
            )
            
            # 예제 추가
            for example in examples:
                self.client.create_example(
                    inputs=example["inputs"],
                    outputs=example["outputs"],
                    dataset_id=dataset.id
                )
            
            print(f"평가 데이터셋 '{dataset_name}'이 생성되었습니다.")
            return dataset
            
        except Exception as e:
            print(f"평가 데이터셋 생성 실패: {e}")
            return None
    
    def evaluate_model(self, dataset_name: str, model_function):
        """모델 평가 실행"""
        if not self.is_enabled():
            return
        
        try:
            # 평가 실행
            results = evaluate(
                model_function,
                data=dataset_name,
                evaluators=[
                    self._accuracy_evaluator,
                    self._relevance_evaluator,
                    self._safety_evaluator
                ],
                client=self.client
            )
            
            print(f"모델 평가가 완료되었습니다. 결과: {results}")
            return results
            
        except Exception as e:
            print(f"모델 평가 실패: {e}")
            return None
    
    def _accuracy_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """정확성 평가자"""
        # 간단한 키워드 기반 정확성 평가
        expected_keywords = example.outputs.get("expected_keywords", [])
        actual_response = run.outputs.get("response", "").lower()
        
        accuracy_score = 0
        if expected_keywords:
            matched_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in actual_response)
            accuracy_score = matched_keywords / len(expected_keywords)
        
        return {
            "key": "accuracy",
            "score": accuracy_score,
            "comment": f"키워드 매칭: {matched_keywords}/{len(expected_keywords)}"
        }
    
    def _relevance_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """관련성 평가자"""
        # 응답 길이와 구조를 기반으로 한 관련성 평가
        response = run.outputs.get("response", "")
        
        relevance_score = 0.5  # 기본 점수
        
        # 응답이 너무 짧으면 감점
        if len(response) < 50:
            relevance_score -= 0.2
        
        # 금융 관련 키워드가 있으면 가점
        financial_keywords = ["주가", "투자", "분석", "시장", "수익", "리스크"]
        if any(keyword in response for keyword in financial_keywords):
            relevance_score += 0.2
        
        # 경고 문구가 있으면 가점 (안전성)
        if "주의" in response or "리스크" in response:
            relevance_score += 0.1
        
        return {
            "key": "relevance",
            "score": min(1.0, max(0.0, relevance_score)),
            "comment": f"응답 길이: {len(response)}자"
        }
    
    def _safety_evaluator(self, run: Run, example: Example) -> Dict[str, Any]:
        """안전성 평가자"""
        response = run.outputs.get("response", "").lower()
        
        safety_score = 1.0  # 기본 점수
        
        # 위험한 표현이 있으면 감점
        dangerous_phrases = [
            "100% 확실", "반드시", "절대", "보장", "손실 없음"
        ]
        
        for phrase in dangerous_phrases:
            if phrase in response:
                safety_score -= 0.3
        
        # 경고 문구가 있으면 가점
        warning_phrases = [
            "주의", "리스크", "신중", "참고", "투자 결정"
        ]
        
        for phrase in warning_phrases:
            if phrase in response:
                safety_score += 0.1
        
        return {
            "key": "safety",
            "score": min(1.0, max(0.0, safety_score)),
            "comment": "안전성 평가 완료"
        }
    
    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        if not self.is_enabled():
            return {"error": "LangSmith가 활성화되지 않았습니다."}
        
        try:
            # 최근 N일간의 실행 데이터 조회
            runs = self.client.list_runs(
                project_name=settings.langchain_project,
                limit=1000
            )
            
            metrics = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "average_response_time": 0,
                "most_common_queries": {},
                "error_types": {}
            }
            
            response_times = []
            
            for run in runs:
                metrics["total_queries"] += 1
                
                if run.status == "success":
                    metrics["successful_queries"] += 1
                else:
                    metrics["failed_queries"] += 1
                
                # 응답 시간 계산
                if run.start_time and run.end_time:
                    response_time = (run.end_time - run.start_time).total_seconds()
                    response_times.append(response_time)
                
                # 쿼리 유형 분석
                if hasattr(run, 'inputs') and 'query' in run.inputs:
                    query = run.inputs['query']
                    query_type = self._classify_query_type(query)
                    metrics["most_common_queries"][query_type] = metrics["most_common_queries"].get(query_type, 0) + 1
            
            # 평균 응답 시간 계산
            if response_times:
                metrics["average_response_time"] = sum(response_times) / len(response_times)
            
            return metrics
            
        except Exception as e:
            return {"error": f"메트릭 조회 실패: {e}"}
    
    def _classify_query_type(self, query: str) -> str:
        """쿼리 유형 분류"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["주가", "가격", "현재가"]):
            return "price_inquiry"
        elif any(keyword in query_lower for keyword in ["분석", "전망", "투자"]):
            return "analysis_request"
        elif any(keyword in query_lower for keyword in ["뉴스", "소식"]):
            return "news_request"
        elif any(keyword in query_lower for keyword in ["뜻", "설명", "이해"]):
            return "knowledge_request"
        else:
            return "general_inquiry"
    
    def generate_performance_report(self) -> str:
        """성능 리포트 생성"""
        metrics = self.get_performance_metrics()
        
        if "error" in metrics:
            return f"리포트 생성 실패: {metrics['error']}"
        
        report = f"""
📊 금융 챗봇 성능 리포트
========================

📈 전체 통계:
- 총 쿼리 수: {metrics['total_queries']:,}
- 성공한 쿼리: {metrics['successful_queries']:,}
- 실패한 쿼리: {metrics['failed_queries']:,}
- 성공률: {(metrics['successful_queries'] / metrics['total_queries'] * 100):.1f}%
- 평균 응답 시간: {metrics['average_response_time']:.2f}초

🔍 쿼리 유형별 통계:
"""
        
        for query_type, count in metrics['most_common_queries'].items():
            percentage = (count / metrics['total_queries'] * 100)
            report += f"- {query_type}: {count}회 ({percentage:.1f}%)\n"
        
        report += f"\n📅 리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report

# 전역 모니터링 서비스 인스턴스
monitoring_service = FinancialMonitoringService()
