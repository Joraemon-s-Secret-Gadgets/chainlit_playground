# backend/routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database as db
import auth  # 👈 방금 추가한 backend/auth.py를 임포트합니다!

router = APIRouter()

class LoginReq(BaseModel):
    email: str
    password: str

class SignupReq(BaseModel):
    name: str
    email: str
    password: str

class ResetPwReq(BaseModel):
    email: str
    new_password: str

@router.post("/login")
def login(req: LoginReq):
    user = db.get_user(req.email)
    # auth.hash_pw()를 사용하여 비밀번호 검증
    if user and user[1] == auth.hash_pw(req.password):
        # user tuple: (username, password, email, reset_token, resume_data)
        return {"status": "success", "user_info": user}
    raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

@router.post("/signup")
def signup(req: SignupReq):
    # 비밀번호를 auth.hash_pw()로 해싱하여 DB에 저장
    success, msg = db.add_user_via_web(req.name, auth.hash_pw(req.password), req.email)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "detail": msg}

@router.post("/reset-pw")
def reset_password(req: ResetPwReq):
    # 새로운 비밀번호도 auth.hash_pw()로 해싱하여 업데이트
    if db.update_password(req.email, auth.hash_pw(req.new_password)):
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="비밀번호 변경 실패")