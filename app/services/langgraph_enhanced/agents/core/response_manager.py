"""
통합 응답 관리자 - 모든 응답 생성을 중앙에서 관리
일관된 응답 형식과 품질 보장
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class ResponseType(Enum):
    """응답 유형"""
    SIMPLE_STOCK = "simple_stock"
    INVESTMENT_ANALYSIS = "investment_analysis"
    NEWS_SUMMARY = "news_summary"
    KNOWLEDGE_EXPLANATION = "knowledge_explanation"
    CHART_RESPONSE = "chart_response"
    GENERAL_RESPONSE = "general_response"
    ERROR_RESPONSE = "error_response"


@dataclass
class ResponseTemplate:
    """응답 템플릿"""
    response_type: ResponseType
    template: str
    variables: List[str]
    style_guide: str


class ResponseManager:
    """💬 통합 응답 관리자 - 모든 응답 생성을 중앙에서 관리"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.response_templates = self._build_response_templates()
        self.style_guide = self._get_style_guide()
    
    def _build_response_templates(self) -> Dict[ResponseType, ResponseTemplate]:
        """응답 템플릿 구성"""
        templates = {
            ResponseType.SIMPLE_STOCK: ResponseTemplate(
                response_type=ResponseType.SIMPLE_STOCK,
                template="""당신은 금융 전문 챗봇입니다. 주가 정보를 간결하고 친근하게 제공해주세요.

## 주가 정보
{stock_data}

## 응답 생성 지침
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 현재가, 변동률, 거래량을 명확히 표시하세요
4. PER, PBR, ROE가 있으면 포함하세요 자세한 정보가 없다면 표시하지 마세요
5. 간결하고 친근한 톤을 유지하세요
6. CoT를 적극 활용해서 분석을 제공하세요.

## 예시 형식
📊 삼성전자 주가 정보
💰 현재가: ₩71,500 (+2.1%)
📊 거래량: 25,000,000주
📈 PER: 15.2배
📊 PBR: 1.3배

💡 더 자세한 분석이 필요하시면 말씀해 주세요! 😊""",
                variables=["stock_data"],
                style_guide="간결하고 친근한 주가 정보 제공"
            ),
            
            ResponseType.INVESTMENT_ANALYSIS: ResponseTemplate(
                response_type=ResponseType.INVESTMENT_ANALYSIS,
                template="""당신은 전문 투자 분석가입니다. 수집된 정보를 종합하여 투자 분석을 제공해주세요.

## 사용자 질문
"{user_query}"

## 수집된 정보
{collected_data}

## 분석 요구사항

### 📊 현재 상황
- 현재가: {current_price}
- 밸류에이션: PER {pe_ratio}, PBR {pbr}
- 재무 상태 요약
- 최근 뉴스 동향

### 💡 투자 의견 (Chain-of-Thought)
**단계별 사고 과정을 명확히 제시하세요:**

1. **📌 현재 상황 평가**
   - 현재 주가 및 밸류에이션 분석
   - 재무 상태 간단 요약
   - 최근 뉴스 제목 언급하며 시장 분위기 파악

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
   - 투자 기간 권장

### ⚠️ 리스크 경고
- 주요 투자 리스크 3가지
- 변동성 요인
- 추가 확인이 필요한 사항

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. **반드시 위의 최신 뉴스 제목을 언급**하며 분석하세요
4. 각 단계마다 "왜 그렇게 판단했는지" 근거를 명확히 제시
5. 숫자와 데이터를 활용하여 구체적으로 작성
6. 투자 권유가 아닌 참고 정보임을 명시

## 중요 원칙
✅ **신뢰성**: 최신 뉴스 제목을 직접 언급하여 분석의 근거 제시
✅ **구체성**: "좋다/나쁘다"가 아닌 "OO 때문에 OO하다"로 설명
✅ **균형성**: 호재와 악재를 모두 객관적으로 분석
✅ **실용성**: 실제 투자에 바로 활용 가능한 구체적 전략 제시""",
                variables=["user_query", "collected_data", "current_price", "pe_ratio", "pbr"],
                style_guide="전문적이고 균형 잡힌 투자 분석 제공"
            ),
            
            ResponseType.NEWS_SUMMARY: ResponseTemplate(
                response_type=ResponseType.NEWS_SUMMARY,
                template="""당신은 금융 뉴스 전문가입니다. 최신 뉴스를 정리하여 제공해주세요.

## 사용자 질문
"{user_query}"

## 뉴스 데이터
{news_data}

## 뉴스 요약 요구사항

### 📰 핵심 뉴스 요약
- 주요 뉴스 3-5개 선별
- 각 뉴스별 핵심 내용 요약
- 출처와 발행일 명시

### 💡 시사점 분석
- 뉴스가 시장에 미치는 영향
- 투자 관점에서의 의미
- 단기/중기 전망

### 📊 종합 의견
- 전체적인 시장 분위기
- 투자자 관점에서의 조언

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 뉴스 출처를 명확히 표시하세요
4. 객관적이고 균형 잡힌 관점 유지

📰 최신 뉴스 요약

🔥 주요 뉴스
   [뉴스 1] 제목 - 출처, 날짜
   핵심 내용 요약
   
   [뉴스 2] 제목 - 출처, 날짜
   핵심 내용 요약

💡 시사점
   시장 영향 분석

📊 종합 의견
   투자자 관점 조언""",
                variables=["user_query", "news_data"],
                style_guide="객관적이고 균형 잡힌 뉴스 요약 제공"
            ),
            
            ResponseType.KNOWLEDGE_EXPLANATION: ResponseTemplate(
                response_type=ResponseType.KNOWLEDGE_EXPLANATION,
                template="""당신은 금융 교육 전문가입니다. 금융 용어나 개념을 쉽게 설명해주세요.

## 사용자 질문
"{user_query}"

## 지식 정보
{knowledge_data}

## 교육 요구사항

### 📚 개념 설명
- 용어의 정의와 의미
- 간단한 예시로 설명
- 실제 투자에서의 활용법

### 💡 실용적 정보
- 투자 결정에 도움이 되는 정보
- 주의사항이나 팁
- 관련된 다른 용어들

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 초보자도 이해할 수 있도록 쉽게 설명
4. 구체적인 예시 포함

📚 [용어명] 개념 설명

🔍 정의
   용어의 정의와 의미

💡 쉽게 이해하기
   간단한 예시로 설명

📊 실제 활용법
   투자에서 어떻게 사용하는지

⚠️ 주의사항
   알아두면 좋은 팁""",
                variables=["user_query", "knowledge_data"],
                style_guide="초보자도 이해할 수 있는 쉽고 친근한 설명"
            ),
            
            ResponseType.CHART_RESPONSE: ResponseTemplate(
                response_type=ResponseType.CHART_RESPONSE,
                template="""당신은 차트 분석 전문가입니다. 차트 정보와 분석을 제공해주세요.

## 사용자 질문
"{user_query}"

## 차트 데이터
{chart_data}

## 차트 분석 요구사항

### 📊 차트 정보
- 차트 유형과 기간
- 주요 기술적 지표
- 차트 패턴 분석

### 📈 기술적 분석
- 추세 분석
- 지지/저항선
- 매수/매도 신호

### 💡 투자 관점
- 차트 기반 투자 조언
- 리스크 요인
- 모니터링 포인트

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 기술적 분석을 쉽게 설명
4. 투자 조언보다는 정보 제공에 중점

📊 차트 분석 결과

📈 기술적 분석
   추세 및 패턴 분석

💡 투자 관점
   차트 기반 정보 제공

⚠️ 주의사항
   리스크 요인 및 모니터링 포인트""",
                variables=["user_query", "chart_data"],
                style_guide="기술적 분석을 쉽게 설명하는 전문적 톤"
            ),
            
            ResponseType.GENERAL_RESPONSE: ResponseTemplate(
                response_type=ResponseType.GENERAL_RESPONSE,
                template="""당신은 친근한 금융 챗봇입니다. 사용자와 자연스럽게 대화하세요.

## 사용자 질문
"{user_query}"

## 응답 요구사항
1. 친근하고 자연스러운 톤
2. 금융 전문 챗봇임을 자연스럽게 어필
3. 도움이 될 수 있는 서비스 안내
4. 이모지를 적절히 사용

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 친근하고 자연스러운 대화체 사용

안녕하세요! 😊
친근한 인사와 서비스 안내""",
                variables=["user_query"],
                style_guide="친근하고 자연스러운 대화체"
            ),
            
            ResponseType.ERROR_RESPONSE: ResponseTemplate(
                response_type=ResponseType.ERROR_RESPONSE,
                template="""당신은 친근한 금융 챗봇입니다. 오류 상황을 자연스럽게 처리하세요.

## 오류 상황
{error_message}

## 응답 요구사항
1. 친근하고 이해심 있는 톤
2. 오류에 대한 간단한 설명
3. 대안 방법 제시
4. 다시 시도할 수 있도록 격려

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요
2. 이모지와 들여쓰기로 구조화하세요
3. 사용자를 실망시키지 않는 긍정적 톤

😅 죄송합니다
오류 설명과 대안 제시""",
                variables=["error_message"],
                style_guide="긍정적이고 해결책을 제시하는 톤"
            )
        }
        
        return templates
    
    def _get_style_guide(self) -> str:
        """공통 스타일 가이드"""
        return """
## 공통 응답 규칙

### 📝 작성 규칙
1. **마크다운 금지**: *, -, #, ### 등 마크다운 기호 사용 금지
2. **이모지 활용**: 적절한 이모지로 가독성 향상
3. **들여쓰기 구조**: 일관된 들여쓰기로 구조화
4. **친근한 톤**: 전문적이면서도 친근한 톤 유지

### 🎯 품질 기준
1. **정확성**: 정확한 데이터와 정보 제공
2. **일관성**: 모든 응답이 일관된 스타일 유지
3. **완성도**: 사용자 질문에 완전히 답변
4. **실용성**: 실제로 도움이 되는 정보 제공

### ⚠️ 주의사항
1. **투자 권유 금지**: 정보 제공에만 집중
2. **면책 조항**: 필요시 면책 조항 포함
3. **객관성**: 편향되지 않은 객관적 정보 제공
4. **신뢰성**: 출처와 근거를 명확히 제시
"""
    
    def generate_response(
        self, 
        response_type: ResponseType, 
        user_query: str, 
        data: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """응답 생성"""
        try:
            # 응답 템플릿 가져오기
            template = self.response_templates.get(response_type)
            if not template:
                return self._generate_fallback_response(user_query, data)
            
            # 데이터 준비
            formatted_data = self._format_data_for_template(data, template.variables)
            
            # 추가 컨텍스트 병합
            if additional_context:
                formatted_data.update(additional_context)
            
            # 프롬프트 생성
            prompt = template.template.format(
                user_query=user_query,
                **formatted_data
            )
            
            # LLM 호출
            response = self.llm_manager.invoke(prompt)
            
            print(f"💬 응답 생성 완료: {response_type.value}")
            
            return response.content
            
        except Exception as e:
            print(f"❌ 응답 생성 오류: {e}")
            return self._generate_error_response(str(e))
    
    def _format_data_for_template(self, data: Dict[str, Any], variables: List[str]) -> Dict[str, Any]:
        """템플릿용 데이터 포맷팅"""
        formatted = {}
        
        for variable in variables:
            if variable == "stock_data":
                formatted[variable] = self._format_stock_data(data.get('financial_data', {}))
            elif variable == "collected_data":
                formatted[variable] = self._format_collected_data(data)
            elif variable == "news_data":
                formatted[variable] = self._format_news_data(data.get('news_data', []))
            elif variable == "knowledge_data":
                formatted[variable] = self._format_knowledge_data(data.get('knowledge_context', ''))
            elif variable == "chart_data":
                formatted[variable] = self._format_chart_data(data.get('chart_data', {}))
            elif variable == "current_price":
                formatted[variable] = data.get('financial_data', {}).get('current_price', 'N/A')
            elif variable == "pe_ratio":
                formatted[variable] = data.get('financial_data', {}).get('pe_ratio', 'N/A')
            elif variable == "pbr":
                formatted[variable] = data.get('financial_data', {}).get('pbr', 'N/A')
            elif variable == "error_message":
                formatted[variable] = data.get('error', '알 수 없는 오류가 발생했습니다.')
        
        return formatted
    
    def _format_stock_data(self, stock_data: Dict[str, Any]) -> str:
        """주가 데이터 포맷팅"""
        if not stock_data or "error" in stock_data:
            return "주가 데이터를 가져올 수 없습니다."
        
        formatted = []
        formatted.append(f"종목: {stock_data.get('company_name', 'N/A')}")
        formatted.append(f"현재가: {stock_data.get('current_price', 'N/A')}원")
        formatted.append(f"변동률: {stock_data.get('price_change_percent', 'N/A')}%")
        formatted.append(f"거래량: {stock_data.get('volume', 'N/A'):,}주")
        
        if stock_data.get('pe_ratio') and stock_data['pe_ratio'] != 'N/A':
            formatted.append(f"PER: {stock_data['pe_ratio']}배")
        if stock_data.get('pbr') and stock_data['pbr'] != 'N/A':
            formatted.append(f"PBR: {stock_data['pbr']}배")
        if stock_data.get('roe') and stock_data['roe'] != 'N/A':
            formatted.append(f"ROE: {stock_data['roe']}%")
        
        return "\n".join(formatted)
    
    def _format_collected_data(self, data: Dict[str, Any]) -> str:
        """수집된 데이터 포맷팅"""
        sections = []
        
        # 금융 데이터
        if data.get('financial_data'):
            sections.append(f"📊 금융 데이터:\n{self._format_stock_data(data['financial_data'])}")
        
        # 분석 결과
        if data.get('analysis_result'):
            analysis_text = data['analysis_result'][:300] + "..." if len(data['analysis_result']) > 300 else data['analysis_result']
            sections.append(f"📈 분석 결과:\n{analysis_text}")
        
        # 뉴스 데이터
        if data.get('news_data'):
            news_count = len(data['news_data'])
            sections.append(f"📰 뉴스 정보: {news_count}건 수집")
        
        # 지식 정보
        if data.get('knowledge_context'):
            knowledge_text = data['knowledge_context'][:200] + "..." if len(data['knowledge_context']) > 200 else data['knowledge_context']
            sections.append(f"📚 지식 정보:\n{knowledge_text}")
        
        # 차트 정보
        if data.get('chart_data'):
            sections.append(f"📊 차트 정보: {data['chart_data'].get('chart_type', 'N/A')}")
        
        return "\n\n".join(sections) if sections else "수집된 정보가 없습니다."
    
    def _format_news_data(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 데이터 포맷팅"""
        if not news_data:
            return "뉴스 데이터가 없습니다."
        
        formatted = []
        for i, news in enumerate(news_data[:5], 1):  # 최대 5개
            title = news.get('title', 'N/A')
            source = news.get('source', 'N/A')
            published = news.get('published', 'N/A')
            formatted.append(f"[{i}] {title} - {source}, {published}")
        
        return "\n".join(formatted)
    
    def _format_knowledge_data(self, knowledge_context: str) -> str:
        """지식 데이터 포맷팅"""
        if not knowledge_context:
            return "지식 정보가 없습니다."
        
        return knowledge_context[:500] + "..." if len(knowledge_context) > 500 else knowledge_context
    
    def _format_chart_data(self, chart_data: Dict[str, Any]) -> str:
        """차트 데이터 포맷팅"""
        if not chart_data or "error" in chart_data:
            return "차트 데이터가 없습니다."
        
        formatted = []
        formatted.append(f"차트 유형: {chart_data.get('chart_type', 'N/A')}")
        formatted.append(f"기간: {chart_data.get('period', 'N/A')}")
        formatted.append(f"기술적 지표: {', '.join(chart_data.get('indicators', []))}")
        
        return "\n".join(formatted)
    
    def _generate_fallback_response(self, user_query: str, data: Dict[str, Any]) -> str:
        """폴백 응답 생성"""
        return f"""안녕하세요! 😊

"{user_query}"에 대한 질문을 받았습니다.

현재 시스템에 일시적인 문제가 있어 정확한 답변을 제공하기 어려운 상황입니다.

💡 다음과 같은 질문을 해보세요:
  • "삼성전자 주가 알려줘"
  • "네이버 투자 분석해줘"
  • "PER이 뭐야?"
  • "오늘 증시 뉴스 알려줘"

다시 시도해주시면 정확한 답변을 제공해드리겠습니다! 😊"""
    
    def _generate_error_response(self, error_message: str) -> str:
        """오류 응답 생성"""
        return f"""😅 죄송합니다!

시스템에 일시적인 문제가 발생했습니다: {error_message}

💡 해결 방법:
1. 잠시 후 다시 시도해주세요
2. 다른 질문으로 시도해보세요
3. 문제가 지속되면 관리자에게 문의해주세요

금융 관련 질문이 있으시면 언제든 물어보세요! 😊"""


# 싱글톤 인스턴스 (LLM Manager 필요)
def create_response_manager(llm_manager):
    """응답 관리자 생성"""
    return ResponseManager(llm_manager)
