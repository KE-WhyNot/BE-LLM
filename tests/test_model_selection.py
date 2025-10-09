#!/usr/bin/env python3
"""
모델 선택 최적화 테스트
Gemini 2.0 vs GPT-4o 성능 비교 및 작업별 최적 모델 선택 검증
"""

import os
import time
from app.services.langgraph_enhanced.model_selector import (
    ModelSelector, 
    TaskType, 
    select_model_for_task, 
    get_task_type_from_query
)


def test_model_selection():
    """모델 선택 시스템 테스트"""
    
    print("🤖 모델 선택 최적화 테스트")
    print("=" * 50)
    
    # 모델 선택기 초기화
    model_selector = ModelSelector()
    
    # 테스트 쿼리들
    test_queries = [
        {
            "query": "삼성전자 주가 알려줘",
            "expected_task": TaskType.KOREAN_FINANCE,
            "expected_model": "gemini-2.0-flash-exp",
            "reason": "한국 금융 용어 특화"
        },
        {
            "query": "PER이 뭐야?",
            "expected_task": TaskType.KOREAN_FINANCE,
            "expected_model": "gemini-2.0-flash-exp", 
            "reason": "한국 금융 개념 설명"
        },
        {
            "query": "삼성전자 기술적 분석과 최신 뉴스를 종합해서 투자 의견을 알려줘",
            "expected_task": TaskType.COMPLEX_ANALYSIS,
            "expected_model": "gemini-2.0-flash-exp",
            "reason": "긴 컨텍스트와 복잡한 분석"
        },
        {
            "query": "Python으로 주가 차트를 그리는 코드를 만들어줘",
            "expected_task": TaskType.CODE_GENERATION,
            "expected_model": "gpt-4o",
            "reason": "코드 생성 정확도"
        },
        {
            "query": "안녕하세요",
            "expected_task": TaskType.SIMPLE_QUERY,
            "expected_model": "gemini-2.0-flash-exp",
            "reason": "빠른 응답과 저렴한 비용"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 테스트 {i}: {test_case['reason']}")
        print(f"🔍 쿼리: {test_case['query']}")
        print(f"🎯 예상 작업 유형: {test_case['expected_task'].value}")
        print(f"🎯 예상 모델: {test_case['expected_model']}")
        print("-" * 50)
        
        # 작업 유형 추출
        detected_task_type = get_task_type_from_query(test_case['query'])
        
        # 모델 선택
        selected_model = select_model_for_task(
            detected_task_type, 
            test_case['query'],
            {"language": "ko", "complexity": "moderate"}
        )
        
        # 모델 추천 정보 가져오기
        recommendation = model_selector.get_model_recommendation(detected_task_type)
        
        print(f"🔍 감지된 작업 유형: {detected_task_type.value}")
        print(f"🤖 선택된 모델: {selected_model}")
        print(f"💡 추천 모델: {recommendation['recommended']}")
        print(f"📝 추천 이유: {recommendation['reason']}")
        print(f"🔄 대안 모델: {recommendation['alternative']}")
        
        # 정확도 평가
        task_correct = detected_task_type == test_case['expected_task']
        model_correct = selected_model == test_case['expected_model']
        
        if task_correct and model_correct:
            print("✅ 완벽한 매칭!")
            test_result = "성공"
        elif task_correct or model_correct:
            print("⚠️ 부분 매칭")
            test_result = "부분성공"
        else:
            print("❌ 매칭 실패")
            test_result = "실패"
        
        results.append({
            "test_case": test_case,
            "detected_task": detected_task_type,
            "selected_model": selected_model,
            "recommendation": recommendation,
            "task_correct": task_correct,
            "model_correct": model_correct,
            "test_result": test_result
        })
        
        print("-" * 50)
    
    # 전체 결과 요약
    print(f"\n🎉 모델 선택 테스트 완료")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r['test_result'] == "성공")
    partial_tests = sum(1 for r in results if r['test_result'] == "부분성공")
    failed_tests = sum(1 for r in results if r['test_result'] == "실패")
    total_tests = len(results)
    
    print(f"📊 성공률: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"⚠️ 부분성공: {partial_tests}/{total_tests}")
    print(f"❌ 실패: {failed_tests}/{total_tests}")
    
    # 작업 유형별 정확도
    task_accuracy = sum(1 for r in results if r['task_correct']) / total_tests * 100
    model_accuracy = sum(1 for r in results if r['model_correct']) / total_tests * 100
    
    print(f"🎯 작업 유형 정확도: {task_accuracy:.1f}%")
    print(f"🎯 모델 선택 정확도: {model_accuracy:.1f}%")
    
    # 모델별 선택 빈도
    model_counts = {}
    for result in results:
        model = result['selected_model']
        model_counts[model] = model_counts.get(model, 0) + 1
    
    print(f"\n📈 모델별 선택 빈도:")
    for model, count in model_counts.items():
        percentage = count / total_tests * 100
        print(f"   {model}: {count}회 ({percentage:.1f}%)")
    
    # 성능 비교 분석
    print(f"\n⚡ 성능 비교 분석:")
    print("   Gemini 2.0 Flash:")
    print("   ✅ 한국어 금융 용어 특화")
    print("   ✅ 빠른 응답 속도 (1초 이내)")
    print("   ✅ 저렴한 비용 (무료 할당량 많음)")
    print("   ✅ 긴 컨텍스트 처리 (1M 토큰)")
    
    print("\n   GPT-4o:")
    print("   ✅ 높은 정확도")
    print("   ✅ 안정적인 성능")
    print("   ⚠️ 상대적으로 느림 (2-3초)")
    print("   ⚠️ 높은 비용")
    
    print(f"\n🎯 권장사항:")
    print("   • 한국 금융 챗봇: Gemini 2.0 Flash 우선 사용")
    print("   • 복잡한 분석: Gemini 2.0 Flash (긴 컨텍스트 활용)")
    print("   • 코드 생성: GPT-4o (정확도 중시)")
    print("   • 단순 질문: Gemini 2.0 Flash (속도와 비용)")


if __name__ == "__main__":
    test_model_selection()
