"""
[파일명: frontend/views/resume_view.py]
역할: 사용자의 기초 스펙(인적사항, 학력, 경력 등)을 입력하고 수정하는 '마이페이지' 기능을 담당합니다.
주요 기능:
1. 백엔드에서 기존 저장된 사용자의 스펙 데이터를 불러와 화면에 자동 매칭
2. 탭(Tabs) UI를 활용하여 방대한 입력 정보를 카테고리별로 분리
3. 입력된 정보를 JSON 구조로 가공하여 백엔드 DB에 업데이트
4. 사용자가 '팩트'를 입력하면, 나중에 AI가 이를 바탕으로 자소서를 생성하는 기반 데이터가 됩니다.
"""

import streamlit as st
import json
import time
from utils import api_client
from utils.ui_components import display_header

# ---------------------------------------------------------
# [마이페이지 메인 뷰 함수]
# ---------------------------------------------------------
def mypage_view():
    """
    사용자의 스펙 보관함 화면을 렌더링하고 데이터 저장 로직을 관리합니다.
    - 입력: 없음 (st.session_state의 유저 정보를 활용)
    - 반환: 없음 (UI 렌더링 및 API 통신)
    """
    # 1. 상단 헤더 및 서비스 가이드 표시
    display_header("내 스펙 보관함")
    st.caption("면접관에게 어필할 객관적인 '팩트'만 입력해 주세요. 부족한 스토리는 AI가 대화로 끌어내 줍니다.")
    
    # ---------------------------------------------------------
    # [데이터 로드 섹션]
    # ---------------------------------------------------------
    # 로그인 시 저장된 세션 상태에서 이메일을 추출합니다 (index 2: 이메일 위치)
    user_email = st.session_state.user_info[2]
    
    # 백엔드 API를 통해 기존에 저장된 resume 데이터를 가져옵니다 (문자열 형태)
    resume_str = api_client.get_user_resume_api(user_email)
    
    # 가져온 문자열(JSON)을 파이썬 딕셔너리로 변환합니다. 데이터가 없으면 빈 딕셔너리로 초기화합니다.
    try: 
        data = json.loads(resume_str) if resume_str else {}
    except Exception: 
        data = {}

    # 각 섹션별로 데이터를 분리하여 변수에 할당 (화면의 value 값으로 사용됨)
    personal = data.get("personal", {})
    edu = data.get("education", {})
    add = data.get("additional", {})

    # ---------------------------------------------------------
    # [UI 입력 폼 섹션]
    # ---------------------------------------------------------
    # 💡 Tip: st.form을 사용하면 내부의 값이 바뀔 때마다 리런(Rerun)되지 않고, 
    # 오직 최하단의 제출 버튼을 눌렀을 때만 데이터가 한꺼번에 전송됩니다.
    with st.form("resume_form"):
        # 정보를 3개의 탭으로 깔끔하게 나눕니다.
        tab1, tab2, tab3 = st.tabs(["👤 인적사항", "🎓 학력", "🏆 경력/스펙"])

        # [Tab 1: 인적사항 영역]
        with tab1:
            col1, col2 = st.columns(2)
            with col1: 
                eng_name = st.text_input("영문 이름", value=personal.get("eng_name", ""))
            with col2:
                gender_opts = ["선택안함", "남성", "여성"]
                curr_gender = personal.get("gender", "선택안함")
                # 기존 데이터가 옵션 중 몇 번째 인덱스인지 찾아 기본값으로 설정합니다.
                gender_idx = gender_opts.index(curr_gender) if curr_gender in gender_opts else 0
                gender = st.selectbox("성별", gender_opts, index=gender_idx)

        # [Tab 2: 학력 정보 영역]
        with tab2:
            school = st.text_input("최종 학력 (학교명)", value=edu.get("school", ""))
            major = st.text_input("전공", value=edu.get("major", ""))

        # [Tab 3: 상세 스펙 영역]
        with tab3:
            # st.text_area는 긴 문장을 입력받을 때 적합합니다.
            exp = st.text_area("직무 관련 경험 (인턴/알바/실무/프로젝트)", value=add.get("internship", ""), height=250)
            awards = st.text_area("수상 내역 및 대외활동", value=add.get("awards", ""), height=150)
            tech = st.text_input("기술 스택 / 자격증 (쉼표로 구분)", value=add.get("tech_stack", ""))

        # ---------------------------------------------------------
        # [데이터 저장 처리 섹션]
        # ---------------------------------------------------------
        if st.form_submit_button("💾 내 스펙 저장하기", type="primary"):
            # 1. 입력된 모든 데이터를 백엔드 DB 구조에 맞게 딕셔너리로 재구성합니다.
            new_resume = {
                "personal": {"eng_name": eng_name, "gender": gender},
                "education": {"school": school, "major": major},
                "additional": {"internship": exp, "awards": awards, "tech_stack": tech},
            }
            
            # 2. 백엔드 API 호출을 통해 업데이트를 요청합니다.
            if api_client.update_resume_data_api(user_email, new_resume):
                st.success("✅ 스펙이 성공적으로 저장되었습니다!")
                # 사용자에게 성공 메시지를 보여주기 위해 1초간 대기합니다.
                time.sleep(1)
                
                # 💡 Tip: 저장이 완료된 후 st.rerun()을 호출하면 최신화된 데이터를 
                # 다시 서버에서 읽어와 화면을 새로 그려줍니다.
                st.rerun()