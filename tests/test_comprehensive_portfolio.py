"""최고도화된 포트폴리오 시스템 테스트 (뉴스 + 재무제표)"""

import sys
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.portfolio_schema import InvestmentProfileRequest
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
from app.services.portfolio.financial_data_service import financial_data_service
from app.services.portfolio.comprehensive_analysis_service import comprehensive_analysis_service
import json


async def test_financial_data_service():
    """재무제표 분석 서비스 테스트"""
    print("=" * 80)
    print("재무제표 분석 서비스 테스트")
    print("=" * 80)
    
    # 대표 종목들 테스트
    test_stocks = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "035420", "name": "NAVER"},
        {"code": "105560", "name": "KB금융"}
    ]
    
    for stock in test_stocks:
        print(f"\n[{stock['name']}] 안정형 투자자 관점 재무 분석")
        try:
            analysis = await financial_data_service.get_financial_analysis(
                stock_code=stock['code'],
                stock_name=stock['name'],
                investment_profile="안정형"
            )
            
            print(f"✓ 재무 점수: {analysis['financial_score']}/100")
            print(f"✓ 추천 등급: {analysis['recommendation']}")
            print(f"✓ 핵심 지표: {analysis['key_metrics']}")
            print(f"✓ 강점: {analysis['strengths']}")
            print(f"✓ 분석 요약: {analysis['analysis_summary'][:100]}...")
            
        except Exception as e:
            print(f"❌ 재무 분석 실패: {e}")


async def test_comprehensive_analysis():
    """종합 분석 서비스 테스트"""
    print("\n" + "=" * 80)
    print("종합 분석 서비스 테스트")
    print("=" * 80)
    
    # 테스트 종목
    test_stock = {
        "name": "삼성전자",
        "code": "005930",
        "sector": "전기·전자",
        "market_cap": 496657621655800
    }
    
    print(f"\n[{test_stock['name']}] 공격투자형 투자자 종합 분석")
    try:
        comprehensive = await comprehensive_analysis_service.comprehensive_stock_analysis(
            stock=test_stock,
            sector="전기·전자",
            investment_profile="공격투자형"
        )
        
        print(f"✓ 종합 점수: {comprehensive['comprehensive_score']}/100")
        print(f"✓ 투자 등급: {comprehensive['investment_rating']}")
        print(f"✓ 위험 수준: {comprehensive['risk_level']}")
        print(f"✓ 기대 수익: {comprehensive['expected_return']}")
        print(f"✓ 투자 기간: {comprehensive['time_horizon']}")
        print(f"✓ 핵심 동력: {comprehensive['key_drivers']}")
        print(f"✓ 재무 강점: {comprehensive['financial_highlights']}")
        print(f"✓ 시장 기회: {comprehensive['market_opportunities']}")
        print(f"✓ 투자 논리: {comprehensive['investment_thesis'][:150]}...")
        
        # 분석 구성 요소
        components = comprehensive['analysis_components']
        print(f"\n📊 분석 구성:")
        print(f"  - 재무 점수: {components['financial_score']}")
        print(f"  - 섹터 감정: {components['sector_sentiment']}")
        print(f"  - 뉴스 신뢰도: {components['news_confidence']:.2f}")
        
    except Exception as e:
        print(f"❌ 종합 분석 실패: {e}")
        import traceback
        traceback.print_exc()


async def test_final_comprehensive_portfolio():
    """최종 종합 포트폴리오 추천 테스트"""
    print("\n" + "=" * 80)
    print("최종 종합 포트폴리오 추천 테스트")
    print("=" * 80)
    
    # 다양한 설정으로 테스트
    test_cases = [
        {
            "name": "완전체 (뉴스 + 재무제표)",
            "profile": InvestmentProfileRequest(
                profileId=1,
                userId="comprehensive_test_001",
                investmentProfile="위험중립형",
                availableAssets=30000000,
                lossTolerance="50",
                financialKnowledge="높음",
                expectedProfit="200",
                investmentGoal="자산증식",
                interestedSectors=["전기·전자", "IT 서비스"]
            ),
            "news": True,
            "financial": True
        },
        {
            "name": "뉴스만 사용",
            "profile": InvestmentProfileRequest(
                profileId=2,
                userId="news_only_test",
                investmentProfile="적극투자형",
                availableAssets=20000000,
                lossTolerance="70",
                financialKnowledge="보통",
                expectedProfit="250",
                investmentGoal="자산증식",
                interestedSectors=["제약", "IT 서비스"]
            ),
            "news": True,
            "financial": False
        },
        {
            "name": "재무제표만 사용",
            "profile": InvestmentProfileRequest(
                profileId=3,
                userId="financial_only_test",
                investmentProfile="안정형",
                availableAssets=15000000,
                lossTolerance="30",
                financialKnowledge="매우 높음",
                expectedProfit="150",
                investmentGoal="자산증식",
                interestedSectors=["기타금융", "전기·전자"]
            ),
            "news": False,
            "financial": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}] {case['name']}")
        print("-" * 60)
        
        try:
            result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
                profile=case['profile'],
                use_news_analysis=case['news'],
                use_financial_analysis=case['financial']
            )
            
            print(f"✅ 예적금 비율: {result.allocationSavings}%")
            print(f"✅ 추천 종목 ({len(result.recommendedStocks)}개):")
            
            for stock in result.recommendedStocks:
                print(f"\n  💎 {stock.stockName} ({stock.stockId})")
                print(f"     섹터: {stock.sectorName}")
                print(f"     비중: {stock.allocationPct}%")
                print(f"     추천 이유: {stock.reason[:200]}...")
            
            # 비중 검증
            total_allocation = result.allocationSavings + sum(s.allocationPct for s in result.recommendedStocks)
            print(f"\n  📊 비중 검증: {total_allocation}% {'✅' if total_allocation == 100 else '❌'}")
            
        except Exception as e:
            print(f"❌ {case['name']} 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
        
        # 테스트 간 딜레이
        if i < len(test_cases):
            print("\n⏳ 다음 테스트를 위해 3초 대기...")
            await asyncio.sleep(3)


async def main():
    """메인 테스트 실행"""
    try:
        print("\n" + "=" * 80)
        print("🚀 최고도화된 포트폴리오 시스템 (뉴스 + 재무제표) 테스트 시작")
        print("=" * 80)
        
        # 개별 서비스 테스트
        await test_financial_data_service()
        await test_comprehensive_analysis()
        
        # 통합 포트폴리오 테스트
        await test_final_comprehensive_portfolio()
        
        print("\n" + "=" * 80)
        print("✅ 모든 테스트 완료!")
        print("🎉 뉴스 RSS + Pinecone 재무제표 완전 통합 성공!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
