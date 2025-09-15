from fastapi import FastAPI
from app.routers import chat

app = FastAPI()

# /app/routers/chat.py 파일에 정의된 API들을 앱에 포함시킵니다.
app.include_router(chat.router)

@app.get("/")
def read_root():
    """서버가 잘 실행되고 있는지 확인하는 기본 주소입니다."""
    return {"message": "Financial Chatbot Service is running"}