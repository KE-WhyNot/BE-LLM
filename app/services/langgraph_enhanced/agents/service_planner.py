"""
서비스 전략 계획 에이전트
여러 서비스를 병렬로 실행할지, 순차로 실행할지 결정
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ServicePlannerAgent(BaseAgent):
    """📋 서비스 전략 계획 에이전트"""
    
    def __init__(self):
        super().__init__(purpose="planning")
        self.agent_name = "service_planner"
    
    def get_prompt_template(self) -> str:
        """서비스 전략 계획 프롬프트 템플릿"""
        return """당신은 금융 챗봇의 서비스 실행 전략을 계획하는 전문가입니다.

## 사용자 질문
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}
- 신뢰도: {confidence}

## 실행 전략 결정

다음을 고려하여 최적의 실행 전략을 계획하세요:

1. **병렬 실행 가능성**
   - 독립적인 서비스들은 동시 실행 가능 (data + news)
   - 의존성 있는 서비스는 순차 실행 필요 (data → analysis)

2. **실행 순서**
   - 데이터 조회가 필요한 경우 먼저 실행
   - 분석/뉴스/지식은 독립적으로 병렬 실행 가능

3. **최적화 전략**
   - simple 쿼리: 최소한의 서비스만 실행
   - moderate 쿼리: 필요한 서비스만 선택적 실행
   - complex 쿼리: 다중 소스 통합을 위해 병렬 실행

## 응답 형식

execution_strategy: [parallel/sequential/hybrid]
parallel_groups: [[서비스1, 서비스2], [서비스3]]
execution_order: [단계1, 단계2, 단계3]
estimated_time: [예상 소요 시간 (초)]
reasoning: [전략 선택 근거]
optimization_tips: [최적화 팁]

## 예시

### 예시 1: 단순 데이터 조회
질문: "삼성전자 주가 알려줘"
execution_strategy: sequential
parallel_groups: [[data]]
execution_order: [data_agent, response_agent]
estimated_time: 1.0
reasoning: 단순 데이터 조회는 병렬화 불필요
optimization_tips: 캐시 활용 가능

### 예시 2: 투자 분석 요청 (분석 + 뉴스 필수)
질문: "네이버 지금 투자해도 될까"
execution_strategy: hybrid
parallel_groups: [[data], [analysis, news]]
execution_order: [data_agent, parallel(analysis_agent+news_agent), response_agent]
estimated_time: 4.0
reasoning: 투자 판단에는 분석과 최신 뉴스가 필수적이므로 병렬 실행
optimization_tips: 분석과 뉴스를 동시에 가져와 빠른 응답

### 예시 3: 복합 분석 요청
질문: "네이버 분석과 최근 뉴스 알려줘"
execution_strategy: hybrid
parallel_groups: [[data], [news, knowledge]]
execution_order: [data_agent, parallel(news_agent+knowledge_agent), analysis_agent, response_agent]
estimated_time: 3.5
reasoning: 데이터 조회 후, 뉴스와 지식은 독립적이므로 병렬 실행
optimization_tips: 뉴스 번역 시간 고려

### 예시 4: 차트/그래프 요청
질문: "테슬라 그래프로 보여줘"
execution_strategy: sequential
parallel_groups: [[visualization]]
execution_order: [visualization_agent, response_agent]
estimated_time: 2.5
reasoning: 차트 생성은 단일 서비스로 처리 가능
optimization_tips: 기간 지정 시 더 빠른 로딩

### 예시 5: 지식 교육
질문: "PER이 뭐야?"
execution_strategy: sequential
parallel_groups: [[knowledge]]
execution_order: [knowledge_agent, response_agent]
estimated_time: 2.0
reasoning: 단일 지식 검색은 순차 실행으로 충분
optimization_tips: RAG 캐시 활용

### 예시 6: 종합 분석
질문: "삼성전자 투자 분석하고 관련 뉴스와 재무제표 용어 설명해줘"
execution_strategy: hybrid
parallel_groups: [[data], [news, knowledge], [analysis]]
execution_order: [data_agent, parallel(news_agent+knowledge_agent), analysis_agent, response_agent]
estimated_time: 5.0
reasoning: 데이터 조회 후 뉴스/지식 병렬 수집, 이후 통합 분석
optimization_tips: 모든 소스 통합으로 풍부한 답변

### 예시 7: 일반 인사
질문: "안녕하세요"
execution_strategy: sequential
parallel_groups: []
execution_order: [response_agent]
estimated_time: 0.5
reasoning: 단순 인사말에는 별도의 서비스 실행이 필요하지 않습니다.
optimization_tips: 바로 응답 에이전트로 처리

## 응답 생성
다음 형식으로 응답하세요:

execution_strategy: [값]
parallel_groups: [값]
execution_order: [값]
estimated_time: [값]
reasoning: [값]
optimization_tips: [값]"""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """전략 응답 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {
                'execution_strategy': 'sequential',
                'parallel_groups': [],
                'execution_order': [],
                'estimated_time': 1.0,
                'reasoning': '',
                'optimization_tips': ''
            }
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'execution_strategy':
                        result['execution_strategy'] = value
                    elif key == 'parallel_groups':
                        # 파싱: [[service1, service2], [service3]]
                        result['parallel_groups'] = self._parse_parallel_groups(value)
                    elif key == 'execution_order':
                        # 파싱: [step1, step2, step3]
                        result['execution_order'] = self._parse_list(value)
                    elif key == 'estimated_time':
                        try:
                            result['estimated_time'] = float(value)
                        except:
                            result['estimated_time'] = 1.0
                    elif key == 'reasoning':
                        result['reasoning'] = value
                    elif key == 'optimization_tips':
                        result['optimization_tips'] = value
            
            return result
            
        except Exception as e:
            print(f"❌ 전략 파싱 오류: {e}")
            # 기본 전략 반환
            return {
                'execution_strategy': 'sequential',
                'parallel_groups': [],
                'execution_order': ['response_agent'],
                'estimated_time': 1.0,
                'reasoning': '파싱 실패, 기본 전략 사용',
                'optimization_tips': ''
            }
    
    def _parse_parallel_groups(self, value: str) -> List[List[str]]:
        """병렬 그룹 파싱"""
        try:
            # [[service1, service2], [service3]] 형식 파싱
            import re
            groups = []
            
            # 대괄호로 묶인 그룹들 추출
            group_pattern = r'\[([^\[\]]+)\]'
            matches = re.findall(group_pattern, value)
            
            for match in matches:
                services = [s.strip() for s in match.split(',')]
                if services and services[0]:  # 빈 그룹 제외
                    groups.append(services)
            
            return groups
        except:
            return []
    
    def _parse_list(self, value: str) -> List[str]:
        """리스트 파싱"""
        try:
            # [item1, item2, item3] 형식 파싱
            value = value.strip('[]')
            items = [item.strip() for item in value.split(',')]
            return [item for item in items if item]
        except:
            return []
    
    def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """서비스 전략 계획"""
        try:
            # 프롬프트 생성
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'general'),
                complexity_level=query_analysis.get('complexity', 'simple'),
                required_services=query_analysis.get('required_services', 'none'),
                confidence=query_analysis.get('confidence', 0.5)
            )
            
            # LLM 호출
            response = self.llm.invoke(prompt)
            
            # 응답 파싱
            strategy = self.parse_response(response.content)
            
            print(f"📋 서비스 전략 계획 완료:")
            print(f"   전략: {strategy['execution_strategy']}")
            print(f"   병렬 그룹: {strategy['parallel_groups']}")
            print(f"   예상 시간: {strategy['estimated_time']}초")
            print(f"   근거: {strategy['reasoning']}")
            
            return {
                'success': True,
                'strategy': strategy,
                'agent_name': self.agent_name
            }
            
        except Exception as e:
            print(f"❌ 서비스 전략 계획 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_name': self.agent_name,
                'strategy': {
                    'execution_strategy': 'sequential',
                    'parallel_groups': [],
                    'execution_order': ['response_agent'],
                    'estimated_time': 1.0,
                    'reasoning': f'오류 발생: {str(e)}',
                    'optimization_tips': ''
                }
            }

