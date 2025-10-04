"""주식 심볼 매핑 및 유틸리티 함수 (동적 설정 기반)"""

import re
from typing import Optional, List
from .stock_config_loader import stock_config_loader


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
        "엘지": "lg",
        "하이닉스": "sk하이닉스"
    }
    
    return aliases.get(normalized, normalized)


def extract_symbol_from_query(query: str) -> Optional[str]:
    """쿼리에서 단일 주식 심볼 추출 (데이터 조회용)
    
    Args:
        query: 사용자 질문
        
    Returns:
        Optional[str]: 주식 심볼 (예: "005930.KS") 또는 None
    """
    if not query:
        return None
    
    # 동적 설정 로더 사용
    symbol = stock_config_loader.get_symbol(query)
    
    if symbol:
        return symbol
    
    # 정규식으로 직접 패턴 매칭 (fallback)
    # 1. 완전한 심볼 패턴 검색 (예: 005930.KS)
    full_symbol_pattern = r'\b\d{6}\.KS\b'
    match = re.search(full_symbol_pattern, query)
    if match:
        return match.group()
    
    # 2. 6자리 숫자만 있는 경우 (예: 005930)
    number_pattern = r'\b(\d{6})\b'
    match = re.search(number_pattern, query)
    if match:
        number = match.group(1)
        return f"{number}.KS"
    
    # 3. 미국 주식 패턴 (예: AAPL)
    us_pattern = r'\b([A-Z]{1,5})\b'
    match = re.search(us_pattern, query.upper())
    if match:
        symbol = match.group(1)
        # 유효한 미국 주식 심볼인지 확인
        if len(symbol) >= 1 and len(symbol) <= 5:
            return symbol
    
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
    
    # 동적 설정에서 검색
    results = stock_config_loader.search_stocks(query, limit=5)
    for symbol, info in results:
        found_symbols.append(symbol)
    
    # 한국 주식의 경우 미국 티커도 추가
    for symbol in found_symbols[:]:  # 복사본으로 순회
        stock_info = stock_config_loader.get_stock_info(symbol)
        if stock_info and stock_info.get('country') == 'korean':
            # 한국 주식의 미국 티커 추가 (일반적인 매핑)
            us_symbol = get_us_symbol_for_korean(symbol)
            if us_symbol:
                found_symbols.append(us_symbol)
    
    # 중복 제거
    return list(set(found_symbols))


def get_us_symbol_for_korean(korean_symbol: str) -> Optional[str]:
    """한국 주식 심볼에 대응하는 미국 티커 반환
    
    Args:
        korean_symbol: 한국 주식 심볼 (예: "005930.KS")
        
    Returns:
        Optional[str]: 미국 티커 또는 None
    """
    # 주요 한국 주식의 미국 티커 매핑
    korean_to_us = {
        "005930.KS": "SSNLF",  # 삼성전자
        "000660.KS": "HXSCL",  # SK하이닉스
        "035420.KS": "NHNCF",  # 네이버
        "005380.KS": "HYMTF",  # 현대차
        "000270.KS": "KIMTF",  # 기아
        "066570.KS": "LPLIY",  # LG전자
        "051910.KS": "LGCHEM", # LG화학
    }
    
    return korean_to_us.get(korean_symbol)


def get_company_name_from_symbol(symbol: str) -> Optional[str]:
    """심볼에서 회사 이름 추출
    
    Args:
        symbol: 주식 심볼 (예: "005930.KS")
        
    Returns:
        Optional[str]: 회사 이름 또는 None
    """
    stock_info = stock_config_loader.get_stock_info(symbol)
    if stock_info and stock_info.get('names'):
        # 한국어 이름 우선 반환
        names = stock_info['names']
        korean_names = [name for name in names if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7AF for char in name)]
        if korean_names:
            return korean_names[0]
        return names[0]
    
    return None


def is_valid_symbol(symbol: str) -> bool:
    """유효한 심볼인지 확인
    
    Args:
        symbol: 주식 심볼
        
    Returns:
        bool: 유효 여부
    """
    # 동적 설정에서 확인
    if stock_config_loader.get_stock_info(symbol):
        return True
    
    # 정규식 패턴으로 확인 (fallback)
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
        "어떻게", "어떤", "무엇", "뭐", "궁금", "궁금해", "궁금합니다", "현재가",
        "차트", "그래프", "시각화", "보여줘", "보여주세요"
    ]
    
    cleaned_query = query
    for keyword in keywords:
        cleaned_query = cleaned_query.replace(keyword, "")
    
    # 공백 제거하고 반환
    return cleaned_query.strip()


def get_all_symbols() -> List[str]:
    """모든 심볼 목록 반환
    
    Returns:
        List[str]: 모든 심볼 리스트
    """
    return stock_config_loader.get_all_symbols()


def get_symbols_by_sector(sector: str) -> List[str]:
    """섹터별 심볼 목록 반환
    
    Args:
        sector: 섹터명 (technology, automotive, biotechnology 등)
        
    Returns:
        List[str]: 해당 섹터의 심볼 목록
    """
    return stock_config_loader.get_symbols_by_sector(sector)


def get_symbols_by_country(country: str) -> List[str]:
    """국가별 심볼 목록 반환
    
    Args:
        country: 국가명 (korean, us, global)
        
    Returns:
        List[str]: 해당 국가의 심볼 목록
    """
    return stock_config_loader.get_symbols_by_country(country)


def search_stocks(keyword: str, limit: int = 10) -> List[tuple]:
    """키워드로 주식 검색
    
    Args:
        keyword: 검색 키워드
        limit: 최대 결과 수
        
    Returns:
        List[tuple]: (심볼, 정보) 튜플 리스트
    """
    return stock_config_loader.search_stocks(keyword, limit)


def reload_stock_config():
    """주식 설정 다시 로드"""
    stock_config_loader.reload_config()


# 하위 호환성을 위한 별칭들
STOCK_SYMBOL_MAPPING = {}  # 더 이상 사용되지 않음 (동적 로딩으로 대체)
STOCK_SYMBOL_MAP = STOCK_SYMBOL_MAPPING
MULTI_SYMBOL_MAPPING = {}  # 더 이상 사용되지 않음
NUMBER_SYMBOL_MAPPING = {}  # 더 이상 사용되지 않음
get_stock_symbol = extract_symbol_from_query


# 디버깅용 함수
def debug_stock_config():
    """주식 설정 디버깅 정보 출력"""
    print("=== 주식 설정 디버깅 정보 ===")
    print(f"총 심볼 수: {len(stock_config_loader.get_all_symbols())}")
    
    # 섹터별 통계
    sectors = ['technology', 'automotive', 'biotechnology', 'chemicals', 'finance']
    for sector in sectors:
        symbols = stock_config_loader.get_symbols_by_sector(sector)
        print(f"{sector}: {len(symbols)}개")
    
    # 국가별 통계
    countries = ['korean', 'us', 'global']
    for country in countries:
        symbols = stock_config_loader.get_symbols_by_country(country)
        print(f"{country}: {len(symbols)}개")
    
    print("=== 디버깅 정보 완료 ===")


if __name__ == "__main__":
    # 테스트 실행
    debug_stock_config()
    
    # 테스트 쿼리들
    test_queries = [
        "삼성전자 주가 알려줘",
        "005930 현재가",
        "AAPL 분석해줘",
        "네이버 뉴스"
    ]
    
    print("\n=== 심볼 추출 테스트 ===")
    for query in test_queries:
        symbol = extract_symbol_from_query(query)
        print(f"'{query}' -> {symbol}")