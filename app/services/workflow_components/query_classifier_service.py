"""쿼리 분류 서비스 - Gemini 2.0 Flash를 사용한 의도 분석"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import settings


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
        """Gemini 2.0 Flash를 사용한 의도 분류"""
        try:
            classification_prompt = f"""당신은 금융 챗봇의 의도 분류 전문가입니다.
사용자 질문을 분석하여 정확히 6가지 카테고리 중 하나로 분류하세요.

## 카테고리 정의
1. **data** - 실시간 주식 가격, 시세, 현재가 조회 요청 (차트 없이 텍스트만)
   예시: "삼성전자 주가 텍스트로만", "SK하이닉스 현재가 숫자만"
   
2. **analysis** - 주식 분석, 투자 전망, 추천 요청
   예시: "삼성전자 투자해도 될까?", "네이버 전망 분석해줘", "LG전자 추천해?"
   
3. **news** - 뉴스, 최신 소식, 동향, 이슈 조회
   예시: "삼성전자 최근 뉴스", "반도체 관련 소식", "최근 시장 이슈"
   
4. **knowledge** - 금융 용어, 개념, 원리 설명 요청
   예시: "PER이 뭐야?", "손절매의 의미는?", "배당금 설명해줘"
   
5. **visualization** - 차트, 그래프, 시각화 요청 (주가/가격/시세 포함)
   예시: "삼성전자 주가 알려줘", "네이버 현재가", "SK하이닉스 가격", "삼성전자 차트 보여줘"
   
6. **general** - 인사, 잡담, 기타 질문
   예시: "안녕", "고마워", "뭐 할 수 있어?"

## 분류 규칙
- 종목명 + "주가/가격/시세/현재가" → **visualization**
- 종목명 + "분석/전망/추천/투자" → **analysis**  
- "뉴스/소식/이슈/동향" 포함 → **news**
- "차트/그래프/시각화/캔들" 포함 → **visualization**
- "뜻/의미/설명/이해/무엇" 포함 → **knowledge**
- 종목명/금융 키워드 없음 → **general**

## 사용자 질문
"{query}"

## 출력
한 단어만 출력하세요 (data, analysis, news, knowledge, visualization, general 중 하나)"""

            response = self.llm.invoke(classification_prompt)
            
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

