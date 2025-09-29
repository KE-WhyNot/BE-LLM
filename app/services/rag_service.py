import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.schema import Document
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

class FinancialRAGService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        금융 전문가 RAG 서비스 초기화
        """
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """벡터 스토어 초기화"""
        try:
            # 기존 벡터 스토어 로드 시도
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("기존 벡터 스토어를 성공적으로 로드했습니다.")
        except Exception as e:
            print(f"벡터 스토어 로드 실패: {e}")
            # 새로운 벡터 스토어 생성
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("새로운 벡터 스토어를 생성했습니다.")
    
    def add_financial_documents(self, documents: List[Document]):
        """금융 문서를 벡터 스토어에 추가"""
        if not documents:
            return
        
        # 문서 분할
        split_docs = self.text_splitter.split_documents(documents)
        
        # 벡터 스토어에 추가
        self.vectorstore.add_documents(split_docs)
        # persist 메서드는 자동으로 호출됨
        print(f"{len(split_docs)}개의 문서 청크를 벡터 스토어에 추가했습니다.")
    
    def get_financial_data(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """Yahoo Finance에서 주식 데이터 가져오기"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            info = ticker.info
            
            if hist.empty:
                return {"error": f"{symbol}에 대한 데이터를 찾을 수 없습니다."}
            
            # 최신 데이터
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # 가격 변화 계산
            price_change = latest['Close'] - previous['Close']
            price_change_percent = (price_change / previous['Close']) * 100
            
            return {
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
                "pe_ratio": info.get('trailingPE', 'Unknown'),
                "dividend_yield": info.get('dividendYield', 'Unknown'),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"데이터 가져오기 실패: {str(e)}"}
    
    def get_financial_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Yahoo Finance RSS에서 실제 금융 뉴스 가져오기"""
        news_list = []
        
        try:
            import feedparser
            
            # 쿼리에 따른 RSS URL 선택
            rss_urls = []
            
            if "삼성" in query or "samsung" in query.lower():
                rss_urls = [
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=005930.KS&region=US&lang=en-US",
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SSNLF&region=US&lang=en-US"
                ]
            elif "kospi" in query.lower() or "코스피" in query:
                rss_urls = [
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^KS11&region=US&lang=en-US",
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"
                ]
            else:
                # 일반적인 금융 뉴스
                rss_urls = [
                    "https://feeds.finance.yahoo.com/rss/2.0/headline",
                    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"
                ]
            
            for rss_url in rss_urls:
                try:
                    print(f"RSS 피드 수집 중: {rss_url}")
                    feed = feedparser.parse(rss_url)
                    
                    if feed.bozo:
                        print(f"RSS 피드 파싱 오류: {feed.bozo_exception}")
                        continue
                    
                    for entry in feed.entries[:max_results//len(rss_urls)]:
                        title = entry.get('title', '').strip()
                        summary = entry.get('summary', '').strip()
                        link = entry.get('link', '').strip()
                        published = entry.get('published', datetime.now().isoformat())
                        
                        # 유효한 뉴스인지 확인
                        if title and len(title) > 5 and link:
                            news_list.append({
                                "title": title,
                                "summary": summary if summary else f"Yahoo Finance: {title}",
                                "url": link,
                                "published": published
                            })
                    
                except Exception as e:
                    print(f"RSS URL {rss_url} 처리 실패: {e}")
                    continue
            
            print(f"Yahoo Finance RSS에서 {len(news_list)}개의 뉴스를 수집했습니다.")
            return news_list[:max_results]
            
        except Exception as e:
            print(f"뉴스 가져오기 실패: {e}")
            # 실패 시 샘플 데이터 반환
            return [
                {
                    "title": f"{query} 관련 최신 뉴스 1",
                    "summary": f"{query}에 대한 분석가 의견과 시장 전망",
                    "url": "https://example.com/news1",
                    "published": datetime.now().isoformat()
                },
                {
                    "title": f"{query} 관련 최신 뉴스 2", 
                    "summary": f"{query}의 실적 발표와 투자자 반응",
                    "url": "https://example.com/news2",
                    "published": datetime.now().isoformat()
                }
            ][:max_results]
    
    def get_news_content_from_url(self, url: str) -> Dict[str, Any]:
        """뉴스 URL에서 실제 내용을 스크래핑"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출 (더 많은 선택자 추가)
            title = ""
            title_selectors = [
                'h1', '.caas-title-wrapper h1', '.headline', 'title',
                '[data-module="ArticleHeader"] h1', '.caas-title',
                'h1[data-testid="headline"]', '.caas-title-wrapper'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # 본문 추출 (더 많은 선택자와 폴백 로직)
            content = ""
            content_selectors = [
                '.caas-body', '.article-body', '.story-body', 
                '.content', '.article-content', 'article p',
                '[data-module="ArticleBody"]', '.caas-body p',
                '.caas-body div', 'article div', '.story-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 모든 p 태그와 div 태그의 텍스트를 합침
                    paragraphs = content_elem.find_all(['p', 'div'])
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 100:  # 충분한 내용이 있으면 중단
                        break
            
            # 폴백: 전체 페이지에서 텍스트 추출
            if not content or len(content) < 100:
                # 모든 p 태그에서 텍스트 추출
                all_paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in all_paragraphs if p.get_text(strip=True)])
                
                # 여전히 부족하면 div 태그도 포함
                if len(content) < 100:
                    all_divs = soup.find_all('div')
                    div_text = ' '.join([d.get_text(strip=True) for d in all_divs if d.get_text(strip=True)])
                    content = content + ' ' + div_text
            
            # 메타 정보 추출
            author = ""
            author_elem = soup.select_one('[data-module="ArticleHeader"] .caas-author-byline-collapse')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            published_date = ""
            date_elem = soup.select_one('time, .caas-attr-time-style')
            if date_elem:
                published_date = date_elem.get_text(strip=True)
            
            return {
                "title": title,
                "content": content,
                "author": author,
                "published_date": published_date,
                "url": url,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": f"뉴스 내용 가져오기 실패: {str(e)}",
                "url": url,
                "success": False
            }
    
    def analyze_news_impact(self, news_content: str, title: str = "") -> Dict[str, Any]:
        """뉴스 내용을 분석하여 주식에 미치는 영향 평가"""
        try:
            # 간단한 키워드 기반 분석 (실제로는 더 정교한 NLP 모델 사용 가능)
            positive_keywords = [
                '상승', '증가', '성장', '개선', '호재', '긍정적', '강세', '돌파',
                'rise', 'increase', 'growth', 'improve', 'positive', 'bullish', 'breakthrough'
            ]
            
            negative_keywords = [
                '하락', '감소', '위기', '악화', '부재', '부정적', '약세', '폭락',
                'fall', 'decrease', 'crisis', 'worse', 'negative', 'bearish', 'crash'
            ]
            
            # 키워드 매칭
            content_lower = news_content.lower()
            title_lower = title.lower()
            combined_text = f"{title_lower} {content_lower}"
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in combined_text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in combined_text)
            
            # 영향도 계산
            total_keywords = positive_count + negative_count
            if total_keywords == 0:
                impact_score = 0
                sentiment = "중립"
            else:
                impact_score = (positive_count - negative_count) / total_keywords
                if impact_score > 0.3:
                    sentiment = "긍정적"
                elif impact_score < -0.3:
                    sentiment = "부정적"
                else:
                    sentiment = "중립"
            
            # 영향도 레벨 결정
            if abs(impact_score) > 0.7:
                impact_level = "높음"
            elif abs(impact_score) > 0.4:
                impact_level = "중간"
            else:
                impact_level = "낮음"
            
            return {
                "sentiment": sentiment,
                "impact_score": impact_score,
                "impact_level": impact_level,
                "positive_keywords_found": positive_count,
                "negative_keywords_found": negative_count,
                "analysis": f"뉴스 분석 결과: {sentiment}적 영향 ({impact_level} 수준)"
            }
            
        except Exception as e:
            return {
                "error": f"뉴스 영향 분석 실패: {str(e)}",
                "sentiment": "분석 불가",
                "impact_score": 0,
                "impact_level": "알 수 없음"
            }
    
    def summarize_news_content(self, news_content: str, title: str = "", max_length: int = 300) -> str:
        """뉴스 내용을 요약"""
        try:
            if not news_content or len(news_content.strip()) < 50:
                return "뉴스 내용이 충분하지 않아 요약할 수 없습니다."
            
            # 간단한 요약 로직 (실제로는 더 정교한 NLP 모델 사용 가능)
            sentences = news_content.split('.')
            
            # 중요한 문장들 선택 (길이와 키워드 기반)
            important_keywords = [
                '주가', '주식', '투자', '수익', '실적', '매출', '이익', '손실',
                'stock', 'price', 'investment', 'revenue', 'profit', 'loss',
                '증가', '감소', '상승', '하락', '성장', '위기'
            ]
            
            scored_sentences = []
            for sentence in sentences:
                if len(sentence.strip()) > 20:  # 너무 짧은 문장 제외
                    score = 0
                    sentence_lower = sentence.lower()
                    
                    # 키워드 점수
                    for keyword in important_keywords:
                        if keyword in sentence_lower:
                            score += 1
                    
                    # 길이 점수 (적당한 길이의 문장 선호)
                    if 50 <= len(sentence) <= 200:
                        score += 1
                    
                    scored_sentences.append((score, sentence.strip()))
            
            # 점수 순으로 정렬하고 상위 문장들 선택
            scored_sentences.sort(reverse=True)
            summary_sentences = [sent[1] for sent in scored_sentences[:3]]
            
            summary = '. '.join(summary_sentences)
            if summary and not summary.endswith('.'):
                summary += '.'
            
            # 길이 제한
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            return summary if summary else "뉴스 요약을 생성할 수 없습니다."
            
        except Exception as e:
            return f"뉴스 요약 생성 실패: {str(e)}"
    
    def create_financial_knowledge_base(self):
        """금융 지식 베이스 생성"""
        financial_documents = []
        
        # 기본 금융 지식 문서들
        basic_knowledge = [
            Document(
                page_content="""
                주식 투자의 기본 원칙:
                1. 분산투자: 여러 종목에 투자하여 리스크를 분산시킵니다.
                2. 장기투자: 단기 변동성보다 장기 성장에 집중합니다.
                3. 기본적 분석: 기업의 재무상태와 사업모델을 분석합니다.
                4. 기술적 분석: 차트와 거래량을 통해 매매 타이밍을 결정합니다.
                5. 리스크 관리: 손실을 제한하고 수익을 극대화합니다.
                """,
                metadata={"source": "investment_basics", "type": "basic_knowledge"}
            ),
            Document(
                page_content="""
                재무제표 분석 방법:
                1. 손익계산서: 매출, 비용, 순이익을 확인하여 수익성을 분석합니다.
                2. 대차대조표: 자산, 부채, 자본을 확인하여 재무안정성을 분석합니다.
                3. 현금흐름표: 현금의 유입과 유출을 확인하여 현금창출능력을 분석합니다.
                4. 주요 재무비율: ROE, ROA, PER, PBR 등을 통해 기업가치를 평가합니다.
                """,
                metadata={"source": "financial_analysis", "type": "analysis_method"}
            ),
            Document(
                page_content="""
                시장 지수와 섹터:
                1. KOSPI: 한국 종합주가지수, 대형주 중심의 시장 전체 지표
                2. KOSDAQ: 한국 거래소 코스닥시장 지수, 중소형주 중심
                3. 주요 섹터: 기술, 금융, 헬스케어, 에너지, 소비재, 산업재 등
                4. 섹터 로테이션: 경제 사이클에 따른 섹터별 투자 전략
                """,
                metadata={"source": "market_indices", "type": "market_knowledge"}
            )
        ]
        
        financial_documents.extend(basic_knowledge)
        
        # 주요 종목 정보 추가
        major_stocks = ["005930.KS", "000660.KS", "035420.KS", "207940.KS", "006400.KS"]
        for symbol in major_stocks:
            stock_data = self.get_financial_data(symbol)
            if "error" not in stock_data:
                stock_doc = Document(
                    page_content=f"""
                    {stock_data['company_name']} ({symbol}) 정보:
                    현재가: {stock_data['current_price']}원
                    전일대비: {stock_data['price_change']}원 ({stock_data['price_change_percent']}%)
                    거래량: {stock_data['volume']:,}주
                    시가총액: {stock_data['market_cap']}
                    PER: {stock_data['pe_ratio']}
                    배당수익률: {stock_data['dividend_yield']}
                    섹터: {stock_data['sector']}
                    """,
                    metadata={"source": f"stock_{symbol}", "type": "stock_info", "symbol": symbol}
                )
                financial_documents.append(stock_doc)
        
        # 벡터 스토어에 추가
        self.add_financial_documents(financial_documents)
        print(f"금융 지식 베이스에 {len(financial_documents)}개의 문서를 추가했습니다.")
    
    def search_relevant_documents(self, query: str, k: int = 5) -> List[Document]:
        """관련 문서 검색"""
        if not self.vectorstore:
            return []
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return docs
        except Exception as e:
            print(f"문서 검색 실패: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> str:
        """쿼리에 대한 컨텍스트 정보 생성"""
        # 관련 문서 검색
        relevant_docs = self.search_relevant_documents(query, k=3)
        
        # 실시간 주식 데이터 추가
        context_parts = []
        
        # 검색된 문서 내용
        if relevant_docs:
            context_parts.append("관련 금융 지식:")
            for doc in relevant_docs:
                context_parts.append(f"- {doc.page_content[:500]}...")
        
        # 쿼리에서 주식 심볼 추출 시도
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["삼성전자", "samsung", "005930"]):
            stock_data = self.get_financial_data("005930.KS")
            if "error" not in stock_data:
                context_parts.append(f"\n삼성전자 실시간 정보:\n{json.dumps(stock_data, ensure_ascii=False, indent=2)}")
        
        return "\n".join(context_parts) if context_parts else "관련 정보를 찾을 수 없습니다."

# 전역 RAG 서비스 인스턴스
rag_service = FinancialRAGService()
