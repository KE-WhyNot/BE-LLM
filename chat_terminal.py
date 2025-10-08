#!/usr/bin/env python3
"""
터미널에서 직접 채팅할 수 있는 인터랙티브 모드
동적 프롬프팅 시스템을 테스트할 수 있습니다.
"""

import requests
import json
import argparse
import os
import sys
from datetime import datetime

class ChatTerminal:
    def __init__(self, server_url="http://localhost:8001", user_id=1):
        self.server_url = server_url
        self.user_id = user_id
        self.session_id = f"terminal_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chat_history = []
        
        print("🤖 금융 챗봇 터미널 시작")
        print("=" * 50)
        print(f"📍 서버: {server_url}")
        print(f"👤 사용자 ID: {user_id}")
        print(f"🆔 세션 ID: {self.session_id}")
        print("=" * 50)
        print("💡 명령어:")
        print("  - 일반 채팅: 그냥 메시지 입력")
        print("  - 종료: 'exit', 'quit', 'q' 입력")
        print("  - 도움말: 'help' 입력")
        print("  - 히스토리: 'history' 입력")
        print("  - 세션 초기화: 'clear' 입력")
        print("=" * 50)
        
    def send_message(self, message):
        """서버에 메시지 전송"""
        try:
            payload = {
                "message": message,
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.server_url}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # 타임아웃을 60초로 증가
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"서버 오류: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."}
        except requests.exceptions.Timeout:
            return {"error": "요청 시간 초과"}
        except Exception as e:
            return {"error": f"오류 발생: {str(e)}"}
    
    def display_response(self, response):
        """응답 표시 (개선 버전)"""
        if "error" in response:
            print(f"\n❌ 오류: {response['error']}\n")
            return
        
        print("\n" + "="*60)
        
        # Pinecone 검색 결과가 있는 경우 (Colab 노트북 방식으로 표시)
        if "pinecone_results" in response:
            pinecone_data = response["pinecone_results"]
            print(f"📊 검색 결과: {len(pinecone_data)}개")
            
            for i, match in enumerate(pinecone_data[:3]):  # 상위 3개만 표시
                print(f"   [{i+1}] 점수: {match.get('score', 0):.4f}")
                print(f"       소스: {match.get('metadata', {}).get('source', 'N/A')}")
                print(f"       내용: {match.get('metadata', {}).get('text', '')[:100]}...")
                print()
        
        # reply_text 우선 (새 API 응답 형식)
        if "reply_text" in response:
            print(f"🤖 {response['reply_text']}")
        # response (이전 형식)
        elif "response" in response:
            print(f"🤖 {response['response']}")
        else:
            print("🤖 응답을 받았습니다.")
            
        # 차트 이미지
        if response.get("chart_image"):
            print("\n📊 차트 이미지가 생성되었습니다!")
        
        # 추가 정보 (선택적)
        action_data = response.get("action_data", {})
        if action_data:
            if "query_type" in action_data:
                print(f"\n🔍 쿼리 타입: {action_data['query_type']}")
            if "workflow_type" in action_data:
                print(f"🔄 워크플로우: {action_data['workflow_type']}")
        
        print("="*60 + "\n")
    
    def show_help(self):
        """도움말 표시"""
        print("\n📖 도움말")
        print("-" * 30)
        print("💬 일반 채팅 예시:")
        print("  - '삼성전자 주가 알려줘'")
        print("  - 'SK하이닉스 차트 보여줘'")
        print("  - '네이버 분석해줘'")
        print("  - '금융 뉴스 알려줘'")
        print("  - '투자 조언해줘'")
        print()
        print("🔍 Pinecone DB 검색 예시:")
        print("  - '바뀐 통화 정책'")
        print("  - '금리 변화'")
        print("  - '경제 동향'")
        print("  - '투자 전략'")
        print()
        print("🔧 명령어:")
        print("  - help: 이 도움말 표시")
        print("  - history: 대화 히스토리 표시")
        print("  - clear: 세션 초기화")
        print("  - exit/quit/q: 프로그램 종료")
        print("-" * 30)
    
    def show_history(self):
        """대화 히스토리 표시 (개선 버전)"""
        if not self.chat_history:
            print("\n📝 대화 히스토리가 없습니다.\n")
            return
            
        print("\n📝 대화 히스토리")
        print("=" * 60)
        for i, (user_msg, bot_response) in enumerate(self.chat_history, 1):
            print(f"\n{i}. 👤 질문: {user_msg}")
            
            # 응답 표시
            if "reply_text" in bot_response:
                preview = bot_response['reply_text'][:150]
                print(f"   🤖 응답: {preview}{'...' if len(bot_response['reply_text']) > 150 else ''}")
            elif "response" in bot_response:
                preview = bot_response['response'][:150]
                print(f"   🤖 응답: {preview}{'...' if len(bot_response['response']) > 150 else ''}")
            elif "error" in bot_response:
                print(f"   ❌ 오류: {bot_response['error']}")
            
            # Pinecone 검색 결과 표시
            if "pinecone_results" in bot_response and bot_response["pinecone_results"]:
                print(f"   🔍 Pinecone 검색: {len(bot_response['pinecone_results'])}개 결과")
            
            # 추가 정보
            action_data = bot_response.get("action_data", {})
            if action_data and "query_type" in action_data:
                print(f"   📋 타입: {action_data['query_type']}")
        
        print("=" * 60 + "\n")
    
    def clear_session(self):
        """세션 초기화"""
        self.session_id = f"terminal_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.chat_history = []
        print("🔄 세션이 초기화되었습니다.")
        print(f"🆔 새로운 세션 ID: {self.session_id}")
    
    def run(self):
        """메인 실행 루프"""
        while True:
            try:
                # 사용자 입력 받기 (EOF 에러 방지)
                try:
                    user_input = input("\n💬 당신: ").strip()
                except EOFError:
                    print("\n👋 입력이 종료되었습니다. 안녕히 가세요!")
                    break
                
                # 빈 입력 처리
                if not user_input:
                    continue
                
                # 명령어 처리
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 안녕히 가세요!")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                elif user_input.lower() == 'clear':
                    self.clear_session()
                    continue
                
                # 서버에 메시지 전송
                print("🔄 처리 중...")
                response = self.send_message(user_input)
                
                # 응답 표시
                self.display_response(response)
                
                # 히스토리에 추가
                self.chat_history.append((user_input, response))
                
            except KeyboardInterrupt:
                print("\n👋 안녕히 가세요!")
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description='금융 챗봇 터미널')
    parser.add_argument('--server', '-s', default='http://localhost:8001',
                       help='서버 URL (기본값: http://localhost:8001)')
    parser.add_argument('--user-id', '-u', type=int, default=1,
                       help='사용자 ID (기본값: 1)')
    
    args = parser.parse_args()
    
    # LangSmith 프로젝트 설정
    os.environ['LANGSMITH_PROJECT'] = 'pr-rundown-hurry-88'
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    
    try:
        chat = ChatTerminal(args.server, args.user_id)
        chat.run()
    except Exception as e:
        print(f"❌ 프로그램 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
