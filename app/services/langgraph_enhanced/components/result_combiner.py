"""
결과 조합기
단일 책임: 여러 서비스 결과를 하나의 응답으로 조합하는 역할만 담당
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import get_enhanced_settings
from ..error_handler import safe_execute_enhanced
from .query_complexity_analyzer import ComplexityAnalysis


class ResultCombiner:
    """결과 조합기"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.combination_templates = self._load_combination_templates()
    
    def _load_combination_templates(self) -> Dict[str, str]:
        """결과 조합 템플릿 로드"""
        return {
            "simple": "📊 **{query}**\n\n{primary_result}",
            "moderate": "📊 **{query}**\n\n{primary_result}\n\n📰 **추가 정보**\n{additional_info}",
            "complex": "📊 **종합 분석: {query}**\n\n{financial_analysis}\n\n📰 **뉴스 정보**\n{news_info}\n\n💡 **투자 의견**\n{investment_opinion}",
            "multi_faceted": "📊 **다면적 분석: {query}**\n\n{comprehensive_analysis}\n\n📈 **차트 분석**\n{chart_analysis}\n\n📰 **시장 동향**\n{market_trends}\n\n🎯 **종합 의견**\n{final_opinion}"
        }
    
    def combine_results(self, 
                       query: str, 
                       service_results: Dict[str, Any], 
                       complexity_analysis: ComplexityAnalysis) -> Dict[str, Any]:
        """서비스 결과들을 조합하여 최종 응답 생성"""
        try:
            complexity_level = complexity_analysis.level.value
            
            # 결과 데이터 추출
            extracted_data = self._extract_result_data(service_results)
            
            # 복잡도에 따른 조합 전략 선택
            if complexity_level == "simple":
                combined_response = self._combine_simple_results(query, extracted_data)
            elif complexity_level == "moderate":
                combined_response = self._combine_moderate_results(query, extracted_data)
            elif complexity_level == "complex":
                combined_response = self._combine_complex_results(query, extracted_data)
            else:  # multi_faceted
                combined_response = self._combine_multi_faceted_results(query, extracted_data)
            
            return {
                "success": True,
                "response": combined_response,
                "data_sources": list(service_results.keys()),
                "combination_strategy": complexity_level,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # 조합 실패 시 기본 응답 반환
            return {
                "success": False,
                "response": self._generate_fallback_response(query, service_results),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_result_data(self, service_results: Dict[str, Any]) -> Dict[str, Any]:
        """서비스 결과에서 데이터 추출"""
        extracted = {}
        
        for service_name, result in service_results.items():
            if result.get("success"):
                data = result.get("data", {})
                
                if service_name == "financial_data":
                    extracted["financial_info"] = self._extract_financial_data(data)
                elif service_name == "analysis":
                    extracted["analysis_info"] = self._extract_analysis_data(data)
                elif service_name == "news":
                    extracted["news_info"] = self._extract_news_data(data)
                elif service_name == "knowledge":
                    extracted["knowledge_info"] = self._extract_knowledge_data(data)
                elif service_name == "visualization":
                    extracted["chart_info"] = self._extract_chart_data(data)
        
        return extracted
    
    def _extract_financial_data(self, data: Dict[str, Any]) -> str:
        """금융 데이터 추출"""
        if isinstance(data, dict) and "data" in data:
            financial_data = data["data"]
            if isinstance(financial_data, dict):
                price = financial_data.get("current_price", "N/A")
                change = financial_data.get("change", "N/A")
                return f"현재가: {price}, 변동: {change}"
        return "금융 데이터를 가져올 수 없습니다."
    
    def _extract_analysis_data(self, data: Dict[str, Any]) -> str:
        """분석 데이터 추출"""
        if isinstance(data, str):
            return data[:200] + "..." if len(data) > 200 else data
        elif isinstance(data, dict) and "analysis" in data:
            return data["analysis"][:200] + "..." if len(data["analysis"]) > 200 else data["analysis"]
        return "분석 결과를 가져올 수 없습니다."
    
    def _extract_news_data(self, data: Dict[str, Any]) -> str:
        """뉴스 데이터 추출"""
        if isinstance(data, list) and data:
            news_items = []
            for item in data[:3]:  # 최대 3개 뉴스
                if isinstance(item, dict):
                    title = item.get("title", "제목 없음")
                    news_items.append(f"• {title}")
            return "\n".join(news_items)
        return "관련 뉴스를 찾을 수 없습니다."
    
    def _extract_knowledge_data(self, data: Dict[str, Any]) -> str:
        """지식 데이터 추출"""
        if isinstance(data, str):
            return data[:150] + "..." if len(data) > 150 else data
        elif isinstance(data, dict) and "context" in data:
            return data["context"][:150] + "..." if len(data["context"]) > 150 else data["context"]
        return "관련 지식을 찾을 수 없습니다."
    
    def _extract_chart_data(self, data: Dict[str, Any]) -> str:
        """차트 데이터 추출"""
        if isinstance(data, dict) and "chart_base64" in data:
            return "차트가 생성되었습니다. 시각적 분석을 참고하세요."
        return "차트를 생성할 수 없습니다."
    
    def _combine_simple_results(self, query: str, extracted_data: Dict[str, Any]) -> str:
        """단순 결과 조합"""
        primary_result = ""
        
        if "financial_info" in extracted_data:
            primary_result = extracted_data["financial_info"]
        elif "knowledge_info" in extracted_data:
            primary_result = extracted_data["knowledge_info"]
        else:
            primary_result = "요청하신 정보를 찾을 수 없습니다."
        
        return f"📊 **{query}**\n\n{primary_result}"
    
    def _combine_moderate_results(self, query: str, extracted_data: Dict[str, Any]) -> str:
        """중간 복잡도 결과 조합"""
        primary_result = extracted_data.get("financial_info", "기본 정보 없음")
        additional_info = ""
        
        if "news_info" in extracted_data:
            additional_info += f"📰 **최신 뉴스**\n{extracted_data['news_info']}\n\n"
        
        if "analysis_info" in extracted_data:
            additional_info += f"📈 **분석**\n{extracted_data['analysis_info']}"
        
        return f"📊 **{query}**\n\n{primary_result}\n\n{additional_info}"
    
    def _combine_complex_results(self, query: str, extracted_data: Dict[str, Any]) -> str:
        """복잡한 결과 조합"""
        financial_analysis = extracted_data.get("financial_info", "금융 데이터 없음")
        news_info = extracted_data.get("news_info", "뉴스 정보 없음")
        analysis_info = extracted_data.get("analysis_info", "분석 정보 없음")
        
        investment_opinion = "종합적인 분석을 바탕으로 투자 결정을 신중히 고려하시기 바랍니다."
        
        return f"""📊 **종합 분석: {query}**

💰 **금융 정보**
{financial_analysis}

📰 **뉴스 정보**
{news_info}

📈 **기술적 분석**
{analysis_info}

💡 **투자 의견**
{investment_opinion}"""
    
    def _combine_multi_faceted_results(self, query: str, extracted_data: Dict[str, Any]) -> str:
        """다면적 결과 조합"""
        comprehensive_analysis = ""
        chart_analysis = ""
        market_trends = ""
        final_opinion = ""
        
        # 종합 분석 구성
        if "financial_info" in extracted_data:
            comprehensive_analysis += f"💰 {extracted_data['financial_info']}\n"
        if "analysis_info" in extracted_data:
            comprehensive_analysis += f"📈 {extracted_data['analysis_info']}\n"
        
        # 차트 분석
        if "chart_info" in extracted_data:
            chart_analysis = extracted_data["chart_info"]
        else:
            chart_analysis = "차트 분석 정보가 없습니다."
        
        # 시장 동향
        if "news_info" in extracted_data:
            market_trends = extracted_data["news_info"]
        else:
            market_trends = "시장 동향 정보가 없습니다."
        
        # 종합 의견
        final_opinion = "다면적 분석 결과를 종합하여 신중한 투자 결정을 권장합니다."
        
        return f"""📊 **다면적 분석: {query}**

📋 **종합 분석**
{comprehensive_analysis}

📈 **차트 분석**
{chart_analysis}

📰 **시장 동향**
{market_trends}

🎯 **종합 의견**
{final_opinion}"""
    
    def _generate_fallback_response(self, query: str, service_results: Dict[str, Any]) -> str:
        """폴백 응답 생성"""
        available_services = list(service_results.keys())
        
        if available_services:
            return f"'{query}'에 대한 부분적인 정보만 제공할 수 있습니다. 사용된 서비스: {', '.join(available_services)}"
        else:
            return f"'{query}'에 대한 정보를 제공할 수 없습니다. 다른 질문을 시도해보세요."
