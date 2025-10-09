"""
통합 동적 프롬프팅 워크플로우 테스트
"""

import os
import sys
import asyncio
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.langgraph_enhanced import integrated_dynamic_workflow
from app.config import settings


def test_integrated_dynamic_workflow():
    """통합 동적 워크플로우 테스트"""
    print("=" * 60)
    print("🚀 통합 동적 프롬프팅 워크플로우 테스트")
    print("=" * 60)
    
    # 테스트 쿼리들
    test_queries = [
        {
            "query": "삼성전자 주가 알려줘",
            "user_id": 1,
            "description": "초보자용 주가 조회"
        },
        {
            "query": "삼성전자 기술적 분석과 시장 동향을 종합적으로 분석해줘",
            "user_id": 2,
            "description": "전문가용 상세 분석"
        },
        {
            "query": "네이버 최신 뉴스",
            "user_id": 1,
            "description": "뉴스 조회"
        },
        {
            "query": "PER이 뭐야?",
            "user_id": 1,
            "description": "지식 검색"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 테스트 {i}: {test_case['description']}")
        print(f"쿼리: {test_case['query']}")
        print("-" * 40)
        
        try:
            # 통합 동적 워크플로우 실행
            result = integrated_dynamic_workflow.process_query(
                query=test_case["query"],
                user_id=test_case["user_id"],
                session_id=f"test_session_{i}"
            )
            
            if "error" in result and result["error"]:
                print(f"❌ 오류: {result['error']}")
                continue
            
            # 결과 출력
            print(f"✅ 응답: {result['response'][:100]}...")
            print(f"👤 사용자 프로필: {result['user_profile']}")
            print(f"🎯 최적화 라우팅: {result['optimization_route']}")
            print(f"📊 처리 단계: {result['processing_steps']}")
            
            # 성능 메트릭
            metrics = result.get('performance_metrics', {})
            if metrics:
                print(f"⏱️ 처리 시간: {metrics.get('total_processing_time', 0):.2f}초")
                print(f"🔍 쿼리 복잡도: {metrics.get('query_complexity', 'unknown')}")
            
            # 차트 데이터 확인
            if result.get('chart_data'):
                print("📊 차트 데이터 생성됨")
            
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 통합 동적 프롬프팅 워크플로우 테스트 완료!")
    print("=" * 60)


def test_user_profile_extraction():
    """사용자 프로필 추출 테스트"""
    print("\n🔍 사용자 프로필 추출 테스트")
    print("-" * 40)
    
    test_queries = [
        "삼성전자 주가 간단하게 알려줘",  # 초보자
        "삼성전자 기술적 분석과 복잡한 시장 동향을 전문적으로 분석해줘",  # 전문가
        "네이버와 SK하이닉스 주가 비교"  # 중급자
    ]
    
    for query in test_queries:
        result = integrated_dynamic_workflow.process_query(query, user_id=1)
        profile = result.get('user_profile', {})
        print(f"쿼리: {query}")
        print(f"추출된 프로필: {profile}")
        print()


def test_performance_comparison():
    """성능 비교 테스트"""
    print("\n⚡ 성능 비교 테스트")
    print("-" * 40)
    
    query = "삼성전자 주가 분석해줘"
    
    # 여러 번 실행하여 평균 성능 측정
    times = []
    for i in range(3):
        start_time = datetime.now()
        result = integrated_dynamic_workflow.process_query(query, user_id=1)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        times.append(processing_time)
        
        print(f"실행 {i+1}: {processing_time:.2f}초")
    
    avg_time = sum(times) / len(times)
    print(f"평균 처리 시간: {avg_time:.2f}초")
    
    if avg_time < 3.0:
        print("✅ 성능 우수 (3초 미만)")
    elif avg_time < 5.0:
        print("⚠️ 성능 보통 (3-5초)")
    else:
        print("❌ 성능 개선 필요 (5초 초과)")


if __name__ == "__main__":
    # 환경 변수 설정 (LangSmith 트레이싱)
    if hasattr(settings, 'langsmith_api_key') and settings.langsmith_api_key:
        os.environ['LANGCHAIN_API_KEY'] = settings.langsmith_api_key
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        os.environ['LANGCHAIN_PROJECT'] = 'financial-chatbot-dynamic'
        print("🔗 LangSmith 트레이싱 활성화됨")
    
    # 테스트 실행
    test_integrated_dynamic_workflow()
    test_user_profile_extraction()
    test_performance_comparison()
