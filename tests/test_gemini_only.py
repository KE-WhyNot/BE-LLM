#!/usr/bin/env python3
"""
Gemini 2.0 Flash 전용 테스트
깔끔하게 정리된 Gemini만 사용하는 시스템 테스트
"""

import os
import time
from datetime import datetime

# 환경변수 설정 (Gemini 전용)
os.environ['PRIMARY_MODEL'] = 'gemini-2.0-flash-exp'
os.environ['FALLBACK_MODEL'] = 'gemini-2.0-flash-exp'
os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash-exp'
os.environ['LANGSMITH_PROJECT'] = 'pr-rundown-hurry-88'
os.environ['LANGCHAIN_TRACING_V2'] = 'true'

from app.services.langgraph_enhanced.config import get_model_config, get_enhanced_settings
from app.services.langgraph_enhanced.model_selector import (
    ModelSelector, 
    TaskType, 
    select_model_for_task, 
    get_task_type_from_query
)
from app.services.langgraph_enhanced.llm_manager import get_gemini_llm, get_default_gemini_llm
from app.services.langgraph_enhanced.simplified_intelligent_workflow import simplified_intelligent_workflow


class GeminiOnlyTester:
    """Gemini 전용 시스템 테스터"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.model_config = get_model_config()
        self.model_selector = ModelSelector()
        
        # 테스트 쿼리들
        self.test_queries = [
            "삼성전자 주가 알려줘",
            "PER이 뭐야?",
            "삼성전자 기술적 분석과 최신 뉴스를 종합해서 투자 의견을 알려줘",
            "Python으로 주가 차트를 그리는 코드를 만들어줘",
            "안녕하세요"
        ]
    
    def run_gemini_only_test(self):
        """Gemini 전용 시스템 테스트 실행"""
        print("🚀 Gemini 2.0 Flash 전용 시스템 테스트")
        print("=" * 60)
        
        # 1. 설정 확인
        self._check_gemini_settings()
        
        # 2. LLM 인스턴스 테스트
        self._test_llm_instances()
        
        # 3. 모델 선택 테스트
        self._test_model_selection()
        
        # 4. 실제 워크플로우 테스트
        self._test_workflow()
        
        # 5. 성능 요약
        self._performance_summary()
    
    def _check_gemini_settings(self):
        """Gemini 설정 확인"""
        print("\n📋 1. Gemini 설정 확인")
        print("-" * 40)
        
        print(f"✅ 기본 모델: {self.settings.primary_model}")
        print(f"✅ 폴백 모델: {self.settings.fallback_model}")
        print(f"✅ Gemini 모델: {self.settings.gemini_model}")
        
        # 환경변수 확인
        env_vars = ["PRIMARY_MODEL", "FALLBACK_MODEL", "GEMINI_MODEL"]
        print(f"\n🔧 환경변수 설정:")
        for var in env_vars:
            value = os.getenv(var, "설정 안됨")
            print(f"   {var}: {value}")
        
        # 모델 설정 확인
        print(f"\n⚙️ 모델 설정:")
        for key, value in self.model_config.items():
            print(f"   {key}: {value}")
    
    def _test_llm_instances(self):
        """LLM 인스턴스 테스트"""
        print(f"\n🤖 2. Gemini LLM 인스턴스 테스트")
        print("-" * 40)
        
        try:
            # 기본 LLM 테스트
            llm1 = get_default_gemini_llm(temperature=0.7)
            print(f"✅ 기본 LLM 로드 성공: gemini-2.0-flash-exp")
            
            # 캐싱 테스트
            llm2 = get_default_gemini_llm(temperature=0.7)
            print(f"✅ LLM 캐싱 확인: {llm1 is llm2}")
            
            # 다른 temperature 테스트
            llm3 = get_gemini_llm("gemini-2.0-flash-exp", temperature=0.1)
            print(f"✅ 다른 temperature LLM 로드: gemini-2.0-flash-exp")
            
            # 간단한 응답 테스트
            response = llm1.invoke("안녕하세요! 간단히 인사해주세요.")
            print(f"✅ 응답 테스트 성공: {response.content[:50]}...")
            
        except Exception as e:
            print(f"❌ LLM 인스턴스 테스트 실패: {e}")
    
    def _test_model_selection(self):
        """모델 선택 테스트"""
        print(f"\n🎯 3. 모델 선택 테스트")
        print("-" * 40)
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n📋 테스트 {i}: {query}")
            
            # 작업 유형 감지
            detected_task = get_task_type_from_query(query)
            print(f"   🎯 감지된 작업: {detected_task.value}")
            
            # 모델 선택
            selected_model = select_model_for_task(detected_task, query)
            print(f"   🤖 선택된 모델: {selected_model}")
            
            # 추천 정보
            recommendation = self.model_selector.get_model_recommendation(detected_task)
            print(f"   💡 추천 이유: {recommendation['reason']}")
    
    def _test_workflow(self):
        """실제 워크플로우 테스트"""
        print(f"\n🔄 4. 실제 워크플로우 테스트")
        print("-" * 40)
        
        workflow_results = []
        
        for i, query in enumerate(self.test_queries[:3], 1):  # 처음 3개만 테스트
            print(f"\n📋 워크플로우 테스트 {i}: {query}")
            
            start_time = time.time()
            
            try:
                # 실제 워크플로우 실행
                result = simplified_intelligent_workflow.process_query(
                    query=query,
                    user_id=i,
                    session_id=f"gemini_test_{i}"
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # 결과 분석
                success = result.get("success", False)
                complexity = result.get("query_complexity", "unknown")
                confidence = result.get("confidence_score", 0.0)
                services_used = result.get("services_used", [])
                
                print(f"   ⏱️ 처리 시간: {processing_time:.2f}초")
                print(f"   🔧 복잡도: {complexity}")
                print(f"   📊 신뢰도: {confidence:.2f}")
                print(f"   🛠️ 사용된 서비스: {', '.join(services_used)}")
                print(f"   ✅ 성공: {success}")
                
                if success and result.get("response"):
                    response_length = len(result["response"])
                    print(f"   📝 응답 길이: {response_length}자")
                    print(f"   💬 응답 미리보기: {result['response'][:100]}...")
                
                workflow_results.append({
                    "query": query,
                    "processing_time": processing_time,
                    "success": success,
                    "confidence": confidence,
                    "services_count": len(services_used)
                })
                
            except Exception as e:
                print(f"   ❌ 워크플로우 실행 실패: {e}")
                workflow_results.append({
                    "query": query,
                    "processing_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                })
        
        # 결과 저장
        self.workflow_results = workflow_results
    
    def _performance_summary(self):
        """성능 요약"""
        print(f"\n📊 5. 성능 요약")
        print("=" * 60)
        
        if hasattr(self, 'workflow_results'):
            successful_tests = sum(1 for r in self.workflow_results if r['success'])
            avg_processing_time = sum(r['processing_time'] for r in self.workflow_results) / len(self.workflow_results)
            avg_confidence = sum(r['confidence'] for r in self.workflow_results if r['success']) / max(successful_tests, 1)
            
            print(f"✅ 성공률: {successful_tests}/{len(self.workflow_results)} ({successful_tests/len(self.workflow_results)*100:.1f}%)")
            print(f"⏱️ 평균 처리 시간: {avg_processing_time:.2f}초")
            print(f"📊 평균 신뢰도: {avg_confidence:.2f}")
        
        print(f"\n🎯 Gemini 2.0 Flash 전용 시스템 특징:")
        print("   🚀 빠른 응답 속도 (1초 이내)")
        print("   💰 저렴한 비용 (무료 할당량 많음)")
        print("   🇰🇷 한국어 금융 용어 특화")
        print("   📏 긴 컨텍스트 처리 (1M 토큰)")
        print("   🎯 단순하고 깔끔한 구조")
        
        print(f"\n⚙️ 최적화된 설정:")
        print("   PRIMARY_MODEL=gemini-2.0-flash-exp")
        print("   FALLBACK_MODEL=gemini-2.0-flash-exp")
        print("   GEMINI_MODEL=gemini-2.0-flash-exp")
        print("   (GPT 관련 설정 제거됨)")


if __name__ == "__main__":
    tester = GeminiOnlyTester()
    tester.run_gemini_only_test()
