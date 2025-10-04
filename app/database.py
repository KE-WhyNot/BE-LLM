from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings

# 환경 변수에서 데이터베이스 URL 가져오기 (보안 강화)
SQLALCHEMY_DATABASE_URL = settings.database_url

# 데이터베이스 연결 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300     # 5분마다 연결 재사용
)

# 데이터베이스와 통신할 세션(Session) 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델의 기초가 될 Base 클래스 생성
Base = declarative_base()