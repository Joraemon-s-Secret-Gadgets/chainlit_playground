"""
[파일명: auth_views.py (또는 관련 UI 파일)]
역할: 사용자의 서비스 진입점인 '로그인' 및 '회원가입' 화면을 렌더링하고 인증 로직을 처리합니다.
주요 기능:
1. 사용자 로그인 처리 및 세션 상태(Session State) 초기화
2. 신규 사용자 회원가입 및 입력값 유효성 검사
3. 화면 전환을 위한 페이지 라우팅 제어
"""

import streamlit as st
import time
from utils import api_client
from utils.ui_components import display_header

# ---------------------------------------------------------
# [로그인 화면 렌더링 섹션]
# ---------------------------------------------------------
def login_view():
    """
    로그인 화면을 구성하고 인증 로직을 수행합니다.
    - 입력: 없음 (st.session_state 참조)
    - 반환: 없음 (UI 렌더링 및 페이지 전환)
    - UI 역할: 사용자 이메일/비밀번호를 입력받아 백엔드와 통신 후 메인 화면(chat)으로 보냅니다.
    """
    # 커스텀 네비게이션 바 표시
    display_header("로그인")
    st.write("")
    
    # 💡 Tip: st.columns를 이용해 로그인 박스를 화면 중앙에 배치합니다. [1:2:1] 비율로 좌우 여백을 줍니다.
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        # 1. 로그인 폼 구성 (st.form을 사용하면 버튼을 누르기 전까지 리런이 발생하지 않아 입력이 매끄럽습니다)
        with st.form("login_form"):
            email = st.text_input("이메일 주소")
            password = st.text_input("비밀번호", type="password")

            # 2. 로그인 버튼 클릭 시 로직
            if st.form_submit_button("로그인", use_container_width=True):
                # 백엔드 API 호출 (성공 여부와 유저 데이터를 받아옴)
                success, user_data_or_error = api_client.login_api(email, password)
                
                if success:
                    # ---------------------------------------------------------
                    # [st.session_state 관리] - 로그인 성공 시 상태 업데이트
                    # ---------------------------------------------------------
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_data_or_error  # 유저 정보 저장
                    st.session_state.menu = "chat"                   # 로그인 후 첫 화면을 채팅으로 설정
                    st.session_state.history_loaded_for = None       # 채팅 내역 로드 상태 초기화
                    
                    # 💡 Tip: Streamlit은 상태가 변하면 즉시 st.rerun()을 호출해 화면을 새로 그려야 반영됩니다.
                    st.rerun()
                else:
                    # 로그인 실패 시 에러 메시지 출력
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

        # 3. 회원가입 페이지 이동 버튼 (폼 외부에 배치)
        if st.button("회원가입", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ---------------------------------------------------------
# [회원가입 화면 렌더링 섹션]
# ---------------------------------------------------------
def signup_view():
    """
    회원가입 화면을 구성하고 신규 계정 생성 로직을 수행합니다.
    - 입력: 없음
    - 반환: 없음
    - UI 역할: 필수 정보를 입력받아 가입 처리를 하고 로그인 화면으로 유도합니다.
    """
    display_header("회원가입")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        # 1. 회원가입 폼 구성
        with st.form("signup_form"):
            new_name = st.text_input("이름 (실명) *")
            new_email = st.text_input("이메일 *")
            new_pw = st.text_input("비밀번호 *", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인 *", type="password")

            # 2. 가입 완료 버튼 클릭 시 로직
            if st.form_submit_button("가입완료", use_container_width=True):
                # [유효성 검사 1] 필수 항목 입력 확인
                if not new_name or not new_email or not new_pw:
                    st.warning("모든 필수 항목을 입력해주세요.")
                # [유효성 검사 2] 비밀번호 일치 확인
                elif new_pw != new_pw_confirm:
                    st.error("비밀번호 확인이 일치하지 않습니다.")
                else:
                    # 3. 백엔드 회원가입 API 호출
                    success, msg = api_client.signup_api(new_name, new_email, new_pw)
                    if success:
                        st.success(msg)
                        time.sleep(1) # 성공 메시지를 보여주기 위해 잠시 대기
                        # 가입 성공 후 로그인 페이지로 자동 전환
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        # 이미 존재하는 이메일 등 백엔드에서 온 에러 메시지 표시
                        st.error(msg)
                        
        # 4. 이전 화면(로그인)으로 돌아가기 버튼
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"
            st.rerun()