# main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from chainlit.utils import mount_chainlit

from database import init_db, add_user_via_web
from auth import hash_pw

init_db()
app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="public")
templates = Jinja2Templates(directory="templates")

# ==========================================
# 라우팅 1: 메인 랜딩 페이지
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    #  FastAPI 문법 적용 
    return templates.TemplateResponse(request=request, name="index.html")

# ==========================================
# 라우팅 2: 회원가입 페이지
# ==========================================
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html")

@app.post("/signup", response_class=HTMLResponse)
async def process_signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    hashed_pw = hash_pw(password)
    success, msg = add_user_via_web(username, hashed_pw, email)
    
    if success:
        return RedirectResponse(url="/chat", status_code=303)
    else:
        # 에러 메시지: context 딕셔너리에 담아서 전달
        return templates.TemplateResponse(request=request, name="signup.html", context={"error_msg": msg})

# ==========================================
# 라우팅 3: 체인릿 앱 마운트
# ==========================================
mount_chainlit(app=app, target="app.py", path="/chat")