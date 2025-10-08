# Pinecone 설정 파일
import os
from app.config import settings

# Pinecone 설정
PINECONE_API_KEY = settings.pinecone_api_key or os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = settings.pinecone_index_name or os.getenv("PINECONE_INDEX_NAME", "finance-rag-index")
EMBEDDING_MODEL_NAME = settings.embedding_model_name or os.getenv("EMBEDDING_MODEL_NAME", "kakaobank/kf-deberta-base")
BATCH_SIZE = settings.batch_size or int(os.getenv("BATCH_SIZE", "32"))
MAX_LENGTH = settings.max_length or int(os.getenv("MAX_LENGTH", "256"))
TOP_K = settings.top_k or int(os.getenv("TOP_K", "20"))

# 네임스페이스 설정
DEFAULT_NAMESPACE = "cat_financial_statements"

print(f"📊 Pinecone 설정:")
print(f"   - API Key: {'설정됨' if PINECONE_API_KEY else '미설정'}")
print(f"   - Index Name: {PINECONE_INDEX_NAME}")
print(f"   - Model: {EMBEDDING_MODEL_NAME}")
print(f"   - Namespace: {DEFAULT_NAMESPACE}")
print(f"   - Top K: {TOP_K}")
