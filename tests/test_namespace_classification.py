"""
네임스페이스 분류 테스트 (실제 RAG 검색 없이 분류만 확인)
"""

from app.services.langgraph_enhanced.agents.knowledge_agent import KnowledgeAgent

def test_namespace_classification():
    """네임스페이스 분류만 테스트"""
    
    agent = KnowledgeAgent()
    
    test_queries = [
        {
            "query": "PER이 뭐야?",
            "expected": "terminology",
            "description": "금융 용어 질문"
        },
        {
            "query": "ROE란 무엇인가요?",
            "expected": "terminology",
            "description": "용어 정의 질문"
        },
        {
            "query": "재무제표 보는 법 알려줘",
            "expected": "financial_analysis",
            "description": "재무 분석 질문"
        },
        {
            "query": "경제 동향 어떻게 분석해?",
            "expected": "financial_analysis",
            "description": "경제 분석 질문"
        },
        {
            "query": "청년 대출 정책 뭐가 있어?",
            "expected": "youth_policy",
            "description": "청년 정책 질문"
        },
        {
            "query": "청년 저축 계좌 알려줘",
            "expected": "youth_policy",
            "description": "청년 금융상품 질문"
        },
        {
            "query": "분산투자 전략 알려줘",
            "expected": "general",
            "description": "일반 투자 전략"
        },
        {
            "query": "리스크 관리 방법",
            "expected": "general",
            "description": "리스크 관리 질문"
        }
    ]
    
    print("=" * 80)
    print("📚 네임스페이스 분류 테스트")
    print("=" * 80)
    
    correct = 0
    total = len(test_queries)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}] {test['description']}")
        print(f"질문: {test['query']}")
        print(f"예상: {test['expected']}")
        
        try:
            # 네임스페이스 결정
            namespace = agent._determine_namespace(test['query'], {})
            
            # 네임스페이스에서 카테고리 추출
            actual_category = None
            for category, ns in agent.namespaces.items():
                if ns == namespace:
                    actual_category = category
                    break
            
            print(f"결과: {actual_category} ({namespace})")
            
            if actual_category == test['expected']:
                print("✅ 정확!")
                correct += 1
            else:
                print(f"❌ 불일치 (예상: {test['expected']}, 결과: {actual_category})")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)
    
    print(f"\n{'='*80}")
    print(f"📊 결과: {correct}/{total} ({correct/total*100:.1f}%) 정확도")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_namespace_classification()

