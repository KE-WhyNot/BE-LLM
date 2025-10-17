"""
지식 에이전트
금융 지식, 용어 설명, 교육 전문 에이전트 (네임스페이스 기반 세분화)
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from app.services.pinecone_rag_service import search_pinecone, get_context_for_query
from app.services.pinecone_config import KNOWLEDGE_NAMESPACES, NAMESPACE_DESCRIPTIONS


class KnowledgeAgent(BaseAgent):
    """📚 지식 에이전트 - 금융 교육 전문가 (네임스페이스 라우팅)"""
    
    def __init__(self):
        super().__init__(purpose="knowledge")
        self.agent_name = "knowledge_agent"
        
        # 네임스페이스 매핑
        self.namespaces = KNOWLEDGE_NAMESPACES
        self.namespace_descriptions = NAMESPACE_DESCRIPTIONS
    
    def _load_knowledge_database(self) -> Dict[str, Dict[str, Any]]:
        """금융 지식 데이터베이스 로드"""
        return {
            "PER": {
                "name": "주가수익비율 (Price-to-Earnings Ratio)",
                "definition": "주가를 주당순이익(EPS)으로 나눈 값으로, 주식의 상대적 가치를 평가하는 지표입니다.",
                "formula": "PER = 주가 ÷ 주당순이익(EPS)",
                "interpretation": {
                    "낮음": "주식이 저평가되었을 가능성이 높습니다.",
                    "높음": "주식이 고평가되었을 가능성이 높습니다.",
                    "적정": "시장에서 합리적으로 평가받고 있습니다."
                },
                "examples": [
                    "삼성전자 주가 70,000원, EPS 5,000원 → PER = 14",
                    "네이버 주가 200,000원, EPS 10,000원 → PER = 20"
                ],
                "related_terms": ["EPS", "PBR", "ROE", "밸류에이션"],
                "usage": "투자 시 주식의 상대적 가치를 판단하는 데 사용됩니다."
            },
            "PBR": {
                "name": "주가순자산비율 (Price-to-Book Ratio)",
                "definition": "주가를 주당순자산(BPS)으로 나눈 값으로, 자산 대비 주식의 가치를 평가하는 지표입니다.",
                "formula": "PBR = 주가 ÷ 주당순자산(BPS)",
                "interpretation": {
                    "낮음": "자산 대비 저평가되었을 가능성이 높습니다.",
                    "높음": "자산 대비 고평가되었을 가능성이 높습니다.",
                    "1.0": "주가가 순자산과 동일한 수준입니다."
                },
                "examples": [
                    "삼성전자 주가 70,000원, BPS 50,000원 → PBR = 1.4",
                    "LG화학 주가 400,000원, BPS 300,000원 → PBR = 1.33"
                ],
                "related_terms": ["BPS", "PER", "ROE", "순자산"],
                "usage": "자산 중심의 가치 평가에 사용됩니다."
            },
            "ROE": {
                "name": "자기자본이익률 (Return on Equity)",
                "definition": "기업이 자기자본을 얼마나 효율적으로 활용하여 이익을 창출하는지를 보여주는 지표입니다.",
                "formula": "ROE = 당기순이익 ÷ 자기자본 × 100",
                "interpretation": {
                    "높음": "자기자본을 효율적으로 활용하고 있습니다.",
                    "낮음": "자기자본 활용 효율성이 낮습니다.",
                    "15% 이상": "우수한 수익성을 보여줍니다."
                },
                "examples": [
                    "당기순이익 1,000억원, 자기자본 5,000억원 → ROE = 20%",
                    "당기순이익 500억원, 자기자본 10,000억원 → ROE = 5%"
                ],
                "related_terms": ["PER", "PBR", "ROA", "자기자본"],
                "usage": "기업의 수익성과 경영 효율성을 평가하는 데 사용됩니다."
            },
            "EPS": {
                "name": "주당순이익 (Earnings Per Share)",
                "definition": "기업의 순이익을 발행주식 수로 나눈 값으로, 주식 1주당 얼마의 이익을 냈는지 보여줍니다.",
                "formula": "EPS = 당기순이익 ÷ 발행주식 수",
                "interpretation": {
                    "증가": "기업의 수익성이 개선되고 있습니다.",
                    "감소": "기업의 수익성이 악화되고 있습니다.",
                    "높음": "주주에게 더 많은 이익을 제공합니다."
                },
                "examples": [
                    "당기순이익 10조원, 발행주식 5억주 → EPS = 20,000원",
                    "당기순이익 5조원, 발행주식 10억주 → EPS = 5,000원"
                ],
                "related_terms": ["PER", "주가", "순이익", "주식수"],
                "usage": "주식의 기본적 가치를 평가하는 데 사용됩니다."
            },
            "분산투자": {
                "name": "분산투자 (Diversification)",
                "definition": "투자 리스크를 줄이기 위해 여러 종목이나 자산에 투자하는 전략입니다.",
                "principles": [
                    "한 종목에 모든 자금을 투자하지 않기",
                    "다양한 업종과 시장에 투자하기",
                    "시간적 분산으로 매수 타이밍 조절하기"
                ],
                "benefits": [
                    "개별 종목 리스크 감소",
                    "전체 포트폴리오 안정성 향상",
                    "장기적 수익률 안정화"
                ],
                "examples": [
                    "삼성전자 30%, 네이버 20%, 카카오 20%, 현대차 15%, 기타 15%",
                    "주식 60%, 채권 30%, 현금 10%"
                ],
                "related_terms": ["포트폴리오", "리스크 관리", "자산배분"],
                "usage": "투자 리스크를 관리하는 기본적인 투자 전략입니다."
            },
            "기술적분석": {
                "name": "기술적 분석 (Technical Analysis)",
                "definition": "주가와 거래량 등 시장 데이터를 분석하여 미래 주가 움직임을 예측하는 방법입니다.",
                "main_indicators": [
                    "이동평균선 (MA)",
                    "RSI (상대강도지수)",
                    "MACD",
                    "볼린저 밴드",
                    "스토캐스틱"
                ],
                "principles": [
                    "주가는 모든 정보를 반영한다",
                    "주가는 추세를 따라 움직인다",
                    "역사는 반복된다"
                ],
                "usage": "단기 투자나 매매 타이밍 결정에 활용됩니다.",
                "related_terms": ["차트 분석", "추세 분석", "지지선", "저항선"],
                "limitations": "기술적 분석만으로는 완벽한 예측이 불가능합니다."
            }
        }
    
    def get_prompt_template(self) -> str:
        """지식 분석 전략 결정 프롬프트 템플릿"""
        return """당신은 금융 교육 전문가입니다. 사용자 요청에 따라 최적의 교육 전략을 결정해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}

## 교육 전략 결정
다음 형식으로 응답해주세요:

education_type: [교육 유형 - concept/example/application/strategy/glossary 중 하나]
difficulty_level: [난이도 - beginner/intermediate/advanced]
focus_area: [집중 영역 - basic/advanced/strategic/practical]
explanation_style: [설명 스타일 - simple/detailed/comprehensive]
include_examples: [예시 포함 - yes/no]
include_formulas: [공식 포함 - yes/no]
related_topics: [관련 주제 포함 - yes/no]

## 전략 예시

요청: "PER이 뭐야?"
education_type: concept
difficulty_level: beginner
focus_area: basic
explanation_style: simple
include_examples: yes
include_formulas: yes
related_topics: yes

요청: "분산투자 전략 알려줘"
education_type: strategy
difficulty_level: intermediate
focus_area: practical
explanation_style: detailed
include_examples: yes
include_formulas: no
related_topics: yes

요청: "기술적 분석 고급 기법"
education_type: application
difficulty_level: advanced
focus_area: advanced
explanation_style: comprehensive
include_examples: yes
include_formulas: yes
related_topics: yes

## 응답 형식
education_type: [값]
difficulty_level: [값]
focus_area: [값]
explanation_style: [값]
include_examples: [값]
include_formulas: [값]
related_topics: [값]"""
    
    def parse_education_strategy(self, response_text: str) -> Dict[str, Any]:
        """교육 전략 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'education_type':
                        result['education_type'] = value
                    elif key == 'difficulty_level':
                        result['difficulty_level'] = value
                    elif key == 'focus_area':
                        result['focus_area'] = value
                    elif key == 'explanation_style':
                        result['explanation_style'] = value
                    elif key == 'include_examples':
                        result['include_examples'] = value.lower() == 'yes'
                    elif key == 'include_formulas':
                        result['include_formulas'] = value.lower() == 'yes'
                    elif key == 'related_topics':
                        result['related_topics'] = value.lower() == 'yes'
            
            # 기본값 설정
            result.setdefault('education_type', 'concept')
            result.setdefault('difficulty_level', 'beginner')
            result.setdefault('focus_area', 'basic')
            result.setdefault('explanation_style', 'simple')
            result.setdefault('include_examples', True)
            result.setdefault('include_formulas', True)
            result.setdefault('related_topics', True)
            
            return result
            
        except Exception as e:
            print(f"❌ 교육 전략 파싱 오류: {e}")
            return {
                'education_type': 'concept',
                'difficulty_level': 'beginner',
                'focus_area': 'basic',
                'explanation_style': 'simple',
                'include_examples': True,
                'include_formulas': True,
                'related_topics': True
            }
    
    def generate_knowledge_explanation_prompt(self, concept: str, knowledge_data: Dict[str, Any], strategy: Dict[str, Any], user_query: str) -> str:
        """지식 설명 프롬프트 생성"""
        return f"""당신은 {strategy.get('difficulty_level', 'beginner')} 수준의 금융 교육 전문가입니다.
{strategy.get('explanation_style', 'simple')}한 설명을 제공해주세요.

## 사용자 요청
"{user_query}"

## 교육 전략
- 교육 유형: {strategy.get('education_type', 'concept')}
- 난이도: {strategy.get('difficulty_level', 'beginner')}
- 집중 영역: {strategy.get('focus_area', 'basic')}
- 설명 스타일: {strategy.get('explanation_style', 'simple')}
- 예시 포함: {'예' if strategy.get('include_examples', True) else '아니오'}
- 공식 포함: {'예' if strategy.get('include_formulas', True) else '아니오'}
- 관련 주제: {'예' if strategy.get('related_topics', True) else '아니오'}

## 개념 정보
{self._format_knowledge_data(concept, knowledge_data, strategy)}

## 설명 요청사항

### 1. 📚 기본 개념 설명
- **정의**: 명확하고 이해하기 쉬운 정의
- **핵심 포인트**: 중요한 특징 3-5개
- **왜 중요한가**: 투자에서의 중요성

### 2. 💡 구체적 설명
- **작동 원리**: 어떻게 작동하는지 단계별 설명
- **활용 방법**: 실제로 어떻게 사용하는지
- **해석 방법**: 결과를 어떻게 이해해야 하는지

### 3. 📊 실용적 예시
- **실제 사례**: 구체적인 숫자와 함께 설명
- **계산 방법**: 단계별 계산 과정
- **비교 분석**: 다른 지표와의 비교

### 4. 🎯 투자 활용법
- **투자 결정**: 어떤 투자 결정에 도움이 되는지
- **주의사항**: 사용할 때 주의해야 할 점
- **한계점**: 이 지표의 한계와 단점

### 5. 🔗 관련 개념
- **연관 지표**: 함께 보면 좋은 다른 지표들
- **심화 학습**: 더 배우면 좋을 내용
- **실무 활용**: 실제 투자에서의 활용법

## 응답 형식
**중요 작성 규칙**:
1. 마크다운 기호(*, -, #, ### 등)를 사용하지 마세요.
2. 이모지와 들여쓰기로 구조화하세요.
3. {strategy.get('difficulty_level', 'beginner')} 수준에 맞는 용어와 설명을 사용하세요.

## 교육 원칙
⚠️ 복잡한 내용도 쉽게 설명
⚠️ 구체적인 예시와 숫자 사용
⚠️ 실용적이고 현실적인 조언 제공"""
    
    def _format_knowledge_data(self, concept: str, knowledge_data: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """지식 데이터 포맷팅"""
        if not knowledge_data:
            return f"{concept}에 대한 정보가 없습니다."
        
        formatted = []
        formatted.append(f"**{knowledge_data.get('name', concept)}**")
        formatted.append(f"정의: {knowledge_data.get('definition', '정의 없음')}")
        
        if strategy.get('include_formulas', True) and 'formula' in knowledge_data:
            formatted.append(f"공식: {knowledge_data['formula']}")
        
        if 'interpretation' in knowledge_data:
            formatted.append("해석:")
            for key, value in knowledge_data['interpretation'].items():
                formatted.append(f"  • {key}: {value}")
        
        if strategy.get('include_examples', True) and 'examples' in knowledge_data:
            formatted.append("예시:")
            for example in knowledge_data['examples']:
                formatted.append(f"  • {example}")
        
        if knowledge_data.get('usage'):
            formatted.append(f"활용: {knowledge_data['usage']}")
        
        if strategy.get('related_topics', True) and 'related_terms' in knowledge_data:
            formatted.append(f"관련 용어: {', '.join(knowledge_data['related_terms'])}")
        
        return "\n".join(formatted)
    
    def _determine_namespace(self, user_query: str, query_analysis: Dict[str, Any]) -> str:
        """쿼리 분석을 통해 적절한 네임스페이스 결정"""
        
        # LLM 기반 네임스페이스 분류
        classification_prompt = f"""당신은 금융 질문을 분석하여 적절한 지식 카테고리를 결정하는 전문가입니다.

사용자 질문: "{user_query}"

다음 카테고리 중 가장 적합한 것을 선택하세요:

1. **terminology** (용어): 금융 용어의 정의, 개념 설명, "~이 뭐야?", "~란?" 등의 질문
   - 예: "PER이 뭐야?", "ROE란 무엇인가요?", "분산투자의 의미는?", "ETF가 뭐야?"
   - 키워드: 뭐야, 무엇, 의미, 정의, 개념, 란, 이란
   
2. **financial_analysis** (재무분석): 재무제표 분석, 경제 동향, 기업 실적, 재무 지표 해석
   - 예: "재무제표 보는 법", "PER 분석 방법", "경제 동향 분석", "기업 실적 평가"
   - 키워드: 재무제표, 경제 동향, 분석 방법, 실적, 재무 지표
   
3. **youth_policy** (청년정책): 청년 금융 지원, 정부 정책, 청년 혜택, 청년 대상 금융상품
   - 예: "청년 대출 정책", "청년 저축 계좌", "청년 지원금", "청년 우대 금리"
   - 키워드: 청년, 청년대상, 청년지원, 청년우대, 청년정책

**중요**: "청년"이라는 단어가 포함되어 있으면 반드시 **youth_policy**로 분류하세요!

다음 형식으로만 응답하세요:
category: [terminology/financial_analysis/youth_policy]
confidence: [0.0-1.0]
reasoning: [선택한 이유]"""

        try:
            response = self.llm.invoke(classification_prompt)
            response_text = response.content.strip()
            
            # 파싱
            category = "terminology"  # 기본값
            for line in response_text.split('\n'):
                if line.startswith('category:'):
                    category = line.split(':', 1)[1].strip()
                    break
            
            # 유효성 검사
            if category not in self.namespaces:
                category = "terminology"
            
            namespace = self.namespaces[category]
            self.log(f"네임스페이스 결정: {category} -> {namespace}")
            
            return namespace
            
        except Exception as e:
            self.log(f"네임스페이스 결정 오류: {e}, 기본값 사용")
            return self.namespaces["terminology"]
    
    def _get_rag_context(self, user_query: str, namespace: str, top_k: int = 5) -> str:
        """특정 네임스페이스에서 RAG 컨텍스트 가져오기"""
        try:
            self.log(f"RAG 검색 시작: {namespace} (top_k={top_k})")
            
            # Pinecone에서 검색
            context = get_context_for_query(
                query=user_query,
                top_k=top_k,
                namespace=namespace
            )
            
            if context and len(context or '') > 0:
                self.log(f"RAG 컨텍스트 발견: {len(context or '')} 글자")
                return context
            else:
                self.log("RAG 컨텍스트 없음")
                return ""
                
        except Exception as e:
            self.log(f"RAG 검색 오류: {e}")
            return ""
    
    def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """지식 에이전트 처리 (네임스페이스 라우팅)"""
        try:
            self.log(f"지식 교육 시작: {user_query}")
            
            # 1. 네임스페이스 결정
            namespace = self._determine_namespace(user_query, query_analysis)
            
            # 2. RAG 컨텍스트 가져오기
            rag_context = self._get_rag_context(user_query, namespace, top_k=5)
            
            # 3. LLM이 교육 전략 결정
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'knowledge'),
                complexity_level=query_analysis.get('complexity_level', 'simple'),
                required_services=query_analysis.get('required_services', [])
            )
            
            response = self.llm.invoke(prompt)
            strategy = self.parse_education_strategy(response.content.strip())
            
            # 4. 설명 생성
            if rag_context:
                # RAG 컨텍스트 기반 설명
                explanation_prompt = f"""당신은 {strategy.get('difficulty_level', 'beginner')} 수준의 금융 교육 전문가입니다.

## 사용자 질문
"{user_query}"

## 관련 지식 (네임스페이스: {namespace})
{rag_context}

## 교육 전략
- 난이도: {strategy.get('difficulty_level', 'beginner')}
- 설명 스타일: {strategy.get('explanation_style', 'simple')}
- 예시 포함: {'예' if strategy.get('include_examples', True) else '아니오'}

## 응답 요구사항
1. 위의 관련 지식을 바탕으로 사용자의 질문에 답변하세요
2. {strategy.get('explanation_style', 'simple')}한 설명 스타일을 유지하세요
3. 난이도 {strategy.get('difficulty_level', 'beginner')}에 맞게 설명하세요
4. 실제 예시를 포함하여 이해하기 쉽게 설명하세요
5. 투자에 실질적으로 도움이 되는 내용을 제공하세요

명확하고 구체적으로 설명해주세요."""
                
                explanation_response = self.llm.invoke(explanation_prompt)
                explanation_result = explanation_response.content
                
                self.log(f"RAG 기반 지식 교육 완료")
            else:
                # RAG 컨텍스트가 없는 경우 일반 설명
                self.log(f"RAG 컨텍스트 없음 - 기본 설명 생성")
                explanation_prompt = f"""당신은 금융 교육 전문가입니다.

## 사용자 질문
"{user_query}"

## 응답 요구사항
1. 사용자의 질문에 대해 일반적인 금융 지식으로 답변하세요
2. 간단명료하게 설명하세요
3. 가능하면 예시를 들어 설명하세요

명확하고 친절하게 설명해주세요."""
                
                explanation_response = self.llm.invoke(explanation_prompt)
                explanation_result = explanation_response.content
            
            return {
                'success': True,
                'namespace': namespace,
                'rag_context_length': len(rag_context) if rag_context else 0,
                'explanation_result': explanation_result,
                'strategy': strategy
            }
            
        except Exception as e:
            self.log(f"지식 에이전트 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"지식 교육 중 오류: {str(e)}",
                'explanation_result': "지식 설명에 실패했습니다. 다시 시도해주세요."
            }
    
    def _extract_concept(self, query: str) -> str:
        """쿼리에서 개념 추출"""
        # 데이터베이스의 키워드들과 매칭
        for concept in self.knowledge_db.keys():
            if concept in query:
                return concept
        
        # 추가 키워드 매칭
        keyword_mapping = {
            '주가수익비율': 'PER',
            '주가순자산비율': 'PBR', 
            '자기자본이익률': 'ROE',
            '주당순이익': 'EPS',
            '기술적 분석': '기술적분석',
            '차트 분석': '기술적분석',
            '분산 투자': '분산투자'
        }
        
        for keyword, concept in keyword_mapping.items():
            if keyword in query:
                return concept
        
        return "일반"

