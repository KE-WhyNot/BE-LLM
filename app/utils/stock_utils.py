"""주식 심볼 매핑 및 유틸리티 함수"""

# 주요 한국 주식 심볼 매핑
STOCK_SYMBOL_MAP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "삼성SDI": "006400.KS",
    "현대모비스": "012330.KS",
    # 필요한 만큼 추가
}

def normalize_company_name(name: str) -> str:
    """회사 이름 정규화"""
    # 공백 및 특수문자 제거
    normalized = ''.join(name.split())
    
    # 흔한 별칭 처리
    aliases = {
        "삼성": "삼성전자",
        "삼전": "삼성전자",
        "하이닉스": "SK하이닉스",
        "현차": "현대차",
        "엘지에너지솔루션": "LG에너지솔루션",
        # 필요한 만큼 추가
    }
    
    return aliases.get(normalized, normalized)

def get_stock_symbol(company_name: str) -> str:
    """회사 이름으로 주식 심볼 찾기"""
    normalized_name = normalize_company_name(company_name)
    return STOCK_SYMBOL_MAP.get(normalized_name)

def extract_company_name(query: str) -> str:
    """사용자 쿼리에서 회사 이름 추출"""
    # 쿼리에서 "주가", "주식" 등의 키워드 제거
    keywords = [
        "주가", "주식", "시세", "가격", "얼마", "알려줘", "알려주세요", "어때", "어떄",
        "최근", "동향", "뉴스", "분석", "전망", "예측", "정보", "상황", "현황",
        "어떻게", "어떤", "무엇", "뭐", "궁금", "궁금해", "궁금합니다"
    ]
    for keyword in keywords:
        query = query.replace(keyword, "")
    
    # 공백 제거하고 반환
    return query.strip()
