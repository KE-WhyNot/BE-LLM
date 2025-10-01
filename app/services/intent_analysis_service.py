from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings

class IntentAnalysisService:
    """가벼운 임베딩 모델을 사용한 질문 의도 분석 서비스"""
    
    def __init__(self):
        try:
            print(f"🔧 임베딩 모델을 로드합니다: {settings.embedding_model_path}")
            self.model = SentenceTransformer(settings.embedding_model_path)
            print("✅ 임베딩 모델 로드 완료")
            
            # 의도 레이블 정의
            self.intent_labels = [
                "market_analysis",     # 시장 분석 요청
                "stock_info",          # 개별 주식 정보 요청
                "news_query",          # 뉴스 관련 질문
                "investment_strategy", # 투자 전략 문의
                "risk_management",    # 리스크 관리 문의
                "general_query"       # 일반적인 금융 질문
            ]
            
            # 의도별 키워드 임베딩 생성
            self._setup_intent_embeddings()
            
        except Exception as e:
            print(f"⚠️ 임베딩 모델 로드 중 오류 발생: {str(e)}")
            raise
            
    def _setup_intent_embeddings(self):
        """의도별 키워드 임베딩 생성"""
        intent_keywords = {
            "market_analysis": [
                "시장 분석", "시장 동향", "시장 전망", "코스피", "코스닥", "주가 지수", "분석해줘", "전망", "투자 전망",
                "market analysis", "market trend", "market outlook", "kospi", "kosdaq", "analyze", "outlook"
            ],
            "stock_info": [
                "주식 정보", "주가", "종목", "현재가", "시세", "주식", "삼성전자", "LG", "현대차", "네이버", "005930",
                "stock price", "stock info", "samsung", "stock symbol", "price", "current price"
            ],
            "news_query": [
                "뉴스", "최신 뉴스", "뉴스 분석", "동향", "소식", "이슈", "최근", "최근 동향", "최근 소식",
                "news", "latest news", "news analysis", "trend", "issue", "recent", "recent trend"
            ],
            "investment_strategy": [
                "투자 전략", "투자 방법", "포트폴리오", "자산 배분", "투자 조언", "추천", "전략", "방법",
                "investment strategy", "portfolio", "asset allocation", "investment advice", "recommend", "strategy"
            ],
            "risk_management": [
                "리스크 관리", "위험 관리", "손실", "보험", "안전", "관리", "방법",
                "risk management", "risk control", "loss", "safety", "management"
            ],
            "general_query": [
                "금융", "투자", "경제", "은행", "대출", "적금", "의미", "뜻", "이해", "설명", "기본", "원리",
                "finance", "investment", "economy", "bank", "loan", "meaning", "explain", "basic", "principle"
            ]
        }
        
        # 각 의도별 임베딩 생성
        self.intent_embeddings = {}
        for intent, keywords in intent_keywords.items():
            # 키워드들을 하나의 텍스트로 결합
            combined_text = " ".join(keywords)
            embedding = self.model.encode(combined_text)
            self.intent_embeddings[intent] = embedding
    
    def analyze_intent(self, query: str) -> dict:
        """사용자 질문의 의도 분석 (임베딩 + 키워드 기반)"""
        try:
            # 1. 키워드 기반 빠른 분류 (높은 정확도)
            keyword_intent = self._analyze_by_keywords(query)
            if keyword_intent:
                return {
                    "intent": keyword_intent,
                    "confidence": 0.9,  # 키워드 기반은 높은 신뢰도
                    "requires_realtime": self._requires_realtime_data(keyword_intent)
                }
            
            # 2. 임베딩 기반 분석 (신뢰도가 낮으면 키워드 폴백)
            query_embedding = self.model.encode(query)
            
            # 각 의도와의 유사도 계산
            similarities = {}
            for intent, intent_embedding in self.intent_embeddings.items():
                similarity = np.dot(query_embedding, intent_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(intent_embedding)
                )
                similarities[intent] = similarity
            
            # 가장 유사한 의도 선택
            predicted_intent = max(similarities, key=similarities.get)
            confidence = similarities[predicted_intent]
            
            # 3. 신뢰도가 낮으면 키워드 기반 폴백
            if confidence < 0.4:
                fallback_intent = self._analyze_by_keywords(query)
                if fallback_intent:
                    predicted_intent = fallback_intent
                    confidence = 0.6  # 폴백 신뢰도
            
            return {
                "intent": predicted_intent,
                "confidence": confidence,
                "requires_realtime": self._requires_realtime_data(predicted_intent)
            }
            
        except Exception as e:
            print(f"의도 분석 중 오류: {e}")
            # 오류 시 키워드 기반 폴백
            fallback_intent = self._analyze_by_keywords(query)
            return {
                "intent": fallback_intent or "general_query",
                "confidence": 0.5,
                "requires_realtime": self._requires_realtime_data(fallback_intent or "general_query")
            }
    
    def _analyze_by_keywords(self, query: str) -> str:
        """키워드 기반 의도 분석"""
        query_lower = query.lower()
        
        # 명확한 키워드 매칭
        keyword_mappings = {
            "stock_info": [
                "주가", "현재가", "시세", "주식", "가격", "종목", "005930", "삼성전자", "네이버", "SK하이닉스"
            ],
            "market_analysis": [
                "분석", "분석해줘", "전망", "투자 전망", "시장 분석", "시장 전망"
            ],
            "news_query": [
                "뉴스", "소식", "동향", "이슈", "최근", "최신"
            ],
            "investment_strategy": [
                "투자 전략", "투자 방법", "포트폴리오", "추천", "전략", "방법"
            ],
            "risk_management": [
                "리스크", "위험", "관리", "손실", "안전"
            ],
            "general_query": [
                "의미", "뜻", "이해", "설명", "기본", "원리", "뭐야", "무엇"
            ]
        }
        
        # 키워드 매칭 점수 계산
        intent_scores = {}
        for intent, keywords in keyword_mappings.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            intent_scores[intent] = score
        
        # 가장 높은 점수의 의도 반환
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return None
    
    def _requires_realtime_data(self, intent: str) -> bool:
        """실시간 데이터가 필요한 의도인지 판단"""
        realtime_intents = {"stock_info", "market_analysis", "news_query"}
        return intent in realtime_intents
