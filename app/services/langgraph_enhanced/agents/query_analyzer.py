"""
쿼리 분석 에이전트
사용자 질문을 분석하여 적절한 에이전트로 라우팅
"""

from typing import Dict, Any
import time
from .base_agent import BaseAgent
from .investment_intent_detector import InvestmentIntentDetector


class QueryAnalyzerAgent(BaseAgent):
    """🔍 쿼리 분석 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="classification")
        self.agent_name = "query_analyzer"
        # 투자 의도 감지 에이전트 초기화
        self.investment_detector = InvestmentIntentDetector()
    
    def get_prompt_template(self) -> str:
        """쿼리 분석 프롬프트 템플릿"""
        return """당신은 금융 전문 챗봇의 쿼리 분석 전문가입니다. 사용자의 질문을 완전히 분석하여 다음 정보를 제공해주세요.

## 사용자 질문
"{user_query}"

## 분석 요청사항

**1단계: 금융 관련 여부 판단 (매우 중요!)**
이 챗봇은 **금융 전문 챗봇**입니다. 질문이 금융/주식/투자/경제와 직접 관련이 있는지 엄격하게 판단하세요.

✅ 금융 관련 (답변 가능):
- 주식 가격, 시세 (예: "삼성전자 주가", "코스피 지수")
- 투자 분석, 의견, 전망 (예: "네이버 투자해도 될까?", "현대차 전망은?")
- 금융 용어 설명 (예: "PER이 뭐야?", "배당수익률이란?")
- 금융/경제 뉴스 (예: "오늘 증시 뉴스", "반도체 시장 동향")
- 차트, 그래프 시각화 (예: "삼성전자 차트 보여줘", "테슬라 주가 그래프")
- 포트폴리오, 재무제표, 기업 분석

❌ 비금융 (답변 거부):
- 요리, 레시피, 음식 (예: "명란소금빵 레시피")
- IT/개발 문제 (예: "CI가 안되는 이유", "코드 에러")
- 일반 지식, 상식 (예: "서울 날씨", "축구 경기 결과")
- 엔터테인먼트 (예: "영화 추천", "게임 공략")
- 개인적인 조언 (금융 외)

**판단 기준**: 질문이 금융/주식/투자/경제 시장과 **직접적으로** 관련이 있어야 합니다.

**2단계: 응답 형식**
다음 형식으로 정확히 응답해주세요:

is_financial_query: [true/false - 금융 관련 여부]
primary_intent: [주요 의도 - data/analysis/news/knowledge/visualization/general/non_financial 중 하나]
  • data: 주가, 시세 등 데이터 조회
  • analysis: 투자 분석, 투자 의견, 전망
  • news: 뉴스, 시장 동향
  • knowledge: 금융 용어, 개념 설명
  • visualization: 차트, 그래프 요청 (키워드: 차트, 그래프, 시각화, 그려줘, 보여줘)
  • general: 인사, 일반 대화
  • non_financial: 금융 무관 질문
confidence: [0.0-1.0 신뢰도]
reasoning: [분석 근거]
required_services: [필요한 서비스들 - data,analysis,news,knowledge,visualization 중 해당하는 것들]
complexity_level: [복잡도 - simple/moderate/complex]
next_agent: [다음 실행할 에이전트 - data_agent/analysis_agent/news_agent/knowledge_agent/visualization_agent/response_agent]

**중요**: 
- 금융 관련이 아닌 질문(is_financial_query: false)이면 primary_intent를 'non_financial'로 설정하세요.
- "차트", "그래프", "그려줘", "시각화", "보여줘" 키워드가 있으면 primary_intent를 'visualization'으로 설정하세요.
- next_agent는 항상 구체적인 작업 에이전트를 선택해야 합니다. response_agent는 마지막 단계에서만 사용됩니다.

## 예시

질문: "삼성전자 주가 알려줘"
is_financial_query: true
primary_intent: data
confidence: 0.95
reasoning: 주가 조회 요청으로 기본 정보 표시가 필요
required_services: data
complexity_level: simple
next_agent: data_agent

질문: "삼성전자 투자해도 될까?"
is_financial_query: true
primary_intent: analysis
confidence: 0.9
reasoning: 투자 분석 요청으로 재무 분석과 투자 의견이 필요
required_services: data,analysis
complexity_level: moderate
next_agent: data_agent

질문: "PER이 뭐야?"
is_financial_query: true
primary_intent: knowledge
confidence: 0.9
reasoning: 금융 용어 설명 요청
required_services: knowledge
complexity_level: simple
next_agent: knowledge_agent

질문: "삼성전자 차트 보여줘"
is_financial_query: true
primary_intent: visualization
confidence: 0.95
reasoning: 주가 차트 시각화 요청
required_services: data,visualization
complexity_level: simple
next_agent: visualization_agent

질문: "네이버 주가 그래프"
is_financial_query: true
primary_intent: visualization
confidence: 0.9
reasoning: 주가 그래프 요청으로 차트 생성 필요
required_services: data,visualization
complexity_level: simple
next_agent: visualization_agent

질문: "명란소금빵 레시피 알려줘"
is_financial_query: false
primary_intent: non_financial
confidence: 0.95
reasoning: 요리 레시피 요청으로 금융과 무관
required_services: none
complexity_level: simple
next_agent: response_agent

질문: "안녕하세요"
is_financial_query: true
primary_intent: general
confidence: 0.95
reasoning: 일반적인 인사, 금융 챗봇이므로 인사는 허용
required_services: none
complexity_level: simple
next_agent: response_agent

## 응답 형식
is_financial_query: [값]
primary_intent: [값]
confidence: [값]
reasoning: [값]
required_services: [값]
complexity_level: [값]
next_agent: [값]"""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """분석 응답 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'is_financial_query':
                        result['is_financial_query'] = value.lower() in ['true', 'yes', '1']
                    elif key == 'primary_intent':
                        result['primary_intent'] = value
                    elif key == 'confidence':
                        result['confidence'] = float(value)
                    elif key == 'reasoning':
                        result['reasoning'] = value
                    elif key == 'required_services':
                        # 쉼표로 구분된 서비스들을 리스트로 변환
                        services = [s.strip() for s in value.split(',') if s.strip()]
                        result['required_services'] = services
                    elif key == 'complexity_level':
                        result['complexity_level'] = value
                    elif key == 'next_agent':
                        result['next_agent'] = value
            
            # 기본값 설정
            result.setdefault('is_financial_query', True)  # 기본은 금융 관련으로 간주
            result.setdefault('primary_intent', 'general')
            result.setdefault('confidence', 0.5)
            result.setdefault('reasoning', '분석 실패')
            result.setdefault('required_services', [])
            result.setdefault('complexity_level', 'simple')
            result.setdefault('next_agent', 'response_agent')
            
            # next_agent가 비어있으면 primary_intent에 따라 설정
            if not result.get('next_agent') or result['next_agent'].strip() == '':
                intent = result.get('primary_intent', 'general')
                if intent == 'data' or intent == 'visualization':
                    result['next_agent'] = 'data_agent'
                elif intent == 'analysis':
                    result['next_agent'] = 'analysis_agent'
                elif intent == 'news':
                    result['next_agent'] = 'news_agent'
                elif intent == 'knowledge':
                    result['next_agent'] = 'knowledge_agent'
                else:
                    result['next_agent'] = 'response_agent'
            
            return result
            
        except Exception as e:
            print(f"❌ 분석 응답 파싱 오류: {e}")
            return {
                'primary_intent': 'general',
                'confidence': 0.0,
                'reasoning': f'파싱 오류: {str(e)}',
                'required_services': [],
                'complexity_level': 'simple',
                'next_agent': 'response_agent'
            }
    
    async def process(self, user_query: str) -> Dict[str, Any]:
        """쿼리 분석 처리 (LLM 기반 투자 의도 감지)"""
        start_time = time.time()
        print(f"🔍 [QueryAnalyzer] 시작 - {user_query[:50]}...")
        
        # 1. LLM 기반 투자 의도 감지 (별도 에이전트)
        investment_start = time.time()
        investment_intent = await self.investment_detector.detect(user_query)
        investment_time = (time.time() - investment_start) * 1000
        print(f"🔍 [QueryAnalyzer] 투자 의도 감지 완료 - {investment_time:.1f}ms")
        
        is_investment_question = investment_intent['is_investment_question']
        requires_deep_analysis = investment_intent['requires_deep_analysis']
        
        # 2. 일반 쿼리 분석
        analysis_start = time.time()
        prompt = self.get_prompt_template().format(user_query=user_query)
        response = await self.llm.ainvoke(prompt)
        analysis_result = self.parse_response(response.content.strip())
        analysis_time = (time.time() - analysis_start) * 1000
        print(f"🔍 [QueryAnalyzer] 쿼리 분석 완료 - {analysis_time:.1f}ms")
        
        # 3. 투자 의도 정보 통합
        analysis_result['is_investment_question'] = is_investment_question
        analysis_result['investment_detection'] = investment_intent
        
        # 4. 투자 질문이면 복잡도 상향 및 analysis 서비스 추가
        if is_investment_question:
            # 복잡도 상향 (최소 moderate)
            if analysis_result.get('complexity_level') == 'simple':
                analysis_result['complexity_level'] = 'moderate'
            
            # 깊은 분석 필요하면 complex로
            if requires_deep_analysis and analysis_result.get('complexity_level') != 'complex':
                analysis_result['complexity_level'] = 'moderate'  # moderate로 설정 (너무 무거우면 안됨)
            
            # 필요 서비스에 analysis 추가
            required_services = analysis_result.get('required_services', [])
            if 'analysis' not in required_services:
                required_services.append('analysis')
                analysis_result['required_services'] = required_services
            
            self.log(f"💡 투자 질문 감지 (신뢰도: {investment_intent['confidence']:.2f})")
            self.log(f"   {investment_intent['reasoning']}")
        
        total_time = (time.time() - start_time) * 1000
        print(f"🔍 [QueryAnalyzer] 전체 완료 - {total_time:.1f}ms | intent={analysis_result.get('primary_intent')} | complexity={analysis_result.get('complexity_level')}")
        
        return analysis_result

