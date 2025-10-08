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

# 지식 에이전트 전용 네임스페이스 매핑
KNOWLEDGE_NAMESPACES = {
    "terminology": "cat_financial_terminology",  # 금융 용어 설명
    "financial_analysis": "cat_financial_statements",  # 재무제표 & 경제동향
    "youth_policy": "cat_youth_policy",  # 청년 정책
    "general": "cat_general_knowledge"  # 일반 금융 지식
}

# 네임스페이스별 설명
NAMESPACE_DESCRIPTIONS = {
    "cat_financial_terminology": "금융 용어, 개념, 정의 관련",
    "cat_financial_statements": "재무제표 분석, 경제 동향, 기업 실적",
    "cat_youth_policy": "청년 금융 지원, 정부 정책, 청년 혜택",
    "cat_general_knowledge": "일반 금융 지식, 투자 전략, 리스크 관리"
}

print(f"📊 Pinecone 설정:")
print(f"   - API Key: {'설정됨' if PINECONE_API_KEY else '미설정'}")
print(f"   - Index Name: {PINECONE_INDEX_NAME}")
print(f"   - Model: {EMBEDDING_MODEL_NAME}")
print(f"   - Default Namespace: {DEFAULT_NAMESPACE}")
print(f"   - Knowledge Namespaces: {len(KNOWLEDGE_NAMESPACES)}개")
print(f"   - Top K: {TOP_K}")
