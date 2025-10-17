"""
시각화 에이전트
차트 생성, 데이터 시각화 전문 에이전트
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from app.services.workflow_components import financial_data_service, visualization_service
from app.utils.stock_utils import extract_symbol_from_query


class VisualizationAgent(BaseAgent):
    """📊 시각화 에이전트 - 차트 및 데이터 시각화 전문가"""
    
    def __init__(self):
        super().__init__(purpose="visualization")
        self.agent_name = "visualization_agent"
    
    def get_prompt_template(self) -> str:
        """시각화 전략 결정 프롬프트 템플릿"""
        return """당신은 데이터 시각화 전문가입니다. 사용자 요청에 따라 최적의 시각화 전략을 결정해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}

## 시각화 전략 결정
다음 형식으로 응답해주세요:

chart_type: [차트 유형 - candlestick/line/bar/volume/technical/comparison 중 하나]
data_period: [데이터 기간 - 1d/1w/1m/3m/6m/1y/2y/5y]
indicators: [기술적 지표 - ma/rsi/macd/bollinger/stochastic/none]
comparison_symbols: [비교 종목 - 없으면 none]
focus_metrics: [집중 지표 - price/volume/technical/fundamental/all]
chart_style: [차트 스타일 - simple/detailed/professional]
include_analysis: [분석 포함 - yes/no]

## 전략 예시

요청: "삼성전자 주가 차트 보여줘"
chart_type: candlestick
data_period: 3m
indicators: ma,rsi
comparison_symbols: none
focus_metrics: price,volume
chart_style: detailed
include_analysis: yes

요청: "네이버 현재가"
chart_type: line
data_period: 1m
indicators: none
comparison_symbols: none
focus_metrics: price
chart_style: simple
include_analysis: no

요청: "삼성전자 vs SK하이닉스 비교"
chart_type: comparison
data_period: 1y
indicators: ma
comparison_symbols: SK하이닉스
focus_metrics: price
chart_style: professional
include_analysis: yes

요청: "카카오 기술적 분석 차트"
chart_type: technical
data_period: 6m
indicators: ma,rsi,macd,bollinger
comparison_symbols: none
focus_metrics: technical
chart_style: professional
include_analysis: yes

## 응답 형식
chart_type: [값]
data_period: [값]
indicators: [값]
comparison_symbols: [값]
focus_metrics: [값]
chart_style: [값]
include_analysis: [값]"""
    
    def parse_visualization_strategy(self, response_text: str) -> Dict[str, Any]:
        """시각화 전략 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'chart_type':
                        result['chart_type'] = value
                    elif key == 'data_period':
                        result['data_period'] = value
                    elif key == 'indicators':
                        if value.lower() == 'none':
                            result['indicators'] = []
                        else:
                            result['indicators'] = [i.strip() for i in value.split(',') if i.strip()]
                    elif key == 'comparison_symbols':
                        if value.lower() == 'none':
                            result['comparison_symbols'] = []
                        else:
                            result['comparison_symbols'] = [s.strip() for s in value.split(',') if s.strip()]
                    elif key == 'focus_metrics':
                        result['focus_metrics'] = [m.strip() for m in value.split(',') if m.strip()]
                    elif key == 'chart_style':
                        result['chart_style'] = value
                    elif key == 'include_analysis':
                        result['include_analysis'] = value.lower() == 'yes'
            
            # 기본값 설정
            result.setdefault('chart_type', 'candlestick')
            result.setdefault('data_period', '3m')
            result.setdefault('indicators', ['ma'])
            result.setdefault('comparison_symbols', [])
            result.setdefault('focus_metrics', ['price', 'volume'])
            result.setdefault('chart_style', 'detailed')
            result.setdefault('include_analysis', True)
            
            return result
            
        except Exception as e:
            print(f"❌ 시각화 전략 파싱 오류: {e}")
            return {
                'chart_type': 'candlestick',
                'data_period': '3m',
                'indicators': ['ma'],
                'comparison_symbols': [],
                'focus_metrics': ['price', 'volume'],
                'chart_style': 'detailed',
                'include_analysis': True
            }
    
    def generate_chart_analysis_prompt(self, chart_data: Dict[str, Any], strategy: Dict[str, Any], user_query: str) -> str:
        """차트 분석 프롬프트 생성"""
        return f"""당신은 전문 차트 분석가입니다. 생성된 차트를 분석하여 투자 인사이트를 제공해주세요.

## 사용자 요청
"{user_query}"

## 차트 설정
- 차트 유형: {strategy.get('chart_type', 'candlestick')}
- 데이터 기간: {strategy.get('data_period', '3m')}
- 기술적 지표: {', '.join(strategy.get('indicators', ['ma']))}
- 집중 지표: {', '.join(strategy.get('focus_metrics', ['price']))}
- 차트 스타일: {strategy.get('chart_style', 'detailed')}

## 차트 데이터
{self._format_chart_data(chart_data)}

## 분석 요청사항

### 1. 📊 차트 개요
- **현재 상황**: 현재 주가와 추세 상황 요약
- **차트 패턴**: 주요 차트 패턴이나 패턴 인식
- **거래량**: 거래량과 주가의 상관관계

### 2. 📈 기술적 분석
- **추세 분석**: 상승/하락/횡보 추세 판단
- **지지선/저항선**: 주요 지지선과 저항선 레벨
- **이동평균**: 단기/중기/장기 이동평균 분석
- **기술적 지표**: RSI, MACD 등 지표 해석

### 3. 💡 투자 관점
- **매수 신호**: 매수를 고려할 수 있는 신호들
- **매도 신호**: 매도를 고려할 수 있는 신호들
- **주의 포인트**: 주의해야 할 위험 요소들

### 4. 🎯 투자 전략
- **진입 타이밍**: 매수 적기 분석
- **목표가**: 상승 목표가 및 하락 위험가
- **손절가**: 손절 기준점 제시
- **투자 기간**: 권장 투자 기간

### 5. 📋 추가 모니터링
- **관찰 지표**: 지속적으로 모니터링할 지표들
- **이벤트 리스크**: 주가에 영향을 줄 수 있는 이벤트들
- **시장 환경**: 전체 시장 환경 고려사항

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요.
2. 이모지와 들여쓰기로 구조화하세요.
3. 구체적인 가격 수준과 퍼센트를 포함하여 분석하세요.

## 중요 주의사항
⚠️ 기술적 분석 한계: 차트 분석은 참고용이며, 100% 정확하지 않습니다.
⚠️ 리스크 고지: 모든 투자에는 원금 손실 위험이 있습니다.
⚠️ 종합 판단: 기술적 분석과 함께 기본적 분석도 고려하세요."""
    
    def _format_chart_data(self, chart_data: Dict[str, Any]) -> str:
        """차트 데이터 포맷팅"""
        if not chart_data:
            return "차트 데이터가 없습니다."
        
        formatted = []
        for key, value in chart_data.items():
            if isinstance(value, dict):
                formatted.append(f"**{key}:**")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  • {sub_key}: {sub_value}")
            else:
                formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """시각화 에이전트 처리"""
        try:
            self.log(f"차트 생성 시작: {user_query}")
            
            # LLM이 시각화 전략 결정
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'visualization'),
                complexity_level=query_analysis.get('complexity_level', 'simple'),
                required_services=query_analysis.get('required_services', [])
            )
            
            response = self.llm.invoke(prompt)
            strategy = self.parse_visualization_strategy(response.content.strip())
            
            # 주식 심볼 추출 (stock_utils 사용 - 한국/미국 주식 모두 지원)
            stock_symbol = extract_symbol_from_query(user_query)
            
            self.log(f"추출된 심볼: {stock_symbol}")
            
            # 차트 생성
            chart_data = {}
            chart_image = None
            
            if stock_symbol:
                try:
                    # 금융 데이터 가져오기
                    financial_data = financial_data_service.get_financial_data(stock_symbol)
                    
                    if 'error' not in financial_data:
                        # 차트 생성 요청 (visualization_service 직접 사용)
                        chart_base64 = visualization_service.create_chart(
                            chart_type='candlestick_volume',
                            data=financial_data,
                            period=strategy['data_period']
                        )
                        
                        if chart_base64:
                            chart_data = {
                                'chart_type': 'candlestick_volume',
                                'period': strategy['data_period'],
                                'symbol': stock_symbol,
                                'indicators': strategy['indicators']
                            }
                            chart_image = chart_base64
                            self.log(f"차트 생성 완료: {stock_symbol}")
                        else:
                            chart_data = {'error': '차트 생성 실패'}
                            self.log("차트 생성 실패: base64 없음")
                    else:
                        chart_data = {'error': financial_data.get('error', '데이터 조회 실패')}
                        self.log(f"데이터 조회 실패: {financial_data.get('error')}")
                        
                except Exception as e:
                    self.log(f"차트 생성 오류: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_data = {'error': str(e)}
            else:
                chart_data = {'error': '종목을 찾을 수 없습니다.'}
            
            # 차트 분석
            if chart_data and 'error' not in chart_data and strategy.get('include_analysis', True):
                analysis_prompt = self.generate_chart_analysis_prompt(chart_data, strategy, user_query)
                analysis_response = self.llm.invoke(analysis_prompt)
                analysis_result = analysis_response.content
                
                self.log("차트 분석 완료")
            else:
                analysis_result = "차트 분석을 수행할 수 없습니다."
            
            return {
                'success': True,
                'chart_data': chart_data,
                'chart_image': chart_image,
                'analysis_result': analysis_result,
                'strategy': strategy,
                'stock_symbol': stock_symbol
            }
            
        except Exception as e:
            self.log(f"시각화 에이전트 오류: {e}")
            return {
                'success': False,
                'error': f"차트 생성 중 오류: {str(e)}",
                'chart_data': {'error': str(e)},
                'analysis_result': "차트 생성에 실패했습니다."
            }

