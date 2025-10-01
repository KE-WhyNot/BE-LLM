"""
LangGraph Enhanced System 테스트
"""

import pytest
from unittest.mock import Mock, patch
from app.services.langgraph_enhanced import (
    prompt_generator,
    enhanced_financial_workflow,
    performance_monitor,
    ai_analysis_service
)


class TestPromptGenerator:
    """프롬프트 생성기 테스트"""
    
    def test_generate_analysis_prompt(self):
        """분석 프롬프트 생성 테스트"""
        financial_data = {
            "symbol": "005930.KS",
            "current_price": 86000,
            "price_change_percent": 3.24
        }
        
        prompt = prompt_generator.generate_analysis_prompt(
            financial_data=financial_data,
            user_query="삼성전자 분석해줘",
            context={"user_profile": "초급 투자자"}
        )
        
        assert "삼성전자 분석해줘" in prompt
        assert "005930.KS" in prompt
        assert "초급 투자자" in prompt
    
    def test_generate_visualization_prompt(self):
        """시각화 프롬프트 생성 테스트"""
        financial_data = {"symbol": "005930.KS", "current_price": 86000}
        
        prompt = prompt_generator.generate_visualization_prompt(
            financial_data=financial_data,
            user_query="삼성전자 차트",
            context={"user_level": "전문가"}
        )
        
        assert "삼성전자 차트" in prompt
        assert "전문가" in prompt


class TestEnhancedFinancialWorkflow:
    """향상된 워크플로우 테스트"""
    
    @patch('app.services.langgraph_enhanced.enhanced_financial_workflow.query_classifier')
    def test_process_query_success(self, mock_classifier):
        """쿼리 처리 성공 테스트"""
        mock_classifier.classify.return_value = "visualization"
        
        result = enhanced_financial_workflow.process_query("삼성전자 주가")
        
        assert result["success"] is True
        assert "action_type" in result
        assert "reply_text" in result
    
    def test_extract_user_context(self):
        """사용자 컨텍스트 추출 테스트"""
        from app.services.langgraph_enhanced.enhanced_financial_workflow import EnhancedFinancialWorkflowService
        
        service = EnhancedFinancialWorkflowService()
        
        # Mock state
        state = {
            "messages": [Mock(content="삼성전자 주가 알려줘")],
            "user_query": "삼성전자 주가"
        }
        
        context = service._extract_user_context(state)
        
        assert "user_profile" in context
        assert "investment_experience" in context
        assert "interests" in context


class TestPerformanceMonitor:
    """성능 모니터링 테스트"""
    
    def test_record_metric(self):
        """메트릭 기록 테스트"""
        performance_monitor.record_metric(
            query="삼성전자 주가",
            query_type="visualization",
            processing_time=1.5,
            success=True,
            user_context={"user_profile": "중급 투자자"}
        )
        
        assert len(performance_monitor.metrics) > 0
    
    def test_get_performance_summary(self):
        """성능 요약 조회 테스트"""
        # 테스트 데이터 추가
        performance_monitor.record_metric(
            query="테스트 쿼리",
            query_type="analysis",
            processing_time=2.0,
            success=True
        )
        
        summary = performance_monitor.get_performance_summary()
        
        assert "total_queries" in summary
        assert "avg_processing_time" in summary
        assert "success_rate" in summary
    
    def test_start_ab_test(self):
        """A/B 테스트 시작 테스트"""
        test_id = performance_monitor.start_ab_test(
            "test_prompt",
            {"variant": "original"},
            {"variant": "optimized"}
        )
        
        assert test_id is not None
        assert test_id in performance_monitor.ab_tests


class TestAIAnalysisService:
    """AI 분석 서비스 테스트"""
    
    @patch('app.services.langgraph_enhanced.ai_analysis_service.ChatOpenAI')
    def test_analyze_data_with_llm(self, mock_llm):
        """LLM을 사용한 데이터 분석 테스트"""
        # Mock LLM 설정
        mock_response = Mock()
        mock_response.content = "삼성전자는 현재 상승 추세에 있습니다."
        mock_llm.return_value.invoke.return_value = mock_response
        
        financial_data = {
            "symbol": "005930.KS",
            "current_price": 86000,
            "price_change_percent": 3.24
        }
        
        result = ai_analysis_service.analyze_data(
            query="삼성전자 분석해줘",
            financial_data=financial_data,
            user_context={"user_profile": "중급 투자자"}
        )
        
        assert "삼성전자" in result
    
    def test_analyze_data_fallback(self):
        """폴백 분석 테스트"""
        financial_data = {
            "symbol": "005930.KS",
            "current_price": 86000,
            "price_change_percent": 3.24
        }
        
        result = ai_analysis_service._fallback_analysis(financial_data)
        
        assert "상승" in result or "하락" in result or "분석" in result


if __name__ == "__main__":
    pytest.main([__file__])
