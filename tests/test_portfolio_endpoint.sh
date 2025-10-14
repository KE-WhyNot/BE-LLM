#!/bin/bash
# 포트폴리오 API 엔드포인트 테스트 스크립트

echo "포트폴리오 API 엔드포인트 테스트"
echo "=================================="

# API 서버 URL (로컬 테스트용)
API_URL="http://localhost:8000"

echo ""
echo "[1] 섹터 목록 조회 테스트"
echo "GET ${API_URL}/api/v1/portfolio/sectors"
echo "---"
curl -X GET "${API_URL}/api/v1/portfolio/sectors" \
  -H "Content-Type: application/json" \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[2] 포트폴리오 추천 테스트 - 안정형"
echo "POST ${API_URL}/api/v1/portfolio"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 1,
    "userId": "test_user_001",
    "investmentProfile": "안정형",
    "availableAssets": 10000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "기타금융", "제약"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[3] 포트폴리오 추천 테스트 - 공격투자형"
echo "POST ${API_URL}/api/v1/portfolio"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 2,
    "userId": "test_user_002",
    "investmentProfile": "공격투자형",
    "availableAssets": 50000000,
    "lossTolerance": "100",
    "financialKnowledge": "매우 높음",
    "expectedProfit": "300",
    "investmentGoal": "자산증식",
    "interestedSectors": ["IT 서비스", "전기·전자", "제약"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "=================================="
echo "테스트 완료!"

