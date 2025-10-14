"""포트폴리오 추천 API 라우터"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.schemas.portfolio_schema import (
    InvestmentProfileRequest,
    PortfolioResponse,
    ErrorResponse
)
from app.services.portfolio.enhanced_portfolio_service import enhanced_portfolio_service

router = APIRouter(prefix="/api/v1", tags=["portfolio"])


## 기본 포트폴리오 엔드포인트 제거됨: 고도화 서비스만 사용


@router.post(
    "/portfolio/enhanced",
    response_model=PortfolioResponse,
    summary="고도화된 포트폴리오 추천",
    description="뉴스 분석과 기업 규모 선호도를 반영한 고도화된 포트폴리오 추천"
)
async def recommend_enhanced_portfolio(
    profile: InvestmentProfileRequest,
    use_news_analysis: bool = True,
    use_financial_analysis: bool = True
):
    """
    최고도화된 포트폴리오 추천 API
    - 실시간 뉴스 분석을 통한 섹터 전망 반영
    - Pinecone 재무제표 데이터 기반 종목 분석
    - 뉴스 + 재무제표 종합 점수 계산
    - 사용자 성향별 기업 규모 선호도 적용
    - 금융 지식도와 손실 허용도 고려
    
    Args:
        profile: 사용자 투자 프로필 정보
        use_news_analysis: 뉴스 분석 사용 여부 (기본: True)
        use_financial_analysis: 재무제표 분석 사용 여부 (기본: True)
        
    Returns:
        PortfolioResponse: 최고도화된 추천 포트폴리오 정보
        
    Raises:
        HTTPException: 추천 실패 시
    """
    try:
        # 최고도화된 포트폴리오 추천 서비스 호출
        result = await enhanced_portfolio_service.recommend_enhanced_portfolio(
            profile, 
            use_news_analysis=use_news_analysis,
            use_financial_analysis=use_financial_analysis
        )
        
        # 응답 생성
        response = PortfolioResponse(
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            code="SUCCESS",
            message="최고도화된 포트폴리오 추천 성공" + (
                f" (뉴스: {'O' if use_news_analysis else 'X'}, 재무제표: {'O' if use_financial_analysis else 'X'})"
            ),
            result=result
        )
        
        return response
        
    except Exception as e:
        # 에러 로깅
        print(f"최고도화된 포트폴리오 추천 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 에러 응답
        raise HTTPException(
            status_code=500,
            detail={
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "code": "INTERNAL_ERROR",
                "message": f"최고도화된 포트폴리오 추천 중 오류가 발생했습니다: {str(e)}"
            }
        )


@router.get(
    "/portfolio/sectors",
    summary="사용 가능한 섹터 목록 조회",
    description="포트폴리오 추천에 사용 가능한 모든 섹터 목록을 반환합니다."
)
async def get_available_sectors():
    """
    사용 가능한 섹터 목록 조회
    
    Returns:
        dict: 섹터 목록
    """
    try:
        from app.utils.portfolio_stock_loader import portfolio_stock_loader
        
        sectors = portfolio_stock_loader.get_all_sectors()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "code": "SUCCESS",
            "message": "섹터 목록 조회 성공",
            "result": {
                "sectors": sectors,
                "count": len(sectors)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "code": "INTERNAL_ERROR",
                "message": f"섹터 목록 조회 중 오류가 발생했습니다: {str(e)}"
            }
        )

