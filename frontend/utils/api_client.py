# frontend/utils/api_client.py
import requests
import json
import streamlit as st

# FastAPI 백엔드 주소 (실제 배포 시 환경 변수로 분리 권장)
BASE_URL = "http://localhost:8000/api"

# ==========================================
# 1. 인증(Auth) API
# ==========================================
def login_api(email, password):
    """[POST] 로그인 요청 (해싱은 백엔드에서 처리)"""
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return True, res.json().get("user_info")
    return False, res.json().get("detail", "로그인 실패")

def signup_api(name, email, password):
    """[POST] 회원가입 요청"""
    res = requests.post(f"{BASE_URL}/auth/signup", json={"name": name, "email": email, "password": password})
    if res.status_code == 200:
        return True, "가입 성공"
    return False, res.json().get("detail", "회원가입 처리 중 오류 발생")

def update_password_api(email, new_password):
    """[POST] 비밀번호 변경 요청"""
    res = requests.post(f"{BASE_URL}/auth/reset-pw", json={"email": email, "new_password": new_password})
    return res.status_code == 200

# ==========================================
# 2. 스펙 보관함(Resume) API
# ==========================================
def get_user_resume_api(email):
    """[GET] 특정 유저의 스펙 데이터 조회"""
    res = requests.get(f"{BASE_URL}/resume/{email}")
    if res.status_code == 200:
        return res.json().get("resume_data", "{}")
    return "{}"

def update_resume_data_api(email, new_resume_data):
    """[PUT] 스펙 데이터 업데이트"""
    res = requests.put(f"{BASE_URL}/resume/{email}", json=new_resume_data)
    return res.status_code == 200

# ==========================================
# 3. 대화 내역(Chat History) API
# ==========================================
def load_chat_history_api(email):
    """[GET] 전체 대화 내역 불러오기"""
    res = requests.get(f"{BASE_URL}/chat/history/{email}")
    if res.status_code == 200:
        return res.json().get("messages", [])
    return []

def save_chat_message_api(email, role, content):
    """[POST] 단일 메시지 DB 저장"""
    requests.post(f"{BASE_URL}/chat/message", json={"email": email, "role": role, "content": content})

def delete_chat_history_api(email):
    """[DELETE] 대화 내역 초기화"""
    requests.delete(f"{BASE_URL}/chat/history/{email}")

# ==========================================
# 4. AI 자소서 생성(Chat Logic) 단계별 API
# ==========================================
# UI의 Progress Card 4단계를 반영하여 백엔드의 4개 엔드포인트 호출
def parse_request_api(prompt, selected_model):
    res = requests.post(f"{BASE_URL}/chat/step-parse", json={"prompt": prompt, "model": selected_model})
    return res.json() if res.status_code == 200 else {}

def generate_local_draft_api(prompt, user_info, selected_model):
    res = requests.post(f"{BASE_URL}/chat/step-draft", json={"prompt": prompt, "user_info": user_info, "model": selected_model})
    return res.json().get("draft") if res.status_code == 200 else None

def refine_with_api_api(draft, prompt, selected_model):
    res = requests.post(f"{BASE_URL}/chat/step-refine", json={"draft": draft, "prompt": prompt, "model": selected_model})
    return res.json().get("refined") if res.status_code == 200 else draft

def fit_length_api(refined, prompt, selected_model):
    res = requests.post(f"{BASE_URL}/chat/step-fit", json={"refined": refined, "prompt": prompt, "model": selected_model})
    return res.json().get("adjusted") if res.status_code == 200 else refined

def build_final_response_api(adjusted, prompt, selected_model):
    res = requests.post(f"{BASE_URL}/chat/step-final", json={"adjusted": adjusted, "prompt": prompt, "model": selected_model})
    return res.json().get("final_response") if res.status_code == 200 else adjusted