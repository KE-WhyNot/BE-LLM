from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    # 환경 설정
    environment: Optional[str] = None
    debug: Optional[bool] = None
    
    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    
    # LangSmith 설정
    langchain_tracing_v2: Optional[bool] = None
    langchain_endpoint: Optional[str] = None
    langchain_project: Optional[str] = None
    
    # 데이터베이스 설정
    database_url: Optional[str] = None
    
    # 벡터 데이터베이스 설정
    chroma_persist_directory: Optional[str] = None
    
    # Neo4j 설정 (Data-Agent용)
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    
    # Gemini 모델 설정
    gemini_temperature: Optional[float] = None
    gemini_max_tokens: Optional[int] = None
    
    # 주식 설정 파일 경로
    stock_config_path: Optional[str] = None
    
    # RAG 설정
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    max_search_results: Optional[int] = None
    
    # Data-Agent 설정
    news_collection_interval: Optional[int] = None
    confidence_threshold: Optional[float] = None
    max_news_results: Optional[int] = None
    
    # RSS 피드 설정
    naver_rss_feeds: Optional[str] = None  # JSON 문자열로 저장
    daum_rss_feeds: Optional[str] = None   # JSON 문자열로 저장
    
    # 금융 키워드 설정
    finance_keywords: Optional[str] = None  # JSON 문자열로 저장
    
    # AI 모델 설정
    relation_extraction_model: Optional[str] = None
    embedding_model: Optional[str] = None
    
    # 성능 설정
    cache_duration: Optional[int] = None
    request_timeout: Optional[int] = None
    
    # 로깅 설정
    log_level: Optional[str] = None
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # .env 파일의 추가 필드들을 무시

# 전역 설정 인스턴스
settings = Settings()

# 환경 변수 설정 (LangSmith 호환성을 위해)
if settings.langsmith_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
if settings.langchain_tracing_v2 is not None:
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2)
if settings.langchain_endpoint:
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
if settings.langchain_project:
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
