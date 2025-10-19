# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('kakaobank/kf-deberta-base')"

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV CHROMA_PERSIST_DIRECTORY=/tmp/chroma_db

# 애플리케이션 실행 (gunicorn with uvicorn workers)
CMD ["gunicorn", "app.main:app", "-w", "8", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "--worker-connections", "1000"]