import streamlit as st
import database as db
import auth
from chat_logic import generate_ai_feedback_stream
import time
import json
import base64
import os
import random

# 페이지 기본 설정
st.set_page_config(page_title="JobPocket", page_icon="public/logo_light.png", layout="wide")
db.init_db()

# 세션 상태 초기화
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_info" not in st.session_state: st.session_state.user_info = None
if "messages" not in st.session_state: st.session_state.messages = []
if "page" not in st.session_state: st.session_state.page = "login"
if "menu" not in st.session_state: st.session_state.menu = "chat"
if "reset_email" not in st.session_state: st.session_state.reset_email = None

# [추가됨] 모델 선택 세션
if "selected_model" not in st.session_state: st.session_state.selected_model = "GPT-4o-mini"

# 비밀번호 재설정 인증용 세션
if "reset_code" not in st.session_state: st.session_state.reset_code = None
if "code_verified" not in st.session_state: st.session_state.code_verified = False

AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"

def apply_custom_css():
    st.markdown("""
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
        </style>
    """, unsafe_allow_html=True)

def display_header(title):
    img_path = "public/logo_light.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <div class="custom-navbar">
                <img src="data:image/png;base64,{encoded_string}" alt="Logo">
                <h1>{title}</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="custom-navbar">
                <h1>{title}</h1>
            </div>
        """, unsafe_allow_html=True)

# 커스텀 CSS 적용
apply_custom_css()

# ==========================================
# 1. 인증 뷰
# ==========================================
def login_view():
    display_header("로그인")
    st.write("") 
    col_left, col_main, col_right = st.columns([1, 2, 1])
    
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
                    st.rerun()
                else: st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("회원가입", use_container_width=True): st.session_state.page = "signup"; st.rerun()
        with col2:
            if st.button("비밀번호 찾기", use_container_width=True): st.session_state.page = "find_password"; st.rerun()

def signup_view():
    display_header("회원가입")
    col_left, col_main, col_right = st.columns([1, 2, 1])
    
    with col_main:
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
    col_left, col_main, col_right = st.columns([1, 2, 1])
    
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
    col_left, col_main, col_right = st.columns([1, 2, 1])
    
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
# 2. 메인 서비스
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
            exp = st.text_area("직무 관련 경험 (인턴/알바/실무/프로젝트)", value=add.get("internship", ""), height=250)
            awards = st.text_area("수상 내역 및 대외활동", value=add.get("awards", ""), height=150)
            tech = st.text_input("기술 스택 / 자격증 (쉼표로 구분)", value=add.get("tech_stack", ""))

        if st.form_submit_button("💾 내 스펙 저장하기", type="primary"):
            new_resume = {
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

    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AI_AVATAR):
            content = message["content"]

            if message["role"] == "assistant" and "[자소서 초안]" in content:
                
                st.markdown(content)

                try:
                    resume_text = content.split("[자소서 초안]")[1].split("[자소서 초안 평가]")[0].strip()
                    
                    st.divider() 
                    st.caption("📋 아래 박스 우측 상단의 아이콘을 눌러 이력서 본문만 쉽게 복사하세요.")
                    st.code(resume_text, language="plaintext")
                except IndexError:
                    pass

                st.write("") 
                col1, col2, col3 = st.columns([1.5, 1.5, 7])
                
                feedback_key = f"feedback_{i}"
                if feedback_key not in st.session_state:
                    st.session_state[feedback_key] = None

                if st.session_state[feedback_key] is None:
                    with col1:
                        if st.button("👍", key=f"good_{i}", use_container_width=True):
                            st.session_state[feedback_key] = "good"
                            st.rerun()
                    with col2:
                        if st.button("👎", key=f"bad_{i}", use_container_width=True):
                            st.session_state[feedback_key] = "bad"
                            st.rerun()
                else:
                    feedback_emoji = "👍" if st.session_state[feedback_key] == "good" else "👎"
                    st.caption(f"✓ AI 초안 평가 완료: **{feedback_emoji}** (소중한 피드백 감사합니다!)")

            else:
                st.markdown(content)    

    if prompt := st.chat_input("지원하실 회사와 직무, 자기소개서의 문항을 작성해주세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR): 
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar=AI_AVATAR):
            # 선택된 모델 정보를 파라미터로 넘겨줍니다.
            response = st.write_stream(generate_ai_feedback_stream(
                prompt, 
                st.session_state.user_info, 
                st.session_state.selected_model
            ))
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # [핵심 Rerun 패치] 화면을 새로고침해야 복사/피드백 UI가 곧바로 생성됩니다.
        st.rerun()

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
                <img src="data:image/png;base64,{encoded_string}" width="160" style="border-radius:20px;">
            </div>
        """, unsafe_allow_html=True)
    
    # [수정됨] 이름 깨짐 원인이었던 안전하지 않은 html 코드를 제거하고 기본 안전 마크다운으로 출력합니다 (db 구조상 인덱스 0번에 이름이 들어감)
    st.sidebar.markdown(f"### 👤 {st.session_state.user_info[0]}님")
    st.sidebar.divider()
    
    # [추가됨] 모델 선택 UI 추가
    st.sidebar.caption("🧠 AI 모델 설정")
    st.session_state.selected_model = st.sidebar.selectbox(
        "사용할 엔진을 선택하세요",
        ["GPT-4o-mini", "GPT-OSS-120B (Groq)"],
        index=0 if st.session_state.selected_model == "GPT-4o-mini" else 1,
        label_visibility="collapsed"
    )
    st.sidebar.divider()
    
    menu = st.sidebar.radio("메뉴 이동", ["💬 AI 자소서 첨삭", "👤 내 스펙 보관함"])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.clear(); st.rerun()
        
    if "AI 자소서 첨삭" in menu: chat_view()
    else: mypage_view()