"""
금융 RAG (Retrieval-Augmented Generation) 서비스

역할: ChromaDB 벡터 스토어 관리 및 금융 지식 검색 (순수 RAG)
- 벡터 스토어 초기화 및 관리
- 문서 추가 (knowledge_base_service에서 호출)
- 유사도 기반 문서 검색
- 지식 쿼리 처리 ("PER이 뭐야?" 등)
"""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Optional
from app.config import settings
from app.utils.common_utils import get_config_manager


class FinancialRAGService:
    """금융 RAG 서비스 - 벡터 검색 전용"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        RAG 서비스 초기화
        
        Args:
            persist_directory: ChromaDB 저장 경로 (None이면 설정에서 가져옴)
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        
        # 공통 설정 사용
        config_manager = get_config_manager()
        rag_settings = config_manager.get_rag_settings()
        chunk_settings = config_manager.get_chunk_settings()
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config_manager.get_embedding_model(),
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_settings['chunk_size'],
            chunk_overlap=chunk_settings['chunk_overlap'],
            length_function=len,
        )
        self.max_search_results = rag_settings['max_search_results']
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """벡터 스토어 초기화"""
        try:
            # 기존 벡터 스토어 로드 시도
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("✅ 기존 벡터 스토어를 성공적으로 로드했습니다.")
        except Exception as e:
            print(f"⚠️ 벡터 스토어 로드 실패: {e}")
            # 새로운 벡터 스토어 생성
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("✅ 새로운 벡터 스토어를 생성했습니다.")
    
    def add_financial_documents(self, documents: List[Document]):
        """
        금융 문서를 벡터 스토어에 추가
        
        호출 위치: knowledge_base_service.py의 build_from_data_directory()
        
        Args:
            documents: LangChain Document 리스트
        """
        if not documents:
            print("⚠️ 추가할 문서가 없습니다.")
            return
        
        # 문서 분할
        split_docs = self.text_splitter.split_documents(documents)
        
        # 벡터 스토어에 추가
        self.vectorstore.add_documents(split_docs)
        print(f"✅ {len(split_docs)}개의 문서 청크를 벡터 스토어에 추가했습니다.")
    
    def search_relevant_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        관련 문서 검색 (벡터 유사도 기반)
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 개수 (None이면 설정값 사용)
            
        Returns:
            List[Document]: 유사도가 높은 상위 k개 문서
        """
        if k is None:
            k = self.max_search_results
            
        if not self.vectorstore:
            print("⚠️ 벡터 스토어가 초기화되지 않았습니다.")
            return []
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            print(f"🔍 '{query}'에 대해 {len(docs)}개의 관련 문서를 찾았습니다.")
            return docs
        except Exception as e:
            print(f"❌ 문서 검색 실패: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> str:
        """
        쿼리에 대한 컨텍스트 정보 생성 (knowledge 쿼리용)
        
        호출 위치: financial_workflow.py의 _search_knowledge()
        
        Args:
            query: 사용자 질문 (예: "PER이 뭐야?", "분산투자란?")
            
        Returns:
            str: 관련 금융 지식 컨텍스트
        """
        # 관련 문서 검색
        relevant_docs = self.search_relevant_documents(query, k=3)
        
        context_parts = []
        
        # 검색된 문서 내용
        if relevant_docs:
            context_parts.append("📚 관련 금융 지식:")
            for i, doc in enumerate(relevant_docs, 1):
                content = doc.page_content[:500]  # 최대 500자
                context_parts.append(f"\n{i}. {content}...")
        else:
            context_parts.append("⚠️ 관련 금융 지식을 찾을 수 없습니다.")
        
        return "\n".join(context_parts)


# 전역 RAG 서비스 인스턴스
rag_service = FinancialRAGService()
