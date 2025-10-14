"""포트폴리오 API 스키마 정의"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class InvestmentProfileRequest(BaseModel):
    """투자 프로필 요청 스키마 (Finance 백엔드에서 받는 형태)"""
    profileId: int = Field(..., description="프로필 ID")
    userId: str = Field(..., description="사용자 ID")
    investmentProfile: str = Field(..., description="투자 성향 (안정형, 안정추구형, 위험중립형, 적극투자형, 공격투자형)")
    availableAssets: int = Field(..., description="투자 가능 자산")
    lossTolerance: str = Field(..., description="감당 가능 손실 (10, 30, 50, 70, 100)")
    financialKnowledge: str = Field(..., description="금융 이해도 (매우 낮음, 낮음, 보통, 높음, 매우 높음)")
    expectedProfit: str = Field(..., description="기대 이익 (150, 200, 250, 300 이상)")
    investmentGoal: str = Field(..., description="투자 목표 (학비, 생활비, 주택마련, 자산증식, 채무상환)")
    interestedSectors: List[str] = Field(..., description="관심 섹터 목록 (화학, 제약, 전기·전자, 운송장비·부품, 기타금융, 기계·장비, 금속, 건설, IT 서비스)")
    createdAt: Optional[str] = Field(None, description="생성 시간")
    updatedAt: Optional[str] = Field(None, description="수정 시간")


class StockRecommendation(BaseModel):
    """개별 주식 추천 정보"""
    stockId: str = Field(..., description="주식 종목 코드")
    stockName: str = Field(..., description="주식 종목명")
    allocationPct: int = Field(..., description="투자 비중 (%)")
    sectorName: str = Field(..., description="섹터명")
    reason: str = Field(..., description="추천 이유")


class PortfolioRecommendationResult(BaseModel):
    """포트폴리오 추천 결과"""
    portfolioId: int = Field(..., description="포트폴리오 ID")
    userId: str = Field(..., description="사용자 ID")
    recommendedStocks: List[StockRecommendation] = Field(..., description="추천 주식 목록")
    allocationSavings: int = Field(..., description="예적금 비율 (%)")
    createdAt: str = Field(..., description="생성 시간")
    updatedAt: str = Field(..., description="수정 시간")


class PortfolioResponse(BaseModel):
    """포트폴리오 API 응답 스키마"""
    timestamp: str = Field(..., description="응답 시간")
    code: str = Field(default="SUCCESS", description="응답 코드")
    message: str = Field(default="포트폴리오 추천 성공", description="응답 메시지")
    result: PortfolioRecommendationResult = Field(..., description="추천 결과")


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    timestamp: str = Field(..., description="응답 시간")
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")

