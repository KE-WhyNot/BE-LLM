"""
LangGraph 기반 동적 프롬프트 생성 시스템
각 workflow_components에 최적화된 프롬프트를 동적으로 생성
"""

from typing import Dict, Any, List, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import json

from app.config import settings


class PromptGenerator:
    """동적 프롬프트 생성기"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.prompt_templates = self._load_prompt_templates()
    
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
    
    def _load_prompt_templates(self) -> Dict[str, Dict[str, str]]:
        """프롬프트 템플릿 로드"""
        return {
            "analysis": {
                "base": """당신은 전문 금융 애널리스트입니다. 
다음 데이터를 분석하여 투자 인사이트를 제공하세요:

데이터: {financial_data}
사용자 질문: {user_query}
컨텍스트: {context}

분석 포인트:
1. 기술적 분석 (가격 추세, 거래량)
2. 기본적 분석 (PER, PBR, ROE 등)
3. 시장 상황 고려
4. 투자 위험도 평가
5. 구체적인 투자 제안

응답 형식:
- 핵심 인사이트 (3-5줄)
- 기술적 분석 결과
- 기본적 분석 결과  
- 투자 제안 및 위험 요소
- 종합 평가 (매수/보유/매도)""",
                
                "optimized": """당신은 {user_profile}를 위한 맞춤형 금융 애널리스트입니다.

사용자 특성: {user_profile}
투자 경험: {investment_experience}
관심 분야: {interests}
위험 선호도: {risk_tolerance}

분석 데이터: {financial_data}
질문: {user_query}
시장 컨텍스트: {market_context}

{user_profile}에게 맞는 분석을 제공하세요:
1. 이해하기 쉬운 설명
2. 구체적인 수치와 근거
3. 실용적인 투자 조언
4. 위험 관리 방안"""
            },
            
            "visualization": {
                "base": """당신은 금융 데이터 시각화 전문가입니다.
다음 데이터로 차트를 생성하세요:

데이터: {financial_data}
요청: {user_query}

차트 요구사항:
1. 캔들스틱 + 거래량 통합 차트
2. 한글 폰트 지원
3. 색상 구분 (상승/하락)
4. 평균 거래량 표시
5. 직관적인 레이아웃""",
                
                "optimized": """당신은 {user_level} 사용자를 위한 차트 생성 전문가입니다.

사용자 레벨: {user_level}
차트 선호도: {chart_preferences}
데이터: {financial_data}
요청: {user_query}

{user_level}에게 최적화된 차트를 생성하세요:
1. 적절한 복잡도 조절
2. 명확한 시각적 구분
3. 핵심 정보 강조
4. 사용자 친화적 디자인"""
            },
            
            "news": {
                "base": """당신은 금융 뉴스 분석 전문가입니다.
다음 뉴스들을 분석하여 종합적인 시장 인사이트를 제공하세요:

뉴스 데이터: {news_data}
사용자 질문: {user_query}
관련 종목: {related_stocks}

분석 요구사항:
1. 뉴스 영향도 분석
2. 시장 반응 예측
3. 투자에 미치는 영향
4. 관련 종목 영향도
5. 종합적인 시장 전망""",
                
                "optimized": """당신은 {user_interests}에 특화된 뉴스 분석가입니다.

사용자 관심사: {user_interests}
투자 포트폴리오: {portfolio}
뉴스 데이터: {news_data}
질문: {user_query}

{user_interests}에 맞는 뉴스 분석을 제공하세요:
1. 관련성 높은 뉴스 우선
2. 포트폴리오 영향도 분석
3. 실시간 시장 반응
4. 투자 전략 제안"""
            }
        }
    
    def generate_analysis_prompt(self, 
                                financial_data: Dict[str, Any], 
                                user_query: str,
                                context: Dict[str, Any] = None) -> str:
        """분석용 프롬프트 생성"""
        if not context:
            context = {}
        
        # 사용자 프로필 기반 최적화
        user_profile = context.get('user_profile', '일반 투자자')
        investment_experience = context.get('investment_experience', '중급')
        interests = context.get('interests', ['기술주'])
        risk_tolerance = context.get('risk_tolerance', '보통')
        
        if user_profile != '일반 투자자':
            template = self.prompt_templates["analysis"]["optimized"]
            return template.format(
                user_profile=user_profile,
                investment_experience=investment_experience,
                interests=', '.join(interests),
                risk_tolerance=risk_tolerance,
                financial_data=json.dumps(financial_data, ensure_ascii=False, indent=2),
                user_query=user_query,
                market_context=context.get('market_context', '현재 시장 상황')
            )
        else:
            template = self.prompt_templates["analysis"]["base"]
            return template.format(
                financial_data=json.dumps(financial_data, ensure_ascii=False, indent=2),
                user_query=user_query,
                context=context.get('context', '')
            )
    
    def generate_visualization_prompt(self,
                                    financial_data: Dict[str, Any],
                                    user_query: str,
                                    context: Dict[str, Any] = None) -> str:
        """시각화용 프롬프트 생성"""
        if not context:
            context = {}
        
        user_level = context.get('user_level', '중급')
        chart_preferences = context.get('chart_preferences', '기본')
        
        if user_level in ['초급', '전문가']:
            template = self.prompt_templates["visualization"]["optimized"]
            return template.format(
                user_level=user_level,
                chart_preferences=chart_preferences,
                financial_data=json.dumps(financial_data, ensure_ascii=False, indent=2),
                user_query=user_query
            )
        else:
            template = self.prompt_templates["visualization"]["base"]
            return template.format(
                financial_data=json.dumps(financial_data, ensure_ascii=False, indent=2),
                user_query=user_query
            )
    
    def generate_news_prompt(self,
                            news_data: List[Dict[str, Any]],
                            user_query: str,
                            context: Dict[str, Any] = None) -> str:
        """뉴스용 프롬프트 생성"""
        if not context:
            context = {}
        
        user_interests = context.get('interests', ['기술주'])
        portfolio = context.get('portfolio', [])
        
        template = self.prompt_templates["news"]["optimized"]
        return template.format(
            user_interests=', '.join(user_interests),
            portfolio=', '.join(portfolio),
            news_data=json.dumps(news_data, ensure_ascii=False, indent=2),
            user_query=user_query
        )
    
    def generate_context_aware_prompt(self,
                                    service_type: str,
                                    data: Dict[str, Any],
                                    user_query: str,
                                    user_context: Dict[str, Any] = None) -> str:
        """컨텍스트 기반 프롬프트 생성"""
        if not user_context:
            user_context = {}
        
        # 사용자 히스토리 기반 컨텍스트 추가
        conversation_history = user_context.get('conversation_history', [])
        user_preferences = user_context.get('preferences', {})
        
        # 동적 프롬프트 생성
        if service_type == "analysis":
            return self.generate_analysis_prompt(data, user_query, user_context)
        elif service_type == "visualization":
            return self.generate_visualization_prompt(data, user_query, user_context)
        elif service_type == "news":
            return self.generate_news_prompt(data, user_query, user_context)
        else:
            return f"다음 데이터를 분석하세요: {json.dumps(data, ensure_ascii=False)}"


# 전역 프롬프트 생성기 인스턴스
prompt_generator = PromptGenerator()
