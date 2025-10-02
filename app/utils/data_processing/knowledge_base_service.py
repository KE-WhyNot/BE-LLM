import os
from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
"""
# RAG 엔진의 실제 구현이 담긴 rag_service 인스턴스를 직접 가져옵니다.
# FinancialRAGService 클래스를 가져오는 것이 아니라, 생성된 전역 인스턴스를 사용합니다.
"""
from app.services.rag_service import rag_service
from app.services.monitoring_service import monitoring_service

class FinancialKnowledgeBaseService:
    """
    지식 콘텐츠를 관리하고 RAG 엔진으로 전달하는 서비스 (최종 버전)
    - 역할: 데이터 소스(e.g., /data 폴더)에서 문서를 로드하여 RAG 엔진에 전달.
    """
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        # RAG 엔진 인스턴스를 멤버 변수로 소유합니다.
        self.rag_engine = rag_service
        self.monitoring_service = monitoring_service

    """
    # 기존: 여러 create 함수들이 각각의 내용을 하드코딩하여 반환
    # 변경: 'data' 디렉토리의 모든 파일을 한번에 로드하여 지식 베이스를 구축하는 단일 함수로 변경
    """
    def build_from_data_directory(self):
        """
        'data' 디렉토리의 모든 .txt 파일을 읽어 RAG 엔진을 통해 지식 베이스를 구축합니다.
        """
        print(f"'{self.data_path}' 디렉토리에서 지식 베이스 구축을 시작합니다.")
        
        if not os.path.exists(self.data_path):
            print(f"오류: '{self.data_path}' 디렉토리를 찾을 수 없습니다.")
            return

        # DirectoryLoader를 사용해 폴더 내 모든 .txt 파일을 한번에 로드합니다.
        loader = DirectoryLoader(
            self.data_path, 
            glob="**/*.txt", 
            loader_cls=TextLoader, 
            loader_kwargs={'encoding': 'utf-8'},
            show_progress=True,
            use_multithreading=True
        )
        
        documents = loader.load()
        
        if not documents:
            print("로드할 문서가 없습니다. 'data' 폴더에 .txt 파일이 있는지 확인하세요.")
            return

        # 로드된 문서를 RAG 엔진의 add_financial_documents 함수에 전달합니다.
        self.rag_engine.add_financial_documents(documents)
        
        print(f"'{self.data_path}'의 모든 문서를 사용하여 지식 베이스 구축을 완료했습니다.")
        self.monitoring_service.log_financial_data_request(
            "knowledge_base_build", 
            {"document_count": len(documents)}, 
            True
        )


# 전역 지식 베이스 서비스 인스턴스 생성
knowledge_base_service = FinancialKnowledgeBaseService()

"""
# 스크립트를 직접 실행할 때 지식 베이스 구축 프로세스를 트리거하도록 __main__ 블록을 추가/수정합니다.
# python app/services/knowledge_base_service.py 명령으로 DB를 손쉽게 업데이트할 수 있습니다.
"""
if __name__ == '__main__':
    # FinancialKnowledgeBaseService 인스턴스의 메서드를 호출하여 지식 베이스를 구축합니다.
    knowledge_base_service.build_from_data_directory()