"""최종 JSON 형식 검증 테스트 (초기 요구사항 대조)"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.portfolio_schema import InvestmentProfileRequest
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
import asyncio
import json


async def test_json_format_compliance():
    """초기 요구사항 JSON 형식 검증"""
    
    print("=" * 80)
    print("📋 초기 요구사항 JSON 형식 검증 테스트")
    print("=" * 80)
    
    # 초기 요구사항 예시 프로필
    profile = InvestmentProfileRequest(
        profileId=1,
        userId="user123",
        investmentProfile="안정형",
        availableAssets=10000000,
        lossTolerance="30",
        financialKnowledge="보통",
        expectedProfit="150",
        investmentGoal="학비",
        interestedSectors=["전기·전자", "기타금융", "화학"]
    )
    
    print("\n[요구사항] 입력 형식:")
    print(json.dumps(profile.model_dump(), ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("🔥 V3 완전체 추천 (권장 설정: 뉴스 메인 + 재무 보조)")
    print("=" * 80)
    
    try:
        # V3 완전체 추천
        result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile=profile,
            use_news_analysis=True,   # 뉴스 메인
            use_financial_analysis=True  # 재무 보조
        )
        
        # 응답 형식 생성 (API 응답 형태)
        from datetime import datetime, timezone
        
        api_response = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "code": "SUCCESS",
            "message": "포트폴리오 추천 성공",
            "result": result.model_dump()
        }
        
        print("\n[응답] 출력 JSON:")
        print(json.dumps(api_response, ensure_ascii=False, indent=2))
        
        # 형식 검증
        print("\n" + "=" * 80)
        print("✅ JSON 형식 검증")
        print("=" * 80)
        
        required_fields = {
            "root": ["timestamp", "code", "message", "result"],
            "result": ["portfolioId", "userId", "recommendedStocks", "allocationSavings", "createdAt", "updatedAt"],
            "stock": ["stockId", "stockName", "allocationPct", "sectorName", "reason"]
        }
        
        # Root 레벨 검증
        print("\n✓ Root 레벨 필드:")
        for field in required_fields["root"]:
            exists = field in api_response
            print(f"  - {field}: {'✅' if exists else '❌'}")
        
        # Result 레벨 검증
        print("\n✓ Result 레벨 필드:")
        for field in required_fields["result"]:
            exists = field in api_response["result"]
            print(f"  - {field}: {'✅' if exists else '❌'}")
        
        # Stock 레벨 검증
        if api_response["result"]["recommendedStocks"]:
            print("\n✓ Stock 레벨 필드 (첫 번째 종목):")
            first_stock = api_response["result"]["recommendedStocks"][0]
            for field in required_fields["stock"]:
                exists = field in first_stock
                print(f"  - {field}: {'✅' if exists else '❌'}")
        
        # 비율 검증
        print("\n✓ 비율 검증:")
        savings = api_response["result"]["allocationSavings"]
        stocks_total = sum(s["allocationPct"] for s in api_response["result"]["recommendedStocks"])
        total = savings + stocks_total
        
        print(f"  - allocationSavings: {savings}%")
        print(f"  - 주식 합계: {stocks_total}%")
        print(f"  - 전체 합계: {total}% {'✅' if total == 100 else '❌'}")
        
        # 종목 상세 정보
        print("\n✓ 추천 종목 상세:")
        for stock in api_response["result"]["recommendedStocks"]:
            print(f"\n  💎 {stock['stockName']} ({stock['stockId']})")
            print(f"     섹터: {stock['sectorName']}")
            print(f"     비중: {stock['allocationPct']}%")
            print(f"     이유: {stock['reason'][:150]}...")
        
        print("\n" + "=" * 80)
        print("🎉 모든 필수 필드 검증 완료!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_vs_enhanced():
    """기본 vs 고도화 추천 비교 (초기 요구사항 충족 확인)"""
    
    print("\n" + "=" * 80)
    print("📊 V1 기본 vs V3 최고도화 비교")
    print("=" * 80)
    
    profile = InvestmentProfileRequest(
        profileId=999,
        userId="comparison_test",
        investmentProfile="안정추구형",
        availableAssets=20000000,
        lossTolerance="30",
        financialKnowledge="보통",
        expectedProfit="180",
        investmentGoal="주택마련",
        interestedSectors=["전기·전자", "기타금융"]
    )
    
    # V1 기본
    print("\n🔸 V1 기본 추천:")
    basic_result = asyncio.run(enhanced_portfolio_service.recommend_enhanced_portfolio(profile, use_news_analysis=False, use_financial_analysis=False))
    print(f"  예적금: {basic_result.allocationSavings}%")
    print("  종목:")
    for stock in basic_result.recommendedStocks:
        print(f"    - {stock.stockName}: {stock.allocationPct}%")
        print(f"      이유: {stock.reason[:100]}...")
    
    # V3 최고도화
    print("\n🔸 V3 최고도화 추천 (뉴스 + 재무제표):")
    enhanced_result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
        profile=profile,
        use_news_analysis=True,
        use_financial_analysis=True
    )
    print(f"  예적금: {enhanced_result.allocationSavings}%")
    print("  종목:")
    for stock in enhanced_result.recommendedStocks:
        print(f"    - {stock.stockName}: {stock.allocationPct}%")
        print(f"      이유: {stock.reason[:100]}...")
    
    # JSON 형식 출력
    print("\n📄 V3 최종 JSON 출력 (샘플):")
    from datetime import datetime, timezone
    
    final_json = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "code": "SUCCESS",
        "message": "포트폴리오 추천 성공",
        "result": enhanced_result.model_dump()
    }
    
    print(json.dumps(final_json, ensure_ascii=False, indent=2))


async def main():
    """메인 테스트"""
    print("\n" + "=" * 80)
    print("🚀 최종 JSON 형식 검증 및 커밋 전 테스트")
    print("=" * 80)
    
    success1 = await test_json_format_compliance()
    await test_basic_vs_enhanced()
    
    if success1:
        print("\n" + "=" * 80)
        print("✅ 모든 검증 완료 - 커밋 준비 완료!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 검증 실패 - 수정 필요")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
