"""
뉴스 에이전트
금융 뉴스 수집, 분석, 요약 전문 에이전트
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from app.services.workflow_components import news_service


class NewsAgent(BaseAgent):
    """📰 뉴스 에이전트 - 금융 뉴스 전문가"""
    
    def __init__(self):
        super().__init__(purpose="news")
        self.agent_name = "news_agent"
    
    def get_prompt_template(self) -> str:
        """뉴스 분석 전략 결정 프롬프트 템플릿"""
        return """당신은 금융 뉴스 전문가입니다. 사용자 요청에 따라 최적의 뉴스 수집 및 분석 전략을 결정해주세요.

## 사용자 요청
"{user_query}"

## 쿼리 분석 결과
- 주요 의도: {primary_intent}
- 복잡도: {complexity_level}
- 필요 서비스: {required_services}

## 뉴스 수집 전략 결정
다음 형식으로 응답해주세요:

search_strategy: [검색 전략 - specific/general/market/sector/company 중 하나]
search_query: [실제 검색에 사용할 쿼리]
news_sources: [뉴스 소스 - google/mk/both]
time_range: [시간 범위 - today/week/month]
analysis_depth: [분석 깊이 - summary/detailed/comprehensive]
focus_areas: [집중 영역 - price_impact/fundamental/technical/sentiment]

## 전략 예시

요청: "삼성전자 뉴스 알려줘"
search_strategy: company
search_query: 삼성전자
news_sources: both
time_range: today
analysis_depth: detailed
focus_areas: price_impact,fundamental

요청: "오늘 시장 뉴스"
search_strategy: market
search_query: 오늘 주식시장 동향
news_sources: google
time_range: today
analysis_depth: comprehensive
focus_areas: sentiment,price_impact

요청: "반도체 업종 뉴스"
search_strategy: sector
search_query: 반도체 업종 뉴스
news_sources: both
time_range: week
analysis_depth: detailed
focus_areas: fundamental,technical

## 응답 형식
search_strategy: [값]
search_query: [값]
news_sources: [값]
time_range: [값]
analysis_depth: [값]
focus_areas: [값]"""
    
    def parse_news_strategy(self, response_text: str) -> Dict[str, Any]:
        """뉴스 전략 파싱"""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'search_strategy':
                        result['search_strategy'] = value
                    elif key == 'search_query':
                        result['search_query'] = value
                    elif key == 'news_sources':
                        result['news_sources'] = value
                    elif key == 'time_range':
                        result['time_range'] = value
                    elif key == 'analysis_depth':
                        result['analysis_depth'] = value
                    elif key == 'focus_areas':
                        # 쉼표로 구분된 영역들을 리스트로 변환
                        areas = [a.strip() for a in value.split(',') if a.strip()]
                        result['focus_areas'] = areas
            
            # 기본값 설정
            result.setdefault('search_strategy', 'general')
            result.setdefault('search_query', '금융 뉴스')
            result.setdefault('news_sources', 'both')
            result.setdefault('time_range', 'today')
            result.setdefault('analysis_depth', 'detailed')
            result.setdefault('focus_areas', ['price_impact'])
            
            return result
            
        except Exception as e:
            print(f"❌ 뉴스 전략 파싱 오류: {e}")
            return {
                'search_strategy': 'general',
                'search_query': '금융 뉴스',
                'news_sources': 'both',
                'time_range': 'today',
                'analysis_depth': 'detailed',
                'focus_areas': ['price_impact']
            }
    
    def generate_news_analysis_prompt(self, news_data: List[Dict[str, Any]], strategy: Dict[str, Any], user_query: str) -> str:
        """뉴스 분석 프롬프트 생성"""
        return f"""당신은 전문 금융 뉴스 애널리스트입니다. 수집된 뉴스를 분석하여 사용자에게 최적의 인사이트를 제공해주세요.

## 사용자 요청
"{user_query}"

## 수집 전략
- 검색 전략: {strategy.get('search_strategy', 'general')}
- 분석 깊이: {strategy.get('analysis_depth', 'detailed')}
- 집중 영역: {', '.join(strategy.get('focus_areas', ['price_impact']))}

## 수집된 뉴스 ({len(news_data)}건)
{self._format_news_data(news_data)}

## 분석 요청사항

### 1. 📰 뉴스 요약 및 핵심 포인트
- 가장 중요한 뉴스 3건 선별
- 각 뉴스의 핵심 내용 요약 (2-3줄)
- 시장에 미치는 영향도 평가 (High/Medium/Low)

### 2. 📈 시장 영향 분석
- 주가에 미칠 영향 예상 (상승/하락/중립)
- 영향 정도 및 근거 설명
- 단기/중기/장기 관점에서의 분석

### 3. 💡 투자자 관점
- 투자자들이 주목해야 할 포인트
- 리스크 요소 및 기회 요소
- 추천 행동 방향 (관찰/매수/매도/보유)

### 4. 🔍 추가 모니터링 포인트
- 지속적으로 관찰해야 할 지표나 이벤트
- 관련 종목이나 업종 영향
- 향후 전망 및 시나리오

## 응답 형식
친근하고 이해하기 쉬운 톤으로 작성하되, 전문적인 분석을 제공해주세요.
각 섹션별로 이모지를 사용하여 가독성을 높여주세요.

## 주의사항
- 객관적이고 균형 잡힌 분석 제공
- 과도한 투자 권유 지양
- 개인 투자자의 상황은 고려하지 않았음을 명시"""
    
    def _format_news_data(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 데이터 포맷팅"""
        if not news_data:
            return "수집된 뉴스가 없습니다."
        
        formatted = []
        for i, news in enumerate(news_data[:10], 1):  # 최대 10건만 표시
            title = news.get('title', '제목 없음')
            summary = news.get('summary', '요약 없음')
            source = news.get('source', '출처 불명')
            published = news.get('published', '날짜 불명')
            
            formatted.append(f"""
**{i}. {title}**
- 출처: {source} | 날짜: {published}
- 요약: {summary}
---""")
        
        return "\n".join(formatted)
    
    def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 에이전트 처리"""
        try:
            self.log(f"뉴스 수집 시작: {user_query}")
            
            # LLM이 뉴스 수집 전략 결정
            prompt = self.get_prompt_template().format(
                user_query=user_query,
                primary_intent=query_analysis.get('primary_intent', 'news'),
                complexity_level=query_analysis.get('complexity_level', 'simple'),
                required_services=query_analysis.get('required_services', [])
            )
            
            response = self.llm.invoke(prompt)
            strategy = self.parse_news_strategy(response.content.strip())
            
            # 실제 뉴스 수집
            news_data = []
            try:
                if strategy['news_sources'] in ['google', 'both']:
                    google_news = news_service.get_comprehensive_news(
                        query=strategy['search_query'],
                        limit=10
                    )
                    if google_news and 'news' in google_news:
                        news_data.extend(google_news['news'])
                
                if strategy['news_sources'] in ['mk', 'both']:
                    mk_news = news_service.get_analysis_context_from_kg(
                        query=strategy['search_query'],
                        limit=5
                    )
                    if mk_news:
                        news_data.extend(mk_news)
                
                # 중복 제거 및 정렬
                news_data = self._deduplicate_news(news_data)
                
            except Exception as e:
                self.log(f"뉴스 수집 오류: {e}")
                news_data = []
            
            # 뉴스 분석
            if news_data:
                analysis_prompt = self.generate_news_analysis_prompt(news_data, strategy, user_query)
                analysis_response = self.llm.invoke(analysis_prompt)
                analysis_result = analysis_response.content
                
                self.log(f"뉴스 분석 완료: {len(news_data)}건")
            else:
                analysis_result = "관련 뉴스를 찾을 수 없습니다. 다른 키워드로 검색해보세요."
                self.log("뉴스를 찾을 수 없음")
            
            return {
                'success': True,
                'news_data': news_data,
                'analysis_result': analysis_result,
                'strategy': strategy
            }
            
        except Exception as e:
            self.log(f"뉴스 에이전트 오류: {e}")
            return {
                'success': False,
                'error': f"뉴스 수집 중 오류: {str(e)}",
                'news_data': [],
                'analysis_result': "뉴스 수집에 실패했습니다."
            }
    
    def _deduplicate_news(self, news_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스 중복 제거"""
        seen_titles = set()
        unique_news = []
        
        for news in news_data:
            title = news.get('title', '').strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        # 날짜순 정렬 (최신순)
        unique_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        return unique_news
