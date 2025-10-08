"""
쿼리 분석 에이전트
사용자 질문을 분석하여 적절한 에이전트로 라우팅
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class QueryAnalyzerAgent(BaseAgent):
    """🔍 쿼리 분석 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="classification")
        self.agent_name = "query_analyzer"
    
    def get_prompt_template(self) -> str:
        """쿼리 분석 프롬프트 템플릿"""
        return """당신은 금융 챗봇의 쿼리 분석 전문가입니다. 사용자의 질문을 완전히 분석하여 다음 정보를 제공해주세요.

## 사용자 질문
"{user_query}"

## 분석 요청사항
다음 형식으로 정확히 응답해주세요:

primary_intent: [주요 의도 - data/analysis/news/knowledge/visualization/general 중 하나]
confidence: [0.0-1.0 신뢰도]
reasoning: [분석 근거]
required_services: [필요한 서비스들 - data,analysis,news,knowledge,visualization 중 해당하는 것들]
complexity_level: [복잡도 - simple/moderate/complex]
next_agent: [다음 실행할 에이전트 - data_agent/analysis_agent/news_agent/knowledge_agent/visualization_agent/response_agent]

**중요**: next_agent는 항상 구체적인 작업 에이전트를 선택해야 합니다. response_agent는 마지막 단계에서만 사용됩니다.

## 예시
질문: "삼성전자 주가 알려줘"
primary_intent: data
confidence: 0.95
reasoning: 주가 조회 요청으로 기본 정보 표시가 필요
required_services: data
complexity_level: simple
next_agent: data_agent

질문: "삼성전자 투자해도 될까?"
primary_intent: analysis
confidence: 0.9
reasoning: 투자 분석 요청으로 재무 분석과 투자 의견이 필요
required_services: data,analysis
complexity_level: moderate
next_agent: data_agent

질문: "오늘 시장 뉴스 알려줘"
primary_intent: news
confidence: 0.95
reasoning: 뉴스 조회 요청
required_services: news
complexity_level: simple
next_agent: news_agent

질문: "PER이 뭐야?"
primary_intent: knowledge
confidence: 0.9
reasoning: 금융 용어 설명 요청
required_services: knowledge
complexity_level: simple
next_agent: knowledge_agent

질문: "안녕하세요"
primary_intent: general
confidence: 0.95
reasoning: 일반적인 인사
required_services: none
complexity_level: simple
next_agent: response_agent

질문: "네이버 현재가"
primary_intent: data
confidence: 0.9
reasoning: 특정 종목의 현재가 조회 요청
required_services: data
complexity_level: simple
next_agent: data_agent

## 응답 형식
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
                    
                    if key == 'primary_intent':
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
    
    def process(self, user_query: str) -> Dict[str, Any]:
        """쿼리 분석 처리"""
        prompt = self.get_prompt_template().format(user_query=user_query)
        response = self.llm.invoke(prompt)
        return self.parse_response(response.content.strip())

