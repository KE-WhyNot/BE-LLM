from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    
    # LangSmith 설정
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "financial-chatbot"
    
    # 데이터베이스 설정
    database_url: str = "mysql+pymysql://root:password@127.0.0.1/financial_db"
    
    # 벡터 데이터베이스 설정
    chroma_persist_directory: str = "./chroma_db"
    
    # 임베딩 모델 설정 (가벼운 모델로 변경)
    embedding_model_path: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Gemini 모델 설정
    gemini_temperature: float = 0.1
    gemini_max_tokens: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # .env 파일의 추가 필드들을 무시

# 전역 설정 인스턴스
settings = Settings()

# 환경 변수 설정
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.google_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key
if settings.langsmith_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2)
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
