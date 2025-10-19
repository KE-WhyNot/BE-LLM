"""
외부 API 서비스

역할: yfinance, Yahoo Finance RSS 등 외부 API 호출을 중앙화
"""

from typing import List, Dict, Any
import yfinance as yf
from datetime import datetime, timedelta
from app.utils.stock_utils import extract_symbols_for_news
from app.utils.common_utils import CacheManager


class ExternalAPIService:
    """외부 금융 API 호출 서비스"""
    
    def __init__(self):
        # 주가 데이터 캐싱 (1분 TTL)
        self.stock_cache = CacheManager(default_ttl=60)
        # 뉴스 데이터 캐싱 (10분 TTL)
        self.news_cache = CacheManager(default_ttl=600)
    
    async def get_stock_data(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """
        yfinance API를 통한 주식 데이터 조회 (캐싱 적용)
        
        Args:
            symbol: 주식 심볼 (예: "005930.KS")
            period: 조회 기간 (기본: "1mo")
            
        Returns:
            Dict: 주식 데이터 또는 에러 메시지
        """
        # 캐시 키 생성
        cache_key = f"stock_{symbol}_{period}"
        
        # 캐시에서 확인
        cached_data = self.stock_cache.get(cache_key)
        if cached_data:
            print(f"📦 캐시에서 주가 데이터 반환: {symbol}")
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            # 비동기로 yfinance 호출
            import asyncio
            hist = await asyncio.to_thread(ticker.history, period=period)
            info = await asyncio.to_thread(lambda: ticker.info)
            
            if hist.empty:
                return {"error": f"{symbol}에 대한 데이터를 찾을 수 없습니다."}
            
            # 최신 데이터
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # 가격 변화 계산
            price_change = latest['Close'] - previous['Close']
            price_change_percent = (price_change / previous['Close']) * 100
            
            # PER 처리 (trailingPE 없으면 forwardPE 사용)
            pe_ratio = info.get('trailingPE', None)
            if pe_ratio is None or pe_ratio == 'N/A':
                pe_ratio = info.get('forwardPE', None)
                if pe_ratio is not None:
                    pe_ratio = round(pe_ratio, 2)
                else:
                    pe_ratio = 'N/A'
            else:
                pe_ratio = round(pe_ratio, 2)
            
            # PBR 처리 (priceToBook 없으면 계산)
            pbr = info.get('priceToBook', None)
            if pbr is None or pbr == 'N/A':
                # PBR 계산: 주가 / (주주지분 / 발행주식수)
                try:
                    total_debt = info.get('totalDebt', 0)
                    debt_to_equity = info.get('debtToEquity', 0)
                    shares_outstanding = info.get('sharesOutstanding', 0)
                    current_price = latest['Close']
                    
                    if total_debt and debt_to_equity and shares_outstanding and current_price:
                        # 주주지분 = 총부채 / 부채비율
                        total_equity = total_debt / debt_to_equity
                        # 주당순자산 = 주주지분 / 발행주식수
                        book_value_per_share = total_equity / shares_outstanding
                        # PBR = 주가 / 주당순자산
                        pbr = current_price / book_value_per_share
                        pbr = round(pbr, 2)
                        print(f"📊 PBR 계산: {current_price} / {book_value_per_share:.2f} = {pbr}")
                    else:
                        pbr = 'N/A'
                except Exception as e:
                    print(f"⚠️ PBR 계산 실패: {e}")
                    pbr = 'N/A'
            else:
                pbr = round(pbr, 2)
            
            # ROE 처리 (백분율로 변환)
            roe = info.get('returnOnEquity', None)
            if roe and isinstance(roe, (int, float)):
                roe = round(roe * 100, 2)  # 소수를 퍼센트로 변환
            else:
                roe = 'Unknown'
            
            # 부채비율 처리
            debt_to_equity = info.get('debtToEquity', 'Unknown')
            
            # EPS 처리
            eps = info.get('trailingEps', 'Unknown')
            
            # 통화 정보 (currency)
            currency = info.get('currency', 'KRW')  # 기본값: KRW
            currency_symbol = self._get_currency_symbol(currency)
            
            data = {
                "symbol": symbol,
                "current_price": round(latest['Close'], 2),
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "volume": int(latest['Volume']),
                "high": round(latest['High'], 2),
                "low": round(latest['Low'], 2),
                "open": round(latest['Open'], 2),
                "company_name": info.get('longName', symbol),
                "sector": info.get('sector', 'Unknown'),
                "market_cap": info.get('marketCap', 'Unknown'),
                "pe_ratio": pe_ratio,
                "pbr": pbr,
                "roe": roe,
                "debt_to_equity": debt_to_equity,
                "eps": eps,
                "dividend_yield": info.get('dividendYield', 'Unknown'),
                "52week_high": info.get('fiftyTwoWeekHigh', 'Unknown'),
                "52week_low": info.get('fiftyTwoWeekLow', 'Unknown'),
                "currency": currency,  # 통화 코드 (USD, KRW 등)
                "currency_symbol": currency_symbol,  # 통화 심볼 ($, ₩ 등)
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')  # 분까지만 표시
            }
            
            # 캐시에 저장
            self.stock_cache.set(cache_key, data)
            print(f"💾 주가 데이터 캐시 저장: {symbol}")
            
            return data
        except Exception as e:
            return {"error": f"데이터 가져오기 실패: {str(e)}"}
    
    def _get_currency_symbol(self, currency: str) -> str:
        """통화 코드를 심볼로 변환
        
        Args:
            currency: 통화 코드 (USD, KRW, EUR 등)
            
        Returns:
            str: 통화 심볼 ($, ₩, € 등)
        """
        currency_map = {
            'USD': '$',
            'KRW': '₩',
            'EUR': '€',
            'JPY': '¥',
            'GBP': '£',
            'CNY': '¥',
            'HKD': 'HK$',
            'SGD': 'S$',
            'AUD': 'A$',
            'CAD': 'C$',
        }
        return currency_map.get(currency, currency)  # 매핑 없으면 코드 그대로 반환
    
    def get_news_from_rss(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Yahoo Finance RSS를 통한 실시간 뉴스 조회
        
        Args:
            query: 검색 쿼리 (회사명, 종목명 등)
            max_results: 최대 결과 개수
            
        Returns:
            List[Dict]: 뉴스 리스트 (제목, 요약, URL, 영향도 분석 포함)
        """
        news_list = []
        
        try:
            import feedparser
            
            # 질문에서 주식 심볼 자동 추출 (stock_utils 사용)
            stock_symbols = extract_symbols_for_news(query)
            
            # RSS URL 생성
            rss_urls = []
            if stock_symbols:
                print(f"🔍 감지된 주식 심볼: {stock_symbols}")
                for symbol in stock_symbols:
                    rss_urls.append(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US")
            else:
                # 일반적인 금융 뉴스
                print("📰 일반 금융 뉴스 검색")
                rss_urls = [
                    "https://feeds.finance.yahoo.com/rss/2.0/headline",
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"
                ]
            
            for rss_url in rss_urls:
                try:
                    print(f"📡 RSS 피드 수집 중: {rss_url}")
                    feed = feedparser.parse(rss_url)
                    
                    if feed.bozo:
                        print(f"⚠️ RSS 피드 파싱 오류: {feed.bozo_exception}")
                        continue
                    
                    for entry in feed.entries[:max_results//len(rss_urls)]:
                        title = entry.get('title', '').strip()
                        summary = entry.get('summary', '').strip()
                        link = entry.get('link', '').strip()
                        
                        # 날짜 형식 변환
                        try:
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
                            else:
                                published_date = datetime.now().strftime('%Y-%m-%d')
                        except:
                            published_date = datetime.now().strftime('%Y-%m-%d')
                        
                        # 유효한 뉴스인지 확인
                        if title and len(title) > 5 and link:
                            # 뉴스 영향도 분석
                            impact_analysis = self._analyze_news_impact(title, summary)
                            
                            news_list.append({
                                "title": title,
                                "summary": summary if summary else f"Yahoo Finance: {title}",
                                "url": link,
                                "published": published_date,
                                "impact_analysis": impact_analysis
                            })
                    
                except Exception as e:
                    print(f"❌ RSS URL {rss_url} 처리 실패: {e}")
                    continue
            
            print(f"✅ Yahoo Finance RSS에서 {len(news_list)}개의 뉴스를 수집했습니다.")
            return news_list[:max_results]
            
        except Exception as e:
            print(f"❌ 뉴스 가져오기 실패: {e}")
            return []
    
    def _analyze_news_impact(self, title: str, summary: str) -> Dict[str, Any]:
        """
        뉴스의 시장 영향도 분석 (키워드 기반)
        
        Args:
            title: 뉴스 제목
            summary: 뉴스 요약
            
        Returns:
            Dict: 영향도 분석 결과
        """
        try:
            # 긍정/부정 키워드 분석
            positive_keywords = [
                '상승', '증가', '성장', '호재', '긍정', '개선', '확대', '투자', '매수',
                'rise', 'increase', 'growth', 'positive', 'improve', 'expand', 'buy', 'gain'
            ]
            negative_keywords = [
                '하락', '감소', '위험', '악재', '부정', '악화', '축소', '매도', '손실',
                'fall', 'decrease', 'risk', 'negative', 'worse', 'reduce', 'sell', 'loss', 'drop'
            ]
            
            text = (title + " " + summary).lower()
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)
            
            # 영향도 점수 계산 (0-100)
            if positive_count > negative_count:
                impact_score = min(positive_count * 20, 100)
                impact_direction = "긍정적"
            elif negative_count > positive_count:
                impact_score = min(negative_count * 20, 100)
                impact_direction = "부정적"
            else:
                impact_score = 50
                impact_direction = "중립적"
            
            # 시장 영향도 예측
            if impact_score >= 80:
                market_impact = "높음 - 주가에 큰 영향 예상"
            elif impact_score >= 60:
                market_impact = "중간 - 주가에 적당한 영향 예상"
            else:
                market_impact = "낮음 - 주가에 미미한 영향 예상"
            
            return {
                "impact_score": impact_score,
                "impact_direction": impact_direction,
                "market_impact": market_impact,
                "positive_keywords": positive_count,
                "negative_keywords": negative_count
            }
            
        except Exception as e:
            return {
                "impact_score": 50,
                "impact_direction": "중립적",
                "market_impact": "분석 불가",
                "positive_keywords": 0,
                "negative_keywords": 0
            }


# 전역 외부 API 서비스 인스턴스
external_api_service = ExternalAPIService()

