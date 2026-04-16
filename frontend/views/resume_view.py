# ~/frontend/views/resume_view.py
import streamlit as st
import json
import time
from utils import api_client
from utils.ui_components import display_header

def mypage_view():
    display_header("내 스펙 보관함")
    st.caption("면접관에게 어필할 객관적인 '팩트'만 입력해 주세요. 부족한 스토리는 AI가 대화로 끌어내 줍니다.")
    
    user_email = st.session_state.user_info[2]
    resume_str = api_client.get_user_resume_api(user_email)
    try: data = json.loads(resume_str) if resume_str else {}
    except Exception: data = {}

    personal = data.get("personal", {})
    edu = data.get("education", {})
    add = data.get("additional", {})

    with st.form("resume_form"):
        tab1, tab2, tab3 = st.tabs(["👤 인적사항", "🎓 학력", "🏆 경력/스펙"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1: eng_name = st.text_input("영문 이름", value=personal.get("eng_name", ""))
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
                "additional": {"internship": exp, "awards": awards, "tech_stack": tech},
            }
            if api_client.update_resume_data_api(user_email, new_resume):
                st.success("✅ 스펙이 성공적으로 저장되었습니다!")
                time.sleep(1)
                st.rerun()