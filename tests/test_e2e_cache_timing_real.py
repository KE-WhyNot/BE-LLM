import os
import time
import pytest


def _check_env_or_skip():
    """실제 실행에 필요한 환경이 갖춰졌는지 점검하고 없으면 스킵"""
    from app.config import settings
    missing = []
    if not getattr(settings, "google_api_key", None):
        missing.append("GOOGLE_API_KEY")
    # Pinecone는 일부 시나리오에서만 쓰이므로 필수는 아님. 필요시 아래 주석 해제
    # try:
    #     from app.services.pinecone_config import PINECONE_API_KEY
    #     if not PINECONE_API_KEY:
    #         missing.append("PINECONE_API_KEY")
    # except Exception:
    #     pass
    if missing:
        pytest.skip(f"실제 E2E 실행 스킵: 필수 환경변수 없음: {', '.join(missing)}")


def _measure(router, prompt):
    t0 = time.perf_counter()
    result = router.process_query(prompt)
    dt = (time.perf_counter() - t0) * 1000
    print(f"\n⏱ '{prompt[:20]}...' 총 소요: {dt:.1f}ms | success={result.get('success')}")
    return dt, result


def test_e2e_cache_timing_real():
    _check_env_or_skip()

    # 전역 LLM 캐시 초기화
    from app.services.langgraph_enhanced.llm_manager import llm_manager
    try:
        llm_manager.clear_cache()
    except Exception:
        pass

    from app.services.langgraph_enhanced.workflow_router import WorkflowRouter
    router = WorkflowRouter()

    scenarios = [
        "안녕하세요",  # 일반 인사
        "삼성전자 주가 알려줘",  # 단순 주가
        "삼성전자 투자 분석해줘",  # 투자 분석(복합)
        "PER이 뭐야?",  # 지식(RAG)
    ]

    strict = os.getenv("STRICT_CACHE_ASSERT", "0") == "1"

    for q in scenarios:
        print(f"\n=== 시나리오: {q} ===")
        # 1차: 캐시 미스
        t1, _ = _measure(router, q)
        # 2차: 캐시 히트 기대
        t2, _ = _measure(router, q)

        # 요약 출력
        delta = t1 - t2
        ratio = (t2 / t1) if t1 > 0 else 0
        print(f"📊 캐시 효과: 1차={t1:.1f}ms → 2차={t2:.1f}ms | Δ={delta:.1f}ms | ratio={ratio:.2f}")

        # 엄격 모드일 때만 성능 단언
        if strict:
            assert t2 <= t1 * 0.9 or delta >= 60.0


