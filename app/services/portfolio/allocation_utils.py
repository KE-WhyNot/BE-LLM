"""자산 비중 정규화 및 타임스탬프 유틸리티"""

from typing import List
from datetime import datetime, timezone


def now_utc_z() -> str:
    """UTC ISO8601 타임스탬프(Z 접미) 생성"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def distribute_equal(num_items: int, total_pct: int) -> List[int]:
    """동일 가중치 분배: 총합이 total_pct가 되도록 균등 분배 후 나머지는 앞쪽에 부여"""
    if num_items <= 0:
        return []
    if total_pct <= 0:
        return [0] * num_items

    base = total_pct // num_items
    remainder = total_pct % num_items

    allocations = [base] * num_items
    for i in range(remainder):
        allocations[i] += 1
    return allocations


def normalize_integer_allocations(scores: List[float], total_pct: int, min_each: int = 1) -> List[int]:
    """가중치(scores)에 비례하여 정수 비중을 배분하고 총합이 total_pct가 되도록 정규화

    - 음수/None 가중치는 0으로 간주
    - min_each가 설정되면 각 항목이 최소 min_each 이상이 되도록 보정(불가능하면 0으로 처리)
    - 가장 큰 소수점 잔여(remainder) 순으로 1씩 배분 (Largest Remainder Method)
    """
    n = len(scores)
    if n == 0:
        return []
    if total_pct <= 0:
        return [0] * n

    # 음수 방지 및 합 계산
    safe_scores = [float(s) if s is not None else 0.0 for s in scores]
    safe_scores = [s if s > 0 else 0.0 for s in safe_scores]
    sum_scores = sum(safe_scores)

    if sum_scores == 0:
        # 모든 가중치가 0이면 균등 분배
        return distribute_equal(n, total_pct)

    # 최소 비중 보장 불가능 시 0으로 처리
    if min_each * n > total_pct:
        min_each = 0

    # 최소 비중 선배정
    base = [min_each] * n
    remaining = total_pct - (min_each * n)

    if remaining <= 0:
        # 이미 총합을 채웠다면 그대로 반환(총합이 정확히 일치하도록 조정)
        # over-allocation 방지: 앞쪽부터 1씩 차감
        over = -remaining
        i = 0
        while over > 0 and any(x > 0 for x in base):
            if base[i % n] > 0:
                base[i % n] -= 1
                over -= 1
            i += 1
        return base

    # 남은 몫을 비례 배분
    proportions = [s / sum_scores for s in safe_scores]
    raw = [p * remaining for p in proportions]
    ints = [int(x) for x in raw]
    used = sum(ints)
    left = remaining - used

    # 잔여를 소수점 큰 순서대로 1씩 분배
    remainders = [(raw[i] - ints[i], i) for i in range(n)]
    remainders.sort(key=lambda x: x[0], reverse=True)

    for _, idx in remainders:
        if left <= 0:
            break
        ints[idx] += 1
        left -= 1

    final_allocations = [base[i] + ints[i] for i in range(n)]

    # 안전망: 총합 보정
    diff = total_pct - sum(final_allocations)
    if diff != 0:
        # diff > 0 이면 큰 항목부터 +1, diff < 0 이면 큰 항목부터 -1
        order = sorted(range(n), key=lambda i: final_allocations[i], reverse=True)
        j = 0
        while diff != 0 and j < 10000:  # 무한루프 방지
            idx = order[j % n]
            if diff > 0:
                final_allocations[idx] += 1
                diff -= 1
            else:
                if final_allocations[idx] > 0:
                    final_allocations[idx] -= 1
                    diff += 1
            j += 1

    return final_allocations


