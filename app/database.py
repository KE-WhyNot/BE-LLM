from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ⚠️ 아래 접속 정보는 실제 프로그래머님의 MySQL 환경에 맞게 수정해야 합니다.
# 형식: "mysql+pymysql://[사용자이름]:[비밀번호]@[DB서버주소]/[DB이름]"
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@127.0.0.1/financial_db"

# 데이터베이스 연결 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 데이터베이스와 통신할 세션(Session) 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델의 기초가 될 Base 클래스 생성
Base = declarative_base()