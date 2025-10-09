# app/services/user_service.py

from app.schemas.user_schema import UserProfile, PortfolioItem
from typing import Dict, Any

class UserService:
    """
    외부 백엔드 서비스에서 사용자 데이터를 가져오는 역할을 합니다.
    """
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        외부 사용자 서비스에서 사용자의 프로필을 가져옵니다.
        참고: 이 함수는 실제 API 호출(예: httpx 또는 requests 사용)로
        대체되어야 하는 임시 모의 구현
        """
        print(f"외부 서비스에서 사용자 ID '{user_id}'의 프로필을 가져옵니다...")
        
        # --- 모의 데이터 시작 ---
        if user_id == "doyun_test":
            mock_data = UserProfile(
                user_id="doyun_test",
                username="권도윤",
                risk_appetite="공격형",
                portfolio=[
                    PortfolioItem(stock_code="005930", quantity=10, average_purchase_price=75000.0),
                    PortfolioItem(stock_code="035420", quantity=5, average_purchase_price=220000.0)
                ]
            )
            return mock_data.model_dump()
        # --- 모의 데이터 끝 ---
            
        return {"error": f"ID가 '{user_id}'인 사용자를 찾을 수 없습니다."}

# 전역 인스턴스 생성
user_service = UserService()