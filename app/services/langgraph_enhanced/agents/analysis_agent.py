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
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요.
2. 이모지와 들여쓰기로 구조화하세요.
3. 숫자와 데이터는 구체적으로 제시하되, 투자 권유는 신중하게 작성하세요.

## 중요 주의사항
⚠️ 면책조항: 이 분석은 참고용이며, 투자 권유가 아닙니다.
⚠️ 개인차 고려: 개인의 투자 목표, 리스크 허용도, 재정 상황은 고려되지 않았습니다.
⚠️ 시장 리스크: 모든 투자에는 원금 손실 위험이 있습니다."""
    
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
            
            # 2. RAG에서 재무제표 데이터 가져오기 (한글 + 영어 모두 검색)
            rag_financial_context = ""
            if stock_name:
                try:
                    self.log(f"RAG 재무제표 검색: {stock_name}")
                    # 한글 이름으로 검색
                    rag_query_kr = f"{stock_name} 재무제표 재무 분석 실적"
                    # 영어 이름으로도 검색
                    english_name = self._get_english_name(stock_name)
                    rag_query_en = f"{english_name} financial statement analysis"
                    
                    # 한글 검색
                    rag_context_kr = get_context_for_query(
                        query=rag_query_kr,
                        top_k=3,
                        namespace=KNOWLEDGE_NAMESPACES["financial_analysis"]
                    )
                    # 영어 검색
                    rag_context_en = get_context_for_query(
                        query=rag_query_en,
                        top_k=3,
                        namespace=KNOWLEDGE_NAMESPACES["financial_analysis"]
                    )
                    
                    # 두 결과 통합
                    if rag_context_kr and rag_context_en:
                        rag_financial_context = f"{rag_context_kr}\n\n{rag_context_en}"
                    elif rag_context_kr:
                        rag_financial_context = rag_context_kr
                    elif rag_context_en:
                        rag_financial_context = rag_context_en
                    
                    if rag_financial_context:
                        self.log(f"RAG 재무제표 발견: {len(rag_financial_context or '')} 글자")
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
                        self.log(f"뉴스 수집 완료: {len(recent_news or [])}건")
                    else:
                        self.log("뉴스 없음")
                        recent_news = []  # None 대신 빈 리스트
                except Exception as e:
                    self.log(f"뉴스 검색 오류: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 4. 통합 분석 수행 (CoT 추가)
            if financial_data or rag_financial_context or news_context:
                # 뉴스 요약 (간단하게)
                news_summary = ""
                if recent_news:
                    news_summary = "\n".join([
                        f"• [{news.get('published', 'N/A')}] {news.get('title', 'N/A')}"
                        for news in recent_news[:3]  # 최대 3개만
                    ])
                
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

## 3. 최신 뉴스 (참고용 - 신뢰성 향상)
{news_summary if news_summary else "최신 뉴스 없음"}

## 분석 요구사항

### 📊 재무 분석
재무제표 데이터를 바탕으로:
- 재무 건전성 (부채비율, 유동비율 등)
- 수익성 (ROE, 영업이익률 등)
- 성장성 (매출 성장률, 이익 성장률 등)

### 📰 최신 동향 (뉴스 기반)
**위의 최신 뉴스 3개를 참고하여**:
- 최근 주요 이슈 및 이벤트
- 호재/악재 판단
- 시장 반응 및 전망

### 💡 종합 투자 의견 (Chain-of-Thought 방식)
**단계별 사고 과정을 명확히 제시하세요:**

1. **📌 현재 상황 평가**
   - 현재 주가: {financial_data.get('current_price', 'N/A')}원
   - 밸류에이션: PER {financial_data.get('pe_ratio', 'N/A')}, PBR {financial_data.get('pbr', 'N/A')}
   - 재무 상태: 간단히 요약
   - 최근 뉴스: 위 3개 뉴스 제목을 언급하며 시장 분위기 파악

2. **✅ 긍정적 요인 (호재)**
   - 뉴스에서 파악된 호재 (구체적 제목 언급)
   - 재무적으로 강한 포인트
   - 성장 가능성 및 긍정적 전망
   - **각 요인마다 "왜 호재인가?" 설명**

3. **⚠️ 부정적 요인 및 리스크 (악재)**
   - 뉴스에서 파악된 악재 (구체적 제목 언급)
   - 재무적 약점
   - 투자 리스크 요소
   - **각 요인마다 "왜 악재인가?" 설명**

4. **🎯 투자 판단 근거 (가장 중요!)**
   - "긍정 vs 부정" 요인 균형 분석
   - **왜 이 회사에 투자해야 하는가? (또는 하지 말아야 하는가?)**
   - 구체적 판단 이유: "OO 때문에 OO하다고 판단합니다"
   - 투자 의견: 매수/적극매수/관망/매도 중 하나
   - 목표가/손절가 제시 (가능한 경우)

5. **📋 구체적 실행 전략**
   - 진입 타이밍: "지금 바로" or "OO원 근처 조정 대기" or "분할 매수"
   - 분할 매수/매도 전략: "3회 분할", "30%씩 매수" 등 구체적
   - 모니터링 포인트: "어떤 지표를 봐야 하는가?"
   - 투자 기간: {strategy.get('time_horizon', 'medium')} 기간 권장

### ⚠️ 리스크 경고
- 주요 투자 리스크 3가지
- 변동성 요인
- 추가 확인이 필요한 사항

## 응답 형식
- **반드시 위의 최신 뉴스 제목을 언급**하며 분석하세요
- 각 단계마다 "왜 그렇게 판단했는지" 근거를 명확히 제시
- 숫자와 데이터를 활용하여 구체적으로 작성
- 이모지를 적절히 사용하여 가독성 향상

## 중요 원칙
✅ **신뢰성**: 최신 뉴스 제목을 직접 언급하여 분석의 근거 제시
✅ **구체성**: "좋다/나쁘다"가 아닌 "OO 때문에 OO하다"로 설명
✅ **균형성**: 호재와 악재를 모두 객관적으로 분석
✅ **실용성**: 실제 투자에 바로 활용 가능한 구체적 전략 제시"""
                
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
                'rag_context_length': len(rag_financial_context) if rag_financial_context else 0,
                'news_count': len(recent_news) if recent_news else 0,
                'news_data': recent_news or [],  # ← 뉴스 데이터 추가 ✨
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
        """쿼리에서 종목명 추출 (키워드 제거 방식)"""
        # 제거할 키워드들
        keywords_to_remove = [
            "주가", "주식", "시세", "가격", "얼마", "알려줘", "알려주세요", "어때", "어떄",
            "최근", "동향", "뉴스", "분석", "전망", "예측", "정보", "상황", "현황",
            "어떻게", "어떤", "무엇", "뭐", "궁금", "궁금해", "궁금합니다", "현재가",
            "차트", "그래프", "시각화", "보여줘", "보여주세요", "투자", "해도", "될까",
            "지금", "매수", "매도", "사도", "팔아도", "괜찮", "추천", "해줘", "해주세요"
        ]
        
        cleaned_query = query
        for keyword in keywords_to_remove:
            cleaned_query = cleaned_query.replace(keyword, "")
        
        # 공백 제거 및 정리
        stock_name = cleaned_query.strip()
        
        # 최소 길이 체크
        if stock_name and len(stock_name) >= 2:
            return stock_name
        
        return None
    
    def _extract_stock_symbol(self, query: str) -> Optional[str]:
        """쿼리에서 주식 심볼 추출"""
        try:
            # stock_utils 사용
            from app.utils.stock_utils import extract_symbol_from_query
            symbol = extract_symbol_from_query(query)
            
            if symbol:
                self.log(f"심볼 추출 성공: {query} → {symbol}")
            else:
                self.log(f"심볼 추출 실패: {query}")
            
            return symbol
            
        except Exception as e:
            self.log(f"심볼 추출 오류: {e}")
            return None

