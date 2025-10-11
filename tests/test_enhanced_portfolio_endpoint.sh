#!/bin/bash
# 고도화된 포트폴리오 API 엔드포인트 테스트 스크립트

echo "고도화된 포트폴리오 API 엔드포인트 테스트"
echo "============================================"

# API 서버 URL (로컬 테스트용)
API_URL="http://localhost:8000"

echo ""
echo "[1] 기본 포트폴리오 추천 테스트 - 안정형"
echo "POST ${API_URL}/api/v1/portfolio"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 1,
    "userId": "basic_test_001",
    "investmentProfile": "안정형",
    "availableAssets": 10000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "기타금융"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[2] 고도화된 포트폴리오 추천 테스트 - 안정형 (뉴스 분석 포함)"
echo "POST ${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 2,
    "userId": "enhanced_test_001",
    "investmentProfile": "안정형",
    "availableAssets": 10000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "기타금융"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[3] 고도화된 포트폴리오 추천 테스트 - 공격투자형 (뉴스 분석 미포함)"
echo "POST ${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=false"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=false" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 3,
    "userId": "enhanced_test_002",
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
echo "[4] 금융지식 높은 위험중립형 투자자 (뉴스 분석 포함)"
echo "POST ${API_URL}/api/v1/portfolio/enhanced"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 4,
    "userId": "enhanced_test_003",
    "investmentProfile": "위험중립형",
    "availableAssets": 30000000,
    "lossTolerance": "70",
    "financialKnowledge": "매우 높음",
    "expectedProfit": "250",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "IT 서비스", "제약", "화학"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[5] 관심 섹터 없는 경우 (기본 섹터 자동 선정)"
echo "POST ${API_URL}/api/v1/portfolio/enhanced"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 5,
    "userId": "enhanced_test_004",
    "investmentProfile": "적극투자형",
    "availableAssets": 20000000,
    "lossTolerance": "50",
    "financialKnowledge": "낮음",
    "expectedProfit": "200",
    "investmentGoal": "학비",
    "interestedSectors": []
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[6] 섹터 목록 조회"
echo "GET ${API_URL}/api/v1/portfolio/sectors"
echo "---"
curl -X GET "${API_URL}/api/v1/portfolio/sectors" \
  -H "Content-Type: application/json" \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "============================================"
echo "테스트 완료!"
echo ""
echo "📊 테스트 요약:"
echo "- 기본 포트폴리오 추천: 기존 로직 (뉴스 분석 없음)"
echo "- 고도화된 추천 (뉴스 분석 포함): 실시간 섹터 전망 반영"
echo "- 고도화된 추천 (뉴스 분석 미포함): 기업 규모 선호도만 적용"
echo "- 기업 규모 분류: 대기업/중견기업/중소기업 자동 분류"
echo "- 투자 성향별 맞춤: 안정형→대기업 선호, 공격형→중소기업 포함"
