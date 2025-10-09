"""
간단한 동적 프롬프팅 테스트
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.langgraph_enhanced.prompt_generator import PromptGenerator
from app.services.langgraph_enhanced.enhanced_workflow_components import (
    enhanced_query_classifier,
    enhanced_financial_data_service,
    enhanced_analysis_service
)


def test_dynamic_prompting():
    """동적 프롬프팅 기본 테스트"""
    print("=" * 60)
    print("🚀 동적 프롬프팅 시스템 테스트")
    print("=" * 60)
    
    # 1. 프롬프트 생성기 테스트
    print("\n1️⃣ 프롬프트 생성기 테스트")
    prompt_gen = PromptGenerator()
    
    user_profile = {
        'level': 'beginner',
        'interests': ['삼성전자'],
        'risk_tolerance': 'conservative'
    }
    
    context = {
        'user_profile': user_profile,
        'investment_experience': 'beginner',
        'interests': ['삼성전자'],
        'risk_tolerance': 'conservative'
    }
    
    try:
        prompt = prompt_gen.generate_analysis_prompt(
            financial_data={'price': 86000, 'volume': 1000000},
            user_query='삼성전자 주가 분석해줘',
            context=context
        )
        print(f"✅ 프롬프트 생성 성공 (길이: {len(prompt)}자)")
        print(f"📝 프롬프트 미리보기: {prompt[:200]}...")
    except Exception as e:
        print(f"❌ 프롬프트 생성 실패: {e}")
    
    # 2. 향상된 쿼리 분류기 테스트
    print("\n2️⃣ 향상된 쿼리 분류기 테스트")
    
    test_queries = [
        "삼성전자 주가 알려줘",
        "삼성전자 기술적 분석해줘",
        "PER이 뭐야?"
    ]
    
    for query in test_queries:
        try:
            classification = enhanced_query_classifier.classify_with_context(
                query, user_profile, {}
            )
            print(f"✅ 쿼리: '{query}' → 분류: {classification}")
        except Exception as e:
            print(f"❌ 분류 실패: {e}")
    
    # 3. 향상된 금융 데이터 서비스 테스트
    print("\n3️⃣ 향상된 금융 데이터 서비스 테스트")
    
    try:
        data = enhanced_financial_data_service.get_financial_data_with_context(
            "삼성전자 주가", user_profile
        )
        print(f"✅ 데이터 조회 성공")
        print(f"📊 데이터 키: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
    
    # 4. 향상된 분석 서비스 테스트
    print("\n4️⃣ 향상된 분석 서비스 테스트")
    
    test_data = {
        'symbol': '005930',
        'current_price': 86000,
        'price_change': 1500,
        'volume': 1000000
    }
    
    try:
        analysis = enhanced_analysis_service.analyze_financial_data_with_context(
            test_data, "삼성전자 주가 분석", user_profile
        )
        print(f"✅ 분석 성공")
        print(f"📝 분석 결과: {analysis[:200]}...")
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 동적 프롬프팅 시스템 테스트 완료!")
    print("=" * 60)


def test_user_profile_extraction():
    """사용자 프로필 추출 테스트"""
    print("\n🔍 사용자 프로필 추출 테스트")
    print("-" * 40)
    
    # 통합 워크플로우에서 프로필 추출 로직 테스트
    from app.services.langgraph_enhanced.integrated_dynamic_workflow import IntegratedDynamicWorkflow
    
    workflow = IntegratedDynamicWorkflow()
    
    test_queries = [
        "삼성전자 주가 간단하게 알려줘",  # 초보자
        "삼성전자 기술적 분석과 복잡한 시장 동향을 전문적으로 분석해줘",  # 전문가
    ]
    
    for query in test_queries:
        try:
            profile = workflow._extract_user_profile(query, [], 1)
            print(f"쿼리: {query}")
            print(f"추출된 프로필: {profile}")
            print()
        except Exception as e:
            print(f"❌ 프로필 추출 실패: {e}")


if __name__ == "__main__":
    # 환경 변수 설정 (LangSmith 트레이싱)
    try:
        from app.config import settings
        if hasattr(settings, 'langsmith_api_key') and settings.langsmith_api_key:
            os.environ['LANGCHAIN_API_KEY'] = settings.langsmith_api_key
            os.environ['LANGCHAIN_TRACING_V2'] = 'true'
            os.environ['LANGCHAIN_PROJECT'] = 'financial-chatbot-dynamic'
            print("🔗 LangSmith 트레이싱 활성화됨")
    except:
        print("⚠️ LangSmith 설정을 로드할 수 없습니다.")
    
    # 테스트 실행
    test_dynamic_prompting()
    test_user_profile_extraction()
