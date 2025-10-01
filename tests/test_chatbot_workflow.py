#!/usr/bin/env python3
"""
챗봇 워크플로우 테스트 스크립트
각 기능별 분기처리가 올바르게 작동하는지 확인
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chatbot.chatbot_service import chatbot_service
from app.services.workflow_components.query_classifier_service import query_classifier
from app.schemas.chat_schema import ChatRequest


class ChatbotWorkflowTester:
    """챗봇 워크플로우 테스트 클래스"""
    
    def __init__(self):
        self.query_classifier = query_classifier
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"    📝 {details}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp
        })
    
    def test_intent_analysis(self):
        """의도 분석 테스트"""
        print("\n🔍 의도 분석 테스트")
        print("=" * 50)
        
        test_cases = [
            ("삼성전자 주가 알려줘", "data"),
            ("삼성전자 분석해줘", "analysis"),
            ("삼성전자 뉴스 알려줘", "news"),
            ("배당주의 의미는", "knowledge"),
            ("안녕하세요", "general"),
            ("PER이 뭐야", "knowledge")
        ]
        
        for query, expected_intent in test_cases:
            try:
                predicted_intent = self.query_classifier.classify(query)
                
                success = predicted_intent == expected_intent
                details = f"예상: {expected_intent}, 실제: {predicted_intent}"
                
                self.log_test(f"의도 분석: '{query}'", success, details)
                
            except Exception as e:
                self.log_test(f"의도 분석: '{query}'", False, f"오류: {str(e)}")
    
    async def test_stock_data_query(self):
        """주식 데이터 조회 테스트"""
        print("\n📊 주식 데이터 조회 테스트")
        print("=" * 50)
        
        test_queries = [
            "삼성전자 주가 알려줘",
            "005930 현재가",
            "SK하이닉스 시세",
            "네이버 주식 정보"
        ]
        
        for query in test_queries:
            try:
                request = ChatRequest(
                    message=query,
                    user_id=1,
                    session_id="test_session"
                )
                
                response = await chatbot_service.process_chat_request(request)
                
                # 응답 검증
                success = (
                    response.reply_text and 
                    len(response.reply_text) > 10 and
                    "오류" not in response.reply_text.lower()
                )
                
                details = f"응답 길이: {len(response.reply_text)}자"
                if not success:
                    details += f", 응답: {response.reply_text[:100]}..."
                
                self.log_test(f"주식 데이터: '{query}'", success, details)
                
            except Exception as e:
                self.log_test(f"주식 데이터: '{query}'", False, f"오류: {str(e)}")
    
    async def test_news_query(self):
        """뉴스 조회 테스트"""
        print("\n📰 뉴스 조회 테스트")
        print("=" * 50)
        
        test_queries = [
            "삼성전자 뉴스",
            "최신 금융 뉴스",
            "시장 동향",
            "투자 관련 소식"
        ]
        
        for query in test_queries:
            try:
                request = ChatRequest(
                    message=query,
                    user_id=1,
                    session_id="test_session"
                )
                
                response = await chatbot_service.process_chat_request(request)
                
                # 응답 검증
                success = (
                    response.reply_text and 
                    len(response.reply_text) > 10 and
                    "오류" not in response.reply_text.lower()
                )
                
                details = f"응답 길이: {len(response.reply_text)}자"
                if not success:
                    details += f", 응답: {response.reply_text[:100]}..."
                
                self.log_test(f"뉴스 조회: '{query}'", success, details)
                
            except Exception as e:
                self.log_test(f"뉴스 조회: '{query}'", False, f"오류: {str(e)}")
    
    async def test_knowledge_query(self):
        """지식 검색 테스트"""
        print("\n📚 지식 검색 테스트")
        print("=" * 50)
        
        test_queries = [
            "배당주의 의미는",
            "PER이 뭔가요",
            "투자의 기본 원칙",
            "리스크 관리 방법"
        ]
        
        for query in test_queries:
            try:
                request = ChatRequest(
                    message=query,
                    user_id=1,
                    session_id="test_session"
                )
                
                response = await chatbot_service.process_chat_request(request)
                
                # 응답 검증
                success = (
                    response.reply_text and 
                    len(response.reply_text) > 10 and
                    "오류" not in response.reply_text.lower()
                )
                
                details = f"응답 길이: {len(response.reply_text)}자"
                if not success:
                    details += f", 응답: {response.reply_text[:100]}..."
                
                self.log_test(f"지식 검색: '{query}'", success, details)
                
            except Exception as e:
                self.log_test(f"지식 검색: '{query}'", False, f"오류: {str(e)}")
    
    async def test_analysis_query(self):
        """분석 요청 테스트"""
        print("\n🔍 분석 요청 테스트")
        print("=" * 50)
        
        test_queries = [
            "삼성전자 분석해줘",
            "투자 전망",
            "시장 분석",
            "포트폴리오 추천"
        ]
        
        for query in test_queries:
            try:
                request = ChatRequest(
                    message=query,
                    user_id=1,
                    session_id="test_session"
                )
                
                response = await chatbot_service.process_chat_request(request)
                
                # 응답 검증
                success = (
                    response.reply_text and 
                    len(response.reply_text) > 10 and
                    "오류" not in response.reply_text.lower()
                )
                
                details = f"응답 길이: {len(response.reply_text)}자"
                if not success:
                    details += f", 응답: {response.reply_text[:100]}..."
                
                self.log_test(f"분석 요청: '{query}'", success, details)
                
            except Exception as e:
                self.log_test(f"분석 요청: '{query}'", False, f"오류: {str(e)}")
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\n📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"✅ 성공: {passed_tests}")
        print(f"❌ 실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 챗봇 워크플로우 테스트 시작")
        print("=" * 60)
        
        # 의도 분석 테스트
        self.test_intent_analysis()
        
        # 각 기능별 테스트
        await self.test_stock_data_query()
        await self.test_news_query()
        await self.test_knowledge_query()
        await self.test_analysis_query()
        
        # 결과 요약
        self.print_summary()


async def main():
    """메인 함수"""
    tester = ChatbotWorkflowTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
