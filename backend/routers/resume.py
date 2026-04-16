from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database as db

router = APIRouter()

# 프론트엔드에서 넘어오는 JSON 데이터 구조 정의
class ResumeData(BaseModel):
    personal: dict
    education: dict
    additional: dict

# 스펙 불러오기 (GET)
@router.get("/{email}")
def get_resume(email: str):
    user = db.get_user(email)
    # user[4]에 resume_data가 들어 있습니다. 데이터가 없으면 빈 JSON 문자열 반환
    if user and user[4]:
        return {"resume": user[4]}
    return {"resume": "{}"}

# 스펙 저장하기 (PUT)
@router.put("/{email}")
def update_resume(email: str, data: ResumeData):
    # Pydantic 모델을 딕셔너리로 변환 후 기존 DB 함수에 바로 전달
    success = db.update_resume_data(email, data.model_dump())
    
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="이력서 업데이트에 실패했습니다.")