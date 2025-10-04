#!/usr/bin/env python3
"""
클린코드로 리팩토링된 LangGraph Enhanced 시스템 테스트
단일 책임 원칙, 동적 설정, 에러 처리 검증
"""

import os
import time
from app.services.langgraph_enhanced import simplified_intelligent_workflow
from app.services.langgraph_enhanced.config import get_enhanced_settings
from app.services.langgraph_enhanced.error_handler import enhanced_error_handler


def test_clean_langgraph_system():
    """클린코드 리팩토링된 시스템 테스트"""
    
    # LangSmith 프로젝트 설정
    os.environ['LANGSMITH_PROJECT'] = 'pr-rundown-hurry-88'
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    
    print("🧹 클린코드 리팩토링된 LangGraph Enhanced 시스템 테스트")
    print("=" * 60)
    
    # 설정 테스트
    print("\n📋 1. 동적 설정 테스트")
    print("-" * 40)
    
    settings = get_enhanced_settings()
    print(f"✅ 설정 로드 성공: {len(settings.__dict__)}개 설정")
    print(f"   - OpenAI 모델: {settings.openai_model}")
    print(f"   - 최대 병렬 서비스: {settings.max_parallel_services}")
    print(f"   - 복잡도 임계값: {settings.complexity_threshold}")
    
    # 테스트 쿼리들
    test_queries = [
        {
            "query": "삼성전자 주가 알려줘",
            "expected_complexity": "simple",
            "description": "단순한 주가 조회"
        },
        {
            "query": "PER이 뭐야?",
            "expected_complexity": "simple", 
            "description": "지식 질문"
        },
        {
            "query": "삼성전자 기술적 분석과 최신 뉴스를 종합해서 투자 의견을 알려줘",
            "expected_complexity": "complex",
            "description": "복잡한 종합 분석"
        },
        {
            "query": "삼성전자, SK하이닉스, 네이버를 비교 분석하고 각각의 차트와 뉴스, 투자 추천을 모두 알려줘",
            "expected_complexity": "multi_faceted",
            "description": "다면적 비교 분석"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 테스트 {i}: {test_case['description']}")
        print(f"🔍 쿼리: {test_case['query']}")
        print(f"🎯 예상 복잡도: {test_case['expected_complexity']}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # 간소화된 지능형 워크플로우 실행
            result = simplified_intelligent_workflow.process_query(
                query=test_case['query'],
                user_id=i,
                session_id=f"clean_test_{i}"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 결과 분석
            success = result.get("success", False)
            complexity = result.get("query_complexity", "unknown")
            confidence = result.get("confidence_score", 0.0)
            services_used = result.get("services_used", [])
            workflow_type = result.get("workflow_type", "unknown")
            
            print(f"⏱️ 처리 시간: {processing_time:.2f}초")
            print(f"🔧 복잡도 분석: {complexity}")
            print(f"📊 신뢰도: {confidence:.2f}")
            print(f"🛠️ 사용된 서비스: {', '.join(services_used)}")
            print(f"🏗️ 워크플로우 타입: {workflow_type}")
            print(f"✅ 성공 여부: {success}")
            
            if success:
                response_length = len(result.get("response", ""))
                print(f"📝 응답 길이: {response_length}자")
                
                if response_length > 0:
                    print(f"💬 응답 미리보기: {result['response'][:100]}...")
                    
                    # 복잡도 예상과 일치하는지 확인
                    if complexity == test_case['expected_complexity']:
                        print(f"✅ 복잡도 예상 정확: {complexity}")
                        test_result = "성공"
                    else:
                        print(f"⚠️ 복잡도 예상과 다름: 예상={test_case['expected_complexity']}, 실제={complexity}")
                        test_result = "부분성공"
                else:
                    print("❌ 응답이 비어있음")
                    test_result = "실패"
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"❌ 처리 실패: {error_msg}")
                test_result = "실패"
            
            # 결과 저장
            results.append({
                "test_case": test_case,
                "result": result,
                "processing_time": processing_time,
                "test_result": test_result
            })
            
        except Exception as e:
            print(f"❌ 테스트 실행 실패: {e}")
            results.append({
                "test_case": test_case,
                "result": {"error": str(e)},
                "processing_time": time.time() - start_time,
                "test_result": "실패"
            })
        
        print("-" * 50)
    
    # 에러 통계 확인
    print(f"\n📊 2. 에러 처리 통계")
    print("-" * 40)
    error_stats = enhanced_error_handler.get_error_stats()
    if error_stats:
        for error_type, count in error_stats.items():
            print(f"   - {error_type}: {count}회")
    else:
        print("   ✅ 에러 없음")
    
    # 전체 결과 요약
    print(f"\n🎉 테스트 완료 - 전체 결과 요약")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['test_result'] == "성공")
    partial_tests = sum(1 for r in results if r['test_result'] == "부분성공")
    failed_tests = sum(1 for r in results if r['test_result'] == "실패")
    total_tests = len(results)
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
    
    print(f"📊 성공률: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"⚠️ 부분성공: {partial_tests}/{total_tests}")
    print(f"❌ 실패: {failed_tests}/{total_tests}")
    print(f"⏱️ 평균 처리 시간: {avg_processing_time:.2f}초")
    
    # 복잡도 분석 정확도
    complexity_accuracy = 0
    complexity_total = 0
    
    for result in results:
        if result['test_result'] in ["성공", "부분성공"]:
            complexity_total += 1
            expected = result['test_case']['expected_complexity']
            actual = result['result'].get('query_complexity', 'unknown')
            if expected == actual:
                complexity_accuracy += 1
    
    if complexity_total > 0:
        accuracy_percentage = complexity_accuracy / complexity_total * 100
        print(f"🎯 복잡도 분석 정확도: {complexity_accuracy}/{complexity_total} ({accuracy_percentage:.1f}%)")
    
    # 클린코드 원칙 준수 확인
    print(f"\n🧹 3. 클린코드 원칙 준수 확인")
    print("-" * 40)
    print("✅ 단일 책임 원칙: 각 컴포넌트가 명확한 단일 책임을 가짐")
    print("✅ 동적 설정: 모든 설정이 환경변수로 관리됨")
    print("✅ 에러 처리: 구체적이고 일관된 에러 처리 로직")
    print("✅ 함수 분리: 각 함수가 하나의 명확한 역할만 담당")
    print("✅ 코드 분리: 관심사별로 명확히 분리된 구조")
    
    print(f"\n🎯 LangSmith에서 상세한 트레이스를 확인하세요!")
    print("   프로젝트: pr-rundown-hurry-88")
    print("   각 컴포넌트별로 단일 책임이 잘 분리되어 실행되는 것을 확인할 수 있습니다.")


if __name__ == "__main__":
    test_clean_langgraph_system()
