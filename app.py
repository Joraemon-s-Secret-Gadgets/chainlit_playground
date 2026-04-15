import base64
import json
import os
import random
import time

import streamlit as st

import auth
import database as db
from chat_logic import (
    build_final_response,
    fit_length_if_needed,
    parse_user_request,
    refine_with_api,
    regenerate_local_draft_if_needed,
)
from database import delete_chat_history, load_chat_history, save_chat_message

# ==========================================
# 페이지 기본 설정 및 초기화
# ==========================================
st.set_page_config(
    page_title="JobPocket",
    page_icon="public/logo_light.png",
    layout="wide",
)
db.init_db()

# 세션 상태 초기화
DEFAULT_SESSION_VALUES = {
    "logged_in": False,
    "user_info": None,
    "messages": [],
    "page": "login",
    "menu": "chat",
    "reset_email": None,
    "selected_model": "GPT-4o-mini",
    "reset_code": None,
    "code_verified": False,
    "history_loaded_for": None,
    "show_welcome": True,
}

for key, value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value

AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"


# ==========================================
# 공통 UI
# ==========================================
def apply_custom_css():
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {display: none !important;}

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        .custom-navbar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid #CAD9F0;
        }

        .custom-navbar img {
            width: 65px;
            object-fit: contain;
            border-radius: 6px;
        }

        .custom-navbar h1 {
            margin: 0;
            padding: 0;
            font-size: 1.6rem;
            font-weight: 800;
            color: #31333F;
            line-height: 1;
        }

        .progress-card {
            padding: 0.9rem 1rem;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            background: #FAFAFA;
            margin-bottom: 0.8rem;
            line-height: 1.8;
        }

        .progress-card b {
            display: block;
            margin-bottom: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_header(title: str):
    img_path = "public/logo_light.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <div class="custom-navbar">
                <img src="data:image/png;base64,{encoded_string}" alt="Logo">
                <h1>{title}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="custom-navbar">
                <h1>{title}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )


apply_custom_css()


# ==========================================
# 인증 뷰
# ==========================================
def login_view():
    display_header("로그인")
    st.write("")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        with st.form("login_form"):
            email = st.text_input("이메일 주소")
            password = st.text_input("비밀번호", type="password")

            if st.form_submit_button("로그인", use_container_width=True):
                user = db.get_user(email)
                if user and user[1] == auth.hash_pw(password):
                    st.session_state.logged_in = True
                    st.session_state.user_info = user
                    st.session_state.menu = "chat"
                    st.session_state.history_loaded_for = None
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("회원가입", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        with col2:
            if st.button("비밀번호 찾기", use_container_width=True):
                st.session_state.page = "find_password"
                st.rerun()


def signup_view():
    display_header("회원가입")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        with st.form("signup_form"):
            new_name = st.text_input("이름 (실명) *")
            new_email = st.text_input("이메일 *")
            new_pw = st.text_input("비밀번호 *", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인 *", type="password")

            if st.form_submit_button("가입완료", use_container_width=True):
                if not new_name or not new_email or not new_pw:
                    st.warning("모든 필수 항목을 입력해주세요.")
                elif new_pw != new_pw_confirm:
                    st.error("비밀번호 확인이 일치하지 않습니다.")
                else:
                    success, msg = db.add_user_via_web(
                        new_name,
                        auth.hash_pw(new_pw),
                        new_email,
                        {},
                    )
                    if success:
                        st.success("회원가입 성공! 로그인해 주세요.")
                        time.sleep(1)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)

        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"
            st.rerun()


def find_password_view():
    display_header("비밀번호 재설정")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        if st.session_state.reset_code is None:
            with st.form("find_pw_form"):
                email = st.text_input("가입하신 이메일 주소")
                if st.form_submit_button("인증번호 발송", use_container_width=True):
                    if db.get_user(email):
                        code = str(random.randint(100000, 999999))
                        st.session_state.reset_code = code
                        st.session_state.reset_email = email
                        st.success(f"테스트용 알림: [ {code} ] 인증번호가 발송되었습니다.")
                    else:
                        st.error("해당 이메일로 가입된 정보가 없습니다.")
        else:
            st.info(f"{st.session_state.reset_email}로 발송된 인증번호 6자리를 입력해주세요.")
            with st.form("verify_code_form"):
                code_input = st.text_input("인증번호 6자리")
                if st.form_submit_button("인증 확인", use_container_width=True):
                    if code_input == st.session_state.reset_code:
                        st.session_state.code_verified = True
                        st.session_state.page = "reset_password"
                        st.rerun()
                    else:
                        st.error("인증번호가 일치하지 않습니다.")

            if st.button("← 이메일 다시 입력하기", use_container_width=True):
                st.session_state.reset_code = None
                st.session_state.reset_email = None
                st.rerun()

        st.write("")
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.reset_code = None
            st.session_state.page = "login"
            st.rerun()


def reset_password_view():
    if not st.session_state.get("code_verified"):
        st.error("비정상적인 접근입니다. 이메일 인증을 다시 진행해 주세요.")
        st.session_state.page = "login"
        st.rerun()

    display_header("새로운 비밀번호 설정")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        with st.form("reset_pw_form"):
            new_pw = st.text_input("새로운 비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")

            if st.form_submit_button("비밀번호 변경", use_container_width=True):
                if new_pw != new_pw_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    if db.update_password(st.session_state.reset_email, auth.hash_pw(new_pw)):
                        st.success("비밀번호가 성공적으로 변경되었습니다!")
                        time.sleep(1.5)
                        st.session_state.reset_email = None
                        st.session_state.reset_code = None
                        st.session_state.code_verified = False
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("처리 중 오류가 발생했습니다.")


# ==========================================
# 메인 서비스
# ==========================================
def mypage_view():
    display_header("내 스펙 보관함")
    st.caption("면접관에게 어필할 객관적인 '팩트'만 입력해 주세요. 스토리는 AI가 대화로 끌어내 줍니다.")
    user_info = st.session_state.user_info

    try:
        data = json.loads(user_info[4]) if user_info[4] else {}
    except Exception:
        data = {}

    personal = data.get("personal", {})
    edu = data.get("education", {})
    add = data.get("additional", {})

    with st.form("resume_form"):
        tab1, tab2, tab3 = st.tabs(["👤 인적사항", "🎓 학력", "🏆 경력/스펙"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                eng_name = st.text_input("영문 이름", value=personal.get("eng_name", ""))
            with col2:
                gender_opts = ["선택안함", "남성", "여성"]
                curr_gender = personal.get("gender", "선택안함")
                gender_idx = gender_opts.index(curr_gender) if curr_gender in gender_opts else 0
                gender = st.selectbox("성별", gender_opts, index=gender_idx)

        with tab2:
            school = st.text_input("최종 학력 (학교명)", value=edu.get("school", ""))
            major = st.text_input("전공", value=edu.get("major", ""))

        with tab3:
            exp = st.text_area(
                "직무 관련 경험 (인턴/알바/실무/프로젝트)",
                value=add.get("internship", ""),
                height=250,
            )
            awards = st.text_area(
                "수상 내역 및 대외활동",
                value=add.get("awards", ""),
                height=150,
            )
            tech = st.text_input(
                "기술 스택 / 자격증 (쉼표로 구분)",
                value=add.get("tech_stack", ""),
            )

        if st.form_submit_button("💾 내 스펙 저장하기", type="primary"):
            new_resume = {
                "personal": {"eng_name": eng_name, "gender": gender},
                "education": {"school": school, "major": major},
                "additional": {"internship": exp, "awards": awards, "tech_stack": tech},
            }
            if db.update_resume_data(user_info[2], new_resume):
                st.session_state.user_info = db.get_user(user_info[2])
                st.success("✅ 스펙이 성공적으로 저장되었습니다!")
                st.rerun()


def render_assistant_message(content: str, message_index: int):
    if "[자소서 초안]" in content:
        st.markdown(content)
        try:
            resume_text = content.split("[자소서 초안]")[1].split("[자소서 초안 평가]")[0].strip()
            st.divider()
            st.caption("📋 아래 박스 우측 상단의 아이콘을 눌러 자소서 본문만 쉽게 복사하세요.")
            st.code(resume_text, language="plaintext")
        except IndexError:
            pass

        st.write("이 대답이 마음에 드시나요?")
        col1, col2, _ = st.columns([0.4, 0.4, 9.2])
        feedback_key = f"feedback_{message_index}"

        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = None

        if st.session_state[feedback_key] is None:
            with col1:
                if st.button("👍", key=f"good_{message_index}"):
                    st.session_state[feedback_key] = "good"
                    st.rerun()
            with col2:
                if st.button("👎", key=f"bad_{message_index}"):
                    st.session_state[feedback_key] = "bad"
                    st.rerun()
        else:
            feedback_emoji = "👍" if st.session_state[feedback_key] == "good" else "👎"
            st.caption(f"✓ AI 초안 평가 완료: **{feedback_emoji}**")
    else:
        st.markdown(content)


def render_progress_card():
    st.markdown(
        """
        <div class="progress-card">
            <b>진행 단계</b>
            1. 문항과 요청 정보 정리<br>
            2. 로컬 모델로 초안 생성<br>
            3. API 모델로 문장 정리<br>
            4. 글자 수와 전체 흐름 최종 점검
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_response_with_progress(prompt: str, user_info: tuple, selected_model: str):
    parsed = None
    local_draft = None
    refined = None
    adjusted = None

    status_box = st.empty()
    step_box = st.empty()

    render_progress_card()

    # 1단계
    status_box.info("입력 내용을 확인하고 있습니다.")
    step_box.caption("1/4 문항과 요청 정보를 정리하고 있습니다.")
    parsed = parse_user_request(prompt, selected_model)
    time.sleep(0.15)

    # 2단계
    company_name = parsed.get("company_display") or parsed.get("company") or "미기재"
    question_name = parsed.get("question") or "자기소개서 문항"
    status_box.info(f"회사/문항 정보를 정리했습니다. ({company_name} / {question_name})")
    step_box.caption("2/4 로컬 모델이 초안을 작성하고 있습니다.")
    local_draft = regenerate_local_draft_if_needed(
        user_message=prompt,
        user_profile=user_info,
        selected_model=selected_model,
        max_attempts=2,
    )

    # 3단계
    status_box.info("로컬 초안이 생성되었습니다. 문장 흐름을 다듬고 있습니다.")
    step_box.caption("3/4 API 모델이 문장을 다듬고 있습니다.")
    try:
        refined = refine_with_api(local_draft, prompt, selected_model)
    except Exception:
        refined = local_draft

    # 4단계
    status_box.info("최종 문장 길이와 전체 흐름을 점검하고 있습니다.")
    step_box.caption("4/4 글자 수와 전체 흐름을 최종 점검하고 있습니다.")
    try:
        adjusted = fit_length_if_needed(refined, prompt, selected_model)
    except Exception:
        adjusted = refined

    final_response = build_final_response(adjusted, prompt, selected_model)
    status_box.success("초안 생성이 완료되었습니다.")
    step_box.empty()

    return final_response


def chat_view():
    display_header("JobPocket")
    user_email = st.session_state.user_info[2]

    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = not bool(st.session_state.messages)

    if st.session_state.show_welcome:
        user_name = st.session_state.user_info[0]

        st.markdown(
            f"""
            <div style="background-color: #F0F8FF; padding: 2.5rem; border-radius: 15px; text-align: center; border: 2px solid #3B82F6; margin-top: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #3B82F6; margin-bottom: 1rem; font-weight: 800;">반갑습니다, {user_name}님! 👋</h2>
                <p style="font-size: 1.2rem; color: #333; margin-bottom: 1.5rem;"><strong>JobPocket</strong>이 여러분의 합격 여정을 함께합니다.</p>
                <div style="text-align: left; display: inline-block; margin-bottom: 2rem; color: #555; font-size: 1.05rem; line-height: 2;">
                    🚀 <b>내 스펙 기반:</b> 입력한 경험을 바탕으로 팩트 중심 초안 생성<br>
                    🤖 <b>듀얼 모델 지원:</b> GPT-4o-mini와 GPT-OSS-120B 선택 가능<br>
                    📝 <b>단계형 생성 안내:</b> 초안 생성부터 최종 정리까지 진행 상태 확인 가능
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("🚀 대화 시작하기", use_container_width=True, type="primary"):
                st.session_state.show_welcome = False

                if not st.session_state.messages:
                    greeting = (
                        "안녕하세요! 지원하시려는 **회사와 직무**, 그리고 **자기소개서 문항**을 편하게 남겨주세요. "
                        "보관함에 등록해 두신 스펙을 바탕으로 맞춤형 자소서 초안을 작성해 드리겠습니다. 😊"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": greeting})
                    save_chat_message(user_email, "assistant", greeting)

                st.rerun()
        return

    # 기존 메시지 렌더링
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AI_AVATAR):
            if message["role"] == "assistant":
                render_assistant_message(message["content"], i)
            else:
                st.markdown(message["content"])

    # 사용자 입력
    if prompt := st.chat_input("지원하실 회사와 직무, 자기소개서의 문항을 작성해주세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message(user_email, "user", prompt)

        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=AI_AVATAR):
            result_box = st.empty()

            try:
                response = generate_response_with_progress(
                    prompt=prompt,
                    user_info=st.session_state.user_info,
                    selected_model=st.session_state.selected_model,
                )

                result_box.markdown(response)

                if "[자소서 초안]" in response:
                    try:
                        resume_text = response.split("[자소서 초안]")[1].split("[자소서 초안 평가]")[0].strip()
                        st.divider()
                        st.caption("📋 아래 박스 우측 상단의 아이콘을 눌러 자소서 본문만 쉽게 복사하세요.")
                        st.code(resume_text, language="plaintext")
                    except IndexError:
                        pass

                st.session_state.messages.append({"role": "assistant", "content": response})
                save_chat_message(user_email, "assistant", response)

            except Exception as e:
                error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
                result_box.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                save_chat_message(user_email, "assistant", error_message)

        st.rerun()


# ==========================================
# 메인 라우팅 및 사이드바
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_view()
    elif st.session_state.page == "signup":
        signup_view()
    elif st.session_state.page == "find_password":
        find_password_view()
    elif st.session_state.page == "reset_password":
        reset_password_view()
else:
    user_email = st.session_state.user_info[2]
    user_name = st.session_state.user_info[0]

    if st.session_state.history_loaded_for != user_email:
        st.session_state.messages = load_chat_history(user_email)
        st.session_state.history_loaded_for = user_email
        st.session_state.show_welcome = not bool(st.session_state.messages)

    with st.sidebar:
        img_path = "public/logo_light.png"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/png;base64,{encoded}" width="130" style="border-radius:15px; margin-bottom:20px;"></div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"### 👤 {user_name}님")

        if st.button("로그아웃", use_container_width=True, key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

        st.divider()

        menu = st.radio("메뉴 이동", ["💬 AI 자소서 첨삭", "👤 내 스펙 보관함"])

        st.write("")
        st.caption("🧠 AI 모델 설정")
        st.session_state.selected_model = st.selectbox(
            "엔진 선택",
            ["GPT-4o-mini", "GPT-OSS-120B (Groq)"],
            index=0 if st.session_state.selected_model == "GPT-4o-mini" else 1,
            label_visibility="collapsed",
        )

        st.divider()

        col_hist_title, col_hist_btn = st.columns([7, 3])
        with col_hist_title:
            st.markdown("#### 📝 대화 기록")
        with col_hist_btn:
            if st.button("🗑️", key="clear_all_btn", use_container_width=True):
                delete_chat_history(user_email)
                st.session_state.messages = []
                st.session_state.show_welcome = True
                st.rerun()

        if st.session_state.messages:
            user_questions = [m for m in st.session_state.messages if m["role"] == "user"]
            with st.container(height=300):
                for q in reversed(user_questions):
                    short_q = q["content"][:15] + "..." if len(q["content"]) > 15 else q["content"]
                    st.markdown(
                        f"<div style='padding:5px 0; font-size:0.9em; color:#555;'>💬 {short_q}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("대화 기록이 없습니다.")

    if "AI 자소서 첨삭" in menu:
        chat_view()
    else:
        mypage_view()