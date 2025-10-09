#!/usr/bin/env python3
"""
FastAPI 서버 실행 스크립트
포트 번호를 지정해서 실행할 수 있습니다.
"""

import argparse
import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    # .env 파일 로드
    load_dotenv()
    print("✅ .env 파일 로드 완료")
    
    parser = argparse.ArgumentParser(description='FastAPI 서버 실행')
    parser.add_argument('--port', '-p', type=int, default=8001, 
                       help='서버 포트 번호 (기본값: 8000)')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='서버 호스트 (기본값: 0.0.0.0)')
    parser.add_argument('--reload', action='store_true', default=True,
                       help='자동 리로드 활성화 (기본값: True)')
    parser.add_argument('--no-reload', action='store_true',
                       help='자동 리로드 비활성화')
    
    args = parser.parse_args()
    
    # 자동 리로드 설정
    reload = args.reload and not args.no_reload
    
    # LangSmith 프로젝트 설정
    os.environ['LANGSMITH_PROJECT'] = 'pr-rundown-hurry-88'
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    
    # Pinecone 환경 변수 설정 (기본값 제공)
    if not os.environ.get('PINECONE_INDEX_NAME'):
        os.environ['PINECONE_INDEX_NAME'] = 'finance-rag-index'
    if not os.environ.get('EMBEDDING_MODEL_NAME'):
        os.environ['EMBEDDING_MODEL_NAME'] = 'kakaobank/kf-deberta-base'
    if not os.environ.get('BATCH_SIZE'):
        os.environ['BATCH_SIZE'] = '32'
    if not os.environ.get('MAX_LENGTH'):
        os.environ['MAX_LENGTH'] = '256'
    if not os.environ.get('TOP_K'):
        os.environ['TOP_K'] = '20'
    
    # Pinecone API Key는 필수
    if not os.environ.get('PINECONE_API_KEY'):
        print("❌ PINECONE_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 PINECONE_API_KEY를 추가하거나 환경 변수로 설정해주세요.")
        return
    
    print("🚀 FastAPI 서버 시작")
    print("=" * 50)
    print(f"📍 포트: {args.port}")
    print(f"🌐 호스트: {args.host}")
    print(f"🔄 자동 리로드: {reload}")
    print(f"📊 LangSmith 프로젝트: {os.environ['LANGSMITH_PROJECT']}")
    print(f"🔑 Pinecone API Key: {'설정됨' if os.environ.get('PINECONE_API_KEY') else '미설정'}")
    print(f"📊 Pinecone Index: {os.environ.get('PINECONE_INDEX_NAME')}")
    print(f"🤖 Embedding Model: {os.environ.get('EMBEDDING_MODEL_NAME')}")
    print(f"📦 Batch Size: {os.environ.get('BATCH_SIZE')}")
    print(f"📏 Max Length: {os.environ.get('MAX_LENGTH')}")
    print(f"🔢 Top K: {os.environ.get('TOP_K')}")
    print("=" * 50)
    print(f"🌍 서버 URL: http://{args.host}:{args.port}")
    print(f"📖 API 문서: http://{args.host}:{args.port}/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=reload
        )
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
