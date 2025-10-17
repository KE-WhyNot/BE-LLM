"""
기본 에이전트 클래스
모든 에이전트의 공통 기능을 제공
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..llm_manager import LLMManager


class BaseAgent(ABC):
    """기본 에이전트 클래스"""
    
    def __init__(self, purpose: str = "general"):
        self.llm_manager = LLMManager()
        self.llm = self.llm_manager.get_llm(purpose=purpose)
        self.purpose = purpose
        self.agent_name = ""
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """프롬프트 템플릿 반환"""
        pass
    
    @abstractmethod
    def process(self, **kwargs) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        pass
    
    def log(self, message: str):
        """로그 출력"""
        print(f"🤖 {self.agent_name}: {message}")

