"""
Data-Agent 사용 예제

이 파일은 Data-Agent의 사용법을 보여주는 예제입니다.
"""

import asyncio
import json
from datetime import datetime
from app.services.workflow_components.data_agent_service import run_data_agent, start_daily_scheduler, stop_scheduler


async def example_manual_execution():
    """수동 실행 예제"""
    print("=" * 60)
    print("Data-Agent 수동 실행 예제")
    print("=" * 60)
    
    # 최근 1일간의 뉴스 수집 및 처리
    result = await run_data_agent(days_back=1)
    
    print("\n📊 실행 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result


def example_scheduler():
    """스케줄러 설정 예제"""
    print("=" * 60)
    print("Data-Agent 스케줄러 설정 예제")
    print("=" * 60)
    
    # 매일 새벽 2시에 자동 실행
    start_daily_scheduler(hour=2, minute=0)
    
    print("✅ 스케줄러가 시작되었습니다.")
    print("매일 새벽 2시에 Data-Agent가 자동으로 실행됩니다.")
    print("중지하려면 stop_scheduler()를 호출하세요.")


async def example_integration_with_chatbot():
    """챗봇과 통합 예제"""
    print("=" * 60)
    print("챗봇과 Data-Agent 통합 예제")
    print("=" * 60)
    
    # 챗봇 서비스에서 Data-Agent 호출
    try:
        # 1. Data-Agent 실행
        print("1. Data-Agent 실행 중...")
        agent_result = await run_data_agent(days_back=1)
        
        if agent_result["status"] == "success":
            print("✅ Data-Agent 실행 성공!")
            
            # 2. 챗봇 서비스에 새로운 지식 알림
            print("2. 챗봇에 새로운 지식 업데이트 알림...")
            
            # 실제로는 챗봇의 RAG 서비스에 새 데이터 반영
            # await chatbot_service.refresh_knowledge_base()
            
            print("✅ 지식 베이스 업데이트 완료!")
            
        else:
            print(f"❌ Data-Agent 실행 실패: {agent_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 통합 실행 실패: {e}")


def example_error_handling():
    """에러 처리 예제"""
    print("=" * 60)
    print("Data-Agent 에러 처리 예제")
    print("=" * 60)
    
    async def safe_run():
        try:
            result = await run_data_agent(days_back=1)
            
            if result["status"] == "success":
                print("✅ Data-Agent 실행 성공")
                return result
            else:
                print(f"⚠️ Data-Agent 실행 실패: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            return None
    
    # 비동기 실행
    asyncio.run(safe_run())


def example_configuration():
    """설정 예제"""
    print("=" * 60)
    print("Data-Agent 설정 예제")
    print("=" * 60)
    
    print("📋 필요한 설정:")
    print("1. Neo4j 데이터베이스 설정")
    print("   - URI: bolt://localhost:7687")
    print("   - 사용자: neo4j")
    print("   - 비밀번호: password")
    
    print("\n2. RSS 피드 설정")
    print("   - Naver 경제 뉴스")
    print("   - Daum 경제 뉴스")
    
    print("\n3. 모델 설정")
    print("   - KF-DeBERTa 모델 (kakaobank/kf-deberta-base)")
    print("   - 관계 추출 파인튜닝 모델")
    
    print("\n4. 환경 변수 (.env 파일)")
    print("   NEO4J_URI=bolt://localhost:7687")
    print("   NEO4J_USER=neo4j")
    print("   NEO4J_PASSWORD=password")


async def main():
    """메인 실행 함수"""
    print("🚀 Data-Agent 예제 실행")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 설정 예제
    example_configuration()
    
    # 2. 수동 실행 예제
    print("\n" + "=" * 60)
    choice = input("수동 실행을 진행하시겠습니까? (y/n): ")
    if choice.lower() == 'y':
        await example_manual_execution()
    
    # 3. 스케줄러 예제
    print("\n" + "=" * 60)
    choice = input("스케줄러 설정을 진행하시겠습니까? (y/n): ")
    if choice.lower() == 'y':
        example_scheduler()
        
        # 5초 후 스케줄러 중지
        await asyncio.sleep(5)
        stop_scheduler()
        print("스케줄러가 중지되었습니다.")
    
    # 4. 에러 처리 예제
    print("\n" + "=" * 60)
    await example_error_handling()
    
    print("\n🎉 모든 예제가 완료되었습니다!")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())
