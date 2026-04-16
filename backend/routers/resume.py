# backend/routers/resume.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import database as db

router = APIRouter()

class ResumeUpdateReq(BaseModel):
    personal: dict = {}
    education: dict = {}
    additional: dict = {}

@router.get("/{email}")
def get_resume(email: str):
    user = db.get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return {"resume_data": user[4] or "{}"}

@router.put("/{email}")
def update_resume(email: str, resume_data: ResumeUpdateReq):
    success = db.update_resume_data(email, resume_data.dict())
    if not success:
        raise HTTPException(status_code=400, detail="스펙 저장 실패")
    return {"status": "success"}