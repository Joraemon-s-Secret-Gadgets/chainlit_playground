from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Any, Optional
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

class StepReviseReq(BaseModel):
    existing_draft: str
    revision_request: str
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
    result_label: str = "자소서 초안"
    change_summary: Optional[str] = None

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

@router.post("/step-parse")
def step_parse(req: StepParseReq):
    return chat_logic.parse_user_request(req.prompt, req.model)

@router.post("/step-draft")
def step_draft(req: StepDraftReq):
    draft = chat_logic.regenerate_local_draft_if_needed(req.prompt, tuple(req.user_info), req.model)
    return {"draft": draft}

@router.post("/step-revise")
def step_revise(req: StepReviseReq):
    revised = chat_logic.revise_existing_draft(req.existing_draft, req.revision_request, req.model)
    return {"revised": revised}

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
    final_response = chat_logic.build_final_response(
        body=req.adjusted,
        user_message=req.prompt,
        selected_model=req.model,
        result_label=req.result_label,
        change_summary=req.change_summary,
    )
    return {"final_response": final_response}
