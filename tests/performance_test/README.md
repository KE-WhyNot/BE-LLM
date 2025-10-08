# 📊 Performance Test 폴더

성능 측정 및 벤치마크 관련 파일들을 관리합니다.

## 📁 파일 구조

```
performance_test/
├── README.md                           # 이 파일
├── performance_benchmark.py            # 전체 성능 벤치마크 (기존 vs Enhanced)
├── simple_benchmark.py                 # 간단한 성능 측정 (기존 시스템)
├── benchmark_analysis.md               # 상세한 성능 분석 보고서
└── simple_benchmark_results.json       # 실제 측정 결과 데이터
```

## 🚀 사용법

### 기존 시스템 성능 측정
```bash
python simple_benchmark.py
```

### 전체 시스템 비교 (향후)
```bash
python performance_benchmark.py
```

## 📊 측정 결과 요약

- **성공률**: 100% (5/5 쿼리 성공)
- **평균 응답 시간**: 1.27초
- **최소 응답 시간**: 0.45초
- **최대 응답 시간**: 2.93초

자세한 내용은 `benchmark_analysis.md`를 참조하세요.
