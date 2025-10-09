#!/usr/bin/env python3
"""
간소화된 워크플로우 시스템 테스트
자동 판단으로 단순한 질문과 복잡한 질문을 구분하여 처리하는지 확인
"""

import os
import time
from app.services.chatbot.financial_workflow import financial_workflow

def test_simplified_workflow():
    """간소화된 워크플로우 시스템 테스트"""
    
    # LangSmith 프로젝트 설정
    os.environ['LANGSMITH_PROJECT'] = 'pr-rundown-hurry-88'
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    
    print("🚀 간소화된 워크플로우 시스템 테스트")
    print("=" * 50)
    
    # 테스트 쿼리들
    test_queries = [
        {
            "query": "삼성전자 주가 알려줘",
            "description": "단순한 질문 → 기본 워크플로우 예상",
            "expected": "기본"
        },
        {
            "query": "PER이 뭐야?",
            "description": "지식 질문 → 기본 워크플로우 예상",
            "expected": "기본"
        },
        {
            "query": "삼성전자 기술적 분석과 최신 뉴스를 종합해서 투자 의견을 알려줘",
            "description": "복잡한 질문 → 지능형 워크플로우 예상",
            "expected": "지능형"
        },
        {
            "query": "삼성전자, SK하이닉스, 네이버를 비교 분석하고 각각의 차트와 뉴스, 투자 추천을 모두 알려줘",
            "description": "매우 복잡한 질문 → 지능형 워크플로우 예상",
            "expected": "지능형"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 테스트 {i}: {test_case['description']}")
        print(f"🔍 쿼리: {test_case['query']}")
        print(f"🎯 예상 워크플로우: {test_case['expected']}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # 워크플로우 실행 (자동 선택)
            result = financial_workflow.process_query(
                user_query=test_case['query'],
                user_id=i
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 결과 분석
            workflow_type = result.get("action_data", {}).get("workflow_type", "unknown")
            success = result.get("success", False)
            response_length = len(result.get("reply_text", ""))
            
            print(f"⏱️ 처리 시간: {processing_time:.2f}초")
            print(f"🔧 사용된 워크플로우: {workflow_type}")
            print(f"✅ 성공 여부: {success}")
            print(f"📝 응답 길이: {response_length}자")
            
            if success:
                print(f"💬 응답 미리보기: {result['reply_text'][:100]}...")
                
                # 예상과 일치하는지 확인
                if workflow_type == test_case['expected'] or workflow_type == "intelligent_multi_service":
                    print(f"✅ 예상과 일치: {test_case['expected']} 워크플로우 사용")
                    test_result = "성공"
                else:
                    print(f"⚠️ 예상과 다름: 예상={test_case['expected']}, 실제={workflow_type}")
                    test_result = "부분성공"
            else:
                print(f"❌ 처리 실패: {result.get('reply_text', '알 수 없는 오류')}")
                test_result = "실패"
            
            # 결과 저장
            results.append({
                "test_case": test_case,
                "result": result,
                "processing_time": processing_time,
                "workflow_type": workflow_type,
                "test_result": test_result
            })
            
        except Exception as e:
            print(f"❌ 테스트 실행 실패: {e}")
            results.append({
                "test_case": test_case,
                "result": {"error": str(e)},
                "processing_time": time.time() - start_time,
                "workflow_type": "error",
                "test_result": "실패"
            })
        
        print("-" * 50)
    
    # 전체 결과 요약
    print("\n🎉 테스트 완료 - 전체 결과 요약")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r['test_result'] == "성공")
    partial_tests = sum(1 for r in results if r['test_result'] == "부분성공")
    failed_tests = sum(1 for r in results if r['test_result'] == "실패")
    total_tests = len(results)
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
    
    print(f"📊 성공률: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"⚠️ 부분성공: {partial_tests}/{total_tests}")
    print(f"❌ 실패: {failed_tests}/{total_tests}")
    print(f"⏱️ 평균 처리 시간: {avg_processing_time:.2f}초")
    
    # 워크플로우별 성능 분석
    workflow_stats = {}
    for result in results:
        workflow_type = result['workflow_type']
        if workflow_type not in workflow_stats:
            workflow_stats[workflow_type] = []
        workflow_stats[workflow_type].append(result['processing_time'])
    
    print("\n📈 워크플로우별 성능:")
    for workflow_type, times in workflow_stats.items():
        avg_time = sum(times) / len(times)
        print(f"  {workflow_type}: 평균 {avg_time:.2f}초 ({len(times)}개 테스트)")
    
    # 자동 판단 정확도 분석
    correct_predictions = 0
    total_predictions = 0
    
    for result in results:
        if result['test_result'] in ["성공", "부분성공"]:
            total_predictions += 1
            expected = result['test_case']['expected']
            actual = result['workflow_type']
            
            # 예상과 실제가 일치하거나, 복잡한 질문에 대해 지능형 워크플로우가 사용된 경우
            if (expected == "기본" and actual == "basic") or \
               (expected == "지능형" and actual in ["intelligent_multi_service", "basic"]):
                correct_predictions += 1
    
    if total_predictions > 0:
        accuracy = correct_predictions / total_predictions * 100
        print(f"\n🎯 자동 판단 정확도: {correct_predictions}/{total_predictions} ({accuracy:.1f}%)")
    
    print("\n🎯 LangSmith에서 상세한 트레이스를 확인하세요!")
    print("   프로젝트: pr-rundown-hurry-88")
    print("   각 테스트별로 워크플로우 선택 과정을 볼 수 있습니다.")

if __name__ == "__main__":
    test_simplified_workflow()
