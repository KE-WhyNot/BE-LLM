"""고도화된 포트폴리오 추천 API 테스트"""

import sys
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.portfolio_schema import InvestmentProfileRequest
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
from app.services.portfolio.sector_analysis_service import sector_analysis_service
from app.utils.portfolio_stock_loader import portfolio_stock_loader
import json


async def test_sector_analysis():
    """섹터 분석 서비스 테스트"""
    print("=" * 80)
    print("섹터 분석 서비스 테스트")
    print("=" * 80)
    
    # 단일 섹터 분석
    print("\n[테스트 1] 단일 섹터 분석 - 전기·전자")
    try:
        sector_analysis = await sector_analysis_service.analyze_sector_outlook(
            sector="전기·전자",
            time_range="week"
        )
        
        print(f"✓ 섹터: {sector_analysis['sector']}")
        print(f"✓ 전망: {sector_analysis['outlook']}")
        print(f"✓ 신뢰도: {sector_analysis['confidence']:.2f}")
        print(f"✓ 감정 점수: {sector_analysis['sentiment_score']:.2f}")
        print(f"✓ 비중 조정: {sector_analysis['weight_adjustment']:.1f}%")
        print(f"✓ 요약: {sector_analysis['summary']}")
        
    except Exception as e:
        print(f"❌ 섹터 분석 실패: {e}")
    
    # 다중 섹터 분석
    print("\n[테스트 2] 다중 섹터 분석")
    try:
        sectors = ["전기·전자", "IT 서비스", "제약"]
        multi_analysis = await sector_analysis_service.analyze_multiple_sectors(
            sectors=sectors,
            time_range="week"
        )
        
        for sector, analysis in multi_analysis.items():
            print(f"✓ {sector}: {analysis['outlook']} (신뢰도: {analysis['confidence']:.2f})")
            
    except Exception as e:
        print(f"❌ 다중 섹터 분석 실패: {e}")


def test_company_size_classification():
    """기업 규모 분류 테스트"""
    print("\n" + "=" * 80)
    print("기업 규모 분류 테스트")
    print("=" * 80)
    
    # 시가총액별 분류
    test_market_caps = [
        (50_000_000_000_000, "50조"),  # 대기업
        (5_000_000_000_000, "5조"),    # 중견기업  
        (500_000_000_000, "5천억"),    # 중소기업
    ]
    
    for market_cap, description in test_market_caps:
        classification = portfolio_stock_loader.classify_by_market_cap(market_cap)
        print(f"✓ {description} → {classification}")
    
    # 섹터별 기업 규모 분포
    print(f"\n✓ 섹터별 기업 규모 분포:")
    sectors = ["전기·전자", "IT 서비스", "제약"]
    
    for sector in sectors:
        sector_stocks = portfolio_stock_loader.get_stocks_by_sector(sector)
        size_distribution = {}
        
        for stock in sector_stocks:
            size = portfolio_stock_loader.classify_by_market_cap(stock.get('market_cap', 0))
            size_distribution[size] = size_distribution.get(size, 0) + 1
        
        print(f"  - {sector}: {dict(size_distribution)}")


async def test_enhanced_portfolio():
    """고도화된 포트폴리오 추천 테스트"""
    print("\n" + "=" * 80)
    print("고도화된 포트폴리오 추천 테스트")
    print("=" * 80)
    
    # 테스트 케이스 1: 안정형 + 뉴스 분석 사용
    print("\n[테스트 1] 안정형 투자자 + 뉴스 분석")
    profile1 = InvestmentProfileRequest(
        profileId=1,
        userId="enhanced_test_001",
        investmentProfile="안정형",
        availableAssets=20000000,
        lossTolerance="30",
        financialKnowledge="보통", 
        expectedProfit="150",
        investmentGoal="자산증식",
        interestedSectors=["전기·전자", "기타금융"]
    )
    
    try:
        result1 = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile1, 
            use_news_analysis=True
        )
        
        print(f"✅ 예적금 비율: {result1.allocationSavings}%")
        print(f"✅ 추천 종목 ({len(result1.recommendedStocks)}개):")
        for stock in result1.recommendedStocks:
            company_size = portfolio_stock_loader.classify_by_market_cap(
                next((s['market_cap'] for s in portfolio_stock_loader.stocks_data 
                     if s['code'] == stock.stockId), 0)
            )
            print(f"  - {stock.stockName} ({stock.stockId}) [{company_size}]")
            print(f"    섹터: {stock.sectorName}, 비중: {stock.allocationPct}%")
            print(f"    이유: {stock.reason[:100]}...")
            
    except Exception as e:
        print(f"❌ 고도화된 포트폴리오 추천 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 테스트 케이스 2: 공격투자형 + 뉴스 분석 미사용
    print("\n[테스트 2] 공격투자형 투자자 + 뉴스 분석 미사용")
    profile2 = InvestmentProfileRequest(
        profileId=2,
        userId="enhanced_test_002",
        investmentProfile="공격투자형",
        availableAssets=50000000,
        lossTolerance="100",
        financialKnowledge="매우 높음",
        expectedProfit="300",
        investmentGoal="자산증식",
        interestedSectors=["IT 서비스", "전기·전자", "제약"]
    )
    
    try:
        result2 = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile2,
            use_news_analysis=False
        )
        
        print(f"✅ 예적금 비율: {result2.allocationSavings}%")
        print(f"✅ 추천 종목 ({len(result2.recommendedStocks)}개):")
        for stock in result2.recommendedStocks:
            company_size = portfolio_stock_loader.classify_by_market_cap(
                next((s['market_cap'] for s in portfolio_stock_loader.stocks_data 
                     if s['code'] == stock.stockId), 0)
            )
            print(f"  - {stock.stockName} ({stock.stockId}) [{company_size}]")
            print(f"    섹터: {stock.sectorName}, 비중: {stock.allocationPct}%")
            print(f"    이유: {stock.reason[:100]}...")
            
    except Exception as e:
        print(f"❌ 고도화된 포트폴리오 추천 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_comparison_basic_vs_enhanced():
    """기본 vs 고도화된 추천 비교 테스트"""
    print("\n" + "=" * 80)
    print("기본 vs 고도화된 추천 비교")
    print("=" * 80)
    
    # 동일한 프로필로 기본/고도화된 추천 비교
    profile = InvestmentProfileRequest(
        profileId=999,
        userId="comparison_test",
        investmentProfile="위험중립형",
        availableAssets=30000000,
        lossTolerance="50",
        financialKnowledge="높음",
        expectedProfit="200",
        investmentGoal="자산증식",
        interestedSectors=["전기·전자", "IT 서비스"]
    )
    
    try:
        # 기본 추천
        print("\n🔸 기본 추천:")
        from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
        import asyncio
        basic_result = asyncio.run(enhanced_portfolio_service.recommend_enhanced_portfolio(profile, use_news_analysis=False, use_financial_analysis=False))
        
        print(f"  예적금: {basic_result.allocationSavings}%")
        print("  추천 종목:")
        for stock in basic_result.recommendedStocks:
            print(f"    - {stock.stockName}: {stock.allocationPct}%")
        
        # 고도화된 추천
        print("\n🔸 고도화된 추천:")
        enhanced_result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile,
            use_news_analysis=True
        )
        
        print(f"  예적금: {enhanced_result.allocationSavings}%")
        print("  추천 종목:")
        for stock in enhanced_result.recommendedStocks:
            company_size = portfolio_stock_loader.classify_by_market_cap(
                next((s['market_cap'] for s in portfolio_stock_loader.stocks_data 
                     if s['code'] == stock.stockId), 0)
            )
            print(f"    - {stock.stockName} [{company_size}]: {stock.allocationPct}%")
        
        # 차이점 분석
        print("\n🔸 차이점 분석:")
        basic_savings = basic_result.allocationSavings
        enhanced_savings = enhanced_result.allocationSavings
        print(f"  예적금 비율 차이: {enhanced_savings - basic_savings:+}%p")
        
        basic_stocks = {s.stockId: s.allocationPct for s in basic_result.recommendedStocks}
        enhanced_stocks = {s.stockId: s.allocationPct for s in enhanced_result.recommendedStocks}
        
        all_stocks = set(list(basic_stocks.keys()) + list(enhanced_stocks.keys()))
        for stock_id in all_stocks:
            basic_pct = basic_stocks.get(stock_id, 0)
            enhanced_pct = enhanced_stocks.get(stock_id, 0)
            if basic_pct != enhanced_pct:
                stock_name = next((s.stockName for s in basic_result.recommendedStocks + enhanced_result.recommendedStocks if s.stockId == stock_id), stock_id)
                print(f"  {stock_name}: {basic_pct}% → {enhanced_pct}% ({enhanced_pct - basic_pct:+}%p)")
                
    except Exception as e:
        print(f"❌ 비교 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    try:
        print("\n" + "=" * 80)
        print("고도화된 포트폴리오 추천 시스템 테스트 시작")
        print("=" * 80)
        
        # 각 테스트 실행
        await test_sector_analysis()
        test_company_size_classification()
        await test_enhanced_portfolio()
        await test_comparison_basic_vs_enhanced()
        
        print("\n" + "=" * 80)
        print("✅ 모든 테스트 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
