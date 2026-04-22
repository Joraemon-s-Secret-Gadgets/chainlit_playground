"""
[파일명: app.py (Main Entry Point)]
역할: JobPocket 서비스의 전체 실행을 관리하는 메인 관제탑 파일입니다.
주요 기능:
1. 웹 브라우저 설정 및 커스텀 디자인(CSS) 로드
2. 전역 상태 변수(Session State) 초기화 (로그인 여부, 대화 내역 등)
3. 인증 상태(로그인 전/후)에 따른 메인 화면 라우팅 제어
4. 사이드바 UI 구성 및 메뉴 전환 로직 관리
"""

import streamlit as st
import os
import base64

from utils.ui_components import apply_custom_css
from utils import api_client
from views import auth_view, resume_view, chat_view

# =========================================================
# 1. 페이지 기본 설정 및 세션 초기화
# =========================================================

# 브라우저 탭에 표시될 제목, 아이콘 및 전체 레이아웃 폭을 설정합니다.
# 💡 Tip: st.set_page_config는 파일 최상단(Import 제외)에서 딱 한 번만 실행되어야 합니다.
st.set_page_config(page_title="JobPocket", page_icon="public/logo_light.png", layout="wide")

# 별도로 정의된 CSS 스타일을 앱에 주입합니다.
apply_custom_css()

# [Session State 초기값 정의]
# Streamlit은 사용자가 버튼을 누를 때마다 코드를 처음부터 다시 실행합니다.
# '상태'를 기억하기 위해 st.session_state라는 전역 저장소를 활용합니다.
DEFAULT_SESSION_VALUES = {
    "logged_in": False,            # 로그인 여부 (True면 메인 서비스 노출)
    "user_info": None,             # 백엔드에서 받아온 유저 이름, 이메일 등 정보
    "messages": [],                # 현재 채팅 화면에 표시되는 대화 내역
    "page": "login",               # 로그인 전 화면 이동 (login, signup, reset_pw 등)
    "menu": "chat",                # 로그인 후 메인 메뉴 (chat: AI 채팅, resume: 스펙 관리)
    "reset_email": None,           # 비밀번호 재설정 시 타겟 이메일
    "selected_model": "GPT-4o-mini", # 사용자가 선택한 AI 엔진 모델명
    "reset_code": None,            # 비밀번호 찾기 시 인증 코드
    "code_verified": False,        # 인증 코드 일치 여부
    "history_loaded_for": None,    # 현재 메모리에 로드된 대화 내역의 유저 이메일
    "show_welcome": True,          # 채팅 시작 전 환영 창 노출 여부
    "pending_prompt": None,        # '보완 적용' 버튼 클릭 시 다음 리런에 처리할 프롬프트
    "current_result_version": 0,   # 자소서 수정안의 차수 (1차, 2차...)
}

# 💡 Tip: 세션 상태가 비어있을 때만 기본값으로 채워넣어 데이터가 초기화되는 것을 방지합니다.
for key, value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 2. 메인 라우팅 (로그인 전 - 인증 화면 영역)
# =========================================================

# 사용자가 로그인하지 않은 상태일 때의 화면 분기입니다.
if not st.session_state.logged_in:
    # st.session_state.page 값에 따라 어떤 뷰(View) 함수를 호출할지 결정합니다.
    if st.session_state.page == "login":
        auth_view.login_view()
    elif st.session_state.page == "signup":
        auth_view.signup_view()
    elif st.session_state.page == "find_password":
        auth_view.find_password_view()
    elif st.session_state.page == "reset_password":
        auth_view.reset_password_view()


# =========================================================
# 3. 사이드바 및 메인 라우팅 (로그인 후 - 메인 서비스 영역)
# =========================================================

else:
    # -----------------------------------------------------
    # [데이터 준비 섹션] - 로그인 직후 정보 추출 및 대화 기록 로드
    # -----------------------------------------------------
    user_email = st.session_state.user_info[2]
    user_name = st.session_state.user_info[0]

    # 페이지가 새로고침될 때마다 DB에 가지 않고, 
    # 로드된 기록이 현재 사용자의 것이 아닐 때만 API를 호출합니다. (최적화)
    if st.session_state.history_loaded_for != user_email:
        st.session_state.messages = api_client.load_chat_history_api(user_email)
        st.session_state.history_loaded_for = user_email
        # 대화 기록이 있으면 환영 인사창을 건너뛰고 채팅창을 바로 보여줍니다.
        st.session_state.show_welcome = not bool(st.session_state.messages)

    # -----------------------------------------------------
    # [사이드바 UI 섹션] - 좌측 고정 메뉴
    # -----------------------------------------------------
    with st.sidebar:
        # 서비스 로고 표시
        img_path = "public/logo_light.png"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/png;base64,{encoded}" width="130" style="border-radius:15px; margin-bottom:20px;"></div>',
                unsafe_allow_html=True,
            )

        # [프로필 및 스펙 관리 페이지 이동]
        # st.popover를 사용해 이름 클릭 시 버튼이 나타나도록 설계했습니다.
        with st.popover(f"👤 {user_name}님", use_container_width=True):
            if st.button("📁 내 스펙 보관함", use_container_width=True):
                st.session_state.menu = "resume"
                st.rerun()

        # [메인 채팅 이동 버튼]
        if st.button("💬 새 채팅 (AI 자소서 첨삭)", use_container_width=True):
            st.session_state.menu = "chat"
            st.rerun()
            
        st.write("")
        st.caption("🧠 AI 모델 설정")
        
        # [AI 모델 선택 드롭다운]
        # 선택된 엔진 정보는 st.session_state.selected_model에 즉시 저장됩니다.
        st.session_state.selected_model = st.selectbox(
            "엔진 선택",
            ["GPT-4o-mini", "GPT-OSS-120B (Groq)"],
            index=0 if st.session_state.selected_model == "GPT-4o-mini" else 1,
            label_visibility="collapsed",
        )

        # [대화 내역 리스트 영역]
        col_hist_title, col_hist_btn = st.columns([7, 3])
        with col_hist_title:
            st.markdown("#### 📝 대화 기록")
        with col_hist_btn:
            # 전체 대화 내역 삭제 버튼
            if st.button("🗑️", key="clear_all_btn", use_container_width=True):
                api_client.delete_chat_history_api(user_email)
                st.session_state.messages = []
                st.session_state.show_welcome = True
                st.session_state.current_result_version = 0
                st.rerun()

        # 최근 대화 내용 요약 표시 (질문 내용만 추출)
        if st.session_state.messages:
            user_questions = [m for m in st.session_state.messages if m["role"] == "user"]
            with st.container(height=300):
                # 최신 대화가 위로 오도록 역순(reversed)으로 표시합니다.
                for q in reversed(user_questions):
                    short_q = q["content"][:15] + "..." if len(q["content"]) > 15 else q["content"]
                    st.markdown(
                        f"<div style='padding:5px 0; font-size:0.9em; color:#555;'>💬 {short_q}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("대화 기록이 없습니다.")

        # [로그아웃 버튼]
        # 사이드바 최하단에 배치하기 위해 빈 공백(spacer)을 삽입 후 버튼을 배치합니다.
        st.markdown('<div class="sidebar-bottom-spacer"></div>', unsafe_allow_html=True)
        if st.button("로그아웃", use_container_width=True, key="logout_sidebar"):
            # 세션의 모든 정보를 비우고 초기 로그인 페이지로 돌아갑니다.
            st.session_state.clear()
            st.rerun()

    # -----------------------------------------------------
    # [메인 뷰 라우팅 섹션] - 사이드바 메뉴 선택에 따른 실제 화면 렌더링
    # -----------------------------------------------------
    # 💡 Tip: 조원들에게 설명할 때 "menu 변수가 바뀌면 이 if문이 작동해서 화면이 교체된다"고 말하면 이해가 빠릅니다.
    if st.session_state.menu == "chat":
        chat_view.chat_view()       # AI 채팅 화면 호출
    else:
        resume_view.mypage_view()   # 내 스펙 보관함 화면 호출