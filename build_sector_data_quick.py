#!/usr/bin/env python3
"""섹터 데이터 빠른 빌드 - 2개 섹터만 테스트용"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.portfolio.sector_data_builder_service import sector_data_builder_service


async def quick_build():
    """빠른 섹터 데이터 빌드 (테스트용 - 2개 섹터만)"""
    
    print("=" * 80)
    print("🚀 섹터 데이터 빠른 빌드 (테스트용)")
    print("=" * 80)
    print()
    
    # 테스트용 섹터 목록 (2개만)
    test_sectors = {"전기·전자", "기타금융"}
    
    print(f"📋 빌드 대상: {len(test_sectors)}개 섹터")
    print(f"   {', '.join(test_sectors)}")
    print()
    
    # 각 섹터 처리
    for i, sector in enumerate(test_sectors, 1):
        print(f"\n[{i}/{len(test_sectors)}] 🏢 {sector} 섹터 처리 중...")
        
        try:
            # 뉴스 수집
            news_data = await sector_data_builder_service._collect_sector_news(sector)
            
            if news_data:
                # LLM 분석
                outlook = await sector_data_builder_service._analyze_sector_outlook(sector, news_data)
                
                # Neo4j 저장
                sector_data_builder_service._save_sector_outlook_to_neo4j(sector, outlook, news_data)
                
                print(f"  ✅ {sector} 완료!")
            else:
                print(f"  ⚠️ {sector}: 뉴스 없음")
        
        except Exception as e:
            print(f"  ❌ {sector} 처리 실패: {e}")
        
        # 섹터 간 대기
        if i < len(test_sectors):
            print(f"  ⏳ 다음 섹터 전 대기 (2초)...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 80)
    print("✅ 빠른 빌드 완료!")
    print("💡 이제 포트폴리오 추천 속도 테스트를 실행하세요:")
    print("   python test_portfolio_speed.py")
    print("=" * 80)
    
    sector_data_builder_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(quick_build())
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        sector_data_builder_service.close()
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sector_data_builder_service.close()

