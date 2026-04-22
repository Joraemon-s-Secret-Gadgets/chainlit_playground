"""
[파일명: frontend/utils/api_client.py]
역할: Streamlit 프론트엔드와 FastAPI 백엔드 사이의 통신을 담당하는 API 클라이언트 모듈입니다.
주요 기능: 
1. 사용자 인증(로그인, 회원가입, 비밀번호 변경)
2. 사용자 스펙 데이터(이력서) 관리
3. 채팅 내역 로드 및 저장, 삭제
4. AI 자소서 생성 로직의 단계별 API 호출
"""

import requests

# 백엔드 서버 주소 (FastAPI 서버가 실행 중인 URL)
BASE_URL = "http://localhost:8000/api"

# ---------------------------------------------------------
# [사용자 인증 관련 API]
# ---------------------------------------------------------

def login_api(email, password):
    """
    사용자 로그인을 처리합니다.
    - 파라미터: email(str), password(str)
    - 반환값: (성공 여부: bool, 유저 정보 혹은 에러 메시지)
    - UI 역할: 로그인 화면에서 호출되어 st.session_state.logged_in 상태를 결정합니다.
    """
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        # 로그인 성공 시 백엔드에서 넘겨준 유저 정보를 반환합니다.
        return True, res.json().get("user_info")
    # 실패 시 백엔드의 'detail' 메시지를 가져옵니다.
    return False, res.json().get("detail", "로그인 실패")

def signup_api(name, email, password):
    """
    신규 회원가입을 처리합니다.
    - 파라미터: name(str), email(str), password(str)
    - 반환값: (성공 여부: bool, 결과 메시지)
    """
    res = requests.post(f"{BASE_URL}/auth/signup", json={"name": name, "email": email, "password": password})
    if res.status_code == 200:
        return True, "가입 성공"
    return False, res.json().get("detail", "회원가입 처리 중 오류 발생")

def update_password_api(email, new_password):
    """
    사용자의 비밀번호를 재설정(변경)합니다.
    - 파라미터: email(str), new_password(str)
    - 반환값: 성공 여부(bool)
    """
    res = requests.post(f"{BASE_URL}/auth/reset-pw", json={"email": email, "new_password": new_password})
    return res.status_code == 200


# ---------------------------------------------------------
# [이력서/스펙 데이터 관리 API]
# ---------------------------------------------------------

def get_user_resume_api(email):
    """
    사용자의 저장된 스펙(이력서 데이터)을 가져옵니다.
    - 파라미터: email(str)
    - 반환값: resume_data(JSON 문자열)
    - UI 역할: '내 스펙 보관함' 뷰에서 데이터를 불러올 때 사용합니다.
    """
    res = requests.get(f"{BASE_URL}/resume/{email}")
    if res.status_code == 200:
        return res.json().get("resume_data", "{}")
    return "{}"

def update_resume_data_api(email, new_resume_data):
    """
    사용자의 스펙 정보를 백엔드 DB에 업데이트(저장)합니다.
    - 파라미터: email(str), new_resume_data(dict)
    - 반환값: 성공 여부(bool)
    """
    res = requests.put(f"{BASE_URL}/resume/{email}", json=new_resume_data)
    return res.status_code == 200


# ---------------------------------------------------------
# [채팅 내역 관리 API]
# ---------------------------------------------------------

def load_chat_history_api(email):
    """
    과거 대화 내역을 백엔드에서 불러옵니다.
    - 파라미터: email(str)
    - 반환값: 메시지 리스트(list)
    - 💡 Tip: Streamlit 재시작 시 st.session_state.messages를 유지하기 위해 필수인 함수입니다.
    """
    res = requests.get(f"{BASE_URL}/chat/history/{email}")
    if res.status_code == 200:
        return res.json().get("messages", [])
    return []

def save_chat_message_api(email, role, content):
    """
    새로운 대화 메시지(사용자 혹은 AI)를 DB에 실시간 저장합니다.
    - 파라미터: email(str), role(str: 'user'/'assistant'), content(str)
    """
    requests.post(f"{BASE_URL}/chat/message", json={"email": email, "role": role, "content": content})

def delete_chat_history_api(email):
    """
    현재 사용자의 모든 대화 기록을 초기화합니다.
    - 파라미터: email(str)
    """
    requests.delete(f"{BASE_URL}/chat/history/{email}")


# ---------------------------------------------------------
# [AI 자소서 생성 단계별 로직 API]
# 💡 이 섹션은 JobPocket의 핵심인 '멀티스텝 생성' 프로세스를 따릅니다.
# ---------------------------------------------------------

def parse_request_api(prompt, selected_model):
    """
    [1단계: 의도 파악] 사용자의 입력에서 자소서 문항과 회사명을 추출합니다.
    - 파라미터: prompt(사용자 입력), selected_model(선택된 AI 모델)
    - 반환값: 추출된 정보가 담긴 딕셔너리
    """
    res = requests.post(f"{BASE_URL}/chat/step-parse", json={"prompt": prompt, "model": selected_model})
    return res.json() if res.status_code == 200 else {}

def generate_local_draft_api(prompt, user_info, selected_model):
    """
    [2단계: 로컬 모델 초안 생성] 사용자의 스펙을 기반으로 1차 초안을 작성합니다.
    - 💡 로컬 모델(Ollama 등)을 사용하여 비용을 절감하는 구간입니다.
    """
    res = requests.post(
        f"{BASE_URL}/chat/step-draft",
        json={"prompt": prompt, "user_info": user_info, "model": selected_model},
    )
    return res.json().get("draft") if res.status_code == 200 else None

def revise_existing_draft_api(existing_draft, revision_request, selected_model):
    """
    [수정 요청 처리] 기존 초안에 대한 사용자의 수정 피드백을 반영합니다.
    """
    res = requests.post(
        f"{BASE_URL}/chat/step-revise",
        json={"existing_draft": existing_draft, "revision_request": revision_request, "model": selected_model},
    )
    return res.json().get("revised") if res.status_code == 200 else existing_draft

def refine_with_api_api(draft, prompt, selected_model):
    """
    [3단계: 고성능 모델 문장 정제] 생성된 초안의 가독성과 전문성을 높입니다.
    - 💡 GPT-4o-mini 등 고성능 API 모델을 주로 사용합니다.
    """
    res = requests.post(f"{BASE_URL}/chat/step-refine", json={"draft": draft, "prompt": prompt, "model": selected_model})
    return res.json().get("refined") if res.status_code == 200 else draft

def fit_length_api(refined, prompt, selected_model):
    """
    [4단계: 글자 수 조정] 사용자가 요청한 분량(예: 500자)에 맞춰 내용을 최적화합니다.
    """
    res = requests.post(f"{BASE_URL}/chat/step-fit", json={"refined": refined, "prompt": prompt, "model": selected_model})
    return res.json().get("adjusted") if res.status_code == 200 else refined

def build_final_response_api(adjusted, prompt, selected_model, result_label="자소서 초안", change_summary=None):
    """
    [최종 결과물 포맷팅] 가이드 및 평가 코멘트를 포함한 최종 답변을 구성합니다.
    - 반환값: 화면에 출력될 최종 마크다운 텍스트
    """
    payload = {
        "adjusted": adjusted,
        "prompt": prompt,
        "model": selected_model,
        "result_label": result_label,
        "change_summary": change_summary,
    }
    res = requests.post(f"{BASE_URL}/chat/step-final", json=payload)
    return res.json().get("final_response") if res.status_code == 200 else adjusted