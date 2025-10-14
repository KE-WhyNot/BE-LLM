"""최고도화된 포트폴리오 시스템 테스트 (뉴스 + 재무제표) - 최적화 버전"""

import sys
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.portfolio_schema import InvestmentProfileRequest
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service
from app.services.portfolio.financial_data_service import financial_data_service
from app.services.portfolio.comprehensive_analysis_service import comprehensive_analysis_service
import json


def format_time(seconds):
    """시간을 읽기 쉬운 형식으로 포맷"""
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}분 {remaining_seconds:.1f}초"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}시간 {int(minutes)}분"


async def test_comprehensive_portfolio_system():
    """최종 종합 포트폴리오 시스템 테스트 - /portfolio/enhanced 엔드포인트 형식"""
    print("🚀 Portfolio Enhanced API Test")
    
    # 시간 측정 시작
    start_time = time.time()
    
    # 테스트 프로필
    test_profile = InvestmentProfileRequest(
        profileId=1,
        userId="comprehensive_test_final",
        investmentProfile="위험중립형",
        availableAssets=30000000,
        lossTolerance="50",
        financialKnowledge="높음",
        expectedProfit="200",
        investmentGoal="자산증식",
        interestedSectors=["전기·전자", "IT 서비스"]
    )
    
    try:
        # 포트폴리오 추천 실행
        result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile=test_profile,
            use_news_analysis=True,
            use_financial_analysis=True
        )
        
        # 총 소요 시간 계산
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 엔드포인트 응답 형식으로 JSON 생성
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        response_json = {
            "timestamp": timestamp,
            "code": "SUCCESS",
            "message": "최고도화된 포트폴리오 추천 성공 (뉴스: O, 재무제표: O)",
            "result": {
                "portfolioId": result.portfolioId,
                "userId": result.userId,
                "recommendedStocks": [
                    {
                        "stockId": stock.stockId,
                        "stockName": stock.stockName,
                        "allocationPct": stock.allocationPct,
                        "sectorName": stock.sectorName,
                        "reason": stock.reason
                    } for stock in result.recommendedStocks
                ],
                "allocationSavings": result.allocationSavings,
                "createdAt": result.createdAt,
                "updatedAt": result.updatedAt
            }
        }
        
        # JSON 출력
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
        
        # 상세 성능 분석 출력
        print(f"\n⏱️ 성능 분석 결과:")
        print(f"📊 총 소요 시간: {format_time(total_duration)}")
        print(f"🔄 처리된 종목 수: {len(result.recommendedStocks)}개")
        
        if len(result.recommendedStocks) > 0:
            avg_time_per_stock = total_duration / len(result.recommendedStocks)
            print(f"📈 종목당 평균 분석 시간: {format_time(avg_time_per_stock)}")
        
        print(f"💰 예적금 비율: {result.allocationSavings}%")
        print(f"📈 주식 비율: {100 - result.allocationSavings}%")
        
        # 분석 종류별 예상 시간 비중
        print(f"\n📋 분석 과정 예상 시간 분포:")
        print(f"  • 뉴스 분석: ~60% (섹터별 뉴스 수집 + 감정 분석)")
        print(f"  • 재무제표 분석: ~30% (Pinecone 검색 + LLM 분석)")
        print(f"  • 종합 분석: ~10% (결과 통합 + 점수 계산)")
        
        return True
        
    except Exception as e:
        # 에러 응답 형식
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        error_response = {
            "timestamp": timestamp,
            "code": "INTERNAL_ERROR",
            "message": f"포트폴리오 추천 중 오류가 발생했습니다: {str(e)}"
        }
        
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
        return False


async def main():
    """메인 테스트 실행"""
    try:
        await test_comprehensive_portfolio_system()
    except Exception as e:
        print(f"❌ Test Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
