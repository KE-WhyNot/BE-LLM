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
                "시장 분석", "시장 동향", "시장 전망", "코스피", "코스닥", "주가 지수",
                "market analysis", "market trend", "market outlook", "kospi", "kosdaq"
            ],
            "stock_info": [
                "주식 정보", "주가", "종목", "삼성전자", "LG", "현대차", "네이버",
                "stock price", "stock info", "samsung", "stock symbol"
            ],
            "news_query": [
                "뉴스", "최신 뉴스", "뉴스 분석", "동향", "소식", "이슈", "최근", "최근 동향", "최근 소식",
                "news", "latest news", "news analysis", "trend", "issue", "recent", "recent trend"
            ],
            "investment_strategy": [
                "투자 전략", "투자 방법", "포트폴리오", "자산 배분", "투자 조언",
                "investment strategy", "portfolio", "asset allocation", "investment advice"
            ],
            "risk_management": [
                "리스크 관리", "위험 관리", "손실", "보험", "안전",
                "risk management", "risk control", "loss", "safety"
            ],
            "general_query": [
                "금융", "투자", "경제", "은행", "대출", "적금",
                "finance", "investment", "economy", "bank", "loan"
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
        """사용자 질문의 의도 분석 (임베딩 기반)"""
        try:
            # 쿼리 임베딩 생성
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
            
            return {
                "intent": predicted_intent,
                "confidence": confidence,
                "requires_realtime": self._requires_realtime_data(predicted_intent)
            }
            
        except Exception as e:
            print(f"의도 분석 중 오류: {e}")
            # 오류 시 기본값 반환
            return {
                "intent": "general_query",
                "confidence": 0.5,
                "requires_realtime": False
            }
    
    def _requires_realtime_data(self, intent: str) -> bool:
        """실시간 데이터가 필요한 의도인지 판단"""
        realtime_intents = {"stock_info", "market_analysis", "news_query"}
        return intent in realtime_intents
