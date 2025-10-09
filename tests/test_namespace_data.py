"""
Pinecone 네임스페이스별 데이터 확인 테스트
각 네임스페이스에 데이터가 있는지, 검색이 제대로 되는지 확인
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pinecone_rag_service import search_pinecone, get_context_for_query
from app.services.pinecone_config import KNOWLEDGE_NAMESPACES, NAMESPACE_DESCRIPTIONS

def test_namespace_data():
    """각 네임스페이스별 데이터 확인"""
    
    print("=" * 80)
    print("📊 Pinecone 네임스페이스 데이터 확인 테스트")
    print("=" * 80)
    print()
    
    # 테스트 쿼리 정의
    test_queries = {
        "terminology": ["ETF가 뭐야", "PER이 뭐야", "ROE란"],
        "financial_analysis": ["삼성전자 재무제표", "경제 동향", "실적 분석"],
        "youth_policy": ["청년 대출", "청년 정책", "청년 지원금"]
    }
    
    results = {}
    
    # 각 네임스페이스 테스트
    for category, namespace in KNOWLEDGE_NAMESPACES.items():
        print(f"\n{'='*80}")
        print(f"📂 카테고리: {category}")
        print(f"🔖 네임스페이스: {namespace}")
        print(f"📝 설명: {NAMESPACE_DESCRIPTIONS.get(namespace, 'N/A')}")
        print(f"{'='*80}\n")
        
        results[category] = {
            "namespace": namespace,
            "queries": []
        }
        
        # 해당 카테고리의 테스트 쿼리 실행
        for query in test_queries.get(category, []):
            print(f"🔍 쿼리: '{query}'")
            print(f"   네임스페이스: {namespace}")
            
            try:
                # 1. search_pinecone 직접 호출
                search_results = search_pinecone(query, top_k=3, namespace=namespace)
                
                if search_results and hasattr(search_results, 'matches'):
                    match_count = len(search_results.matches)
                    print(f"   ✅ 검색 성공: {match_count}개 매치")
                    
                    if match_count > 0:
                        for i, match in enumerate(search_results.matches[:2], 1):
                            score = match.score
                            text = match.metadata.get('text', 'N/A')[:100]
                            print(f"      [{i}] 점수: {score:.4f}")
                            print(f"          텍스트: {text}...")
                    
                    results[category]["queries"].append({
                        "query": query,
                        "success": True,
                        "match_count": match_count,
                        "has_data": match_count > 0
                    })
                else:
                    print(f"   ⚠️ 검색 결과 없음 (None 또는 matches 없음)")
                    results[category]["queries"].append({
                        "query": query,
                        "success": False,
                        "match_count": 0,
                        "has_data": False
                    })
                
                # 2. get_context_for_query 테스트
                context = get_context_for_query(query, top_k=3, namespace=namespace)
                if context and len(context) > 0:
                    print(f"   📄 컨텍스트 길이: {len(context)} 글자")
                    print(f"   📄 컨텍스트 미리보기: {context[:150]}...")
                else:
                    print(f"   ❌ 컨텍스트 없음 (빈 문자열)")
                
            except Exception as e:
                print(f"   ❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                
                results[category]["queries"].append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
            
            print()
    
    # 최종 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    for category, result in results.items():
        namespace = result["namespace"]
        queries = result["queries"]
        
        success_count = sum(1 for q in queries if q.get("success", False))
        has_data_count = sum(1 for q in queries if q.get("has_data", False))
        total = len(queries)
        
        status = "✅" if has_data_count > 0 else "❌"
        print(f"\n{status} {category} ({namespace}):")
        print(f"   - 성공한 검색: {success_count}/{total}")
        print(f"   - 데이터 있는 쿼리: {has_data_count}/{total}")
        
        if has_data_count == 0:
            print(f"   ⚠️ 경고: 이 네임스페이스에 데이터가 없거나 검색되지 않습니다!")


def test_timeout_issue():
    """타임아웃 문제 디버깅"""
    print("\n" + "=" * 80)
    print("⏱️ 타임아웃 문제 디버깅")
    print("=" * 80)
    
    import time
    
    test_query = "ETF가 뭐야"
    namespace = KNOWLEDGE_NAMESPACES["terminology"]
    
    print(f"\n🔍 쿼리: '{test_query}'")
    print(f"🔖 네임스페이스: {namespace}")
    
    try:
        print("   ⏳ 검색 시작...")
        start_time = time.time()
        
        results = search_pinecone(test_query, top_k=3, namespace=namespace)
        
        elapsed = time.time() - start_time
        print(f"   ✅ 검색 완료: {elapsed:.2f}초")
        
        if results and hasattr(results, 'matches'):
            print(f"   📊 결과: {len(results.matches)}개")
        else:
            print(f"   ⚠️ 결과 없음")
        
        if elapsed > 5:
            print(f"   ⚠️ 경고: 검색이 {elapsed:.2f}초나 걸렸습니다 (느림)")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 오류: {e} ({elapsed:.2f}초)")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Pinecone 네임스페이스 데이터 확인 시작\n")
    
    # 1. 각 네임스페이스 데이터 확인
    test_namespace_data()
    
    # 2. 타임아웃 문제 디버깅
    test_timeout_issue()
    
    print("\n✅ 테스트 완료")

