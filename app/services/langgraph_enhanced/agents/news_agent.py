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
search_query: [실제 검색에 사용할 쿼리 - 영어로 작성 (예: Samsung Electronics, KOSPI, SK Hynix)]
news_sources: [뉴스 소스 - google/mk/both]
time_range: [시간 범위 - today/week/month]
analysis_depth: [분석 깊이 - summary/detailed/comprehensive]
focus_areas: [집중 영역 - price_impact/fundamental/technical/sentiment]

## 중요: search_query는 반드시 영어로 작성하세요!
- 한국 기업명은 영어로 변환 (예: 삼성전자 → Samsung Electronics, SK하이닉스 → SK Hynix, 현대자동차 → Hyundai Motor)
- 시장/지수명도 영어로 (예: 코스피 → KOSPI, 반도체 → Semiconductor)

## 전략 예시

요청: "삼성전자 뉴스 알려줘"
search_strategy: company
search_query: Samsung Electronics
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
- **반드시 각 뉴스의 정확한 출처(source)와 발행일(published)을 함께 표기하세요**
- 시장에 미치는 영향도 평가 (High/Medium/Low)
- 출처 표기 예시: (출처: Reuters, 2024-05-15)

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
    
    async def process(self, user_query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 에이전트 처리 (async)"""
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
            
            print(f"🔍 [NewsAgent] 생성된 전략:")
            print(f"   - search_strategy: {strategy.get('search_strategy')}")
            print(f"   - search_query: {strategy.get('search_query')}")
            print(f"   - news_sources: {strategy.get('news_sources')}")
            
            # 실제 뉴스 수집 (async)
            news_data = []
            mk_context = ""  # 매일경제 컨텍스트는 별도로 저장
            
            try:
                if strategy['news_sources'] in ['google', 'both']:
                    print(f"📰 [NewsAgent] Google RSS에서 뉴스 수집 시작: {strategy['search_query']}")
                    # async 함수 직접 호출 - 리스트 반환
                    google_news = await news_service.get_comprehensive_news(
                        query=strategy['search_query']
                    )
                    
                    print(f"   ✅ [NewsAgent] Google RSS 결과: {len(google_news) if google_news else 0}개")
                    
                    if google_news and isinstance(google_news, list):
                        news_data.extend(google_news)
                
                if strategy['news_sources'] in ['mk', 'both']:
                    # 매일경제 KG 컨텍스트는 한국어 핵심 키워드 사용
                    # 예: "금리 뉴스 분석해줘" → "금리"
                    korean_keyword = self._extract_korean_keyword(user_query)
                    print(f"   📚 [NewsAgent] 매일경제 KG 검색 키워드: {korean_keyword}")
                    
                    # async 함수 호출 - 문자열 반환
                    mk_context = await news_service.get_analysis_context_from_kg(
                        query=korean_keyword,
                        limit=5
                    )
                
                # 중복 제거 및 정렬
                news_data = self._deduplicate_news(news_data)
                
            except Exception as e:
                self.log(f"뉴스 수집 오류: {e}")
                import traceback
                traceback.print_exc()
                news_data = []
                mk_context = ""
            
            # 뉴스 분석
            if news_data or mk_context:
                analysis_prompt = self.generate_news_analysis_prompt(news_data, strategy, user_query)
                
                # 매일경제 컨텍스트 추가
                if mk_context:
                    analysis_prompt += f"\n\n{mk_context}"
                
                analysis_response = self.llm.invoke(analysis_prompt)
                analysis_result = analysis_response.content
                
                self.log(f"뉴스 분석 완료: {len(news_data or [])}건")
            else:
                analysis_result = "관련 뉴스를 찾을 수 없습니다. 다른 키워드로 검색해보세요."
                self.log("뉴스를 찾을 수 없음")
            
            return {
                'success': True,
                'news_data': news_data,
                'analysis_result': analysis_result,
                'strategy': strategy,
                'mk_context': mk_context
            }
            
        except Exception as e:
            self.log(f"뉴스 에이전트 오류: {e}")
            return {
                'success': False,
                'error': f"뉴스 수집 중 오류: {str(e)}",
                'news_data': [],
                'analysis_result': "뉴스 수집에 실패했습니다."
            }
    
    def _extract_korean_keyword(self, user_query: str) -> str:
        """한국어 쿼리에서 핵심 키워드 추출
        
        예: "삼성전자 뉴스 알려줘" → "삼성전자"
            "금리 뉴스 분석해줘" → "금리"
        """
        # 제거할 불용어
        stopwords = ['뉴스', '알려줘', '분석', '해줘', '관련', '최신', '오늘', '어제']
        
        # 공백으로 분리
        words = user_query.split()
        
        # 불용어 제거
        keywords = [w for w in words if w not in stopwords]
        
        # 키워드가 있으면 첫 번째, 없으면 원본
        return keywords[0] if keywords else user_query
    
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

