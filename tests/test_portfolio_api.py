"""포트폴리오 추천 API 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.portfolio_schema import InvestmentProfileRequest
from app.services.portfolio.portfolio_recommendation_service import portfolio_recommendation_service
from app.utils.portfolio_stock_loader import portfolio_stock_loader
import json


def test_stock_loader():
    """주식 데이터 로더 테스트"""
    print("=" * 80)
    print("주식 데이터 로더 테스트")
    print("=" * 80)
    
    # 모든 섹터 조회
    sectors = portfolio_stock_loader.get_all_sectors()
    print(f"\n✓ 사용 가능한 섹터 ({len(sectors)}개):")
    for sector in sectors:
        sector_stocks = portfolio_stock_loader.get_stocks_by_sector(sector)
        print(f"  - {sector}: {len(sector_stocks)}개 종목")
    
    # 특정 섹터의 종목 조회
    print(f"\n✓ '전기·전자' 섹터의 종목:")
    electronics_stocks = portfolio_stock_loader.get_stocks_by_sector("전기·전자")
    for stock in electronics_stocks:
        print(f"  - {stock['name']} ({stock['code']}): {', '.join(stock['characteristics'])}")
    
    # 안정적인 종목 조회
    print(f"\n✓ 안정적인 종목 (상위 3개):")
    stable_stocks = portfolio_stock_loader.get_stable_stocks(limit=3)
    for stock in stable_stocks:
        print(f"  - {stock['name']} ({stock['code']}): 시가총액 {stock['market_cap']:,}원")


def test_portfolio_recommendation():
    """포트폴리오 추천 서비스 테스트"""
    print("\n" + "=" * 80)
    print("포트폴리오 추천 서비스 테스트")
    print("=" * 80)
    
    # 테스트 케이스 1: 안정형 투자자
    print("\n[테스트 1] 안정형 투자자")
    profile1 = InvestmentProfileRequest(
        profileId=1,
        userId="test_user_001",
        investmentProfile="안정형",
        availableAssets=10000000,
        lossTolerance="30",
        financialKnowledge="보통",
        expectedProfit="150",
        investmentGoal="자산증식",
        interestedSectors=["전기·전자", "기타금융", "제약"]
    )
    
    result1 = portfolio_recommendation_service.recommend_portfolio(profile1)
    print(f"✓ 예적금 비율: {result1.allocationSavings}%")
    print(f"✓ 추천 종목 ({len(result1.recommendedStocks)}개):")
    for stock in result1.recommendedStocks:
        print(f"  - {stock.stockName} ({stock.stockId})")
        print(f"    섹터: {stock.sectorName}, 비중: {stock.allocationPct}%")
        print(f"    이유: {stock.reason}")
    
    # 테스트 케이스 2: 공격투자형 투자자
    print("\n[테스트 2] 공격투자형 투자자")
    profile2 = InvestmentProfileRequest(
        profileId=2,
        userId="test_user_002",
        investmentProfile="공격투자형",
        availableAssets=50000000,
        lossTolerance="100",
        financialKnowledge="매우 높음",
        expectedProfit="300",
        investmentGoal="자산증식",
        interestedSectors=["IT 서비스", "전기·전자", "제약"]
    )
    
    result2 = portfolio_recommendation_service.recommend_portfolio(profile2)
    print(f"✓ 예적금 비율: {result2.allocationSavings}%")
    print(f"✓ 추천 종목 ({len(result2.recommendedStocks)}개):")
    for stock in result2.recommendedStocks:
        print(f"  - {stock.stockName} ({stock.stockId})")
        print(f"    섹터: {stock.sectorName}, 비중: {stock.allocationPct}%")
        print(f"    이유: {stock.reason}")
    
    # 테스트 케이스 3: 관심 섹터 없음 (기본 추천)
    print("\n[테스트 3] 관심 섹터 없음 (기본 추천)")
    profile3 = InvestmentProfileRequest(
        profileId=3,
        userId="test_user_003",
        investmentProfile="위험중립형",
        availableAssets=20000000,
        lossTolerance="50",
        financialKnowledge="낮음",
        expectedProfit="200",
        investmentGoal="학비",
        interestedSectors=[]
    )
    
    result3 = portfolio_recommendation_service.recommend_portfolio(profile3)
    print(f"✓ 예적금 비율: {result3.allocationSavings}%")
    print(f"✓ 추천 종목 ({len(result3.recommendedStocks)}개):")
    for stock in result3.recommendedStocks:
        print(f"  - {stock.stockName} ({stock.stockId})")
        print(f"    섹터: {stock.sectorName}, 비중: {stock.allocationPct}%")
        print(f"    이유: {stock.reason}")


def test_api_response_format():
    """API 응답 형식 테스트"""
    print("\n" + "=" * 80)
    print("API 응답 형식 테스트")
    print("=" * 80)
    
    profile = InvestmentProfileRequest(
        profileId=999,
        userId="format_test_user",
        investmentProfile="안정추구형",
        availableAssets=30000000,
        lossTolerance="30",
        financialKnowledge="보통",
        expectedProfit="200",
        investmentGoal="주택마련",
        interestedSectors=["전기·전자", "기타금융"]
    )
    
    result = portfolio_recommendation_service.recommend_portfolio(profile)
    
    # JSON으로 변환 테스트
    result_dict = result.model_dump()
    result_json = json.dumps(result_dict, ensure_ascii=False, indent=2)
    
    print("\n✓ JSON 응답 예시:")
    print(result_json)
    
    # 비율 합계 검증
    total_stock_pct = sum(stock.allocationPct for stock in result.recommendedStocks)
    print(f"\n✓ 비율 검증:")
    print(f"  - 예적금: {result.allocationSavings}%")
    print(f"  - 주식 합계: {total_stock_pct}%")
    print(f"  - 전체 합계: {result.allocationSavings + total_stock_pct}%")
    
    if result.allocationSavings + total_stock_pct == 100:
        print("  ✓ 비율 합계 검증 통과!")
    else:
        print("  ✗ 비율 합계 검증 실패!")


def main():
    """메인 테스트 실행"""
    try:
        print("\n" + "=" * 80)
        print("포트폴리오 추천 시스템 테스트 시작")
        print("=" * 80)
        
        # 각 테스트 실행
        test_stock_loader()
        test_portfolio_recommendation()
        test_api_response_format()
        
        print("\n" + "=" * 80)
        print("✓ 모든 테스트 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

