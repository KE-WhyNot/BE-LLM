"""
실제 성능 측정 벤치마크 테스트

기존 시스템 vs LangGraph Enhanced 시스템 성능 비교
"""

import time
import asyncio
import statistics
from typing import Dict, List, Any
from datetime import datetime
import json

# 기존 시스템 import
from app.services.chatbot.chatbot_service import FinancialChatbotService
from app.services.workflow_components.query_classifier_service import QueryClassifierService

# LangGraph Enhanced 시스템 import
from app.services.langgraph_enhanced.enhanced_financial_workflow import EnhancedFinancialWorkflow
from app.services.langgraph_enhanced.performance_monitor import PerformanceMonitor

class PerformanceBenchmark:
    """성능 벤치마크 테스트 클래스"""
    
    def __init__(self):
        self.existing_chatbot = FinancialChatbotService()
        self.enhanced_workflow = EnhancedFinancialWorkflow()
        self.performance_monitor = PerformanceMonitor()
        
        # 테스트 쿼리들
        self.test_queries = [
            "삼성전자 주가 알려줘",
            "애플 주식 분석해줘", 
            "투자 전략 추천해줘",
            "PER이 뭐야?",
            "최신 금융 뉴스 보여줘",
            "포트폴리오 구성 어떻게 해야 할까?",
            "시장 전망은 어때?",
            "리스크 관리 방법 알려줘"
        ]
    
    async def test_existing_system(self) -> Dict[str, Any]:
        """기존 시스템 성능 측정"""
        print("🔍 기존 시스템 성능 측정 중...")
        
        results = {
            "system": "기존 시스템",
            "total_queries": len(self.test_queries),
            "response_times": [],
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"  📝 테스트 {i}/{len(self.test_queries)}: {query}")
            
            start_time = time.time()
            try:
                # 기존 시스템 호출
                response = await self.existing_chatbot.process_query({
                    "query": query,
                    "user_id": "benchmark_test"
                })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                results["response_times"].append(response_time)
                results["success_count"] += 1
                
                print(f"    ✅ 성공 ({response_time:.2f}초)")
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                
                results["response_times"].append(response_time)
                results["error_count"] += 1
                results["errors"].append({
                    "query": query,
                    "error": str(e),
                    "response_time": response_time
                })
                
                print(f"    ❌ 실패 ({response_time:.2f}초): {str(e)}")
        
        # 통계 계산
        if results["response_times"]:
            results["avg_response_time"] = statistics.mean(results["response_times"])
            results["min_response_time"] = min(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
            results["success_rate"] = results["success_count"] / results["total_queries"] * 100
        
        results["end_time"] = datetime.now().isoformat()
        return results
    
    async def test_enhanced_system(self) -> Dict[str, Any]:
        """LangGraph Enhanced 시스템 성능 측정"""
        print("🚀 LangGraph Enhanced 시스템 성능 측정 중...")
        
        results = {
            "system": "LangGraph Enhanced",
            "total_queries": len(self.test_queries),
            "response_times": [],
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"  📝 테스트 {i}/{len(self.test_queries)}: {query}")
            
            start_time = time.time()
            try:
                # Enhanced 시스템 호출
                response = await self.enhanced_workflow.process_query({
                    "query": query,
                    "user_id": "benchmark_test"
                })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                results["response_times"].append(response_time)
                results["success_count"] += 1
                
                print(f"    ✅ 성공 ({response_time:.2f}초)")
                
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                
                results["response_times"].append(response_time)
                results["error_count"] += 1
                results["errors"].append({
                    "query": query,
                    "error": str(e),
                    "response_time": response_time
                })
                
                print(f"    ❌ 실패 ({response_time:.2f}초): {str(e)}")
        
        # 통계 계산
        if results["response_times"]:
            results["avg_response_time"] = statistics.mean(results["response_times"])
            results["min_response_time"] = min(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
            results["success_rate"] = results["success_count"] / results["total_queries"] * 100
        
        results["end_time"] = datetime.now().isoformat()
        return results
    
    def compare_results(self, existing_results: Dict[str, Any], enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """두 시스템 결과 비교"""
        comparison = {
            "test_date": datetime.now().isoformat(),
            "total_queries": len(self.test_queries),
            "comparison": {}
        }
        
        # 응답 시간 비교
        if "avg_response_time" in existing_results and "avg_response_time" in enhanced_results:
            time_improvement = ((existing_results["avg_response_time"] - enhanced_results["avg_response_time"]) / existing_results["avg_response_time"]) * 100
            comparison["comparison"]["response_time"] = {
                "existing": existing_results["avg_response_time"],
                "enhanced": enhanced_results["avg_response_time"],
                "improvement_percent": time_improvement
            }
        
        # 성공률 비교
        if "success_rate" in existing_results and "success_rate" in enhanced_results:
            success_improvement = enhanced_results["success_rate"] - existing_results["success_rate"]
            comparison["comparison"]["success_rate"] = {
                "existing": existing_results["success_rate"],
                "enhanced": enhanced_results["success_rate"],
                "improvement_percent": success_improvement
            }
        
        # 에러율 비교
        existing_error_rate = existing_results["error_count"] / existing_results["total_queries"] * 100
        enhanced_error_rate = enhanced_results["error_count"] / enhanced_results["total_queries"] * 100
        error_improvement = existing_error_rate - enhanced_error_rate
        
        comparison["comparison"]["error_rate"] = {
            "existing": existing_error_rate,
            "enhanced": enhanced_error_rate,
            "improvement_percent": error_improvement
        }
        
        return comparison
    
    def print_results(self, existing_results: Dict[str, Any], enhanced_results: Dict[str, Any], comparison: Dict[str, Any]):
        """결과 출력"""
        print("\n" + "="*60)
        print("📊 성능 벤치마크 결과")
        print("="*60)
        
        print(f"\n🔍 기존 시스템:")
        print(f"  - 평균 응답 시간: {existing_results.get('avg_response_time', 0):.2f}초")
        print(f"  - 성공률: {existing_results.get('success_rate', 0):.1f}%")
        print(f"  - 에러율: {existing_results['error_count']}/{existing_results['total_queries']} ({existing_results['error_count']/existing_results['total_queries']*100:.1f}%)")
        
        print(f"\n🚀 LangGraph Enhanced:")
        print(f"  - 평균 응답 시간: {enhanced_results.get('avg_response_time', 0):.2f}초")
        print(f"  - 성공률: {enhanced_results.get('success_rate', 0):.1f}%")
        print(f"  - 에러율: {enhanced_results['error_count']}/{enhanced_results['total_queries']} ({enhanced_results['error_count']/enhanced_results['total_queries']*100:.1f}%)")
        
        print(f"\n📈 개선 효과:")
        if "response_time" in comparison["comparison"]:
            time_improvement = comparison["comparison"]["response_time"]["improvement_percent"]
            print(f"  - 응답 시간: {time_improvement:+.1f}%")
        
        if "success_rate" in comparison["comparison"]:
            success_improvement = comparison["comparison"]["success_rate"]["improvement_percent"]
            print(f"  - 성공률: {success_improvement:+.1f}%")
        
        if "error_rate" in comparison["comparison"]:
            error_improvement = comparison["comparison"]["error_rate"]["improvement_percent"]
            print(f"  - 에러율: {error_improvement:+.1f}%")
        
        print("="*60)
    
    async def run_benchmark(self):
        """전체 벤치마크 실행"""
        print("🚀 성능 벤치마크 시작!")
        print(f"📝 테스트 쿼리 수: {len(self.test_queries)}개")
        print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 기존 시스템 테스트
        existing_results = await self.test_existing_system()
        
        print("\n" + "-"*40)
        
        # Enhanced 시스템 테스트
        enhanced_results = await self.test_enhanced_system()
        
        # 결과 비교
        comparison = self.compare_results(existing_results, enhanced_results)
        
        # 결과 출력
        self.print_results(existing_results, enhanced_results, comparison)
        
        # 결과 저장
        results_data = {
            "existing_system": existing_results,
            "enhanced_system": enhanced_results,
            "comparison": comparison
        }
        
        with open("benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과가 benchmark_results.json에 저장되었습니다.")
        
        return results_data

async def main():
    """메인 실행 함수"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_benchmark()
    return results

if __name__ == "__main__":
    asyncio.run(main())
