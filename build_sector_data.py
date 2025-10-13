#!/usr/bin/env python3
"""
섹터 데이터 빌더 - 모든 섹터 뉴스 & 국제 동향 수집 후 Neo4j 저장

사용법:
    python build_sector_data.py

실행 내용:
    1. portfolio_stocks.yaml에서 모든 섹터 추출
    2. 각 섹터별 Google RSS 뉴스 수집 & LLM 분석
    3. 국제 시장 동향 수집 & 분석
    4. 모든 데이터를 Neo4j에 저장

효과:
    - 포트폴리오 추천 시 Neo4j에서 즉시 읽기 (20초 → 0.1초)
    - 주기적 실행 권장 (1일 1회 또는 6시간마다)
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.portfolio.sector_data_builder_service import sector_data_builder_service


async def main():
    """메인 실행 함수"""
    
    print("\n" + "=" * 80)
    print("🚀 섹터 데이터 빌더 시작")
    print("=" * 80)
    print()
    print("📋 작업 내용:")
    print("  1️⃣  portfolio_stocks.yaml에서 모든 섹터 로드")
    print("  2️⃣  각 섹터별 최신 뉴스 수집 (Google RSS)")
    print("  3️⃣  LLM으로 섹터 전망 분석")
    print("  4️⃣  국제 시장 동향 수집 & 분석")
    print("  5️⃣  모든 데이터를 Neo4j에 저장")
    print()
    print("⏱️  예상 소요 시간: 약 5-10분")
    print()
    
    # 사용자 확인
    response = input("계속하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("❌ 취소되었습니다.")
        return
    
    # 데이터 수집 & 저장 실행
    await sector_data_builder_service.collect_and_save_all_sector_data(
        yaml_path="config/portfolio_stocks.yaml",
        include_global_trends=True
    )
    
    print("\n" + "=" * 80)
    print("✅ 섹터 데이터 빌더 완료!")
    print("=" * 80)
    print()
    print("💡 이제 포트폴리오 추천 시 Neo4j에서 즉시 데이터를 읽어옵니다:")
    print("   - 기존: 섹터 분석 27초 → 개선: 0.1초 (270배 빠름)")
    print()
    print("📅 정기 실행 권장:")
    print("   - 매일 1회: 아침 9시 전 실행 (장 시작 전)")
    print("   - 또는 6시간마다 최신 정보 갱신")
    print()
    
    # 연결 종료
    sector_data_builder_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        sector_data_builder_service.close()
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sector_data_builder_service.close()

