"""
신뢰도 계산 에이전트
답변의 신뢰도를 평가하고 품질을 보장
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class ConfidenceCalculatorAgent(BaseAgent):
    """📊 신뢰도 계산 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="analysis")
        self.agent_name = "confidence_calculator"
    
    def get_prompt_template(self) -> str:
        """신뢰도 계산 프롬프트 템플릿"""
        return """당신은 AI 응답의 신뢰도를 평가하는 전문가입니다.

## 사용자 질문
"{user_query}"

## 생성된 응답
{generated_response}

## 사용된 정보 소스
{information_sources}

## 신뢰도 평가 기준

다음 요소들을 고려하여 신뢰도를 평가하세요:

### 1. 정보의 완전성 (0-25점)
- 질문에 대한 답변이 완전한가?
- 필요한 정보가 모두 포함되었는가?
- 부족한 정보는 없는가?

### 2. 정보의 일관성 (0-25점)
- 여러 소스의 정보가 일치하는가?
- 모순되는 내용은 없는가?
- 논리적으로 연결되는가?

### 3. 정보의 정확성 (0-25점)
- 최신 데이터를 사용했는가?
- 신뢰할 수 있는 소스인가?
- 검증 가능한 정보인가?

### 4. 정보의 유용성 (0-25점)
- 사용자에게 실질적 도움이 되는가?
- 실행 가능한 조언을 포함하는가?
- 추가 가치를 제공하는가?

## 응답 형식

overall_confidence: [0.0-1.0 전체 신뢰도]
completeness_score: [0-25 완전성 점수]
consistency_score: [0-25 일관성 점수]
accuracy_score: [0-25 정확성 점수]
usefulness_score: [0-25 유용성 점수]
total_score: [0-100 총점]
grade: [A/B/C/D/F 등급]
reasoning: [평가 근거]
improvement_suggestions: [개선 제안]
warnings: [주의사항]

## 예시

### 예시 1: 높은 신뢰도
질문: "삼성전자 주가 알려줘"
응답: "삼성전자(005930) 현재가는 71,500원(+2.1%)입니다..."

overall_confidence: 0.95
completeness_score: 25
consistency_score: 25
accuracy_score: 24
usefulness_score: 23
total_score: 97
grade: A
reasoning: 실시간 데이터를 사용하여 정확하고 완전한 답변 제공
improvement_suggestions: 거래량 정보 추가 가능
warnings: 실시간 데이터는 지연될 수 있음

### 예시 2: 중간 신뢰도
질문: "내일 주가 예측해줘"
응답: "과거 데이터를 바탕으로 상승 가능성이 있으나..."

overall_confidence: 0.60
completeness_score: 18
consistency_score: 20
accuracy_score: 15
usefulness_score: 17
total_score: 70
grade: C
reasoning: 예측은 본질적으로 불확실하며, 근거가 다소 부족
improvement_suggestions: 더 구체적인 분석 근거 제시 필요
warnings: 주가 예측은 보장되지 않음을 명시 필요

### 예시 3: 낮은 신뢰도
질문: "해외 주식 추천해줘"
응답: "몇 가지 해외 주식이 있습니다만..."

overall_confidence: 0.40
completeness_score: 10
consistency_score: 12
accuracy_score: 8
usefulness_score: 15
total_score: 45
grade: F
reasoning: 구체적 근거 부족, 범위 벗어남
improvement_suggestions: 시스템 범위 명확히 안내, 국내 주식으로 유도
warnings: 해외 주식 정보는 현재 시스템 범위 밖

## 지금 평가할 내용

위 형식으로 제공된 응답의 신뢰도를 평가하세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """신뢰도 평가 응답 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {
                'overall_confidence': 0.8,
                'completeness_score': 20,
                'consistency_score': 20,
                'accuracy_score': 20,
                'usefulness_score': 20,
                'total_score': 80,
                'grade': 'B',
                'reasoning': '',
                'improvement_suggestions': '',
                'warnings': ''
            }
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'overall_confidence':
                        try:
                            result['overall_confidence'] = float(value)
                        except:
                            pass
                    elif key == 'completeness_score':
                        try:
                            result['completeness_score'] = int(value)
                        except:
                            pass
                    elif key == 'consistency_score':
                        try:
                            result['consistency_score'] = int(value)
                        except:
                            pass
                    elif key == 'accuracy_score':
                        try:
                            result['accuracy_score'] = int(value)
                        except:
                            pass
                    elif key == 'usefulness_score':
                        try:
                            result['usefulness_score'] = int(value)
                        except:
                            pass
                    elif key == 'total_score':
                        try:
                            result['total_score'] = int(value)
                        except:
                            pass
                    elif key == 'grade':
                        result['grade'] = value
                    elif key == 'reasoning':
                        result['reasoning'] = value
                    elif key == 'improvement_suggestions':
                        result['improvement_suggestions'] = value
                    elif key == 'warnings':
                        result['warnings'] = value
            
            return result
            
        except Exception as e:
            print(f"❌ 신뢰도 파싱 오류: {e}")
            return {
                'overall_confidence': 0.7,
                'total_score': 70,
                'grade': 'C',
                'reasoning': '파싱 오류로 기본값 사용',
                'improvement_suggestions': '',
                'warnings': ''
            }
    
    def process(
        self, 
        user_query: str, 
        generated_response: str,
        information_sources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """신뢰도 계산"""
        try:
            # 정보 소스 포맷팅
            sources_text = self._format_sources(information_sources)
            
            # 프롬프트 생성
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                generated_response=generated_response,
                information_sources=sources_text
            )
            
            # LLM 호출
            response = self.llm.invoke(prompt)
            
            # 응답 파싱
            evaluation = self.parse_response(response.content)
            
            print(f"📊 신뢰도 평가 완료:")
            print(f"   전체 신뢰도: {evaluation['overall_confidence']:.2f}")
            print(f"   총점: {evaluation['total_score']}/100 ({evaluation['grade']})")
            print(f"   근거: {evaluation['reasoning']}")
            
            if evaluation['warnings']:
                print(f"   ⚠️ 주의: {evaluation['warnings']}")
            
            return {
                'success': True,
                'evaluation': evaluation,
                'agent_name': self.agent_name
            }
            
        except Exception as e:
            print(f"❌ 신뢰도 계산 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_name': self.agent_name,
                'evaluation': {
                    'overall_confidence': 0.7,
                    'total_score': 70,
                    'grade': 'C',
                    'reasoning': f'오류 발생: {str(e)}'
                }
            }
    
    def _format_sources(self, information_sources: Dict[str, Any]) -> str:
        """정보 소스 포맷팅"""
        formatted = []
        
        if 'data' in information_sources:
            formatted.append("- Data: 실시간 주가 데이터")
        if 'analysis' in information_sources:
            formatted.append("- Analysis: Neo4j KG + Pinecone RAG 기반 분석")
        if 'news' in information_sources:
            formatted.append("- News: Google RSS 실시간 뉴스")
        if 'knowledge' in information_sources:
            formatted.append("- Knowledge: Pinecone RAG 지식 베이스")
        if 'neo4j' in information_sources:
            formatted.append("- Neo4j: 매일경제 뉴스 관계 그래프")
        if 'pinecone' in information_sources:
            formatted.append("- Pinecone: 4,961개 금융 문서 벡터")
        
        return '\n'.join(formatted) if formatted else "정보 소스 없음"


# 싱글톤 인스턴스
confidence_calculator = ConfidenceCalculatorAgent()

