"""
간단한 성능 측정 테스트

기존 시스템의 실제 성능 측정
"""

import time
import asyncio
import statistics
from typing import Dict, List, Any
from datetime import datetime
import json

# 기존 시스템 import
from app.services.chatbot.chatbot_service import FinancialChatbotService

class SimpleBenchmark:
    """간단한 성능 벤치마크 테스트 클래스"""
    
    def __init__(self):
        self.chatbot = FinancialChatbotService()
        
        # 테스트 쿼리들
        self.test_queries = [
            "삼성전자 주가 알려줘",
            "애플 주식 분석해줘", 
            "PER이 뭐야?",
            "최신 금융 뉴스 보여줘",
            "투자 전략 추천해줘"
        ]
    
    async def test_system(self) -> Dict[str, Any]:
        """시스템 성능 측정"""
        print("🔍 시스템 성능 측정 중...")
        
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
                # 시스템 호출
                from app.schemas.chat_schema import ChatRequest
                request = ChatRequest(
                    message=query,
                    user_id=1,
                    session_id="benchmark_session"
                )
                response = await self.chatbot.process_chat_request(request)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                results["response_times"].append(response_time)
                results["success_count"] += 1
                
                print(f"    ✅ 성공 ({response_time:.2f}초)")
                print(f"    📄 응답 길이: {len(str(response))}자")
                
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
    
    def print_results(self, results: Dict[str, Any]):
        """결과 출력"""
        print("\n" + "="*60)
        print("📊 실제 성능 측정 결과")
        print("="*60)
        
        print(f"\n🔍 시스템: {results['system']}")
        print(f"📝 총 쿼리 수: {results['total_queries']}개")
        print(f"✅ 성공: {results['success_count']}개")
        print(f"❌ 실패: {results['error_count']}개")
        print(f"📈 성공률: {results.get('success_rate', 0):.1f}%")
        
        if results["response_times"]:
            print(f"\n⏱️ 응답 시간:")
            print(f"  - 평균: {results['avg_response_time']:.2f}초")
            print(f"  - 최소: {results['min_response_time']:.2f}초")
            print(f"  - 최대: {results['max_response_time']:.2f}초")
        
        if results["errors"]:
            print(f"\n❌ 에러 목록:")
            for error in results["errors"]:
                print(f"  - {error['query']}: {error['error']}")
        
        print("="*60)
    
    async def run_benchmark(self):
        """벤치마크 실행"""
        print("🚀 성능 벤치마크 시작!")
        print(f"📝 테스트 쿼리 수: {len(self.test_queries)}개")
        print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 시스템 테스트
        results = await self.test_system()
        
        # 결과 출력
        self.print_results(results)
        
        # 결과 저장
        with open("simple_benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과가 simple_benchmark_results.json에 저장되었습니다.")
        
        return results

async def main():
    """메인 실행 함수"""
    benchmark = SimpleBenchmark()
    results = await benchmark.run_benchmark()
    return results

if __name__ == "__main__":
    asyncio.run(main())
