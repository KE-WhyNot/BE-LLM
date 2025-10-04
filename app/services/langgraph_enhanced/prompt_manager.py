"""
프롬프트 관리자 (Gemini 전용)
동적 프롬프트 생성 및 템플릿 관리
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from .llm_manager import get_gemini_llm


class PromptManager:
    """프롬프트 관리자"""
    
    def __init__(self):
        self.llm = get_gemini_llm(temperature=0.1)
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_prompt_templates(self) -> Dict[str, Dict[str, str]]:
        """프롬프트 템플릿 로드"""
        return {
            "classification": {
                "base": """당신은 금융 챗봇의 의도 분류 전문가입니다.
사용자 질문을 분석하여 정확히 6가지 카테고리 중 하나로 분류하세요.

## 카테고리 정의
1. **data** - 실시간 주식 가격, 시세, 현재가 조회 요청 (차트 없이 텍스트만)
   예시: "삼성전자 주가 텍스트로만", "SK하이닉스 현재가 숫자만"

2. **analysis** - 투자 분석, 매수/매도 의견, 재무 분석 요청
   예시: "삼성전자 투자해도 될까?", "네이버 분석해줘", "카카오 매수 추천?"

3. **news** - 뉴스, 시장 동향, 공시 정보 조회 요청
   예시: "삼성전자 뉴스 알려줘", "최근 반도체 뉴스는?", "오늘 시장 동향"

4. **knowledge** - 금융 용어, 개념, 전략 설명 요청
   예시: "PER이 뭐야?", "분산투자란?", "ROE 설명해줘", "기술적 분석이란?"

5. **visualization** - 차트, 그래프, 시각화 요청 (주가/가격/시세 포함)
   예시: "삼성전자 주가 알려줘", "네이버 현재가", "SK하이닉스 가격", "삼성전자 차트 보여줘"

6. **general** - 인사, 도움말, 기타 일반적인 대화
   예시: "안녕하세요", "도움말", "뭐 할 수 있어?", "고마워"

## 분석 기준
- 주가/가격/현재가 키워드가 있으면 **visualization** (차트 포함 응답)
- 분석/투자/매수/매도 키워드가 있으면 **analysis**
- 뉴스/뉴스/시장/공시 키워드가 있으면 **news**
- 용어/개념/설명 키워드가 있으면 **knowledge**
- 단순 데이터만 요청하면 **data**
- 그 외에는 **general**

## 출력
한 단어만 출력하세요 (data, analysis, news, knowledge, visualization, general 중 하나)""",

                "examples": [
                    "삼성전자 주가 알려줘 → visualization",
                    "PER이 뭐야? → knowledge", 
                    "삼성전자 투자해도 될까? → analysis",
                    "삼성전자 뉴스 알려줘 → news",
                    "안녕하세요 → general"
                ]
            },
            
            "analysis": {
                "base": """당신은 전문 금융 애널리스트입니다.
다음 데이터를 분석하여 투자 인사이트를 제공하세요.

## 분석 데이터
{financial_data}

## 사용자 질문
{user_query}

## 분석 지침
1. **기본 분석**: 현재가, 변동률, 거래량 등 기본 지표 분석
2. **재무 분석**: PER, PBR, ROE, 부채비율 등 재무 지표 해석
3. **투자 의견**: 매수/매도/보유 의견 (신중하게)
4. **리스크 요소**: 투자 시 주의할 점
5. **추가 확인사항**: 더 확인해야 할 정보

## 응답 형식
📊 **기본 분석**
• 현재가: {current_price} ({change_pct}%)
• 거래량: {volume:,}주
• 시가총액: {market_cap}

📈 **재무 분석**
• PER: {pe_ratio} ({pe_analysis})
• PBR: {pbr} ({pbr_analysis})
• ROE: {roe}% ({roe_analysis})

💡 **투자 의견**
{investment_opinion}

⚠️ **리스크 요소**
{risk_factors}

📋 **추가 확인사항**
{additional_checks}

## 주의사항
- 객관적이고 균형 잡힌 분석을 제공하세요
- 투자 권유가 아닌 참고 정보임을 명시하세요
- 개인 투자자의 상황을 고려하지 않았음을 알려주세요""",

                "dynamic": """당신은 {user_profile} 사용자를 위한 맞춤형 금융 분석가입니다.
사용자의 투자 경험과 선호도를 고려하여 분석을 제공하세요.

## 사용자 프로필
{user_profile}

## 분석 데이터
{financial_data}

## 맞춤형 분석 요청
{user_query}

## 맞춤형 분석 지침
1. **사용자 수준에 맞는 설명**: {experience_level} 수준에 맞춘 용어 사용
2. **관심 분야 반영**: {interests} 관련 인사이트 포함
3. **리스크 허용도 고려**: {risk_tolerance} 수준에 맞는 조언
4. **투자 목표 반영**: {investment_goals} 달성에 도움이 되는 분석

## 응답 형식
{formatted_response}"""
            },
            
            "news": {
                "base": """당신은 금융 뉴스 전문가입니다.
다음 뉴스들을 분석하여 시장에 미치는 영향을 설명하세요.

## 뉴스 데이터
{news_data}

## 사용자 질문
{user_query}

## 분석 지침
1. **뉴스 요약**: 핵심 내용 간단히 정리
2. **시장 영향**: 주가나 시장에 미칠 영향 분석
3. **투자 관점**: 투자자 관점에서의 해석
4. **추가 확인**: 더 알아봐야 할 사항

## 응답 형식
📰 **뉴스 요약**
{news_summary}

📈 **시장 영향 분석**
{market_impact}

💡 **투자자 관점**
{investor_perspective}

📋 **추가 확인사항**
{additional_checks}"""
            },
            
            "knowledge": {
                "base": """당신은 금융 교육 전문가입니다.
다음 지식 정보를 바탕으로 사용자의 질문에 답변하세요.

## 지식 정보
{knowledge_context}

## 사용자 질문
{user_query}

## 교육 지침
1. **명확한 설명**: 이해하기 쉽게 설명
2. **구체적 예시**: 실제 사례로 설명
3. **실용적 활용**: 어떻게 활용할 수 있는지
4. **관련 개념**: 연관된 다른 개념들

## 응답 형식
📚 **{concept_name}란?**
{concept_definition}

💡 **구체적 예시**
{concrete_examples}

🎯 **실제 활용법**
{practical_usage}

🔗 **관련 개념**
{related_concepts}

❓ **더 알아보기**
{further_learning}"""
            },
            
            "visualization": {
                "base": """당신은 금융 데이터 시각화 전문가입니다.
다음 데이터를 바탕으로 차트를 생성하고 해석하세요.

## 차트 데이터
{chart_data}

## 사용자 질문
{user_query}

## 시각화 지침
1. **차트 타입 결정**: 데이터에 가장 적합한 차트 선택
2. **시각적 요소**: 색상, 스타일, 레이블 설정
3. **데이터 해석**: 차트에서 읽을 수 있는 인사이트
4. **활용 가이드**: 차트를 어떻게 활용할지

## 차트 설정
- 차트 타입: {chart_type}
- 데이터 범위: {data_range}
- 주요 지표: {key_indicators}

## 해석 가이드
{chart_interpretation}"""
            }
        }
    
    def generate_classification_prompt(self, query: str) -> str:
        """분류용 프롬프트 생성"""
        template = self.prompt_templates["classification"]["base"]
        examples = self.prompt_templates["classification"]["examples"]
        
        prompt = f"""{template}

## 예시
{chr(10).join(examples)}

## 사용자 질문
{query}

분류 결과:"""
        
        return prompt
    
    def generate_analysis_prompt(self, 
                               financial_data: Dict[str, Any], 
                               user_query: str,
                               user_context: Optional[Dict[str, Any]] = None) -> str:
        """분석용 프롬프트 생성"""
        template = self.prompt_templates["analysis"]["base"]
        
        # 사용자 프로필이 있으면 동적 프롬프트 사용
        if user_context and user_context.get("user_profile"):
            return self._generate_dynamic_analysis_prompt(financial_data, user_query, user_context)
        
        # 기본 분석 프롬프트
        prompt = template.format(
            financial_data=self._format_financial_data(financial_data),
            user_query=user_query,
            current_price=financial_data.get('current_price', 'N/A'),
            change_pct=financial_data.get('price_change_percent', 0),
            volume=financial_data.get('volume', 0),
            market_cap=financial_data.get('market_cap', 'N/A'),
            pe_ratio=financial_data.get('pe_ratio', 'N/A'),
            pbr=financial_data.get('pbr', 'N/A'),
            roe=financial_data.get('roe', 'N/A'),
            pe_analysis=self._analyze_pe_ratio(financial_data.get('pe_ratio')),
            pbr_analysis=self._analyze_pbr(financial_data.get('pbr')),
            roe_analysis=self._analyze_roe(financial_data.get('roe')),
            investment_opinion=self._generate_investment_opinion(financial_data),
            risk_factors=self._generate_risk_factors(financial_data),
            additional_checks=self._generate_additional_checks(financial_data)
        )
        
        return prompt
    
    def generate_news_prompt(self, 
                           news_data: List[Dict[str, Any]], 
                           user_query: str) -> str:
        """뉴스용 프롬프트 생성"""
        template = self.prompt_templates["news"]["base"]
        
        prompt = template.format(
            news_data=self._format_news_data(news_data),
            user_query=user_query,
            news_summary=self._generate_news_summary(news_data),
            market_impact=self._generate_market_impact(news_data),
            investor_perspective=self._generate_investor_perspective(news_data),
            additional_checks=self._generate_additional_checks_news(news_data)
        )
        
        return prompt
    
    def generate_knowledge_prompt(self, 
                                knowledge_context: str, 
                                user_query: str) -> str:
        """지식용 프롬프트 생성"""
        template = self.prompt_templates["knowledge"]["base"]
        
        # 질문에서 개념 추출
        concept_name = self._extract_concept_name(user_query)
        
        prompt = template.format(
            knowledge_context=knowledge_context,
            user_query=user_query,
            concept_name=concept_name,
            concept_definition=self._generate_concept_definition(knowledge_context, concept_name),
            concrete_examples=self._generate_concrete_examples(concept_name),
            practical_usage=self._generate_practical_usage(concept_name),
            related_concepts=self._generate_related_concepts(concept_name),
            further_learning=self._generate_further_learning(concept_name)
        )
        
        return prompt
    
    def generate_visualization_prompt(self, 
                                    chart_data: Dict[str, Any], 
                                    user_query: str) -> str:
        """시각화용 프롬프트 생성"""
        template = self.prompt_templates["visualization"]["base"]
        
        prompt = template.format(
            chart_data=self._format_chart_data(chart_data),
            user_query=user_query,
            chart_type=chart_data.get('chart_type', 'candlestick_volume'),
            data_range=chart_data.get('data_range', '최근 1개월'),
            key_indicators=chart_data.get('key_indicators', '주가, 거래량'),
            chart_interpretation=self._generate_chart_interpretation(chart_data)
        )
        
        return prompt
    
    # ===== 헬퍼 메서드들 =====
    
    def _generate_dynamic_analysis_prompt(self, 
                                        financial_data: Dict[str, Any], 
                                        user_query: str,
                                        user_context: Dict[str, Any]) -> str:
        """동적 분석 프롬프트 생성"""
        template = self.prompt_templates["analysis"]["dynamic"]
        
        user_profile = user_context.get("user_profile", {})
        
        prompt = template.format(
            user_profile=self._format_user_profile(user_profile),
            financial_data=self._format_financial_data(financial_data),
            user_query=user_query,
            experience_level=user_profile.get("experience_level", "중급"),
            interests=user_profile.get("interests", "주식 투자"),
            risk_tolerance=user_profile.get("risk_tolerance", "중간"),
            investment_goals=user_profile.get("investment_goals", "안정적 수익"),
            formatted_response=self._generate_formatted_response(financial_data)
        )
        
        return prompt
    
    def _format_financial_data(self, data: Dict[str, Any]) -> str:
        """금융 데이터 포맷팅"""
        if not data:
            return "데이터 없음"
        
        formatted = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                formatted.append(f"• {key}: {value:,}")
            else:
                formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_news_data(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 데이터 포맷팅"""
        if not news_data:
            return "뉴스 없음"
        
        formatted = []
        for i, news in enumerate(news_data, 1):
            title = news.get('title', '제목 없음')
            summary = news.get('summary', '요약 없음')
            formatted.append(f"{i}. {title}\n   {summary}")
        
        return "\n".join(formatted)
    
    def _format_chart_data(self, chart_data: Dict[str, Any]) -> str:
        """차트 데이터 포맷팅"""
        if not chart_data:
            return "차트 데이터 없음"
        
        formatted = []
        for key, value in chart_data.items():
            formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        """사용자 프로필 포맷팅"""
        if not profile:
            return "프로필 없음"
        
        formatted = []
        for key, value in profile.items():
            formatted.append(f"• {key}: {value}")
        
        return "\n".join(formatted)
    
    # 분석 헬퍼 메서드들
    def _analyze_pe_ratio(self, pe_ratio) -> str:
        """PER 분석"""
        if not isinstance(pe_ratio, (int, float)) or pe_ratio <= 0:
            return "분석 불가"
        
        if pe_ratio < 10:
            return "저평가 구간"
        elif pe_ratio < 15:
            return "적정 수준"
        elif pe_ratio < 25:
            return "약간 높음"
        else:
            return "고평가 구간"
    
    def _analyze_pbr(self, pbr) -> str:
        """PBR 분석"""
        if not isinstance(pbr, (int, float)) or pbr <= 0:
            return "분석 불가"
        
        if pbr < 1:
            return "저평가 가능성"
        elif pbr < 2:
            return "적정 수준"
        else:
            return "프리미엄 반영"
    
    def _analyze_roe(self, roe) -> str:
        """ROE 분석"""
        if not isinstance(roe, (int, float)) or roe <= 0:
            return "분석 불가"
        
        if roe > 20:
            return "매우 우수"
        elif roe > 15:
            return "양호한 수준"
        elif roe > 10:
            return "보통 수준"
        else:
            return "개선 필요"
    
    def _generate_investment_opinion(self, data: Dict[str, Any]) -> str:
        """투자 의견 생성"""
        # 간단한 로직으로 투자 의견 생성
        pe_ratio = data.get('pe_ratio', 0)
        pbr = data.get('pbr', 0)
        roe = data.get('roe', 0)
        
        positive_signals = 0
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 0 and pe_ratio < 15:
            positive_signals += 1
        if isinstance(pbr, (int, float)) and pbr > 0 and pbr < 2:
            positive_signals += 1
        if isinstance(roe, (int, float)) and roe > 0 and roe > 15:
            positive_signals += 1
        
        if positive_signals >= 2:
            return "긍정적인 신호가 많습니다. 관심을 가져볼 만합니다."
        elif positive_signals >= 1:
            return "혼조세를 보이고 있습니다. 추가 정보 확인이 필요합니다."
        else:
            return "신중한 접근이 필요합니다. 더 자세한 분석을 권합니다."
    
    def _generate_risk_factors(self, data: Dict[str, Any]) -> str:
        """리스크 요소 생성"""
        risks = []
        
        pe_ratio = data.get('pe_ratio', 0)
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 30:
            risks.append("• 고평가 위험")
        
        debt_ratio = data.get('debt_to_equity', 0)
        if isinstance(debt_ratio, (int, float)) and debt_ratio > 200:
            risks.append("• 높은 부채비율")
        
        if not risks:
            risks.append("• 일반적인 투자 리스크")
        
        return "\n".join(risks)
    
    def _generate_additional_checks(self, data: Dict[str, Any]) -> str:
        """추가 확인사항 생성"""
        checks = [
            "• 최근 뉴스 및 공시사항 확인",
            "• 경쟁사와의 비교 분석",
            "• 업종 전체의 시장 동향",
            "• 본인의 투자 목표 및 리스크 허용 수준"
        ]
        return "\n".join(checks)
    
    def _generate_formatted_response(self, data: Dict[str, Any]) -> str:
        """포맷된 응답 생성"""
        return """📊 **기본 분석**
• 현재가, 변동률, 거래량 분석

📈 **재무 분석**  
• PER, PBR, ROE 등 재무 지표 해석

💡 **투자 의견**
• 매수/매도/보유 의견 (신중하게)

⚠️ **리스크 요소**
• 투자 시 주의할 점

📋 **추가 확인사항**
• 더 확인해야 할 정보"""
    
    # 기타 헬퍼 메서드들 (간단한 구현)
    def _generate_news_summary(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 요약 생성"""
        return "주요 뉴스 내용 요약"
    
    def _generate_market_impact(self, news_data: List[Dict[str, Any]]) -> str:
        """시장 영향 분석"""
        return "시장에 미칠 영향 분석"
    
    def _generate_investor_perspective(self, news_data: List[Dict[str, Any]]) -> str:
        """투자자 관점 생성"""
        return "투자자 관점에서의 해석"
    
    def _generate_additional_checks_news(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 추가 확인사항"""
        return "추가로 확인해야 할 사항"
    
    def _extract_concept_name(self, query: str) -> str:
        """개념명 추출"""
        # 간단한 키워드 추출
        keywords = ["PER", "PBR", "ROE", "배당", "분산투자", "기술적 분석"]
        for keyword in keywords:
            if keyword in query:
                return keyword
        return "금융 개념"
    
    def _generate_concept_definition(self, context: str, concept: str) -> str:
        """개념 정의 생성"""
        return f"{concept}에 대한 명확한 정의"
    
    def _generate_concrete_examples(self, concept: str) -> str:
        """구체적 예시 생성"""
        return f"{concept}의 실제 사례"
    
    def _generate_practical_usage(self, concept: str) -> str:
        """실용적 활용법 생성"""
        return f"{concept}의 활용 방법"
    
    def _generate_related_concepts(self, concept: str) -> str:
        """관련 개념 생성"""
        return f"{concept}와 관련된 다른 개념들"
    
    def _generate_further_learning(self, concept: str) -> str:
        """추가 학습 제안"""
        return f"{concept}에 대해 더 알아볼 내용"
    
    def _generate_chart_interpretation(self, chart_data: Dict[str, Any]) -> str:
        """차트 해석 가이드 생성"""
        return "차트에서 읽을 수 있는 인사이트"


# 전역 프롬프트 관리자 인스턴스
prompt_manager = PromptManager()
