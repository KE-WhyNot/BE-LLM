"""
AI Agent 기반 분석 서비스
동적 프롬프트 생성으로 효율 극대화
"""

from typing import Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import json

from app.config import settings
from app.services.langgraph_enhanced.prompt_generator import prompt_generator


class AIAnalysisService:
    """AI Agent 기반 금융 데이터 분석 서비스"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=settings.google_api_key
            )
        elif settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.openai_api_key
            )
        return None
    
    def analyze_data(self, 
                    query: str, 
                    financial_data: Dict[str, Any],
                    user_context: Dict[str, Any] = None) -> str:
        """AI Agent 기반 데이터 분석"""
        try:
            if not self.llm:
                return self._fallback_analysis(financial_data)
            
            # 동적 프롬프트 생성
            prompt = prompt_generator.generate_context_aware_prompt(
                service_type="analysis",
                data=financial_data,
                user_query=query,
                user_context=user_context or {}
            )
            
            # AI 분석 실행
            messages = [
                SystemMessage(content="당신은 전문 금융 애널리스트입니다."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"AI 분석 중 오류: {e}")
            return self._fallback_analysis(financial_data)
    
    def _fallback_analysis(self, financial_data: Dict[str, Any]) -> str:
        """폴백 분석 (기존 로직)"""
        if not financial_data or "error" in financial_data:
            return "분석할 데이터가 없습니다."
        
        analysis_parts = []
        
        # 가격 변화 분석
        price_change_percent = financial_data.get('price_change_percent', 0)
        if price_change_percent > 0:
            analysis_parts.append(f"📈 주가가 {price_change_percent:.2f}% 상승했습니다.")
        elif price_change_percent < 0:
            analysis_parts.append(f"📉 주가가 {abs(price_change_percent):.2f}% 하락했습니다.")
        
        # PER 분석
        pe_ratio = financial_data.get('pe_ratio', 0)
        if pe_ratio > 0:
            if pe_ratio < 15:
                analysis_parts.append(f"💰 PER {pe_ratio:.1f}는 상대적으로 저평가된 수준입니다.")
            elif pe_ratio > 25:
                analysis_parts.append(f"⚠️ PER {pe_ratio:.1f}는 상대적으로 고평가된 수준입니다.")
            else:
                analysis_parts.append(f"📊 PER {pe_ratio:.1f}는 적정 수준입니다.")
        
        # 거래량 분석
        volume = financial_data.get('volume', 0)
        if volume > 0:
            analysis_parts.append(f"📊 거래량: {volume:,}주")
        
        return "\n".join(analysis_parts) if analysis_parts else "분석 결과를 생성할 수 없습니다."


# 전역 AI 분석 서비스 인스턴스
ai_analysis_service = AIAnalysisService()
