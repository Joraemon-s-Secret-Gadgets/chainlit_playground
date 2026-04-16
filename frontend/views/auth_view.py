# ~/frontend/views/auth_view.py
import streamlit as st
import time
import random
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("회원가입", use_container_width=True):
                st.session_state.page = "signup"; st.rerun()
        with col2:
            if st.button("비밀번호 찾기", use_container_width=True):
                st.session_state.page = "find_password"; st.rerun()

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
                        st.session_state.page = "login"; st.rerun()
                    else:
                        st.error(msg)
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"; st.rerun()

def find_password_view():
    display_header("비밀번호 재설정")
    _, col_main, _ = st.columns([1, 2, 1])
    
    with col_main:
        if st.session_state.reset_code is None:
            with st.form("find_pw_form"):
                email = st.text_input("가입하신 이메일 주소")
                if st.form_submit_button("인증번호 발송", use_container_width=True):
                    code = str(random.randint(100000, 999999))
                    st.session_state.reset_code = code
                    st.session_state.reset_email = email
                    st.success(f"테스트용 알림: [ {code} ] 인증번호가 발송되었습니다.")
        else:
            st.info(f"{st.session_state.reset_email}로 발송된 인증번호 6자리를 입력해주세요.")
            with st.form("verify_code_form"):
                code_input = st.text_input("인증번호 6자리")
                if st.form_submit_button("인증 확인", use_container_width=True):
                    if code_input == st.session_state.reset_code:
                        st.session_state.code_verified = True
                        st.session_state.page = "reset_password"; st.rerun()
                    else:
                        st.error("인증번호가 일치하지 않습니다.")
            if st.button("← 이메일 다시 입력하기", use_container_width=True):
                st.session_state.reset_code = None; st.session_state.reset_email = None; st.rerun()
        
        st.write("")
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.reset_code = None; st.session_state.page = "login"; st.rerun()

def reset_password_view():
    if not st.session_state.get("code_verified"):
        st.error("비정상적인 접근입니다. 이메일 인증을 다시 진행해 주세요.")
        st.session_state.page = "login"; st.rerun()

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
                    if api_client.update_password_api(st.session_state.reset_email, new_pw):
                        st.success("비밀번호가 성공적으로 변경되었습니다!")
                        time.sleep(1.5)
                        st.session_state.reset_email = None; st.session_state.reset_code = None
                        st.session_state.code_verified = False; st.session_state.page = "login"; st.rerun()
                    else:
                        st.error("처리 중 오류가 발생했습니다.")