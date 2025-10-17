"""
데이터 에이전트
금융 데이터 조회 및 간단한 주가 응답 생성
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from app.services.workflow_components import financial_data_service


class DataAgent(BaseAgent):
    """📊 데이터 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="analysis")
        self.agent_name = "data_agent"
    
    def get_prompt_template(self) -> str:
        """데이터 전략 결정 프롬프트 템플릿"""
        return """당신은 금융 데이터 조회 전문가입니다. 사용자 요청에 따라 최적의 데이터 조회 전략을 결정해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}

## 중요: 주식 심볼 변환

**Yahoo Finance에서 사용하는 정확한 심볼**을 data_query에 입력하세요.

### 변환 규칙:
1. 한국 주식: 6자리 코드 + `.KS`
   - 예: 삼성전자 → 005930.KS, 네이버 → 035420.KS

2. 미국 주식: 표준 티커 심볼 (1~5자 알파벳)
   - 예: 테슬라 → TSLA, 애플 → AAPL, 디즈니 → DIS, 스타벅스 → SBUX, 나이키 → NKE
   - **당신의 금융 지식을 활용하여 모든 회사명을 정확한 티커 심볼로 변환하세요**

3. 유럽 주식: 티커 + 거래소 접미사
   - 프랑스 (파리): `.PA` (예: LVMH → MC.PA, 에르메스 → RMS.PA)
   - 영국 (런던): `.L` (예: BP → BP.L)
   - 독일 (프랑크푸르트): `.DE` (예: BMW → BMW.DE)

4. 이미 심볼 형태인 경우: 그대로 사용
   - 예: "TSLA 주가" → TSLA, "DIS 차트" → DIS

중요: 
- 회사명(한글/영어)을 받으면 반드시 Yahoo Finance 티커 심볼로 변환하세요
- 개별 상장되지 않은 브랜드(예: 구찌)는 모기업 심볼(Kering)을 사용하거나 "상장되지 않음" 안내

## 데이터 조회 전략
다음 형식으로 응답해주세요:

data_query: [Yahoo Finance 심볼 - 반드시 티커 심볼 형태]
data_type: [조회할 데이터 타입 - stock/price/volume/market 등]
additional_info: [추가로 필요한 정보]

## 예시

요청: "삼성전자 주가 알려줘"
data_query: 005930.KS
data_type: stock
additional_info: current_price,change_rate,volume

요청: "디즈니 현재가"
data_query: DIS
data_type: stock
additional_info: current_price,change_rate

요청: "인텔 주가"
data_query: INTC
data_type: stock
additional_info: current_price,change_rate,volume

## 응답 형식
data_query: [Yahoo Finance 티커 심볼]
data_type: [값]
additional_info: [값]"""
    
    def parse_data_strategy(self, response_text: str) -> Dict[str, Any]:
        """데이터 전략 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'data_query':
                        result['data_query'] = value
                    elif key == 'data_type':
                        result['data_type'] = value
                    elif key == 'additional_info':
                        result['additional_info'] = value
            
            # 기본값 설정
            result.setdefault('data_query', '삼성전자')
            result.setdefault('data_type', 'stock')
            result.setdefault('additional_info', 'current_price')
            
            return result
            
        except Exception as e:
            print(f"❌ 데이터 전략 파싱 오류: {e}")
            return {
                'data_query': '삼성전자',
                'data_type': 'stock', 
                'additional_info': 'current_price'
            }
    
    def is_simple_price_request(self, user_query: str, query_analysis: Dict[str, Any]) -> bool:
        """간단한 주가 요청인지 판단"""
        # 주요 의도가 visualization이거나 data이고 복잡도가 simple인 경우
        if (query_analysis.get('primary_intent') in ['visualization', 'data'] and 
            query_analysis.get('complexity_level') == 'simple'):
            
            # 간단한 주가 요청 패턴들
            simple_patterns = [
                "주가 알려줘", "현재가 알려줘", "가격 알려줘", "시세 알려줘",
                "주가", "현재가", "가격", "시세", "알려줘"
            ]
            
            query_lower = user_query.lower()
            for pattern in simple_patterns:
                if pattern in query_lower:
                    return True
        
        return False
    
    def generate_simple_price_response(self, data: Dict[str, Any], user_query: str) -> str:
        """간단한 주가 응답 생성"""
        try:
            if not data or "error" in data:
                return "죄송합니다. 주가 정보를 가져올 수 없습니다."
            
            # 기본 주가 정보 추출
            stock_name = data.get('company_name', '종목')
            current_price = data.get('current_price', 'N/A')
            change_rate = data.get('price_change_percent', 'N/A')
            change_amount = data.get('price_change', 'N/A')
            volume = data.get('volume', 'N/A')
            currency_symbol = data.get('currency_symbol', '₩')  # 통화 심볼 가져오기
            
            # 간단하고 친근한 응답 생성
            response_parts = [
                f"📊 **{stock_name}** 주가 정보",
                "",
                f"💰 **현재가**: {currency_symbol}{current_price:,}" if isinstance(current_price, (int, float)) else f"💰 **현재가**: {currency_symbol}{current_price}",
            ]
            
            if change_rate != 'N/A' and change_amount != 'N/A':
                change_symbol = "📈" if (isinstance(change_rate, (int, float)) and change_rate > 0) or (isinstance(change_amount, (int, float)) and change_amount > 0) else "📉"
                change_rate_str = f"+{change_rate}%" if isinstance(change_rate, (int, float)) and change_rate > 0 else f"{change_rate}%"
                change_amount_str = f"+{currency_symbol}{change_amount:,}" if isinstance(change_amount, (int, float)) and change_amount > 0 else f"{currency_symbol}{change_amount:,}"
                response_parts.append(f"{change_symbol} **변동**: {change_rate_str} ({change_amount_str})")
            
            if volume != 'N/A':
                response_parts.append(f"📊 **거래량**: {volume:,}주" if isinstance(volume, (int, float)) else f"📊 **거래량**: {volume}")
            
            # PER, PBR 추가
            pe_ratio = data.get('pe_ratio', 'N/A')
            pbr = data.get('pbr', 'N/A')
            roe = data.get('roe', 'N/A')
            
            if pe_ratio != 'N/A' and pe_ratio != 'Unknown':
                response_parts.append(f"📈 **PER**: {pe_ratio}배")
            if pbr != 'N/A' and pbr != 'Unknown':
                response_parts.append(f"📊 **PBR**: {pbr}배")
            if roe != 'N/A' and roe != 'Unknown':
                response_parts.append(f"💹 **ROE**: {roe}%")
            
            response_parts.extend([
                "",
                "💡 더 자세한 분석이나 차트가 필요하시면 말씀해 주세요!"
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            print(f"❌ 간단한 주가 응답 생성 오류: {e}")
            return f"📊 주가 정보를 가져왔지만 표시 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 에이전트 처리"""
        try:
            self.log(f"데이터 조회 시작: {user_query}")
            
            # LLM이 데이터 조회 전략 결정
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'unknown'),
                complexity_level=query_analysis.get('complexity_level', 'simple'),
                required_services=query_analysis.get('required_services', [])
            )
            
            response_text = self.invoke_llm_with_cache(prompt, purpose="analysis", log_label="data_strategy")
            strategy = self.parse_data_strategy(response_text.strip())
            
            # 실제 데이터 조회
            data = financial_data_service.get_financial_data(strategy['data_query'])
            
            result = {
                'success': "error" not in data,
                'data': data,
                'strategy': strategy
            }
            
            if "error" in data:
                result['error'] = data["error"]
                self.log(f"데이터 조회 실패: {data['error']}")
            else:
                self.log(f"데이터 조회 완료: {strategy['data_query']}")
                
                # 간단한 주가 요청인지 확인
                if self.is_simple_price_request(user_query, query_analysis):
                    # 간단한 주가 요청이면 바로 응답 생성
                    simple_response = self.generate_simple_price_response(data, user_query)
                    result['simple_response'] = simple_response
                    result['is_simple_request'] = True
                    self.log(f"간단한 주가 응답 생성: {strategy['data_query']}")
                else:
                    result['is_simple_request'] = False
            
            return result
            
        except Exception as e:
            self.log(f"데이터 에이전트 오류: {e}")
            return {
                'success': False,
                'error': f"데이터 조회 중 오류: {str(e)}",
                'is_simple_request': False
            }

