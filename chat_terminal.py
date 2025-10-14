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
        """서버에 메시지 전송 (응답 시간 측정)"""
        try:
            payload = {
                "message": message,
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            
            # 시작 시간 기록
            start_time = datetime.now()
            
            response = requests.post(
                f"{self.server_url}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # 타임아웃을 60초로 증가
            )
            
            # 종료 시간 기록
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                # 응답 시간 추가
                result['response_time'] = response_time
                return result
            else:
                return {"error": f"서버 오류: {response.status_code}", "response_time": response_time}
                
        except requests.exceptions.ConnectionError:
            return {"error": "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."}
        except requests.exceptions.Timeout:
            return {"error": "요청 시간 초과"}
        except Exception as e:
            return {"error": f"오류 발생: {str(e)}"}
    
    def display_response(self, response):
        """응답 표시 (실제 사용자가 보는 것과 동일 - reply_text만)"""
        if "error" in response:
            print(f"\n❌ 오류: {response['error']}")
            # 응답 시간 표시
            if "response_time" in response:
                print(f"⏱️  응답 시간: {response['response_time']:.2f}초\n")
            else:
                print()
            return
        
        # 메인 응답 텍스트만 표시 (사용자가 실제로 보는 내용)
        if "reply_text" in response:
            print(f"\n{response['reply_text']}")
        elif "response" in response:
            print(f"\n{response['response']}")
        else:
            print("\n응답을 받았습니다.")
            
        # 차트 이미지 알림만
        if response.get("chart_image"):
            print("\n📊 차트 이미지가 생성되었습니다!")
        
        # 응답 시간 표시
        if "response_time" in response:
            response_time = response['response_time']
            print(f"\n응답 시간: {response_time:.2f}초\n")
    
    def show_help(self):
        """도움말 표시"""
        print("\n📖 도움말")
        print("-" * 50)
        print("💬 채팅 예시:")
        print("  📊 주가 조회:")
        print("    - '삼성전자 주가 알려줘'")
        print("    - 'SK하이닉스 현재가는?'")
        print()
        print("  📈 투자 분석:")
        print("    - '네이버 투자 분석해줘'")
        print("    - '카카오 매수 타이밍인가요?'")
        print()
        print("  📰 뉴스 조회:")
        print("    - '삼성전자 최근 뉴스'")
        print("    - '반도체 시장 동향'")
        print()
        print("  📚 금융 지식:")
        print("    - 'PER이 뭐야?'")
        print("    - '배당수익률 설명해줘'")
        print()
        print("  📊 차트:")
        print("    - 'LG전자 차트 보여줘'")
        print("    - '현대차 주가 그래프'")
        print()
        print("🔧 명령어:")
        print("  - help: 이 도움말 표시")
        print("  - history: 대화 히스토리 표시")
        print("  - clear: 세션 초기화")
        print("  - exit/quit/q: 프로그램 종료")
        print("-" * 50)
    
    def show_history(self):
        """대화 히스토리 표시"""
        if not self.chat_history:
            print("\n📝 대화 히스토리가 없습니다.\n")
            return
            
        print("\n📝 대화 히스토리")
        print("=" * 70)
        for i, (user_msg, bot_response) in enumerate(self.chat_history, 1):
            print(f"\n{i}. 👤: {user_msg}")
            
            # 응답 표시 (reply_text만)
            if "reply_text" in bot_response:
                preview = bot_response['reply_text'][:150]
                print(f"   🤖: {preview}{'...' if len(bot_response['reply_text']) > 150 else ''}")
            elif "response" in bot_response:
                preview = bot_response['response'][:150]
                print(f"   🤖: {preview}{'...' if len(bot_response['response']) > 150 else ''}")
            elif "error" in bot_response:
                print(f"   ❌ 오류: {bot_response['error']}")
        
        print("=" * 70 + "\n")
    
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
