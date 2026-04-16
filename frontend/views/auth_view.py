import streamlit as st
import time
from utils import api_client
from utils.ui_components import display_header

def login_view():
    display_header("로그인")
    st.write("")
    _, col_main, _ = st.columns([1, 2, 1])

    with col_main:
        with st.form("login_form"):
            email = st.text_input("이메일 주소")
            password = st.text_input("비밀번호", type="password")

            if st.form_submit_button("로그인", use_container_width=True):
                success, user_data_or_error = api_client.login_api(email, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_data_or_error
                    st.session_state.menu = "chat"
                    st.session_state.history_loaded_for = None
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

        # 비밀번호 찾기 버튼을 삭제
        if st.button("회원가입", use_container_width=True):
            st.session_state.page = "signup"
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
                    success, msg = api_client.signup_api(new_name, new_email, new_pw)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)
                        
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"
            st.rerun()