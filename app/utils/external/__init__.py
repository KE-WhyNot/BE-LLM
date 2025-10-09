"""
외부 API 유틸리티 모듈

역할: yfinance, Yahoo Finance RSS 등 외부 API 호출을 중앙화
"""

from .external_api_service import ExternalAPIService, external_api_service

__all__ = ['ExternalAPIService', 'external_api_service']
