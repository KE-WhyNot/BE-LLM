"""쿼리 분류 서비스 - Gemini 2.0 Flash를 사용한 의도 분석 (동적 프롬프팅)"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import settings
from app.services.langgraph_enhanced import prompt_manager


class QueryClassifierService:
    """사용자 쿼리를 분류하는 서비스"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        # Google Gemini 우선 사용
        if settings.google_api_key:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                google_api_key=settings.google_api_key
            )
        elif settings.openai_api_key:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.openai_api_key
            )
        else:
            print("⚠️ API 키가 설정되지 않았습니다. 키워드 기반 분류를 사용합니다.")
            return None
    
    def classify(self, query: str) -> str:
        """쿼리를 분류하여 카테고리 반환
        
        Args:
            query: 사용자 질문
            
        Returns:
            str: "data", "analysis", "news", "knowledge", "visualization", "general" 중 하나
        """
        # LLM을 사용한 의도 분류
        if self.llm:
            return self._classify_with_llm(query)
        else:
            # LLM이 없을 때는 키워드 기반 폴백
            return self._classify_with_keywords(query)
    
    def _classify_with_llm(self, query: str) -> str:
        """Gemini 2.0 Flash를 사용한 의도 분류 (동적 프롬프팅)"""
        try:
            # ✨ 동적 프롬프트 생성 (prompt_manager 사용)
            messages = prompt_manager.generate_classification_prompt(query)
            
            # LLM 호출
            response = self.llm.invoke(messages)
            
            # 응답에서 카테고리 추출
            result = response.content.strip().lower()
            
            # 유효한 카테고리인지 확인
            valid_types = ["data", "analysis", "news", "knowledge", "visualization", "general"]
            for valid_type in valid_types:
                if valid_type in result:
                    return valid_type
            
            # 유효하지 않으면 키워드 기반 폴백
            return self._classify_with_keywords(query)
            
        except Exception as e:
            print(f"LLM 분류 중 오류: {e}")
            return self._classify_with_keywords(query)
    
    def _classify_with_keywords(self, query: str) -> str:
        """키워드 기반 분류 (폴백)"""
        query_lower = query.lower()
        
        # 주식 종목명 리스트
        stock_names = [
            "삼성전자", "sk하이닉스", "하이닉스", "네이버", "카카오", "현대차", "기아",
            "lg전자", "삼성바이오", "포스코", "sk텔레콤", "삼성sdi",
            "samsung", "hynix", "naver", "kakao", "hyundai", "kia"
        ]
        
        # 종목명이 포함되어 있는지 확인
        has_stock_name = any(stock in query_lower for stock in stock_names)
        
        # 1순위: 명확한 키워드
        if any(keyword in query_lower for keyword in ["차트", "그래프", "시각화", "캔들", "그림", "주가", "가격", "현재가", "시세"]):
            return "visualization"
        elif any(keyword in query_lower for keyword in ["뉴스", "소식", "이슈", "공시"]):
            return "news"
        elif any(keyword in query_lower for keyword in ["뜻", "이해", "설명", "의미", "무엇", "뭐야"]):
            return "knowledge"
        
        # 2순위: 종목명 + 분석/투자 키워드 = analysis
        elif has_stock_name and any(keyword in query_lower for keyword in ["분석", "전망", "투자", "추천", "의견", "전략"]):
            return "analysis"
        
        # 3순위: 종목명 + 주식 = data
        elif has_stock_name and "주식" in query_lower:
            return "data"
        
        # 4순위: 종목명만 있으면 data
        elif has_stock_name:
            return "data"
        
        # 5순위: 분석/투자 키워드만 있으면 general (종목 없음)
        elif any(keyword in query_lower for keyword in ["분석", "전망", "투자", "추천", "전략"]):
            return "general"
        
        else:
            return "general"


# 전역 서비스 인스턴스
query_classifier = QueryClassifierService()

