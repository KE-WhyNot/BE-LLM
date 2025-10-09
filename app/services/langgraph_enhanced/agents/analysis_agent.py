"""
분석 에이전트
투자 분석, 재무 분석, 투자 추천 전문 에이전트
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from app.services.workflow_components import financial_data_service, news_service
from app.services.pinecone_rag_service import get_context_for_query
from app.services.pinecone_config import KNOWLEDGE_NAMESPACES


class AnalysisAgent(BaseAgent):
    """📈 분석 에이전트 - 투자 분석 전문가"""
    
    def __init__(self):
        super().__init__(purpose="analysis")
        self.agent_name = "analysis_agent"
    
    def get_prompt_template(self) -> str:
        """분석 전략 결정 프롬프트 템플릿"""
        return """당신은 전문 투자 분석가입니다. 사용자 요청에 따라 최적의 분석 전략을 결정해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}

## 분석 전략 결정
다음 형식으로 응답해주세요:

analysis_type: [분석 유형 - investment/technical/fundamental/valuation/risk 중 하나 또는 여러개]
data_requirements: [필요 데이터 - price/financial/ratios/technical/industry/market]
analysis_depth: [분석 깊이 - basic/intermediate/advanced/comprehensive]
time_horizon: [투자 기간 - short/medium/long/all]
risk_level: [리스크 수준 - conservative/moderate/aggressive]
focus_areas: [집중 영역 - profitability/liquidity/growth/value/momentum]
recommendation_style: [추천 스타일 - cautious/balanced/optimistic]

## 전략 예시

요청: "삼성전자 투자해도 될까?"
analysis_type: investment,fundamental,valuation
data_requirements: price,financial,ratios,industry
analysis_depth: comprehensive
time_horizon: medium
risk_level: moderate
focus_areas: profitability,growth,value
recommendation_style: balanced

요청: "네이버 기술적 분석해줘"
analysis_type: technical
data_requirements: price,technical
analysis_depth: advanced
time_horizon: short
risk_level: moderate
focus_areas: momentum
recommendation_style: cautious

요청: "카카오 밸류에이션 해줘"
analysis_type: valuation,fundamental
data_requirements: financial,ratios,industry
analysis_depth: comprehensive
time_horizon: long
risk_level: conservative
focus_areas: value,profitability
recommendation_style: cautious

## 응답 형식
analysis_type: [값]
data_requirements: [값]
analysis_depth: [값]
time_horizon: [값]
risk_level: [값]
focus_areas: [값]
recommendation_style: [값]"""
    
    def parse_analysis_strategy(self, response_text: str) -> Dict[str, Any]:
        """분석 전략 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'analysis_type':
                        # 쉼표로 구분된 분석 유형들을 리스트로 변환
                        types = [t.strip() for t in value.split(',') if t.strip()]
                        result['analysis_type'] = types
                    elif key == 'data_requirements':
                        # 쉼표로 구분된 데이터 요구사항들을 리스트로 변환
                        requirements = [r.strip() for r in value.split(',') if r.strip()]
                        result['data_requirements'] = requirements
                    elif key == 'analysis_depth':
                        result['analysis_depth'] = value
                    elif key == 'time_horizon':
                        result['time_horizon'] = value
                    elif key == 'risk_level':
                        result['risk_level'] = value
                    elif key == 'focus_areas':
                        # 쉼표로 구분된 집중 영역들을 리스트로 변환
                        areas = [a.strip() for a in value.split(',') if a.strip()]
                        result['focus_areas'] = areas
                    elif key == 'recommendation_style':
                        result['recommendation_style'] = value
            
            # 기본값 설정
            result.setdefault('analysis_type', ['investment'])
            result.setdefault('data_requirements', ['price', 'financial'])
            result.setdefault('analysis_depth', 'comprehensive')
            result.setdefault('time_horizon', 'medium')
            result.setdefault('risk_level', 'moderate')
            result.setdefault('focus_areas', ['profitability', 'value'])
            result.setdefault('recommendation_style', 'balanced')
            
            return result
            
        except Exception as e:
            print(f"❌ 분석 전략 파싱 오류: {e}")
            return {
                'analysis_type': ['investment'],
                'data_requirements': ['price', 'financial'],
                'analysis_depth': 'comprehensive',
                'time_horizon': 'medium',
                'risk_level': 'moderate',
                'focus_areas': ['profitability', 'value'],
                'recommendation_style': 'balanced'
            }
    
    def generate_investment_analysis_prompt(self, financial_data: Dict[str, Any], strategy: Dict[str, Any], user_query: str) -> str:
        """투자 분석 프롬프트 생성"""
        return f"""당신은 {strategy.get('risk_level', 'moderate')} 수준의 투자 분석가입니다. 
{strategy.get('analysis_depth', 'comprehensive')} 수준의 분석을 제공해주세요.

## 사용자 요청
"{user_query}"

## 분석 전략
- 분석 유형: {', '.join(strategy.get('analysis_type', ['investment']))}
- 투자 기간: {strategy.get('time_horizon', 'medium')}
- 리스크 수준: {strategy.get('risk_level', 'moderate')}
- 집중 영역: {', '.join(strategy.get('focus_areas', ['profitability']))}
- 추천 스타일: {strategy.get('recommendation_style', 'balanced')}

## 금융 데이터
{self._format_financial_data(financial_data)}

## 분석 요청사항

### 1. 📊 기본 분석
- **현재가 및 변동률**: {financial_data.get('current_price', 'N/A')}원 ({financial_data.get('price_change_percent', 0)}%)
- **거래량 분석**: {financial_data.get('volume', 'N/A')}주
- **시장 상황**: 거래량과 가격 변동의 상관관계 분석

### 2. 📈 재무 분석
- **PER**: {financial_data.get('pe_ratio', 'N/A')} - 업종 평균 대비 평가
- **PBR**: {financial_data.get('pbr', 'N/A')} - 자산 가치 대비 평가
- **ROE**: {financial_data.get('roe', 'N/A')}% - 수익성 분석
- **부채비율**: {financial_data.get('debt_to_equity', 'N/A')}% - 재무 안정성

### 3. 💡 투자 의견 (신중하게 작성)
- **투자 매력도**: 1-10점 척도로 평가
- **투자 등급**: 매수/적극매수/보유/중립/매도 중 선택
- **투자 근거**: 구체적이고 객관적인 근거 제시
- **투자 리스크**: 주요 리스크 요소 3-5개

### 4. 🎯 투자 전략
- **적합한 투자자**: {strategy.get('risk_level', 'moderate')} 리스크 선호 투자자
- **투자 기간**: {strategy.get('time_horizon', 'medium')} 기간
- **투자 포인트**: 매수 타이밍 및 전략
- **손절/익절 기준**: 구체적인 가격 수준 제시

### 5. 📋 추가 고려사항
- **업종 전망**: 관련 업종의 전망
- **경쟁사 비교**: 주요 경쟁사 대비 포지션
- **시장 환경**: 현재 시장 환경에서의 적합성

## 응답 형식
각 섹션별로 이모지와 함께 구조화하여 작성하세요.
숫자와 데이터는 구체적으로 제시하되, 투자 권유는 신중하게 작성하세요.

## 중요 주의사항
⚠️ **면책조항**: 이 분석은 참고용이며, 투자 권유가 아닙니다.
⚠️ **개인차 고려**: 개인의 투자 목표, 리스크 허용도, 재정 상황은 고려되지 않았습니다.
⚠️ **시장 리스크**: 모든 투자에는 원금 손실 위험이 있습니다."""
    
    def _format_financial_data(self, data: Dict[str, Any]) -> str:
        """금융 데이터 포맷팅"""
        if not data:
            return "금융 데이터가 없습니다."
        
        formatted = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if 'price' in key.lower() or 'amount' in key.lower():
                    formatted.append(f"• {key}: {value:,.0f}원")
                elif 'percent' in key.lower() or 'ratio' in key.lower():
                    formatted.append(f"• {key}: {value:.2f}%")
                else:
                    formatted.append(f"• {key}: {value:,}")
            else:
                formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    async def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """분석 에이전트 처리 (RAG + 뉴스 통합)"""
        try:
            self.log(f"투자 분석 시작: {user_query}")
            
            # LLM이 분석 전략 결정
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'analysis'),
                complexity_level=query_analysis.get('complexity_level', 'moderate'),
                required_services=query_analysis.get('required_services', [])
            )
            
            response = self.llm.invoke(prompt)
            strategy = self.parse_analysis_strategy(response.content.strip())
            
            # 종목명 추출
            stock_symbol = self._extract_stock_symbol(user_query)
            stock_name = self._extract_stock_name(user_query)
            
            # 1. 실시간 금융 데이터 수집
            financial_data = {}
            if stock_symbol:
                try:
                    financial_data = financial_data_service.get_financial_data(stock_symbol)
                    if "error" in financial_data:
                        self.log(f"실시간 데이터 수집 실패: {financial_data['error']}")
                        financial_data = {}
                except Exception as e:
                    self.log(f"실시간 데이터 수집 오류: {e}")
                    financial_data = {}
            
            # 2. RAG에서 재무제표 데이터 가져오기
            rag_financial_context = ""
            if stock_name:
                try:
                    self.log(f"RAG 재무제표 검색: {stock_name}")
                    rag_query = f"{stock_name} 재무제표 재무 분석 실적"
                    rag_financial_context = get_context_for_query(
                        query=rag_query,
                        top_k=5,
                        namespace=KNOWLEDGE_NAMESPACES["financial_analysis"]
                    )
                    if rag_financial_context:
                        self.log(f"RAG 재무제표 발견: {len(rag_financial_context)} 글자")
                    else:
                        self.log("RAG 재무제표 없음")
                except Exception as e:
                    self.log(f"RAG 재무제표 검색 오류: {e}")
            
            # 3. 뉴스 데이터 가져오기
            news_context = ""
            recent_news = []
            if stock_name:
                try:
                    self.log(f"최신 뉴스 검색: {stock_name}")
                    # 영어 이름으로 변환하여 검색
                    english_name = self._get_english_name(stock_name)
                    news_data = await news_service.get_comprehensive_news(
                        query=english_name,
                        use_google_rss=True,
                        translate=True
                    )
                    
                    if news_data and isinstance(news_data, list):
                        recent_news = news_data[:5]  # 최근 5개 뉴스
                        news_summaries = []
                        for news in recent_news:
                            summary = f"- {news.get('title', 'N/A')}"
                            if news.get('published'):
                                summary += f" ({news.get('published')})"
                            news_summaries.append(summary)
                        news_context = "\n".join(news_summaries)
                        self.log(f"뉴스 수집 완료: {len(recent_news)}건")
                    else:
                        self.log("뉴스 없음")
                except Exception as e:
                    self.log(f"뉴스 검색 오류: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 4. 통합 분석 수행
            if financial_data or rag_financial_context or news_context:
                analysis_prompt = f"""당신은 전문 투자 분석가입니다. 다음 정보를 종합하여 투자 분석을 제공해주세요.

## 사용자 질문
"{user_query}"

## 분석 전략
- 분석 유형: {strategy.get('analysis_type', 'investment')}
- 분석 깊이: {strategy.get('analysis_depth', 'comprehensive')}
- 투자 기간: {strategy.get('time_horizon', 'medium')}
- 리스크 수준: {strategy.get('risk_level', 'moderate')}
- 집중 영역: {strategy.get('focus_areas', 'profitability,growth')}

## 1. 실시간 금융 데이터
{self._format_financial_data(financial_data) if financial_data else "실시간 데이터 없음"}

## 2. 재무제표 및 재무 분석 (RAG)
{rag_financial_context if rag_financial_context else "재무제표 데이터 없음"}

## 3. 최신 뉴스
{news_context if news_context else "최신 뉴스 없음"}

## 분석 요구사항
1. **재무 분석**: 재무제표 데이터를 바탕으로 재무 건전성, 수익성, 성장성 평가
2. **뉴스 분석**: 최신 뉴스를 반영한 시장 동향 및 이슈 파악
3. **종합 평가**: 재무 + 뉴스를 통합한 투자 의견
4. **투자 추천**: 구체적인 투자 전략 및 주의사항

다음 형식으로 응답해주세요:

### 📊 재무 분석
[재무제표 기반 분석]

### 📰 뉴스 분석
[최신 뉴스 기반 동향 분석]

### 💡 종합 투자 의견
[통합 분석 및 투자 추천]

### ⚠️ 주의사항
[리스크 및 주의할 점]
"""
                
                analysis_response = self.llm.invoke(analysis_prompt)
                analysis_result = analysis_response.content
                
                self.log(f"통합 투자 분석 완료: {stock_symbol or stock_name}")
            else:
                analysis_result = f"""
📊 **분석 불가 안내**

죄송합니다. {stock_name or stock_symbol or '해당 종목'}의 데이터를 충분히 가져올 수 없어 상세한 분석을 제공할 수 없습니다.

**대안 방법:**
1. 정확한 종목명으로 다시 질문해주세요
2. 다른 종목에 대해 분석을 요청해주세요
3. 일반적인 투자 분석 방법에 대해 문의해주세요

**예시 질문:**
- "삼성전자 투자 분석해줘"
- "네이버 주가 분석"
- "카카오 밸류에이션"
"""
                self.log("데이터 부족으로 분석 불가")
            
            return {
                'success': True,
                'financial_data': financial_data,
                'rag_context_length': len(rag_financial_context),
                'news_count': len(recent_news),
                'analysis_result': analysis_result,
                'strategy': strategy,
                'stock_symbol': stock_symbol,
                'stock_name': stock_name
            }
            
        except Exception as e:
            self.log(f"분석 에이전트 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"투자 분석 중 오류: {str(e)}",
                'analysis_result': "분석에 실패했습니다. 다시 시도해주세요."
            }
    
    def _format_financial_data(self, data: Dict[str, Any]) -> str:
        """금융 데이터 포맷팅"""
        if not data or "error" in data:
            return "데이터 없음"
        
        formatted = []
        if "current_price" in data:
            formatted.append(f"현재가: {data['current_price']}원")
        if "change_percent" in data:
            formatted.append(f"등락률: {data['change_percent']}%")
        if "volume" in data:
            formatted.append(f"거래량: {data['volume']:,}주")
        if "per" in data:
            formatted.append(f"PER: {data['per']}")
        if "pbr" in data:
            formatted.append(f"PBR: {data['pbr']}")
        
        return "\n".join(formatted) if formatted else "데이터 없음"
    
    def _get_english_name(self, korean_name: str) -> str:
        """한글 종목명을 영어로 변환"""
        name_mapping = {
            '삼성전자': 'Samsung Electronics',
            '네이버': 'Naver',
            '카카오': 'Kakao',
            'SK하이닉스': 'SK Hynix',
            'LG화학': 'LG Chem',
            '현대차': 'Hyundai Motor',
            'POSCO': 'POSCO',
            '기아': 'Kia',
            'LG전자': 'LG Electronics',
            '삼성바이오로직스': 'Samsung Biologics'
        }
        return name_mapping.get(korean_name, korean_name)
    
    def _extract_stock_name(self, query: str) -> Optional[str]:
        """쿼리에서 종목명 추출"""
        stock_names = [
            '삼성전자', '네이버', '카카오', 'SK하이닉스', 'LG화학',
            '현대차', 'POSCO', '기아', 'LG전자', '삼성바이오로직스'
        ]
        
        for name in stock_names:
            if name in query:
                return name
        
        return None
    
    def _extract_stock_symbol(self, query: str) -> Optional[str]:
        """쿼리에서 주식 심볼 추출"""
        # 간단한 키워드 매칭
        stock_keywords = {
            '삼성전자': '005930',
            '네이버': '035420', 
            '카카오': '035720',
            'SK하이닉스': '000660',
            'LG화학': '051910',
            '현대차': '005380',
            'POSCO': '005490',
            'KB금융': '105560',
            '신한지주': '055550',
            'LG전자': '066570'
        }
        
        for keyword, symbol in stock_keywords.items():
            if keyword in query:
                return symbol
        
        return None

