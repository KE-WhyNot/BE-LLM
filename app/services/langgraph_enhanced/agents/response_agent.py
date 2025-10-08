"""
응답 에이전트
최종 응답 생성 및 통합 전문 에이전트
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class ResponseAgent(BaseAgent):
    """💬 응답 에이전트 - 최종 응답 생성 전문가"""
    
    def __init__(self):
        super().__init__(purpose="response")
        self.agent_name = "response_agent"
    
    def get_prompt_template(self) -> str:
        """최종 응답 생성 프롬프트 템플릿"""
        return """당신은 전문 금융 챗봇입니다. 수집된 모든 정보를 종합하여 사용자에게 최적의 응답을 제공해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 신뢰도: {confidence}
- 필요 서비스: {required_services}

## 수집된 정보
{collected_information}

## 응답 생성 지침

### 1. 📋 응답 구조
- **인사**: 친근한 인사로 시작
- **핵심 답변**: 사용자 질문에 대한 직접적인 답변
- **상세 정보**: 수집된 데이터를 활용한 구체적 정보
- **추가 조언**: 도움이 되는 추가 정보나 조언
- **마무리**: 친근한 마무리와 추가 질문 유도

### 2. 💡 응답 원칙
- **정확성**: 정확한 데이터와 정보 제공
- **친근성**: 이해하기 쉽고 친근한 톤 사용
- **구체성**: 구체적인 숫자와 예시 포함
- **실용성**: 실제 투자에 도움이 되는 정보 제공
- **균형성**: 객관적이고 균형 잡힌 관점 유지

### 3. 📊 데이터 활용
- 수집된 금융 데이터가 있으면 구체적인 숫자로 설명
- 차트 정보가 있으면 시각적 요소 언급
- 뉴스 정보가 있으면 최신 동향 반영
- 분석 결과가 있으면 투자 관점 포함

### 4. 🎯 사용자 맞춤화
- 질문의 복잡도에 맞는 설명 수준 조절
- 투자 경험 수준에 맞는 용어 사용
- 구체적인 조언보다는 참고 정보 제공

### 5. ⚠️ 주의사항
- 투자 권유가 아닌 정보 제공임을 명시
- 개인의 투자 상황은 고려되지 않았음을 알림
- 투자 리스크에 대한 경고 포함

## 응답 형식
친근하고 전문적인 톤으로 작성하되, 이모지를 적절히 사용하여 가독성을 높이세요.
각 섹션은 명확하게 구분하여 작성하세요.

## 예시 톤
"안녕하세요! [질문]에 대해 답변드릴게요.
[핵심 답변]
[상세 정보]
[추가 조언]
더 궁금한 점이 있으시면 언제든 말씀해 주세요! 😊"

이제 위의 지침에 따라 최적의 응답을 생성해주세요."""
    
    def process(self, user_query: str, query_analysis: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """응답 에이전트 처리"""
        try:
            self.log(f"최종 응답 생성 시작")
            
            # 수집된 정보 포맷팅
            collected_info = self._format_collected_information(collected_data)
            
            # 최종 응답 생성
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'general'),
                complexity_level=query_analysis.get('complexity_level', 'simple'),
                confidence=query_analysis.get('confidence', 0.5),
                required_services=query_analysis.get('required_services', []),
                collected_information=collected_info
            )
            
            response = self.llm.invoke(prompt)
            final_response = response.content
            
            self.log("최종 응답 생성 완료")
            
            return {
                'success': True,
                'final_response': final_response,
                'collected_data_summary': self._create_data_summary(collected_data)
            }
            
        except Exception as e:
            self.log(f"응답 에이전트 오류: {e}")
            return {
                'success': False,
                'error': f"응답 생성 중 오류: {str(e)}",
                'final_response': "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            }
    
    def _format_collected_information(self, collected_data: Dict[str, Any]) -> str:
        """수집된 정보 포맷팅"""
        info_sections = []
        
        # 금융 데이터
        if collected_data.get('financial_data'):
            financial_data = collected_data['financial_data']
            if 'error' not in financial_data:
                info_sections.append(f"""
📊 **금융 데이터**
• 종목: {financial_data.get('company_name', 'N/A')}
• 현재가: {financial_data.get('current_price', 'N/A'):,}원
• 변동률: {financial_data.get('price_change_percent', 'N/A')}%
• 거래량: {financial_data.get('volume', 'N/A'):,}주
• PER: {financial_data.get('pe_ratio', 'N/A')}
• PBR: {financial_data.get('pbr', 'N/A')}
• ROE: {financial_data.get('roe', 'N/A')}%""")
        
        # 분석 결과
        if collected_data.get('analysis_result'):
            info_sections.append(f"""
📈 **투자 분석**
{collected_data['analysis_result'][:500]}{'...' if len(collected_data['analysis_result']) > 500 else ''}""")
        
        # 뉴스 정보
        if collected_data.get('news_data'):
            news_count = len(collected_data['news_data'])
            info_sections.append(f"""
📰 **뉴스 정보**
• 수집된 뉴스: {news_count}건
• 주요 뉴스: {collected_data['news_data'][0].get('title', 'N/A') if news_count > 0 else 'N/A'}""")
        
        # 뉴스 분석
        if collected_data.get('news_analysis'):
            info_sections.append(f"""
📰 **뉴스 분석**
{collected_data['news_analysis'][:300]}{'...' if len(collected_data['news_analysis']) > 300 else ''}""")
        
        # 지식 정보
        if collected_data.get('knowledge_explanation'):
            info_sections.append(f"""
📚 **지식 정보**
{collected_data['knowledge_explanation'][:300]}{'...' if len(collected_data['knowledge_explanation']) > 300 else ''}""")
        
        # 차트 정보
        if collected_data.get('chart_data'):
            chart_data = collected_data['chart_data']
            if 'error' not in chart_data:
                info_sections.append(f"""
📊 **차트 정보**
• 차트 유형: {chart_data.get('chart_type', 'N/A')}
• 데이터 기간: {chart_data.get('period', 'N/A')}
• 기술적 지표: {', '.join(chart_data.get('indicators', []))}""")
        
        # 차트 분석
        if collected_data.get('chart_analysis'):
            info_sections.append(f"""
📊 **차트 분석**
{collected_data['chart_analysis'][:300]}{'...' if len(collected_data['chart_analysis']) > 300 else ''}""")
        
        if not info_sections:
            return "수집된 정보가 없습니다."
        
        return "\n\n".join(info_sections)
    
    def _create_data_summary(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """수집된 데이터 요약 생성"""
        summary = {
            'has_financial_data': bool(collected_data.get('financial_data')),
            'has_analysis': bool(collected_data.get('analysis_result')),
            'has_news': bool(collected_data.get('news_data')),
            'has_knowledge': bool(collected_data.get('knowledge_explanation')),
            'has_chart': bool(collected_data.get('chart_data')),
            'data_sources': [],
            'total_data_points': 0
        }
        
        # 데이터 소스 추적
        if summary['has_financial_data']:
            summary['data_sources'].append('financial_data')
        if summary['has_analysis']:
            summary['data_sources'].append('analysis')
        if summary['has_news']:
            summary['data_sources'].append('news')
        if summary['has_knowledge']:
            summary['data_sources'].append('knowledge')
        if summary['has_chart']:
            summary['data_sources'].append('chart')
        
        # 총 데이터 포인트 계산
        for key, value in collected_data.items():
            if isinstance(value, list):
                summary['total_data_points'] += len(value)
            elif isinstance(value, dict) and value:
                summary['total_data_points'] += 1
            elif isinstance(value, str) and value:
                summary['total_data_points'] += 1
        
        return summary
