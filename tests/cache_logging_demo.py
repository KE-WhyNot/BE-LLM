import time


from app.services.langgraph_enhanced.agents.base_agent import BaseAgent


class FakeLLMManager:
    """LLM 호출 캐시/지연을 모사하는 페이크 매니저"""
    def __init__(self):
        self._cache = {}

    def get_llm(self, *args, **kwargs):
        return object()  # 더미 객체

    def invoke_with_cache(self, llm, prompt: str, purpose: str = "general") -> str:
        key = (prompt, purpose)
        if key in self._cache:
            print("📦 [FAKE] cache hit")
            return self._cache[key]
        # 첫 호출에는 인위적 지연
        time.sleep(0.2)
        resp = f"FAKE_RESPONSE[{purpose}] for {prompt[:30]}"
        self._cache[key] = resp
        print("🆕 [FAKE] cache set")
        return resp


class MinimalAgent(BaseAgent):
    def __init__(self):
        # super().__init__ 호출을 피하고 직접 주입(실제 LLM 사용 방지)
        self.llm_manager = FakeLLMManager()
        self.llm = self.llm_manager.get_llm(purpose="analysis")
        self.purpose = "analysis"
        self.agent_name = "minimal_agent"

    def get_prompt_template(self) -> str:
        return "테스트 프롬프트: {msg}"

    def process(self, msg: str):
        prompt = self.get_prompt_template().format(msg=msg)
        # 1차 호출(캐시 미스 → 지연)
        r1 = self.invoke_llm_with_cache(prompt, purpose=self.purpose, log_label="demo_call")
        # 2차 호출(캐시 히트 → 즉시)
        r2 = self.invoke_llm_with_cache(prompt, purpose=self.purpose, log_label="demo_call")
        return r1, r2


def main():
    agent = MinimalAgent()
    t0 = time.time()
    r1, r2 = agent.process("안녕하세요")
    dt = (time.time() - t0) * 1000
    print(f"\n⏱ 전체 실행 시간: {dt:.1f}ms")
    print(f"응답 동일성 확인: {r1 == r2}")


if __name__ == "__main__":
    main()


