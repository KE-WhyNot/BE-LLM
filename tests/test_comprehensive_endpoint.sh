#!/bin/bash
# 최고도화된 포트폴리오 API 엔드포인트 테스트 (뉴스 + 재무제표 통합)

echo "🚀 최고도화된 포트폴리오 API 테스트 (뉴스 RSS + Pinecone 재무제표)"
echo "================================================================="

# API 서버 URL (로컬 테스트용)
API_URL="http://localhost:8000"

echo ""
echo "[1] 완전체 추천 - 뉴스 + 재무제표 모두 사용"
echo "POST ${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true&use_financial_analysis=true"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true&use_financial_analysis=true" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 1,
    "userId": "full_analysis_test",
    "investmentProfile": "위험중립형",
    "availableAssets": 25000000,
    "lossTolerance": "50",
    "financialKnowledge": "높음",
    "expectedProfit": "200",
    "investmentGoal": "자산증식",
    "interestedSectors": ["전기·전자", "IT 서비스"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[2] 뉴스만 사용 - 재무제표 분석 제외"
echo "POST ${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true&use_financial_analysis=false"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=true&use_financial_analysis=false" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 2,
    "userId": "news_only_test",
    "investmentProfile": "적극투자형",
    "availableAssets": 40000000,
    "lossTolerance": "70",
    "financialKnowledge": "보통",
    "expectedProfit": "250",
    "investmentGoal": "자산증식",
    "interestedSectors": ["제약", "IT 서비스", "전기·전자"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[3] 재무제표만 사용 - 뉴스 분석 제외"
echo "POST ${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=false&use_financial_analysis=true"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced?use_news_analysis=false&use_financial_analysis=true" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 3,
    "userId": "financial_only_test",
    "investmentProfile": "안정형",
    "availableAssets": 15000000,
    "lossTolerance": "30",
    "financialKnowledge": "매우 높음",
    "expectedProfit": "150",
    "investmentGoal": "자산증식",
    "interestedSectors": ["기타금융", "전기·전자"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[4] 기본 추천과 비교"
echo "POST ${API_URL}/api/v1/portfolio (기본)"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 4,
    "userId": "basic_comparison",
    "investmentProfile": "안정추구형",
    "availableAssets": 20000000,
    "lossTolerance": "30",
    "financialKnowledge": "보통",
    "expectedProfit": "180",
    "investmentGoal": "주택마련",
    "interestedSectors": ["전기·전자", "기타금융"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "[5] 공격투자형 + 완전체 분석"
echo "POST ${API_URL}/api/v1/portfolio/enhanced (전체 기능)"
echo "---"
curl -X POST "${API_URL}/api/v1/portfolio/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "profileId": 5,
    "userId": "aggressive_full_test",
    "investmentProfile": "공격투자형",
    "availableAssets": 100000000,
    "lossTolerance": "100",
    "financialKnowledge": "매우 높음",
    "expectedProfit": "300",
    "investmentGoal": "자산증식",
    "interestedSectors": ["IT 서비스", "제약", "전기·전자", "화학"]
  }' \
  2>/dev/null | python3 -m json.tool

echo ""
echo ""
echo "================================================================="
echo "🎉 최고도화된 포트폴리오 API 테스트 완료!"
echo ""
echo "📊 테스트 시나리오 요약:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 🔥 완전체: 뉴스 RSS + Pinecone 재무제표 모두 활용"
echo "2. 📰 뉴스만: RSS 뉴스 분석만 사용"  
echo "3. 📊 재무만: 재무제표 분석만 사용"
echo "4. ⚡ 기본: 기존 방식과 비교"
echo "5. 🚀 종합: 모든 기능을 활용한 공격투자형"
echo ""
echo "🎯 핵심 개선사항:"
echo "• 실시간 뉴스 → 섹터 전망 → 비중 조정"
echo "• Pinecone 재무제표 → ROE/PER/성장률 → 종목 점수"
echo "• 뉴스 + 재무제표 → 종합 점수 → 최적 종목 선정"
echo "• 시장 전망 summary → 상세한 추천 근거 제공"
echo "• 특성 기반 분류 → 대기업/중소기업 → 개인 선호 반영"
echo "================================================================="
