"""
풀백 에이전트
실패한 작업에 대한 대안 전략 제공 및 실행
"""

from typing import Dict, Any, List, Optional, Callable
from .base_agent import BaseAgent
import asyncio


class FallbackAgent(BaseAgent):
    """🔄 풀백 에이전트 - 실패한 작업의 대안 전략 실행"""
    
    def __init__(self):
        super().__init__(purpose="fallback")
        self.agent_name = "fallback_agent"
    
    async def execute_with_fallback(self,
                                    primary_func: Callable,
                                    fallback_funcs: List[Callable],
                                    *args,
                                    **kwargs) -> Dict[str, Any]:
        """
        Primary 함수 실행 후 실패 시 순차적으로 풀백 함수 시도
        
        Args:
            primary_func: 1차 실행 함수
            fallback_funcs: 풀백 함수 리스트 (순서대로 시도)
            *args, **kwargs: 함수에 전달할 인자
            
        Returns:
            Dict: {
                'success': bool,
                'data': Any,
                'source': str,  # 성공한 소스 (primary, fallback_1, fallback_2 등)
                'attempts': int,  # 시도 횟수
                'errors': List[str]  # 발생한 에러들
            }
        """
        errors = []
        attempts = 0
        
        # 1차 시도: Primary
        try:
            attempts += 1
            self.log(f"Primary 함수 시도: {primary_func.__name__}")
            
            # async 함수 처리
            if asyncio.iscoroutinefunction(primary_func):
                result = await primary_func(*args, **kwargs)
            else:
                result = primary_func(*args, **kwargs)
            
            if result and self._is_valid_result(result):
                self.log(f"✅ Primary 성공: {primary_func.__name__}")
                return {
                    'success': True,
                    'data': result,
                    'source': 'primary',
                    'attempts': attempts,
                    'errors': []
                }
            else:
                self.log(f"⚠️ Primary 결과 없음: {primary_func.__name__}")
                errors.append(f"Primary returned empty result")
        except Exception as e:
            self.log(f"❌ Primary 실패: {primary_func.__name__} - {e}")
            errors.append(f"Primary error: {str(e)}")
        
        # 2차 시도: Fallback 순차 실행
        for idx, fallback_func in enumerate(fallback_funcs, 1):
            try:
                attempts += 1
                self.log(f"Fallback {idx} 시도: {fallback_func.__name__}")
                
                # async 함수 처리
                if asyncio.iscoroutinefunction(fallback_func):
                    result = await fallback_func(*args, **kwargs)
                else:
                    result = fallback_func(*args, **kwargs)
                
                if result and self._is_valid_result(result):
                    self.log(f"✅ Fallback {idx} 성공: {fallback_func.__name__}")
                    return {
                        'success': True,
                        'data': result,
                        'source': f'fallback_{idx}',
                        'attempts': attempts,
                        'errors': errors
                    }
                else:
                    self.log(f"⚠️ Fallback {idx} 결과 없음: {fallback_func.__name__}")
                    errors.append(f"Fallback {idx} returned empty result")
            except Exception as e:
                self.log(f"❌ Fallback {idx} 실패: {fallback_func.__name__} - {e}")
                errors.append(f"Fallback {idx} error: {str(e)}")
        
        # 모든 시도 실패
        self.log(f"❌ 모든 시도 실패 (Primary + {len(fallback_funcs)}개 Fallback)")
        return {
            'success': False,
            'data': None,
            'source': 'none',
            'attempts': attempts,
            'errors': errors
        }
    
    def _is_valid_result(self, result: Any) -> bool:
        """결과가 유효한지 검증"""
        if result is None:
            return False
        
        # 리스트인 경우
        if isinstance(result, list):
            return len(result) > 0
        
        # 딕셔너리인 경우
        if isinstance(result, dict):
            return len(result) > 0
        
        # 문자열인 경우
        if isinstance(result, str):
            return len(result.strip()) > 0
        
        # 그 외
        return True
    
    async def execute_parallel_with_fallback(self,
                                            funcs: List[Callable],
                                            *args,
                                            **kwargs) -> Dict[str, Any]:
        """
        여러 함수를 병렬로 실행하고, 가장 먼저 성공한 결과 반환
        
        Args:
            funcs: 병렬 실행할 함수 리스트
            *args, **kwargs: 함수에 전달할 인자
            
        Returns:
            Dict: 가장 먼저 성공한 결과
        """
        self.log(f"병렬 풀백 시작: {len(funcs)}개 함수")
        
        # 모든 함수를 비동기 태스크로 변환
        tasks = []
        for func in funcs:
            if asyncio.iscoroutinefunction(func):
                tasks.append(func(*args, **kwargs))
            else:
                # 동기 함수는 비동기로 래핑
                async def wrapper():
                    return func(*args, **kwargs)
                tasks.append(wrapper())
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 첫 번째 유효한 결과 찾기
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                self.log(f"⚠️ 함수 {idx+1} 실패: {result}")
                continue
            
            if result and self._is_valid_result(result):
                self.log(f"✅ 함수 {idx+1} 성공 (병렬)")
                return {
                    'success': True,
                    'data': result,
                    'source': f'parallel_{idx+1}',
                    'attempts': len(funcs),
                    'errors': []
                }
        
        # 모든 함수 실패
        self.log(f"❌ 모든 병렬 함수 실패")
        return {
            'success': False,
            'data': None,
            'source': 'none',
            'attempts': len(funcs),
            'errors': [str(r) for r in results if isinstance(r, Exception)]
        }


class NewsSourceFallback:
    """뉴스 소스 전용 풀백 헬퍼"""
    
    def __init__(self, fallback_agent: FallbackAgent):
        self.fallback_agent = fallback_agent
    
    async def get_news_with_fallback(self,
                                    query: str,
                                    primary_source: str = "google_rss",
                                    limit: int = 5) -> Dict[str, Any]:
        """
        뉴스 수집 with 자동 풀백
        
        Args:
            query: 검색 쿼리
            primary_source: 1차 소스 ("google_rss" or "mk_rss")
            limit: 뉴스 개수
            
        Returns:
            Dict: 뉴스 수집 결과
        """
        from app.services.workflow_components.google_rss_translator import search_google_news
        from app.services.workflow_components.mk_rss_simple import search_mk_news_simple
        from app.services.workflow_components.news_service import news_service
        
        # Primary와 Fallback 정의
        if primary_source == "google_rss":
            primary_func = search_google_news
            fallback_funcs = [
                lambda q, l: search_mk_news_simple(q, l),
                lambda q, l: news_service.get_financial_news(q)
            ]
        else:  # mk_rss
            primary_func = search_mk_news_simple
            fallback_funcs = [
                lambda q, l: search_google_news(q, l),
                lambda q, l: news_service.get_financial_news(q)
            ]
        
        # 풀백 실행
        result = await self.fallback_agent.execute_with_fallback(
            primary_func,
            fallback_funcs,
            query,
            limit
        )
        
        return result
    
    async def get_kg_context_with_fallback(self,
                                          query: str,
                                          limit: int = 3) -> str:
        """
        지식그래프 컨텍스트 with 자동 풀백
        
        Args:
            query: 검색 쿼리
            limit: 기사 개수
            
        Returns:
            str: 컨텍스트 문자열
        """
        from app.services.workflow_components.mk_rss_simple import search_mk_news_simple
        from app.services.workflow_components.google_rss_translator import search_google_news
        
        async def get_mk_context(q: str, l: int) -> str:
            """매일경제 컨텍스트 생성"""
            articles = await search_mk_news_simple(q, l)
            if not articles:
                return ""
            
            context_parts = ["📚 참고 자료 (매일경제 지식그래프):"]
            for i, article in enumerate(articles, 1):
                context_parts.append(f"\n[기사 {i}] {article['title']}")
                if article.get('summary'):
                    context_parts.append(f"요약: {article['summary'][:200]}...")
                context_parts.append(f"출처: {article['link']}")
                context_parts.append(f"날짜: {article['published']}")
            
            return "\n".join(context_parts)
        
        async def get_google_context(q: str, l: int) -> str:
            """Google RSS 컨텍스트 생성"""
            articles = await search_google_news(q, l)
            if not articles:
                return ""
            
            context_parts = ["📰 참고 자료 (Google RSS):"]
            for i, article in enumerate(articles, 1):
                context_parts.append(f"\n[기사 {i}] {article.get('title', '')}")
                if article.get('summary'):
                    context_parts.append(f"요약: {article['summary'][:200]}...")
                context_parts.append(f"출처: {article.get('url', '')}")
            
            return "\n".join(context_parts)
        
        # 풀백 실행
        result = await self.fallback_agent.execute_with_fallback(
            get_mk_context,
            [get_google_context],
            query,
            limit
        )
        
        if result['success']:
            return result['data']
        else:
            return ""


# 전역 인스턴스
_fallback_agent = None
_news_source_fallback = None


def get_fallback_agent() -> FallbackAgent:
    """풀백 에이전트 싱글톤 인스턴스 반환"""
    global _fallback_agent
    if _fallback_agent is None:
        _fallback_agent = FallbackAgent()
    return _fallback_agent


def get_news_source_fallback() -> NewsSourceFallback:
    """뉴스 소스 풀백 헬퍼 싱글톤 인스턴스 반환"""
    global _news_source_fallback
    if _news_source_fallback is None:
        _news_source_fallback = NewsSourceFallback(get_fallback_agent())
    return _news_source_fallback

