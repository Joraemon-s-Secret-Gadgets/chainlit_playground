import streamlit as st
import os
import base64

from utils.ui_components import apply_custom_css
from utils import api_client
from views import auth_view, resume_view, chat_view

# ==========================================
# 1. 페이지 기본 설정 및 세션 초기화
# ==========================================
st.set_page_config(page_title="JobPocket", page_icon="public/logo_light.png", layout="wide")
apply_custom_css()

DEFAULT_SESSION_VALUES = {
    "logged_in": False, "user_info": None, "messages": [], "page": "login",
    "menu": "chat", "reset_email": None, "selected_model": "GPT-4o-mini",
    "reset_code": None, "code_verified": False, "history_loaded_for": None,
    "show_welcome": True,
}
for key, value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. 메인 라우팅 (로그인 전)
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.page == "login": auth_view.login_view()
    elif st.session_state.page == "signup": auth_view.signup_view()
    elif st.session_state.page == "find_password": auth_view.find_password_view()
    elif st.session_state.page == "reset_password": auth_view.reset_password_view()

# ==========================================
# 3. 사이드바 및 메인 라우팅 (로그인 후)
# ==========================================
else:
    user_email = st.session_state.user_info[2]
    user_name = st.session_state.user_info[0]

    # 대화 내역 불러오기
    if st.session_state.history_loaded_for != user_email:
        st.session_state.messages = api_client.load_chat_history_api(user_email)
        st.session_state.history_loaded_for = user_email
        st.session_state.show_welcome = not bool(st.session_state.messages)

    # 사이드바 렌더링
    with st.sidebar:
        img_path = "public/logo_light.png"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{encoded}" width="130" style="border-radius:15px; margin-bottom:20px;"></div>', unsafe_allow_html=True)

        st.markdown(f"### 👤 {user_name}님")

        if st.button("로그아웃", use_container_width=True, key="logout_sidebar"):
            st.session_state.clear(); st.rerun()

        st.divider()
        menu = st.radio("메뉴 이동", ["💬 AI 자소서 첨삭", "👤 내 스펙 보관함"])
        
        st.write("")
        st.caption("🧠 AI 모델 설정")
        st.session_state.selected_model = st.selectbox(
            "엔진 선택", ["GPT-4o-mini", "GPT-OSS-120B (Groq)"],
            index=0 if st.session_state.selected_model == "GPT-4o-mini" else 1,
            label_visibility="collapsed",
        )

        st.divider()
        col_hist_title, col_hist_btn = st.columns([7, 3])
        with col_hist_title: st.markdown("#### 📝 대화 기록")
        with col_hist_btn:
            if st.button("🗑️", key="clear_all_btn", use_container_width=True):
                api_client.delete_chat_history_api(user_email)
                st.session_state.messages = []
                st.session_state.show_welcome = True
                st.rerun()

        if st.session_state.messages:
            user_questions = [m for m in st.session_state.messages if m["role"] == "user"]
            with st.container(height=300):
                for q in reversed(user_questions):
                    short_q = q["content"][:15] + "..." if len(q["content"]) > 15 else q["content"]
                    st.markdown(f"<div style='padding:5px 0; font-size:0.9em; color:#555;'>💬 {short_q}</div>", unsafe_allow_html=True)
        else:
            st.caption("대화 기록이 없습니다.")

    # 뷰 렌더링
    if "AI 자소서 첨삭" in menu:
        chat_view.chat_view()
    else:
        resume_view.mypage_view()