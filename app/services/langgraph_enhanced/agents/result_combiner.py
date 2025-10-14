"""
결과 통합 에이전트
여러 에이전트의 결과를 LLM이 통합하여 일관성 있고 풍부한 답변 생성
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ResultCombinerAgent(BaseAgent):
    """🔗 결과 통합 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="response")
        self.agent_name = "result_combiner"
    
    def get_prompt_template(self) -> str:
        """결과 통합 프롬프트 템플릿"""
        return """당신은 여러 소스의 정보를 통합하여 사용자에게 최적의 답변을 제공하는 전문가입니다.

## 오늘 날짜 (반드시 이 날짜를 사용, 임의의 날짜 작성 금지)
{current_date}

## 사용자 질문
"{user_query}"

## 수집된 정보

{collected_results}

## 통합 작업

다음 단계로 정보를 통합하세요:

1. **정보 우선순위 결정**
   - 핵심 정보 식별
   - 중복 정보 제거
   - 상충되는 정보 조정

2. **일관성 있는 구조 생성**
   - 논리적 흐름 구성
   - 섹션별 정리
   - 핵심 포인트 강조

3. **추가 인사이트 도출**
   - 정보 간 연관성 분석
   - 시사점 제시
   - 실용적 조언 추가

4. **신뢰도 평가**
   - 각 정보의 신뢰성 평가
   - 불확실한 정보 명시
   - 근거 제시

## 응답 형식

### 통합 답변
[사용자 친화적이고 구조화된 답변]

**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요.
2. 이모지와 간단한 구조로 가독성 높게 작성하세요.
3. 정보 출처, 신뢰도 점수, 추가 제안 등의 메타 정보는 포함하지 마세요.
4. 순수하게 질문에 대한 답변만 제공하세요.
5. **반드시 수집된 모든 데이터를 상세히 활용하세요** - 간단한 요약이 아닌 구체적인 분석을 제공하세요.
6. **투자 분석 질문의 경우**: 현재 상황, 투자 의견, 리스크 요인, 주의사항을 모두 포함하세요.
7. **뉴스 정보가 있으면**: 구체적인 뉴스 내용과 시사점을 포함하세요.
8. **재무 데이터가 있으면**: PER, PBR, ROE 등 모든 지표를 해석하세요.
9. CoT를 적극 활용해서 분석을 제공하세요.
10. **날짜 표기 시 반드시 {current_date}를 사용**하고, 다른 날짜를 추정하거나 생성하지 마세요.
11. **PER, PBR 값이 제공되면 반드시 본문에 숫자로 포함**하세요.

**포맷 예시**:
📊 삼성전자 투자 분석

🏢 현재 상황
   주가: 71,500원 (+2.1%)
   PER: 15.2 (적정 수준)
   
💡 투자 의견: 매수
   반도체 업황 개선이 예상되며, 현재 밸류에이션이 합리적입니다.
   
⚠️ 리스크 요인
   - 글로벌 경기 둔화 우려
   - 중국 시장 불확실성

## 예시

### 예시 1: 데이터 + 분석 통합
질문: "삼성전자 투자해도 될까?"

수집 정보:
- Data: 현재가 71,500원, PER 15.2, PBR 1.3, ROE 8.5%, 거래량 25M주
- Analysis: 반도체 업황 개선 예상, 목표가 80,000원, AI 메모리 수요 증가
- News: 3분기 실적 발표 예정, HBM3 메모리 공급 계약 체결

통합 답변:
📊 삼성전자 투자 분석

🏢 현재 상황
   현재가: 71,500원 (+2.1%)
   PER: 15.2배 (업계 평균 18배 대비 저평가)
   PBR: 1.3배 (적정 수준)
   ROE: 8.5% (전년 대비 1.2%p 상승)
   거래량: 2,500만주 (평균 대비 15% 증가)

💡 투자 의견: 매수 추천
   반도체 업황 개선이 예상되며, 현재 밸류에이션이 합리적인 수준입니다.
   AI 메모리 수요 증가로 HBM3 매출 확대가 기대됩니다.
   목표가는 80,000원으로 약 12%의 상승 여력이 있습니다.

📰 최근 동향
   HBM3 메모리 공급 계약 체결로 AI 반도체 시장 진출 가속화
   3분기 실적 발표에서 메모리 사업부 회복세 예상

⚠️ 리스크 요인
   글로벌 경기 둔화 우려
   중국 시장 불확실성
   메모리 가격 변동성

📌 주의사항: 투자 결정은 본인의 판단과 책임하에 이루어져야 하며, 이 분석은 참고용입니다.

### 예시 2: 데이터 + 뉴스 + 지식 통합
질문: "네이버 현재가와 최근 뉴스, PER 의미 알려줘"

통합 답변:
📊 네이버 종합 정보

💰 현재 주가 정보
   현재가: 210,500원 (-1.4%)
   PER: 22.3배

📚 PER이란?
   PER(주가수익비율)은 주가를 주당순이익(EPS)으로 나눈 값입니다.
   네이버의 PER 22.3배는 투자금을 회수하는데 약 22년이 걸린다는 의미로,
   IT 업종 평균(20배)보다 다소 높은 편입니다.

📰 최근 뉴스
   AI 검색 서비스 '큐:' 출시 (긍정적)
   광고 매출 성장세 지속

💬 종합 의견
   현재 밸류에이션이 다소 높지만, AI 신사업 진출로 성장 모멘텀이 기대됩니다.

📌 주의사항: 투자 결정은 본인의 판단과 책임하에 이루어져야 하며, 이 분석은 참고용입니다.

### 예시 3: 테슬라 투자 분석 (실제 케이스)
질문: "테슬라 지금 들어가도 될까?"

수집 정보:
- Data: 현재가 $413.49, PBR 17.24, PER N/A, 거래량 110M주
- Analysis: 성장/가치/모멘텀 투자 고려, 중간 리스크 수준
- News: 최신 테슬라 관련 뉴스 2건, AI 자율주행 기술 발전

통합 답변:
📊 테슬라 투자 분석

🏢 현재 상황
   현재가: $413.49 (-5.06%)
   PBR: 17.24배 (매우 높은 수준)
   PER: N/A (정보 없음)
   거래량: 1억 1천만주 (평균 대비 높음)

💡 투자 의견: 신중한 검토 필요
   성장/가치/모멘텀 투자를 고려하는 투자자에게 적합할 수 있습니다.
   중간 정도의 리스크를 감수할 수 있다면 투자 가능성이 있습니다.
   하지만 PBR이 매우 높아 밸류에이션 리스크가 큽니다.

📰 최근 동향
   AI 자율주행 기술 발전으로 미래 성장성 기대
   전기차 시장 경쟁 심화로 마진 압박 우려

⚠️ 리스크 요인
   주가 변동성이 매우 높음
   높은 PBR로 인한 밸류에이션 리스크
   경쟁사 대비 기술 우위 지속성 불확실

📌 주의사항: 투자 결정은 본인의 판단과 책임하에 이루어져야 하며, 이 분석은 참고용입니다.

## 지금 통합할 내용

위 형식으로 수집된 정보를 통합하여 응답을 생성하세요. **반드시 모든 수집된 데이터를 상세히 활용하고, 구체적인 분석과 근거를 제시하세요.**"""
    
    def process(
        self, 
        user_query: str, 
        agent_results: Dict[str, Any],
        query_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """결과 통합"""
        try:
            # 수집된 결과 포맷팅
            collected_results = self._format_agent_results(agent_results)
            
            # 프롬프트 생성 (현재 날짜 포함)
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                collected_results=collected_results,
                current_date=current_date
            )
            
            # LLM 호출
            response = self.llm.invoke(prompt)
            combined_response = response.content
            
            # 신뢰도 추출
            confidence = self._extract_confidence(combined_response)
            
            print(f"🔗 결과 통합 완료 (신뢰도: {confidence:.2f})")
            
            return {
                'success': True,
                'combined_response': combined_response,
                'confidence': confidence,
                'sources': list(agent_results.keys()),
                'agent_name': self.agent_name
            }
            
        except Exception as e:
            print(f"❌ 결과 통합 오류: {e}")
            
            # 폴백: 단순 결합
            fallback_response = self._create_fallback_response(
                user_query, 
                agent_results
            )
            
            return {
                'success': False,
                'error': str(e),
                'combined_response': fallback_response,
                'confidence': 0.5,
                'sources': list(agent_results.keys()),
                'agent_name': self.agent_name
            }
    
    def _format_agent_results(self, agent_results: Dict[str, Any]) -> str:
        """에이전트 결과 포맷팅"""
        formatted = []
        
        for agent_name, result in agent_results.items():
            if result.get('success'):
                formatted.append(f"\n### {agent_name} 결과:")
                
                # 각 에이전트별로 관련 데이터 추출
                if 'financial_data' in result:
                    data = result['financial_data']
                    formatted.append(f"- 주가: {data.get('current_price', 'N/A')}")
                    formatted.append(f"- PER: {data.get('pe_ratio', 'N/A')}")
                    formatted.append(f"- PBR: {data.get('pbr', 'N/A')}")
                    formatted.append(f"- ROE: {data.get('roe', 'N/A')}")
                
                if 'analysis_result' in result:
                    formatted.append(f"- 분석: {result['analysis_result'][:200]}...")
                
                if 'news_data' in result:
                    news_count = len(result.get('news_data') or [])
                    formatted.append(f"- 뉴스 {news_count}건 수집")
                    if news_count > 0:
                        # 모든 뉴스 표시 (최대 10개)
                        for i, news in enumerate(result['news_data'][:10], 1):
                            formatted.append(f"  [{i}] {news.get('title', 'N/A')}")
                            formatted.append(f"      출처: {news.get('source', 'N/A')}, 날짜: {news.get('published', 'N/A')[:10]}")

                
                if 'explanation_result' in result:
                    formatted.append(f"- 설명: {result['explanation_result'][:200]}...")
                
                if 'chart_data' in result:
                    formatted.append(f"- 차트: {result['chart_data'].get('chart_type', 'N/A')}")
            else:
                formatted.append(f"\n### {agent_name} 결과:")
                formatted.append(f"- 오류: {result.get('error', 'Unknown error')}")
        
        return '\n'.join(formatted) if formatted else "수집된 정보 없음"
    
    def _extract_confidence(self, response_text: str) -> float:
        """응답에서 신뢰도 추출"""
        try:
            import re
            match = re.search(r'overall_confidence:\s*([\d.]+)', response_text)
            if match:
                return float(match.group(1))
            return 0.8  # 기본값
        except:
            return 0.8
    
    def _create_fallback_response(
        self, 
        user_query: str, 
        agent_results: Dict[str, Any]
    ) -> str:
        """폴백 응답 생성"""
        response_parts = [f"질문: {user_query}\n"]
        
        for agent_name, result in agent_results.items():
            if result.get('success'):
                response_parts.append(f"\n**{agent_name}**:")
                
                if 'financial_data' in result:
                    data = result['financial_data']
                    response_parts.append(
                        f"주가: {data.get('current_price', 'N/A')}, "
                        f"PER: {data.get('per', 'N/A')}"
                    )
                
                if 'analysis_result' in result:
                    response_parts.append(result['analysis_result'][:300])
                
                if 'news_data' in result and result['news_data']:
                    response_parts.append(
                        f"최신 뉴스: {result['news_data'][0].get('title', '')}"
                    )
                
                if 'explanation_result' in result:
                    response_parts.append(result['explanation_result'][:300])
        
        return '\n'.join(response_parts)

