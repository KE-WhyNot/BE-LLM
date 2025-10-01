"""
포트폴리오 제안 서비스 테스트 스크립트
"""

import sys
import os
# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app.services.portfolio.portfolio_advisor import portfolio_advisor

def test_portfolio_advisor():
    """포트폴리오 제안 서비스 테스트"""
    
    # 테스트 데이터 1: 적극투자형 사용자 (요구사항 예시)
    test_data_1 = {
        "user_data": {
            "age": 29,
            "investment_type": "적극투자형",
            "total_capital": 50000000,
            "investment_purpose": "주택 자금 마련 (5~10년)",
            "investment_experience_years": 3,
            "interested_sectors": ["반도체", "AI", "2차전지"]
        },
        "market_data": {
            "market_summary": "현재 KOSPI는 전일 대비 0.5% 상승 마감했으며, 미국 연준의 금리 동결 기조가 유지되고 있습니다. 인플레이션 둔화 조짐이 보이나, 국제 유가 변동성은 여전히 시장의 주요 변수입니다.",
            "sector_outlook": {
                "반도체": "AI 시장 확대로 HBM(고대역폭 메모리) 수요가 폭발적으로 증가하고 있어, 관련 기업들의 실적 개선이 기대되는 긍정적인 상황입니다.",
                "AI": "글로벌 빅테크 기업들의 경쟁적인 투자로 단기적인 조정이 있을 수 있으나, 장기적인 성장성은 매우 높게 평가됩니다.",
                "2차전지": "전기차 시장의 일시적 수요 둔화로 단기적인 변동성이 크지만, 장기적인 친환경 정책 기조에 따라 성장 가능성은 유효합니다.",
                "항공주": "국제 유가 안정 및 여행 수요 회복으로 점진적인 실적 개선이 예상됩니다."
            }
        }
    }
    
    # 테스트 데이터 2: 안정형 사용자
    test_data_2 = {
        "user_data": {
            "age": 45,
            "investment_type": "안정형",
            "total_capital": 100000000,
            "investment_purpose": "노후 자금 마련 (10년 이상)",
            "investment_experience_years": 1,
            "interested_sectors": ["은행", "통신"]
        },
        "market_data": {
            "market_summary": "금리 상승 기조로 인해 은행주가 상승세를 보이고 있으며, 통신업계는 5G 확산으로 안정적인 성장을 지속하고 있습니다.",
            "sector_outlook": {
                "은행": "금리 상승으로 순이자마진 확대가 예상되어 실적 개선이 기대됩니다.",
                "통신": "5G 서비스 확산과 데이터 사용량 증가로 안정적인 성장이 예상됩니다.",
                "반도체": "AI 수요 증가로 장기적 성장 가능성이 높지만, 단기적 변동성이 클 수 있습니다."
            }
        }
    }
    
    # 테스트 데이터 3: 공격투자형 사용자
    test_data_3 = {
        "user_data": {
            "age": 25,
            "investment_type": "공격투자형",
            "total_capital": 30000000,
            "investment_purpose": "자산 증식 (10년 이상)",
            "investment_experience_years": 5,
            "interested_sectors": ["AI", "바이오"]
        },
        "market_data": {
            "market_summary": "테크 주식들이 조정을 받고 있지만, AI와 바이오 분야는 여전히 높은 성장성을 보이고 있습니다.",
            "sector_outlook": {
                "AI": "단기 조정에도 불구하고 장기적 성장성은 매우 높습니다.",
                "바이오": "신약 개발 성과와 정부 지원으로 긍정적인 전망입니다.",
                "반도체": "AI 수요 증가로 관련 기업들의 실적이 개선되고 있습니다."
            }
        }
    }
    
    print("=" * 80)
    print("🎯 개인화된 투자 포트폴리오 제안 서비스 테스트")
    print("=" * 80)
    
    # 테스트 1: 적극투자형 사용자 (요구사항 예시)
    print("\n📊 테스트 1: 적극투자형 사용자 (29세, 5천만원)")
    print("-" * 60)
    result_1 = portfolio_advisor.analyze_portfolio(
        test_data_1["user_data"], 
        test_data_1["market_data"]
    )
    print(json.dumps(result_1, ensure_ascii=False, indent=2))
    
    # 테스트 2: 안정형 사용자
    print("\n📊 테스트 2: 안정형 사용자 (45세, 1억원)")
    print("-" * 60)
    result_2 = portfolio_advisor.analyze_portfolio(
        test_data_2["user_data"], 
        test_data_2["market_data"]
    )
    print(json.dumps(result_2, ensure_ascii=False, indent=2))
    
    # 테스트 3: 공격투자형 사용자
    print("\n📊 테스트 3: 공격투자형 사용자 (25세, 3천만원)")
    print("-" * 60)
    result_3 = portfolio_advisor.analyze_portfolio(
        test_data_3["user_data"], 
        test_data_3["market_data"]
    )
    print(json.dumps(result_3, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    test_portfolio_advisor()
