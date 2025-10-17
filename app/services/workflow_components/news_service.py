"""뉴스 조회 서비스 (yfinance 우선 + 캐싱 + Google RSS 풀백 + 번역/정규화/중복 제거)"""

import asyncio
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timezone
import yfinance as yf
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.services.workflow_components.data_agent_service import NewsCollector
from app.services.workflow_components.mk_rss_scraper import MKKnowledgeGraphService, search_mk_news
from app.services.workflow_components.google_rss_translator import google_rss_translator, search_google_news
from app.utils.common_utils import CacheManager
from deep_translator import GoogleTranslator
from app.services.langgraph_enhanced.llm_manager import llm_manager
from app.utils.stock_utils import get_company_name_from_symbol
# prompt_manager는 agents/에서 개별 관리


class NewsService:
    """금융 뉴스 조회를 담당하는 서비스 (통합 뉴스 서비스)
    
    뉴스 소스:
    1. yfinance (우선)
    2. Google RSS (실시간, 자동 번역) - 풀백
    3. 매일경제 RSS + Neo4j (임베딩 컨텍스트, 분석용)
    """
    
    def __init__(self):
        self.news_collector = NewsCollector()  # data_agent의 수집기 (폴백용)
        self.mk_kg_service = MKKnowledgeGraphService()  # 매일경제 지식그래프
        self.google_translator = google_rss_translator  # Google RSS 번역
        self.llm = self._initialize_llm()
        # 뉴스 캐시(10분), 네거티브 캐시(30초)
        self.news_cache = CacheManager(default_ttl=600)
        self.negative_cache_ttl = 30
        # 번역기 (필요 시만 사용)
        self._translator: Optional[GoogleTranslator] = None
    
    def _initialize_llm(self):
        """LLM 초기화"""
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                google_api_key=settings.google_api_key
            )
        return None
    
    async def get_financial_news(self, query: str) -> List[Dict[str, Any]]:
        """한국어 금융 뉴스를 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            query: 뉴스 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 한국어 뉴스 리스트
        """
        try:
            print(f"📰 한국어 금융 뉴스 검색: {query}")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = await self.news_collector.collect_news(days_back=1)
            
            # 쿼리와 관련된 기사 필터링
            relevant_articles = []
            for article in articles:
                # 제목이나 내용에 쿼리 키워드가 포함된 경우
                if (query.lower() in article.title.lower() or 
                    (article.content and query.lower() in article.content.lower())):
                    
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score
                    }
                    relevant_articles.append(news_item)
            
            print(f"✅ 관련 뉴스 {len(relevant_articles)}개 발견")
            return relevant_articles[:5]  # 최대 5개 반환
            
        except Exception as e:
            print(f"❌ 한국어 뉴스 조회 중 오류: {e}")
            return []
    
    async def get_latest_market_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최신 한국 시장 뉴스 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 한국어 시장 뉴스 리스트
        """
        try:
            print(f"📈 최신 한국 시장 뉴스 조회 (최대 {limit}개)")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = await self.news_collector.collect_news(days_back=1)
            
            # 시장 관련 키워드로 필터링
            market_keywords = ['시장', '주식', '증시', '코스피', '코스닥', '거래량', '상승', '하락']
            market_articles = []
            
            for article in articles:
                # 시장 관련 키워드가 포함된 기사만 선택
                if any(keyword in article.title.lower() for keyword in market_keywords):
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score
                    }
                    market_articles.append(news_item)
            
            print(f"✅ 시장 뉴스 {len(market_articles)}개 발견")
            return market_articles[:limit]
            
        except Exception as e:
            print(f"❌ 최신 시장 뉴스 조회 중 오류: {e}")
            return []
    
    async def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """특정 종목의 한국어 뉴스 조회 (data_agent의 NewsCollector 사용)
        
        Args:
            symbol: 주식 심볼 (예: "005930.KS")
            limit: 조회할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 한국어 종목 뉴스 리스트
        """
        try:
            # 심볼에서 회사명 추출하여 검색
            company_name = get_company_name_from_symbol(symbol)
            if not company_name:
                # 심볼을 직접 사용
                company_name = symbol.replace(".KS", "")
            
            print(f"📊 {company_name} 관련 한국어 뉴스 검색")
            
            # data_agent의 NewsCollector를 사용해서 한국어 뉴스 수집
            articles = await self.news_collector.collect_news(days_back=3)  # 3일간의 뉴스
            
            # 해당 종목과 관련된 기사 필터링
            stock_articles = []
            for article in articles:
                # 제목이나 내용에 회사명이 포함된 경우
                if (company_name.lower() in article.title.lower() or 
                    (article.content and company_name.lower() in article.content.lower())):
                    
                    news_item = {
                        'title': article.title,
                        'summary': article.content or '',
                        'url': article.link,
                        'published': article.published,
                        'source': 'korean_rss',
                        'is_financial': article.is_financial,
                        'topic_score': article.topic_score,
                        'symbol': symbol,
                        'company_name': company_name
                    }
                    stock_articles.append(news_item)
            
            print(f"✅ {company_name} 관련 뉴스 {len(stock_articles)}개 발견")
            return stock_articles[:limit]
            
        except Exception as e:
            print(f"❌ 종목 뉴스 조회 중 오류: {e}")
            return []
    
    def generate_news_analysis(self, 
                               query: str, 
                               news_data: List[Dict[str, Any]]) -> str:
        """✨ LLM 기반 동적 프롬프팅 뉴스 분석 (새로운 메서드)
        
        Args:
            query: 사용자 질문
            news_data: 뉴스 데이터 리스트
            
        Returns:
            str: AI 생성 뉴스 분석 결과
        """
        if not self.llm or not news_data:
            # LLM이 없거나 뉴스가 없으면 단순 나열
            return self._format_news_simple(news_data)
        
        try:
            # ✨ 동적 프롬프트 생성
            messages = prompt_manager.generate_news_prompt(
                news_data=news_data,
                user_query=query
            )
            
            # LLM 호출
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"❌ AI 뉴스 분석 생성 오류: {e}")
            # 오류 시 단순 나열로 폴백
            return self._format_news_simple(news_data)
    
    def _format_news_simple(self, news_data: List[Dict[str, Any]]) -> str:
        """뉴스 단순 포맷팅 (폴백용)"""
        if not news_data:
            return "관련 뉴스를 찾을 수 없습니다."
        
        result = f"📰 총 {len(news_data)}개의 뉴스:\n\n"
        for i, news in enumerate(news_data, 1):
            result += f"{i}. {news['title']}\n"
            result += f"   {news.get('summary', '')[:100]}...\n"
            result += f"   🔗 {news['url']}\n\n"
        
        return result
    
    async def get_mk_news_with_embedding(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """✨ 매일경제 지식그래프 컨텍스트 검색 (분석/판단용)
        
        ⚠️ 용도: 뉴스 요청이 아닌, 분석/판단 시 컨텍스트로만 사용
        
        사용 사례:
        - "삼성전자 투자 분석해줘" → 매일경제 KG에서 관련 기사 컨텍스트 제공
        - "최근 반도체 시장 전망은?" → 매일경제 KG에서 배경 지식 제공
        
        Args:
            query: 검색 쿼리
            category: 뉴스 카테고리 (economy, politics, securities, international, headlines)
            limit: 반환할 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 임베딩 기반 검색된 컨텍스트 (분석용)
        """
        try:
            print(f"📚 매일경제 KG 컨텍스트 검색 (분석용): {query}")
            
            # 매일경제 지식그래프에서 검색 (타임아웃 6s)
            import asyncio
            try:
                mk_results = await asyncio.wait_for(
                    self.mk_kg_service.search_news(query, category, limit),
                    timeout=6.0
                )
            except asyncio.TimeoutError:
                print("⏱️ 매일경제 KG 검색 타임아웃(6s)")
                mk_results = []
            
            # 결과 포맷팅
            formatted_results = []
            for article in mk_results:
                news_item = {
                    'title': article['title'],
                    'summary': article['summary'] or '',
                    'content': article.get('content', ''),  # 분석용 전체 내용
                    'url': article['link'],
                    'published': article['published'],
                    'source': 'mk_knowledge_graph',
                    'category': article['category'],
                    'similarity_score': article['similarity'],
                    'is_financial': self._is_financial_content(article['title']),
                    'topic_score': article['similarity']
                }
                formatted_results.append(news_item)
            
            print(f"✅ 매일경제 KG 컨텍스트 {len(formatted_results)}개 발견 (분석용)")
            return formatted_results
            
        except Exception as e:
            print(f"❌ 매일경제 KG 컨텍스트 검색 중 오류: {e}")
            return []
    
    async def get_analysis_context_from_kg(self, query: str, limit: int = 3) -> str:
        """분석/판단을 위한 매일경제 지식그래프 컨텍스트 생성
        
        ⚠️ 용도: 뉴스가 아닌, 분석 시 배경 지식 제공 (KG 역할)
        ✨ FallbackAgent 사용
        
        Args:
            query: 분석 대상 쿼리 (한국어)
            limit: 참고할 기사 개수
            
        Returns:
            str: LLM에 제공할 컨텍스트 문자열
        """
        try:
            from app.services.langgraph_enhanced.agents import get_news_source_fallback
            
            print(f"📚 매일경제 KG 컨텍스트 검색 (분석용, FallbackAgent): {query}")
            
            # FallbackAgent를 통한 자동 풀백 실행
            fallback_helper = get_news_source_fallback()
            context = await fallback_helper.get_kg_context_with_fallback(query, limit)
            
            return context
            
        except Exception as e:
            print(f"❌ 매일경제 KG 컨텍스트 생성 중 치명적 오류: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _is_financial_content(self, text: str) -> bool:
        """텍스트가 금융 관련인지 판단"""
        finance_keywords = [
            '주식', '증권', '금융', '은행', '투자', '경제', '시장', '주가',
            'PER', 'PBR', '배당', '상장', 'IPO', 'M&A', '인수', '합병',
            '기준금리', '인플레이션', 'GDP', '환율', '달러', '엔화',
            '삼성전자', 'SK하이닉스', 'LG전자', '현대차', '기아',
            '상승', '하락', '급등', '급락', '거래량', '시가총액'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in finance_keywords)
    
    async def get_today_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """오늘 하루의 시장 뉴스 종합 분석용
        
        Args:
            limit: 가져올 뉴스 개수
            
        Returns:
            List[Dict[str, Any]]: 오늘의 주요 시장 뉴스 리스트
        """
        try:
            print(f"📈 오늘 하루 시장 뉴스 수집 ({limit}개)")
            
            # 다양한 키워드로 뉴스 수집
            market_keywords = [
                "stock market", "korean market", "KOSPI", "KOSDAQ",
                "economy", "finance", "investment", "trading",
                "Samsung", "LG", "SK", "Hyundai", "KIA",
                "semiconductor", "AI", "technology"
            ]
            
            all_news = []
            for keyword in market_keywords[:5]:  # 상위 5개 키워드만 사용
                try:
                    keyword_news = await search_google_news(keyword, limit=3)
                    all_news.extend(keyword_news)
                    if len(all_news) >= limit:
                        break
                except Exception as e:
                    print(f"   ⚠️ 키워드 '{keyword}' 뉴스 수집 실패: {e}")
                    continue
            
            # 중복 제거 및 정렬
            unique_news = self._remove_duplicates(all_news)
            sorted_news = self._sort_news_by_relevance(unique_news, "오늘 하루 시장 뉴스")
            
            print(f"✅ 오늘 하루 시장 뉴스 수집 완료: {len(sorted_news)}개")
            return sorted_news[:limit]
            
        except Exception as e:
            print(f"❌ 오늘 하루 시장 뉴스 수집 중 오류: {e}")
            return []

    async def get_comprehensive_news(self, 
                                    query: str, 
                                    use_google_rss: bool = True,
                                    translate: bool = True,
                                    korean_query: str = None) -> List[Dict[str, Any]]:
        """✨ 종합 뉴스 검색 (병렬 수집 + .KS는 KG/RSS 우선 + 무가정)
        - yfinance / Neo4j KG / Google RSS를 병렬 실행하고 제한시간 내 결과 선택
        - 한국(.KS) 종목은 KG→RSS→yfinance 우선, 그 외는 yfinance→RSS→KG
        - 뉴스가 없으면 가정/추정 생성 없이 빈 결과 반환
        """
        try:
            from app.services.langgraph_enhanced.agents import get_news_source_fallback
            print(f"📰 종합 뉴스 검색 시작: {query}")
            overall_start = datetime.now()
            
            # 특별 케이스
            if query == "오늘 하루 시장 뉴스":
                return await self.get_today_market_news(limit=10)
            
            # 심볼 추정으로 KR 여부 판단
            symbol_hint = self._maybe_extract_symbol(query)
            is_kr = bool(symbol_hint and symbol_hint.endswith('.KS'))
            
            # 준비: 작업 정의
            async def run_yf():
                yf_key = self._make_cache_key("yf", query)
                cached = self.news_cache.get(yf_key)
                if cached is not None:
                    print(f"📦 yfinance 캐시 HIT: {len(cached)}개")
                    return cached
                _t0 = datetime.now()
                data = await self._try_yfinance_news(query, limit=8, translate=translate)
                print(f"⏱ yfinance 소요: {(datetime.now()-_t0).total_seconds()*1000:.1f}ms")
                if data:
                    self.news_cache.set(yf_key, data, ttl=600)
                else:
                    self.news_cache.set(yf_key, [], ttl=self.negative_cache_ttl)
                return data
            
            async def run_kg():
                try:
                    _t0 = datetime.now()
                    _data = await asyncio.wait_for(self.get_mk_news_with_embedding(query, limit=8), timeout=6.0)
                    print(f"⏱ KG 소요: {(datetime.now()-_t0).total_seconds()*1000:.1f}ms")
                    return _data
                except Exception as _e:
                    print(f"⚠️ KG 실패/타임아웃: {_e}")
                    return []
            
            async def run_rss():
                if not use_google_rss:
                    return []
                try:
                    fallback_helper = get_news_source_fallback()
                    _t0 = datetime.now()
                    result = await asyncio.wait_for(
                        fallback_helper.get_news_with_fallback(query=query, primary_source="google_rss", limit=8),
                        timeout=6.0
                    )
                    print(f"⏱ RSS 소요: {(datetime.now()-_t0).total_seconds()*1000:.1f}ms")
                    return result['data'] if result.get('success') else []
                except Exception as _e:
                    print(f"⚠️ RSS 실패/타임아웃: {_e}")
                    return []
            
            # 병렬 실행
            tasks = [run_yf(), run_kg(), run_rss()]
            yf_news, kg_news, rss_news = await asyncio.gather(*tasks, return_exceptions=False)
            
            # 선택 우선순위
            candidates = []
            if is_kr:
                candidates = [kg_news, rss_news, yf_news]
            else:
                candidates = [yf_news, rss_news, kg_news]
            
            # 첫 비어있지 않은 후보 선택
            for cand in candidates:
                if cand:
                    selected = cand
                    break
            else:
                selected = []
            
            # 중복 제거 및 정렬
            unique_news = self._remove_duplicates(selected)
            sorted_news = self._sort_news_by_relevance(unique_news, query)
            
            elapsed = (datetime.now() - overall_start).total_seconds() * 1000
            print(f"✅ 실시간 뉴스 검색 결과: {len(sorted_news)}개 (중복 제거 후) | {elapsed:.1f}ms | KR={is_kr}")
            return sorted_news[:10]
        except Exception as e:
            print(f"❌ 뉴스 검색 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _try_yfinance_news(self, query: str, limit: int = 8, translate: bool = True) -> List[Dict[str, Any]]:
        """yfinance 뉴스 시도(티커 추정 → 뉴스 수집 → 정규화/번역/정렬)"""
        symbol = self._maybe_extract_symbol(query)
        if not symbol:
            return []
        try:
            print(f"🔎 yfinance 뉴스 시도: symbol={symbol}")
            ticker = yf.Ticker(symbol)

            # 네트워크 지연 방지를 위해 executor + 타임아웃 적용
            loop = asyncio.get_event_loop()
            try:
                items = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: getattr(ticker, "news", None)),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                print("⏱️ yfinance 뉴스 조회 타임아웃(5s)")
                items = None

            items = items or []
            if not items:
                return []
            normalized: List[Dict[str, Any]] = []
            for it in items[:limit]:
                title = it.get("title", "").strip()
                link = it.get("link") or it.get("url") or ""
                pub_ts = it.get("providerPublishTime") or it.get("provider_publish_time")
                if isinstance(pub_ts, (int, float)):
                    published = datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat()
                else:
                    published = datetime.now(timezone.utc).isoformat()
                summary = it.get("summary", "")
                news_item = {
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published": published,
                    "source": "yfinance",
                    "language": "en",
                    "translated": False,
                    "symbol": symbol
                }
                normalized.append(news_item)
            # 번역(옵션)
            if translate and normalized:
                await self._ensure_translator()
                # 타이틀은 반드시 번역, 요약은 선택적(시간 단축)
                async def _tr_title(n: Dict[str, Any]):
                    n["title_en"] = n.get("title", "")
                    if self._translator and n["title_en"]:
                        try:
                            n["title"] = await asyncio.wait_for(
                                self._translate_text(n["title_en"]), timeout=3.0
                            )
                        except Exception:
                            n["title"] = n["title_en"]
                    else:
                        n["title"] = n["title_en"]
                    n["translated"] = True
                    n["language"] = "ko"

                async def _tr_summary(n: Dict[str, Any]):
                    n["summary_en"] = n.get("summary", "")
                    if self._translator and n["summary_en"]:
                        try:
                            n["summary"] = await asyncio.wait_for(
                                self._translate_text(n["summary_en"][:400]), timeout=3.0
                            )
                        except Exception:
                            n["summary"] = n["summary_en"]

                # 병렬 번역(타이틀 필수, 요약은 베스트Effort)
                await asyncio.gather(*[_tr_title(n) for n in normalized], return_exceptions=True)
                await asyncio.gather(*[_tr_summary(n) for n in normalized], return_exceptions=True)
            return normalized
        except Exception as e:
            print(f"❌ yfinance 뉴스 오류: {e}")
            return []

    async def _ensure_translator(self):
        if self._translator is None:
            try:
                self._translator = GoogleTranslator(source='auto', target='ko')
            except Exception:
                self._translator = None

    async def _translate_text(self, text: str) -> str:
        """번역 비동기 헬퍼(run_in_executor)"""
        if not text:
            return text
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._translator.translate, text)
        except Exception:
            return text

    def _maybe_extract_symbol(self, text: str) -> Optional[str]:
        """심볼 추정: 규칙 기반 → 캐시 → LLM 폴백(데이터 에이전트 방식 차용)"""
        t = (text or "").strip()
        # 한국: 6자리.KS
        if re.match(r"^\d{6}\.KS$", t):
            return t
        # 미국: 대문자/숫자/.-/^ 최대 10자
        if re.match(r"^[A-Z0-9\.^\-]{1,10}$", t):
            return t
        # 텍스트에서 심볼 추출 시도
        try:
            from app.utils.stock_utils import extract_symbol_from_query
            symbol = extract_symbol_from_query(t)
            if symbol:
                return symbol
        except Exception:
            return None
        # 캐시 확인
        key = self._make_cache_key("symres", t)
        cached = self.news_cache.get(key)
        if cached is not None:
            return cached or None
        # LLM 폴백으로 심볼 해석(데이터 에이전트 방식의 규칙을 프롬프트에 포함)
        try:
            resolved = self._resolve_symbol_with_llm(t)
            # 결과 캐시(양/음)
            self.news_cache.set(key, resolved or "", ttl=24 * 3600 if resolved else 300)
            return resolved
        except Exception:
            # 음수 캐시(5분)
            self.news_cache.set(key, "", ttl=300)
            return None

    def _resolve_symbol_with_llm(self, query_text: str) -> Optional[str]:
        """LLM을 사용해 회사명/자유 질의를 Yahoo Finance 티커로 매핑
        - 한국: 6자리 + .KS (예: 삼성전자 → 005930.KS)
        - 미국: 표준 티커 (AAPL, TSLA 등)
        - 유럽: 거래소 접미사 (예: MC.PA, BMW.DE)
        - 출력 형식: data_query: <TICKER> 한 줄만
        """
        prompt = f"""
당신은 금융 데이터 전문가입니다. 아래 질의를 Yahoo Finance에서 사용하는 정확한 티커로 변환하세요.

규칙:
- 한국 주식: 6자리 코드 + .KS (삼성전자→005930.KS, 네이버→035420.KS)
- 미국 주식: 표준 티커 (테슬라→TSLA, 애플→AAPL, 디즈니→DIS)
- 유럽/기타: 거래소 접미사 (LVMH→MC.PA, BMW→BMW.DE)
- 불명확하면 가장 가능성 높은 단일 티커를 제시

질의: "{query_text}"

정확히 아래 한 줄만 반환:
data_query: <TICKER>
"""
        llm = llm_manager.get_llm(purpose="classification")
        text = llm_manager.invoke_with_cache(llm, prompt, purpose="classification")
        # 파싱
        try:
            for line in (text or "").splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    if k.strip().lower() == "data_query":
                        ticker = v.strip()
                        # 간단 유효성 검사
                        if re.match(r"^\d{6}\.KS$", ticker) or re.match(r"^[A-Z][A-Z0-9\.^\-]{0,9}$", ticker):
                            return ticker
                        return ticker  # 느슨 허용(추가 검증은 downstream)
        except Exception:
            pass
        return None

    def _make_cache_key(self, source: str, query: str) -> str:
        q = (query or "").strip().lower()
        q = re.sub(r"\s+", " ", q)
        return f"news:{source}:{q}"
    
    def _remove_duplicates(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 뉴스 제거 (URL + 제목 유사도 기반)"""
        seen_urls = set()
        seen_titles = []
        unique_news = []
        
        for news in news_list:
            url = news.get('url', '')
            title = news.get('title', '')
            
            # URL 중복 체크
            if url and url in seen_urls:
                continue
            
            # 제목 유사도 체크 (간단한 방법)
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_title_similarity(title, seen_title) > 0.9:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(url)
                seen_titles.append(title)
                unique_news.append(news)
        
        return unique_news
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """제목 유사도 계산 (간단한 Jaccard 유사도)"""
        if not title1 or not title2:
            return 0.0
        
        # 단어 집합으로 변환
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        # Jaccard 유사도
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _sort_news_by_relevance(self, 
                                news_list: List[Dict[str, Any]], 
                                query: str) -> List[Dict[str, Any]]:
        """뉴스를 관련도 + 최신순으로 정렬"""
        import datetime
        
        def calculate_score(news: Dict[str, Any]) -> float:
            """뉴스 점수 계산"""
            score = 0.0
            
            # 1. 관련도 점수 (similarity_score 또는 topic_score)
            similarity = news.get('similarity_score', news.get('topic_score', 0.5))
            score += similarity * 0.7
            
            # 2. 최신성 점수 (24시간 이내 +0.3, 48시간 이내 +0.2, 그 외 +0.1)
            try:
                published = news.get('published', '')
                if published:
                    pub_date = datetime.datetime.fromisoformat(published.replace('Z', '+00:00'))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    hours_diff = (now - pub_date).total_seconds() / 3600
                    
                    if hours_diff < 24:
                        score += 0.3
                    elif hours_diff < 48:
                        score += 0.2
                    else:
                        score += 0.1
            except:
                score += 0.1
            
            return score
        
        # 점수 기준 정렬
        return sorted(news_list, key=calculate_score, reverse=True)
    
    async def update_mk_knowledge_base(self, days_back: int = 7) -> Dict[str, Any]:
        """매일경제 지식베이스 업데이트"""
        try:
            print(f"🔄 매일경제 지식베이스 업데이트 시작 (최근 {days_back}일)")
            
            result = await self.mk_kg_service.update_knowledge_graph(days_back)
            
            if result.get('status') == 'success':
                print(f"✅ 지식베이스 업데이트 완료: {result['articles_collected']}개 기사")
            else:
                print(f"❌ 지식베이스 업데이트 실패: {result.get('error', '알 수 없는 오류')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 지식베이스 업데이트 중 오류: {e}")
            return {"status": "error", "error": str(e)}


# 전역 서비스 인스턴스
news_service = NewsService()
