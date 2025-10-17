"""
기본 에이전트 클래스
모든 에이전트의 공통 기능을 제공
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time
try:
    # 실제 실행 환경에서는 전역 llm_manager를 사용
    from ..llm_manager import llm_manager as _global_llm_manager
except Exception:
    # 테스트/데모 환경에서 외부 의존성 없이 임시 매니저를 주입 가능
    _global_llm_manager = None


class BaseAgent(ABC):
    """기본 에이전트 클래스"""
    
    def __init__(self, purpose: str = "general"):
        # 전역 LLM 매니저 공유 (캐시 공유). 테스트 환경에서는 외부 의존성 없이 주입 가능
        self.llm_manager = _global_llm_manager
        self.llm = self.llm_manager.get_llm(purpose=purpose) if self.llm_manager else None
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

    def invoke_llm_with_cache(self, prompt: str, purpose: str = None, log_label: str = None) -> str:
        """LLM 호출(캐시 적용) + 실행 시간 로깅 공통 헬퍼"""
        label = log_label or "llm_invoke"
        start = time.time()
        print(f"⏳ [{self.agent_name}] {label} 시작")
        try:
            response_text = self.llm_manager.invoke_with_cache(
                self.llm,
                prompt,
                purpose=(purpose or self.purpose)
            )
            elapsed = (time.time() - start) * 1000
            print(f"✅ [{self.agent_name}] {label} 완료 - {elapsed:.1f}ms")
            return response_text
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ [{self.agent_name}] {label} 실패 - {elapsed:.1f}ms - {e}")
            raise

