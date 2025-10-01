"""주식 심볼 매핑 및 유틸리티 함수"""

import re
from typing import Optional, List


# 통합 주식 심볼 매핑 (한글 -> 심볼)
STOCK_SYMBOL_MAPPING = {
    # 삼성 관련
    "삼성": "005930.KS",
    "삼성전자": "005930.KS",
    "삼전": "005930.KS",
    "samsung": "005930.KS",
    
    # 하이닉스 관련
    "하이닉스": "000660.KS",
    "sk하이닉스": "000660.KS",
    "skhynix": "000660.KS",
    "hynix": "000660.KS",
    "sk hynix": "000660.KS",
    
    # LG 관련
    "lg": "066570.KS",
    "lg전자": "066570.KS",
    "lg화학": "051910.KS",
    "lg에너지솔루션": "373220.KS",
    "엘지에너지솔루션": "373220.KS",
    
    # 네이버 관련
    "네이버": "035420.KS",
    "naver": "035420.KS",
    
    # 카카오 관련
    "카카오": "035720.KS",
    "kakao": "035720.KS",
    
    # 현대차 관련
    "현대차": "005380.KS",
    "현차": "005380.KS",
    "현대자동차": "005380.KS",
    "hyundai": "005380.KS",
    "현대모비스": "012330.KS",
    
    # 기아 관련
    "기아": "000270.KS",
    "kia": "000270.KS",
    
    # SK텔레콤 관련
    "sk텔레콤": "017670.KS",
    "sktelecom": "017670.KS",
    
    # POSCO 관련
    "포스코": "005490.KS",
    "posco": "005490.KS",
    
    # 삼성 계열사
    "삼성바이오로직스": "207940.KS",
    "삼성바이오": "207940.KS",
    "samsung biologics": "207940.KS",
    "삼성sdi": "006400.KS",
    "samsung sdi": "006400.KS",
}

# 뉴스 조회용 다중 심볼 매핑 (한 회사의 여러 티커)
MULTI_SYMBOL_MAPPING = {
    # 삼성 관련
    "삼성": ["005930.KS", "SSNLF"],
    "삼성전자": ["005930.KS", "SSNLF"],
    "samsung": ["005930.KS", "SSNLF"],
    
    # 하이닉스 관련
    "하이닉스": ["000660.KS", "HXSCL"],
    "sk하이닉스": ["000660.KS", "HXSCL"],
    "hynix": ["000660.KS", "HXSCL"],
    
    # LG 관련
    "lg": ["003550.KS", "LPLIY"],
    "lg전자": ["003550.KS", "LPLIY"],
    "lg화학": ["051910.KS", "LGCHEM"],
    
    # 네이버 관련
    "네이버": ["035420.KS", "NHNCF"],
    "naver": ["035420.KS", "NHNCF"],
    
    # 카카오 관련
    "카카오": ["035720.KS", "KAKAO"],
    "kakao": ["035720.KS", "KAKAO"],
    
    # 현대차 관련
    "현대차": ["005380.KS", "HYMTF"],
    "현대자동차": ["005380.KS", "HYMTF"],
    "hyundai": ["005380.KS", "HYMTF"],
    
    # 기아 관련
    "기아": ["000270.KS", "KIMTF"],
    "kia": ["000270.KS", "KIMTF"],
    
    # SK텔레콤 관련
    "sk텔레콤": ["017670.KS", "SKM"],
    "sktelecom": ["017670.KS", "SKM"],
    
    # POSCO 관련
    "포스코": ["005490.KS", "PKX"],
    "posco": ["005490.KS", "PKX"],
    
    # 시장 지수
    "코스피": ["^KS11"],
    "kospi": ["^KS11"],
    "코스닥": ["^KQ11"],
    "kosdaq": ["^KQ11"],
    "나스닥": ["^IXIC"],
    "nasdaq": ["^IXIC"],
    "다우": ["^DJI"],
    "dow": ["^DJI"],
    "s&p500": ["^GSPC"],
    "sp500": ["^GSPC"]
}

# 6자리 숫자 코드 매핑
NUMBER_SYMBOL_MAPPING = {
    "005930": "005930.KS",  # 삼성전자
    "000660": "000660.KS",  # SK하이닉스
    "035420": "035420.KS",  # 네이버
    "207940": "207940.KS",  # 삼성바이오로직스
    "006400": "006400.KS",  # 삼성SDI
    "005380": "005380.KS",  # 현대차
    "000270": "000270.KS",  # 기아
    "017670": "017670.KS",  # SK텔레콤
    "005490": "005490.KS",  # POSCO
    "066570": "066570.KS",  # LG전자
    "051910": "051910.KS",  # LG화학
    "373220": "373220.KS",  # LG에너지솔루션
    "012330": "012330.KS",  # 현대모비스
    "035720": "035720.KS",  # 카카오
}


def normalize_company_name(name: str) -> str:
    """회사 이름 정규화
    
    Args:
        name: 회사 이름
        
    Returns:
        str: 정규화된 회사 이름
    """
    # 공백 및 특수문자 제거
    normalized = ''.join(name.split()).lower()
    
    # 흔한 별칭 처리
    aliases = {
        "삼전": "삼성전자",
        "현차": "현대차",
    }
    
    return aliases.get(normalized, normalized)


def extract_symbol_from_query(query: str) -> Optional[str]:
    """쿼리에서 단일 주식 심볼 추출 (데이터 조회용)
    
    Args:
        query: 사용자 질문
        
    Returns:
        Optional[str]: 주식 심볼 (예: "005930.KS") 또는 None
    """
    query_lower = query.lower()
    
    # 띄어쓰기 제거 (예: "현대 차" -> "현대차")
    query_no_space = query.replace(" ", "")
    query_lower_no_space = query_lower.replace(" ", "")
    
    # 1. 심볼 매핑에서 검색 (원본, 소문자, 띄어쓰기 제거 모두 확인)
    for keyword, symbol in STOCK_SYMBOL_MAPPING.items():
        if (keyword in query or keyword in query_lower or 
            keyword in query_no_space or keyword in query_lower_no_space):
            return symbol
    
    # 2. 완전한 심볼 패턴 검색 (예: 005930.KS)
    full_symbol_pattern = r'\b\d{6}\.KS\b'
    match = re.search(full_symbol_pattern, query)
    if match:
        return match.group()
    
    # 3. 6자리 숫자만 있는 경우 (예: 005930)
    number_pattern = r'\b(\d{6})\b'
    match = re.search(number_pattern, query)
    if match:
        number = match.group(1)
        if number in NUMBER_SYMBOL_MAPPING:
            return NUMBER_SYMBOL_MAPPING[number]
        else:
            # 알려지지 않은 번호도 .KS 추가
            return f"{number}.KS"
    
    return None


def extract_symbols_for_news(query: str) -> List[str]:
    """쿼리에서 다중 주식 심볼 추출 (뉴스 조회용)
    
    Args:
        query: 사용자 질문
        
    Returns:
        List[str]: 주식 심볼 리스트
    """
    found_symbols = []
    query_lower = query.lower()
    
    for keyword, symbols in MULTI_SYMBOL_MAPPING.items():
        if keyword in query_lower:
            found_symbols.extend(symbols)
    
    # 중복 제거
    return list(set(found_symbols))


def get_company_name_from_symbol(symbol: str) -> Optional[str]:
    """심볼에서 회사 이름 추출
    
    Args:
        symbol: 주식 심볼 (예: "005930.KS")
        
    Returns:
        Optional[str]: 회사 이름 또는 None
    """
    symbol_to_name = {v: k for k, v in STOCK_SYMBOL_MAPPING.items() 
                     if not k.islower()}  # 영문 제외
    
    return symbol_to_name.get(symbol)


def is_valid_symbol(symbol: str) -> bool:
    """유효한 심볼인지 확인
    
    Args:
        symbol: 주식 심볼
        
    Returns:
        bool: 유효 여부
    """
    # 한국 주식 패턴 (6자리.KS)
    korean_pattern = r'^\d{6}\.KS$'
    if re.match(korean_pattern, symbol):
        return True
    
    # 미국 주식 패턴 (대문자 1-5자)
    us_pattern = r'^[A-Z]{1,5}$'
    if re.match(us_pattern, symbol):
        return True
    
    # 지수 패턴 (^로 시작)
    index_pattern = r'^\^[A-Z0-9]+$'
    if re.match(index_pattern, symbol):
        return True
    
    return False


def extract_company_name(query: str) -> str:
    """사용자 쿼리에서 회사 이름 추출
    
    Args:
        query: 사용자 질문
        
    Returns:
        str: 추출된 회사 이름
    """
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


# 하위 호환성을 위한 별칭
STOCK_SYMBOL_MAP = STOCK_SYMBOL_MAPPING
get_stock_symbol = extract_symbol_from_query
