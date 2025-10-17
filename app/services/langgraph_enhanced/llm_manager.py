"""
LLM 관리자 (Gemini 2.0 Flash 전용)
깔끔하게 Gemini만 사용하도록 단순화
"""

from typing import Optional, List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.utils.common_utils import CacheManager
import hashlib
import time

try:
    import numpy as _np
    from sentence_transformers import SentenceTransformer
except Exception:
    _np = None
    SentenceTransformer = None


class LLMManager:
    """LLM 관리자 (Gemini 전용)"""
    
    def __init__(self):
        self.llm_cache = {}
        self.default_model = "gemini-2.0-flash"  # 정식 2.0 버전, 높은 할당량
        # LLM 응답 캐싱 (5분 TTL)
        self.response_cache = CacheManager(default_ttl=300)
        # 목적별 TTL 테이블
        self.purpose_ttl: Dict[str, int] = {
            "classification": 90,
            "analysis": 120,
            "news": 300,
            "knowledge": 3600,
            "response": 600,
            "general": 300,
        }
        # 의미(임베딩) 기반 캐시
        self.semantic_cache_enabled = _np is not None and SentenceTransformer is not None
        self._semantic_model = None
        self.semantic_cache: Dict[str, List[Dict[str, Any]]] = {}  # purpose -> entries
        self.semantic_capacity_per_purpose = 500
    
    def get_llm(self, 
                model_name: Optional[str] = None, 
                temperature: float = 0.7,
                purpose: str = "general",
                **kwargs) -> ChatGoogleGenerativeAI:
        """
        Gemini LLM 인스턴스 반환 (용도별 최적화된 파라미터)
        """
        t0 = time.time()
        # 모델명이 없으면 기본 모델 사용
        if model_name is None:
            model_name = self.default_model
        
        # 용도별 최적화된 파라미터 설정
        optimized_params = self._get_optimized_params(purpose, temperature, **kwargs)
        
        # 캐시에서 확인
        cache_key = f"{model_name}_{purpose}_{optimized_params['temperature']}_{hash(str(optimized_params))}"
        if cache_key in self.llm_cache:
            llm_cached = self.llm_cache[cache_key]
            print(f"📦 get_llm HIT: {model_name} ({purpose}) - {(time.time()-t0)*1000:.1f}ms")
            return llm_cached
        # API 키 확인
        google_api_key = settings.google_api_key
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

        # Gemini LLM 인스턴스 생성
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            **optimized_params
        )
        
        # 캐시에 저장
        self.llm_cache[cache_key] = llm
        
        print(f"🤖 Gemini LLM 로드: {model_name} ({purpose}, temperature: {optimized_params['temperature']}) - {(time.time()-t0)*1000:.1f}ms")
        return llm
    
    def _get_optimized_params(self, purpose: str, temperature: float, **kwargs) -> dict:
        """용도별 최적화된 LLM 파라미터 반환"""
        base_params = {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
            **kwargs
        }
        
        # 용도별 최적화
        if purpose == "classification":
            return {
                **base_params,
                "temperature": 0.1,  # 분류는 일관성 중요
                "max_output_tokens": 512,  # 구조화된 응답을 위해 충분한 토큰
                "top_p": 0.8
            }
        elif purpose == "analysis":
            return {
                **base_params,
                "temperature": 0.3,  # 분석은 균형잡힌 창의성
                "max_output_tokens": 4096,  # 상세한 분석 필요
                "top_p": 0.9
            }
        elif purpose == "news":
            return {
                **base_params,
                "temperature": 0.2,  # 뉴스는 객관성 중요
                "max_output_tokens": 2048,
                "top_p": 0.85
            }
        elif purpose == "knowledge":
            return {
                **base_params,
                "temperature": 0.4,  # 교육적 설명은 적당한 창의성
                "max_output_tokens": 3072,
                "top_p": 0.9
            }
        elif purpose == "response":
            return {
                **base_params,
                "temperature": 0.7,  # 응답은 자연스러움 중요
                "max_output_tokens": 2048,
                "top_p": 0.9
            }
        else:  # general
            return base_params
    
    def get_default_llm(self, temperature: float = 0.7, purpose: str = "general", **kwargs) -> ChatGoogleGenerativeAI:
        """기본 Gemini LLM 반환"""
        return self.get_llm(model_name=None, temperature=temperature, purpose=purpose, **kwargs)
    
    def invoke_with_cache(self, llm: ChatGoogleGenerativeAI, prompt: str, purpose: str = "general") -> str:
        """LLM 호출 시 캐싱 적용 + 타이밍 로그"""
        t0 = time.time()
        cache_key = hashlib.md5(f"{prompt}_{purpose}".encode()).hexdigest()
        cached_response = self.response_cache.get(cache_key)
        if cached_response:
            print(f"📦 LLM 응답 캐시 HIT: {purpose} - {(time.time()-t0)*1000:.1f}ms")
            return cached_response
        print(f"⏳ LLM 호출 시작: {purpose}")
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        ttl = self.purpose_ttl.get(purpose, 300)
        self.response_cache.set(cache_key, response_text, ttl=ttl)
        print(f"💾 LLM 응답 캐시 저장: {purpose} - {(time.time()-t0)*1000:.1f}ms (ttl={ttl}s)")
        return response_text

    # === 의미(임베딩) 기반 캐시 ===
    def _get_embedding_model(self):
        if not self.semantic_cache_enabled:
            return None
        if self._semantic_model is None:
            try:
                # 경량 모델 기본 사용
                self._semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.semantic_cache_enabled = False
                self._semantic_model = None
        return self._semantic_model

    def _semantic_lookup(self, prompt: str, purpose: str, threshold: float = 0.92) -> Optional[str]:
        if not self.semantic_cache_enabled:
            return None
        model = self._get_embedding_model()
        if model is None:
            return None
        entries = self.semantic_cache.get(purpose, [])
        if not entries:
            return None
        try:
            qv = model.encode([prompt])[0]
            best = None
            best_sim = -1.0
            for e in entries:
                sim = float(_np.dot(qv, e["vec"]) / ( _np.linalg.norm(qv) * _np.linalg.norm(e["vec"]) + 1e-9 ))
                if sim > best_sim:
                    best_sim = sim
                    best = e
            if best and best_sim >= threshold:
                print(f"📦🔎 의미 캐시 HIT: {purpose} (sim={best_sim:.3f})")
                return best["response"]
        except Exception:
            return None
        return None

    def _semantic_store(self, prompt: str, purpose: str, response_text: str):
        if not self.semantic_cache_enabled:
            return
        model = self._get_embedding_model()
        if model is None:
            return
        try:
            vec = model.encode([prompt])[0]
            entries = self.semantic_cache.setdefault(purpose, [])
            entries.append({"vec": vec, "response": response_text})
            # 용량 제한
            if len(entries) > self.semantic_capacity_per_purpose:
                self.semantic_cache[purpose] = entries[-self.semantic_capacity_per_purpose:]
        except Exception:
            pass

    def invoke_with_semantic_cache(self, llm: ChatGoogleGenerativeAI, prompt: str, purpose: str = "general", threshold: float = 0.92) -> str:
        # 1) 정확 캐시 조회
        exact = self.invoke_with_cache(llm, prompt, purpose)
        if exact is not None:
            # invoke_with_cache는 miss 시 LLM을 호출하므로, 의미 캐시만 별도로 제공하려면 분리 필요.
            # 여기서는 의미 캐시 우선 시나리오를 위해 정확 캐시 조회만 선행 체크 후 직접 처리
            cache_key = hashlib.md5(f"{prompt}_{purpose}".encode()).hexdigest()
            cached_only = self.response_cache.get(cache_key)
            if cached_only is not None:
                return cached_only
        # 2) 의미 캐시 조회
        sem = self._semantic_lookup(prompt, purpose, threshold)
        if sem is not None:
            return sem
        # 3) LLM 호출 후 저장
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        ttl = self.purpose_ttl.get(purpose, 300)
        cache_key = hashlib.md5(f"{prompt}_{purpose}".encode()).hexdigest()
        self.response_cache.set(cache_key, response_text, ttl=ttl)
        self._semantic_store(prompt, purpose, response_text)
        print(f"💾 의미 캐시에 저장: {purpose}")
        return response_text
    
    def clear_cache(self):
        """LLM 캐시 초기화"""
        self.llm_cache.clear()
        self.response_cache.clear()
        print("🧹 LLM 캐시가 초기화되었습니다.")


# 전역 LLM 관리자 인스턴스
llm_manager = LLMManager()


def get_gemini_llm(model_name: Optional[str] = None, 
                   temperature: float = 0.7, 
                   **kwargs) -> ChatGoogleGenerativeAI:
    """Gemini LLM 인스턴스 반환 (편의 함수)"""
    return llm_manager.get_llm(model_name, temperature, **kwargs)


def get_default_gemini_llm(temperature: float = 0.7, **kwargs) -> ChatGoogleGenerativeAI:
    """기본 Gemini LLM 반환 (편의 함수)"""
    return llm_manager.get_default_llm(temperature, **kwargs)
