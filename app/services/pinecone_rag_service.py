# 간단한 Pinecone RAG 서비스 (기존 시스템과 호환)
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from pinecone import Pinecone
from app.services.pinecone_config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBEDDING_MODEL_NAME, 
    MAX_LENGTH, TOP_K, DEFAULT_NAMESPACE
)

# 전역 변수
_pinecone_client = None
_pinecone_index = None
_tokenizer = None
_model = None
_device = None


def get_pinecone_client():
    """Pinecone 클라이언트 초기화"""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
        print("✅ Pinecone 클라이언트 초기화 완료")
    return _pinecone_client


def get_pinecone_index():
    """Pinecone 인덱스 연결"""
    global _pinecone_index
    if _pinecone_index is None:
        client = get_pinecone_client()
        _pinecone_index = client.Index(PINECONE_INDEX_NAME)
        print(f"✅ Pinecone 인덱스 연결: {PINECONE_INDEX_NAME}")
    return _pinecone_index


def get_embedding_model():
    """임베딩 모델 초기화"""
    global _tokenizer, _model, _device
    if _tokenizer is None or _model is None:
        print(f"🤖 임베딩 모델 로딩: {EMBEDDING_MODEL_NAME}")
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
        _model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME).to(_device).eval()
        print("✅ 임베딩 모델 로딩 완료")
    return _tokenizer, _model, _device


def mean_pooling(last_hidden_state, attention_mask):
    """평균 풀링으로 문장 임베딩 생성"""
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    summed = (last_hidden_state * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def embed_text(text):
    """텍스트를 임베딩으로 변환"""
    tokenizer, model, device = get_embedding_model()
    
    with torch.no_grad():
        encoded = tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt"
        ).to(device)

        outputs = model(**encoded)
        last_hidden_state = outputs.last_hidden_state

        embeddings = mean_pooling(last_hidden_state, encoded["attention_mask"])
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy()[0]


async def search_pinecone(query: str, top_k: int = None, namespace: str = None):
    """Pinecone에서 검색"""
    if top_k is None:
        top_k = TOP_K
    if namespace is None:
        namespace = DEFAULT_NAMESPACE
        
    try:
        index = get_pinecone_index()
        query_embedding = embed_text(query)
        
        # 비동기로 Pinecone 쿼리 실행
        import asyncio
        results = await asyncio.to_thread(
            index.query,
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        
        return results
    except Exception as e:
        print(f"❌ Pinecone 검색 오류: {e}")
        return None


async def get_context_for_query(query: str, top_k: int = 5, namespace: str = None):
    """쿼리에 대한 컨텍스트 반환 (namespace 지원)"""
    try:
        results = await search_pinecone(query, top_k=top_k, namespace=namespace)
        
        # results가 None인 경우 처리
        if results is None:
            print("⚠️ Pinecone 검색 결과가 None입니다")
            return ""
        
        if results and hasattr(results, 'matches') and results.matches:
            context_parts = []
            for match in results.matches:
                text = match.metadata.get("text", "") if hasattr(match, 'metadata') else ""
                if text:
                    context_parts.append(text)
            
            if context_parts:
                context = "\n".join(context_parts)
                print(f"✅ Pinecone에서 {len(context_parts)}개 문서 검색 완료 (namespace: {namespace or 'default'})")
                return context
            else:
                print("ℹ️ Pinecone에서 관련 문서를 찾을 수 없습니다 (텍스트 없음)")
                return ""
        else:
            print("ℹ️ Pinecone에서 관련 문서를 찾을 수 없습니다")
            return ""
            
    except Exception as e:
        print(f"❌ 컨텍스트 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return ""


class PineconeRAGService:
    """Pinecone 기반 RAG 서비스 (기존 시스템과 호환)"""
    
    def __init__(self):
        self.initialized = False
    
    def initialize(self):
        """서비스 초기화"""
        try:
            # Pinecone 초기화
            get_pinecone_client()
            get_pinecone_index()
            
            # 모델 초기화
            get_embedding_model()
            
            self.initialized = True
            print("✅ Pinecone RAG 서비스 초기화 완료")
            return True
        except Exception as e:
            print(f"❌ Pinecone RAG 서비스 초기화 실패: {e}")
            return False
    
    async def get_context_for_query(self, query: str, top_k: int = 5) -> str:
        """쿼리에 대한 컨텍스트 반환 (기존 시스템과 호환)"""
        try:
            results = await search_pinecone(query, top_k=top_k)
            
            # results가 None인 경우 처리
            if results is None:
                print("⚠️ Pinecone 검색 결과가 None입니다")
                return ""
            
            if results and hasattr(results, 'matches') and results.matches:
                context_parts = []
                for match in results.matches:
                    text = match.metadata.get("text", "") if hasattr(match, 'metadata') else ""
                    if text:
                        context_parts.append(text)
                
                if context_parts:
                    context = "\n".join(context_parts)
                    print(f"✅ Pinecone에서 {len(context_parts)}개 문서 검색 완료")
                    return context
                else:
                    print("ℹ️ Pinecone에서 관련 문서를 찾을 수 없습니다 (텍스트 없음)")
                    return ""
            else:
                print("ℹ️ Pinecone에서 관련 문서를 찾을 수 없습니다")
                return ""
                
        except Exception as e:
            print(f"❌ 컨텍스트 검색 실패: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def search(self, query: str, top_k: int = 5) -> list:
        """검색 결과 반환"""
        try:
            results = await search_pinecone(query, top_k=top_k)
            
            if results and results.matches:
                formatted_results = []
                for match in results.matches:
                    formatted_results.append({
                        "id": match.id,
                        "score": match.score,
                        "text": match.metadata.get("text", ""),
                        "metadata": match.metadata
                    })
                return formatted_results
            else:
                return []
                
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            return []
    
    def get_stats(self):
        """인덱스 통계 반환"""
        try:
            index = get_pinecone_index()
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "metric": stats.metric
            }
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return None


# 전역 RAG 서비스 인스턴스 (기존 시스템과 호환)
pinecone_rag_service = PineconeRAGService()
