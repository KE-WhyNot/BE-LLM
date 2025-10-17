"""
투자 의도 감지 에이전트
LLM 기반으로 사용자 질문이 투자 판단/분석을 요구하는지 감지
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class InvestmentIntentDetector(BaseAgent):
    """💡 투자 의도 감지 에이전트 - LLM 기반"""
    
    def __init__(self):
        super().__init__(purpose="classification")
        self.agent_name = "investment_intent_detector"
    
    def get_prompt_template(self) -> str:
        """투자 의도 감지 프롬프트"""
        return """당신은 사용자 질문의 의도를 파악하는 전문가입니다.

## 사용자 질문
"{user_query}"

## 판단 기준

사용자가 다음과 같은 정보를 요구하면 **투자 의도 있음**으로 판단하세요:

### ✅ 투자 의도가 있는 경우:
1. **투자 판단 요청**
   - "투자해도 될까?", "사도 될까?", "매수해도 괜찮아?"
   - "지금 들어가도 돼?", "살 만해?", "팔아야 할까?"
   
2. **투자 분석 요청**
   - "분석해줘", "전망 알려줘", "투자 의견 줘"
   - "어떻게 보여?", "어떻게 생각해?", "괜찮아?"
   
3. **추천 요청**
   - "추천해줘", "좋을까?", "나쁠까?"
   - "괜찮은 종목", "좋은 주식"

4. **평가 요청**
   - "어때?", "어떨까?", "어떤가?"
   - "좋아?", "나빠?", "괜찮아?"

### ❌ 투자 의도가 없는 경우:
1. **단순 정보 조회**
   - "주가 알려줘", "현재가 얼마야?"
   - "시세 알려줘", "가격 보여줘"
   
2. **뉴스 조회**
   - "뉴스 알려줘", "최근 소식"
   
3. **지식 질문**
   - "PER이 뭐야?", "ROE가 뭐야?"
   
4. **차트 요청**
   - "차트 보여줘", "그래프 그려줘"

5. **일반 대화**
   - "안녕", "고마워", "도와줘"

## 중요 원칙

⚠️ **애매한 경우는 투자 의도 있음으로 판단하세요!**
- 사용자가 실질적인 도움을 원하는 것 같으면 → 투자 의도 있음
- 단순 사실 확인이 아니라 판단을 요구하면 → 투자 의도 있음

## 응답 형식

정확히 다음 형식으로만 응답하세요:

is_investment_question: [yes/no]
confidence: [0.0-1.0]
reasoning: [판단 근거를 한 문장으로]
requires_deep_analysis: [true/false - 깊은 분석이 필요한가?]

## 예시

질문: "삼성전자 주가 알려줘"
is_investment_question: no
confidence: 0.95
reasoning: 단순 주가 정보 조회 요청으로 투자 판단 불필요
requires_deep_analysis: false

질문: "삼성전자 지금 투자해도 될까?"
is_investment_question: yes
confidence: 0.98
reasoning: 명확한 투자 판단 요청으로 분석 필수
requires_deep_analysis: true

질문: "네이버 어때?"
is_investment_question: yes
confidence: 0.85
reasoning: 애매하지만 평가를 요구하므로 투자 의도로 판단
requires_deep_analysis: true

질문: "카카오 분석해줘"
is_investment_question: yes
confidence: 0.95
reasoning: 명확한 분석 요청
requires_deep_analysis: true

질문: "PER이 뭐야?"
is_investment_question: no
confidence: 0.98
reasoning: 금융 용어 설명 요청으로 지식 제공만 필요
requires_deep_analysis: false

질문: "테슬라 뉴스 알려줘"
is_investment_question: no
confidence: 0.90
reasoning: 뉴스 조회 요청으로 투자 판단 불필요
requires_deep_analysis: false

질문: "현대차 좋아?"
is_investment_question: yes
confidence: 0.92
reasoning: 평가 요청으로 투자 의도 포함
requires_deep_analysis: true

## 응답
is_investment_question: [값]
confidence: [값]
reasoning: [값]
requires_deep_analysis: [값]"""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """응답 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'is_investment_question':
                        result['is_investment_question'] = value.lower() == 'yes'
                    elif key == 'confidence':
                        try:
                            result['confidence'] = float(value)
                        except:
                            result['confidence'] = 0.5
                    elif key == 'reasoning':
                        result['reasoning'] = value
                    elif key == 'requires_deep_analysis':
                        result['requires_deep_analysis'] = value.lower() == 'true'
            
            # 기본값 설정
            result.setdefault('is_investment_question', False)
            result.setdefault('confidence', 0.5)
            result.setdefault('reasoning', '판단 불가')
            result.setdefault('requires_deep_analysis', False)
            
            return result
            
        except Exception as e:
            print(f"❌ 투자 의도 감지 파싱 오류: {e}")
            return {
                'is_investment_question': False,
                'confidence': 0.0,
                'reasoning': f'파싱 오류: {str(e)}',
                'requires_deep_analysis': False
            }
    
    def process(self, user_query: str, query_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """BaseAgent 인터페이스 구현 (detect 호출)"""
        return self.detect(user_query)
    
    def detect(self, user_query: str) -> Dict[str, Any]:
        """투자 의도 감지"""
        try:
            prompt = self.get_prompt_template().format(user_query=user_query)
            response = self.llm.invoke(prompt)
            result = self.parse_response(response.content.strip())
            
            self.log(f"투자 의도 감지: {result['is_investment_question']} (신뢰도: {result['confidence']:.2f})")
            self.log(f"  근거: {result['reasoning']}")
            
            return result
            
        except Exception as e:
            self.log(f"투자 의도 감지 오류: {e}")
            return {
                'is_investment_question': False,
                'confidence': 0.0,
                'reasoning': f'오류 발생: {str(e)}',
                'requires_deep_analysis': False
            }

