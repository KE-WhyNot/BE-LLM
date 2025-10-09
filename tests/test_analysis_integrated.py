"""
AnalysisAgent RAG + 뉴스 통합 테스트
"""

from app.services.langgraph_enhanced.workflow_router import WorkflowRouter

def test_analysis_with_rag_and_news():
    """삼성전자 분석 테스트 (RAG + 뉴스)"""
    
    router = WorkflowRouter()
    
    test_query = "삼성전자 주식 분석해줘"
    
    print("=" * 80)
    print("📊 통합 투자 분석 테스트 (RAG + 뉴스)")
    print("=" * 80)
    print(f"질문: {test_query}")
    print("-" * 80)
    
    try:
        result = router.process_query(test_query, 'test_analysis')
        
        if result.get('success'):
            print("\n✅ 분석 성공")
            print(f"응답 길이: {len(result.get('reply_text', ''))} 글자")
            print("\n" + "=" * 80)
            print("📝 응답 내용:")
            print("=" * 80)
            print(result.get('reply_text', ''))
        else:
            print(f"\n❌ 분석 실패: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")


if __name__ == "__main__":
    test_analysis_with_rag_and_news()

