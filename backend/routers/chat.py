# ~/backend/routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any
import database as db
from services import chat_logic

router = APIRouter()

class ChatMessage(BaseModel):
    email: str
    role: str
    content: str

class StepParseReq(BaseModel):
    prompt: str
    model: str

class StepDraftReq(BaseModel):
    prompt: str
    user_info: List[Any]
    model: str

class StepRefineReq(BaseModel):
    draft: str
    prompt: str
    model: str

class StepFitReq(BaseModel):
    refined: str
    prompt: str
    model: str

class StepFinalReq(BaseModel):
    adjusted: str
    prompt: str
    model: str

# --- 대화 기록 관리 ---
@router.get("/history/{email}")
def get_history(email: str):
    messages = db.load_chat_history(email)
    return {"messages": messages}

@router.post("/message")
def save_message(req: ChatMessage):
    db.save_chat_message(req.email, req.role, req.content)
    return {"status": "success"}

@router.delete("/history/{email}")
def delete_history(email: str):
    db.delete_chat_history(email)
    return {"status": "success"}

# --- 4단계 AI 생성 로직 ---
@router.post("/step-parse")
def step_parse(req: StepParseReq):
    parsed = chat_logic.parse_user_request(req.prompt, req.model)
    return parsed

@router.post("/step-draft")
def step_draft(req: StepDraftReq):
    # tuple 타입 변환 (FastAPI에서 list로 받음)
    draft = chat_logic.regenerate_local_draft_if_needed(req.prompt, tuple(req.user_info), req.model)
    return {"draft": draft}

@router.post("/step-refine")
def step_refine(req: StepRefineReq):
    try:
        refined = chat_logic.refine_with_api(req.draft, req.prompt, req.model)
    except Exception:
        refined = req.draft
    return {"refined": refined}

@router.post("/step-fit")
def step_fit(req: StepFitReq):
    try:
        adjusted = chat_logic.fit_length_if_needed(req.refined, req.prompt, req.model)
    except Exception:
        adjusted = req.refined
    return {"adjusted": adjusted}

@router.post("/step-final")
def step_final(req: StepFinalReq):
    final_response = chat_logic.build_final_response(req.adjusted, req.prompt, req.model)
    return {"final_response": final_response}