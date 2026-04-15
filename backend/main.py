from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database as db

# 분리해 둔 라우터들 임포트
from routers import auth, resume, chat

app = FastAPI(title="JobPocket API", description="AI Cover Letter Assistant Backend")

# CORS 설정 (Streamlit 프론트엔드 포트 8501에서의 접근을 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 상용 배포 시 ["http://localhost:8501"] 등으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 시작 시 데이터베이스 초기화
@app.on_event("startup")
def startup_event():
    db.init_db()

# 라우터 연결
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat Logic"])

@app.get("/")
def root():
    return {"message": "JobPocket Backend is Running!"}