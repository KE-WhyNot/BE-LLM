from pydantic import BaseModel, Field
from typing import List

class PortfolioItem(BaseModel):
    """사용자 포트폴리오의 개별 종목 정보"""
    stock_code: str = Field(..., description="종목 코드 (예: '005930')")
    quantity: int = Field(..., description="보유 수량")
    average_purchase_price: float = Field(..., description="평균 매수 단가")

class UserProfile(BaseModel):
    """API를 통해 받아올 사용자 프로필 정보"""
    user_id: str = Field(..., description="고유 사용자 ID")
    username: str = Field(..., description="사용자 이름")
    risk_appetite: str = Field(..., description="투자 성향 (예: '안정형', '공격형')")
    portfolio: List[PortfolioItem] = Field(..., description="사용자 포트폴리오 목록")