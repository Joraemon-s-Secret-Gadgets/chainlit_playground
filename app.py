# app.py
import streamlit as st
import database as db
import auth
from chat_logic import generate_ai_feedback_stream
import time
import json
import base64
import os

st.set_page_config(page_title="JobPocket", page_icon="public/logo_light.png", layout="wide")
db.init_db()

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_info" not in st.session_state: st.session_state.user_info = None
if "messages" not in st.session_state: st.session_state.messages = []
if "page" not in st.session_state: st.session_state.page = "login"
if "menu" not in st.session_state: st.session_state.menu = "chat"
if "reset_email" not in st.session_state: st.session_state.reset_email = None

AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"

def apply_custom_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .custom-header {
            display: flex; align-items: center; gap: 15px; margin-bottom: 2rem; padding-top: 1rem;
        }
        .custom-header img { width: 45px; height: 45px; object-fit: contain; border-radius: 8px; }
        .custom-header h1 { margin: 0; padding: 0; font-size: 2.2rem; font-weight: 800; color: #212529; }
        </style>
    """, unsafe_allow_html=True)

def display_header(title):
    img_path = "public/logo_light.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <div class="custom-header">
                <img src="data:image/png;base64,{encoded_string}" alt="Logo">
                <h1>{title}</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.title(title)

apply_custom_css()

# ==========================================
# 1. 인증 뷰
# ==========================================
def login_view():
    display_header("로그인")
    st.write("") 
    with st.form("login_form"):
        email = st.text_input("이메일 주소")
        password = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", use_container_width=True):
            user = db.get_user(email)
            if user and user[1] == auth.hash_pw(password):
                st.session_state.logged_in = True
                st.session_state.user_info = user
                st.session_state.menu = "chat"
                st.rerun()
            else: st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("회원가입", use_container_width=True): st.session_state.page = "signup"; st.rerun()
    with col2:
        if st.button("비밀번호 찾기", use_container_width=True): st.session_state.page = "find_password"; st.rerun()

def signup_view():
    display_header("회원가입")
    with st.form("signup_form"):
        new_name = st.text_input("이름 (실명) *")
        new_email = st.text_input("이메일  *")
        new_pw = st.text_input("비밀번호 *", type="password")
        new_pw_confirm = st.text_input("비밀번호 확인 *", type="password")
        if st.form_submit_button("가입완료", use_container_width=True):
            if not new_name or not new_email or not new_pw: st.warning("모든 필수 항목을 입력해주세요.")
            elif new_pw != new_pw_confirm: st.error("비밀번호 확인이 일치하지 않습니다.")
            else:
                success, msg = db.add_user_via_web(new_name, auth.hash_pw(new_pw), new_email, {})
                if success:
                    st.success("회원가입 성공! 로그인해 주세요.")
                    time.sleep(1); st.session_state.page = "login"; st.rerun()
                else: st.error(msg)
    if st.button("← 로그인으로 돌아가기"): st.session_state.page = "login"; st.rerun()

def find_password_view():
    display_header("비밀번호 재설정")
    with st.form("find_pw_form"):
        email = st.text_input("이메일 주소")
        if st.form_submit_button("사용자 확인"):
            if db.get_user(email):
                st.session_state.reset_email = email; st.session_state.page = "reset_password"; st.rerun()
            else: st.error("해당 이메일로 가입된 정보가 없습니다.")
    if st.button("← 로그인으로 돌아가기"): st.session_state.page = "login"; st.rerun()

def reset_password_view():
    display_header("새로운 비밀번호 설정")
    with st.form("reset_pw_form"):
        new_pw = st.text_input("새로운 비밀번호", type="password")
        new_pw_confirm = st.text_input("비밀번호 확인", type="password")
        if st.form_submit_button("비밀번호 변경"):
            if new_pw != new_pw_confirm: st.error("비밀번호가 일치하지 않습니다.")
            else:
                if db.update_password(st.session_state.reset_email, auth.hash_pw(new_pw)):
                    st.success("비밀번호가 성공적으로 변경되었습니다!")
                    time.sleep(1.5); st.session_state.reset_email = None; st.session_state.page = "login"; st.rerun()
                else: st.error("처리 중 오류가 발생했습니다.")

# ==========================================
# 2. 메인 서비스 (Mypage 초경량화 - 연락처 제거)
# ==========================================
def mypage_view():
    display_header("내 스펙 보관함")
    st.caption("면접관에게 어필할 객관적인 '팩트'만 입력해 주세요. 스토리는 AI가 대화로 끌어내 줍니다.")
    user_info = st.session_state.user_info
    
    try: data = json.loads(user_info[4]) if user_info[4] else {}
    except: data = {}

    personal = data.get("personal", {})
    edu = data.get("education", {})
    add = data.get("additional", {})

    with st.form("resume_form"):
        tab1, tab2, tab3 = st.tabs(["👤 인적사항", "🎓 학력", "🏆 경력/스펙"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                # 연락처 항목 완전히 제거됨
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
            exp = st.text_area("직무 관련 경험 (인턴/알바/실무/프로젝트)", value=add.get("internship", ""))
            awards = st.text_area("수상 내역 및 대외활동", value=add.get("awards", ""))
            tech = st.text_input("기술 스택 / 자격증 (쉼표로 구분)", value=add.get("tech_stack", ""))

        if st.form_submit_button("💾 내 스펙 저장하기", type="primary"):
            new_resume = {
                # 저장 로직에서도 phone 제거
                "personal": {"eng_name": eng_name, "gender": gender},
                "education": {"school": school, "major": major},
                "additional": {"internship": exp, "awards": awards, "tech_stack": tech}
            }
            if db.update_resume_data(user_info[2], new_resume):
                st.session_state.user_info = db.get_user(user_info[2])
                st.success("✅ 스펙이 성공적으로 저장되었습니다!")
                st.rerun()

def chat_view():
    display_header("JobPocket")
    
    if not st.session_state.user_info[4] or st.session_state.user_info[4] == "{}":
        st.warning("💡 **스펙이 비어있네요! 왼쪽 메뉴에서 기본 스펙을 적어주시면 더 좋은 인터뷰가 진행됩니다.**")

    for msg in st.session_state.messages:
        avatar_img = USER_AVATAR if msg["role"] == "user" else AI_AVATAR
        with st.chat_message(msg["role"], avatar=avatar_img):
            st.markdown(msg["content"])

    if prompt := st.chat_input("지원하실 회사와 직무를 편하게 말씀해 주세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR): 
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar=AI_AVATAR):
            response = st.write_stream(generate_ai_feedback_stream(prompt, st.session_state.user_info))
            st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# 3. 메인 라우팅 (사이드바)
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.page == "login": login_view()
    elif st.session_state.page == "signup": signup_view()
    elif st.session_state.page == "find_password": find_password_view()
    elif st.session_state.page == "reset_password": reset_password_view()
else:
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    img_path = "public/logo_light.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.sidebar.markdown(f"""
            <div style="display:flex; justify-content:center; align-items:center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{encoded_string}" width="80" style="border-radius:10px;">
            </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"<h3 style='text-align: center;'>{st.session_state.user_info[0]}님</h3>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    menu = st.sidebar.radio("메뉴 이동", ["💬 AI 자소서 첨삭", "👤 내 스펙 보관함"])
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.clear(); st.rerun()
        
    if "AI 자소서 첨삭" in menu: chat_view()
    else: mypage_view()