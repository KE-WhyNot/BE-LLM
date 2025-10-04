"""
주식 설정 로더

YAML 파일에서 주식 심볼 설정을 동적으로 로드하는 유틸리티
"""

import yaml
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class StockConfigLoader:
    """주식 설정 로더 클래스"""
    
    def __init__(self, config_path: str = "config/stocks.yaml"):
        """
        주식 설정 로더 초기화
        
        Args:
            config_path: YAML 설정 파일 경로
        """
        self.config_path = config_path
        self._config = None
        self._stock_mapping = {}
        self._symbol_mapping = {}
        self._load_config()
    
    def _load_config(self):
        """YAML 설정 파일 로드"""
        try:
            # 프로젝트 루트 기준으로 경로 설정
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / self.config_path
            
            if not config_file.exists():
                raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            self._build_mappings()
            print(f"✅ 주식 설정 로드 완료: {len(self._stock_mapping)}개 종목")
            
        except Exception as e:
            print(f"❌ 주식 설정 로드 실패: {e}")
            self._config = {}
            self._stock_mapping = {}
            self._symbol_mapping = {}
    
    def _build_mappings(self):
        """매핑 딕셔너리 생성"""
        self._stock_mapping = {}
        self._symbol_mapping = {}
        
        # 한국 주식
        korean_stocks = self._config.get('korean_stocks', {})
        for stock_id, stock_info in korean_stocks.items():
            symbol = stock_info['symbol']
            names = stock_info['names']
            
            # 이름 -> 심볼 매핑
            for name in names:
                self._stock_mapping[name.lower()] = symbol
            
            # 심볼 -> 정보 매핑
            self._symbol_mapping[symbol] = {
                'names': names,
                'sector': stock_info.get('sector', 'unknown'),
                'description': stock_info.get('description', ''),
                'market_cap_rank': stock_info.get('market_cap_rank', 999),
                'country': 'korean'
            }
        
        # 미국 주식
        us_stocks = self._config.get('us_stocks', {})
        for stock_id, stock_info in us_stocks.items():
            symbol = stock_info['symbol']
            names = stock_info['names']
            
            # 이름 -> 심볼 매핑
            for name in names:
                self._stock_mapping[name.lower()] = symbol
            
            # 심볼 -> 정보 매핑
            self._symbol_mapping[symbol] = {
                'names': names,
                'sector': stock_info.get('sector', 'unknown'),
                'description': stock_info.get('description', ''),
                'market_cap_rank': stock_info.get('market_cap_rank', 999),
                'country': 'us'
            }
        
        # 지수
        indices = self._config.get('indices', {})
        for index_id, index_info in indices.items():
            symbol = index_info['symbol']
            names = index_info['names']
            
            # 이름 -> 심볼 매핑
            for name in names:
                self._stock_mapping[name.lower()] = symbol
            
            # 심볼 -> 정보 매핑
            self._symbol_mapping[symbol] = {
                'names': names,
                'sector': 'index',
                'description': index_info.get('description', ''),
                'market_cap_rank': 0,
                'country': 'global'
            }
    
    def get_symbol(self, query: str) -> Optional[str]:
        """
        쿼리에서 주식 심볼 추출
        
        Args:
            query: 사용자 입력 쿼리
            
        Returns:
            주식 심볼 또는 None
        """
        if not query:
            return None
        
        # 띄어쓰기 제거 및 소문자 변환
        query_clean = query.replace(' ', '').lower()
        
        # 1. 정확한 매칭
        if query_clean in self._stock_mapping:
            return self._stock_mapping[query_clean]
        
        # 2. 부분 매칭 (긴 이름부터)
        sorted_names = sorted(self._stock_mapping.keys(), key=len, reverse=True)
        for name in sorted_names:
            if name in query_clean or query_clean in name:
                return self._stock_mapping[name]
        
        # 3. 6자리 숫자만 있는 경우 (.KS 추가)
        if query_clean.isdigit() and len(query_clean) == 6:
            return f"{query_clean}.KS"
        
        # 4. 완전한 심볼 패턴 검색
        if '.KS' in query_clean or query_clean.startswith('^'):
            return query_clean.upper()
        
        return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        심볼로 주식 정보 조회
        
        Args:
            symbol: 주식 심볼
            
        Returns:
            주식 정보 딕셔너리 또는 None
        """
        return self._symbol_mapping.get(symbol)
    
    def get_all_symbols(self) -> List[str]:
        """모든 심볼 목록 반환"""
        return list(self._symbol_mapping.keys())
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """
        섹터별 심볼 목록 반환
        
        Args:
            sector: 섹터명 (technology, automotive, biotechnology 등)
            
        Returns:
            해당 섹터의 심볼 목록
        """
        symbols = []
        for symbol, info in self._symbol_mapping.items():
            if info.get('sector') == sector:
                symbols.append(symbol)
        return symbols
    
    def get_symbols_by_country(self, country: str) -> List[str]:
        """
        국가별 심볼 목록 반환
        
        Args:
            country: 국가명 (korean, us, global)
            
        Returns:
            해당 국가의 심볼 목록
        """
        symbols = []
        for symbol, info in self._symbol_mapping.items():
            if info.get('country') == country:
                symbols.append(symbol)
        return symbols
    
    def search_stocks(self, keyword: str, limit: int = 10) -> List[Tuple[str, Dict]]:
        """
        키워드로 주식 검색
        
        Args:
            keyword: 검색 키워드
            limit: 최대 결과 수
            
        Returns:
            (심볼, 정보) 튜플 리스트
        """
        results = []
        keyword_lower = keyword.lower()
        
        for symbol, info in self._symbol_mapping.items():
            found = False
            # 이름에서 검색
            for name in info['names']:
                if keyword_lower in name.lower():
                    results.append((symbol, info))
                    found = True
                    break
            
            # 설명에서 검색 (이름에서 찾지 못한 경우만)
            if not found and keyword_lower in info.get('description', '').lower():
                results.append((symbol, info))
        
        # 시가총액 순으로 정렬
        results.sort(key=lambda x: x[1].get('market_cap_rank', 999))
        
        return results[:limit]
    
    def reload_config(self):
        """설정 파일 다시 로드"""
        self._load_config()
    
    def get_config(self) -> Dict:
        """전체 설정 반환"""
        return self._config


# 전역 인스턴스
stock_config_loader = StockConfigLoader()
