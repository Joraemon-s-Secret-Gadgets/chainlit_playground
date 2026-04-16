# ~/frontend/views/chat_view.py
import streamlit as st
import time
from utils import api_client
from utils.ui_components import display_header

AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"

def render_assistant_message(content: str, message_index: int):
    if "[자소서 초안]" in content:
        st.markdown(content)
        try:
            resume_text = content.split("[자소서 초안]")[1].split("[자소서 초안 평가]")[0].strip()
            st.divider()
            st.caption("📋 아래 박스 우측 상단의 아이콘을 눌러 자소서 본문만 쉽게 복사하세요.")
            st.code(resume_text, language="plaintext")
        except IndexError: pass

        st.write("이 대답이 마음에 드시나요?")
        col1, col2, _ = st.columns([0.4, 0.4, 9.2])
        feedback_key = f"feedback_{message_index}"

        if feedback_key not in st.session_state: st.session_state[feedback_key] = None

        if st.session_state[feedback_key] is None:
            with col1:
                if st.button("👍", key=f"good_{message_index}"):
                    st.session_state[feedback_key] = "good"; st.rerun()
            with col2:
                if st.button("👎", key=f"bad_{message_index}"):
                    st.session_state[feedback_key] = "bad"; st.rerun()
        else:
            feedback_emoji = "👍" if st.session_state[feedback_key] == "good" else "👎"
            st.caption(f"✓ AI 초안 평가 완료: **{feedback_emoji}**")
    else:
        st.markdown(content)

def render_progress_card():
    st.markdown("""
        <div class="progress-card">
            <b>진행 단계</b>
            1. 문항과 요청 정보 정리<br>
            2. 로컬 모델로 초안 생성<br>
            3. API 모델로 문장 정리<br>
            4. 글자 수와 전체 흐름 최종 점검
        </div>
    """, unsafe_allow_html=True)

def generate_response_with_progress(prompt: str, user_info: tuple, selected_model: str):
    status_box = st.empty()
    step_box = st.empty()
    render_progress_card()

    status_box.info("입력 내용을 확인하고 있습니다.")
    step_box.caption("1/4 문항과 요청 정보를 정리하고 있습니다.")
    parsed = api_client.parse_request_api(prompt, selected_model)
    time.sleep(0.15)

    company_name = parsed.get("company_display") or parsed.get("company") or "미기재"
    question_name = parsed.get("question") or "자기소개서 문항"
    status_box.info(f"회사/문항 정보를 정리했습니다. ({company_name} / {question_name})")
    step_box.caption("2/4 로컬 모델이 초안을 작성하고 있습니다.")
    local_draft = api_client.generate_local_draft_api(prompt, user_info, selected_model)

    status_box.info("로컬 초안이 생성되었습니다. 문장 흐름을 다듬고 있습니다.")
    step_box.caption("3/4 API 모델이 문장을 다듬고 있습니다.")
    refined = api_client.refine_with_api_api(local_draft, prompt, selected_model)

    status_box.info("최종 문장 길이와 전체 흐름을 점검하고 있습니다.")
    step_box.caption("4/4 글자 수와 전체 흐름을 최종 점검하고 있습니다.")
    adjusted = api_client.fit_length_api(refined, prompt, selected_model)

    final_response = api_client.build_final_response_api(adjusted, prompt, selected_model)
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
        st.markdown(f"""
            <div style="background-color: #F0F8FF; padding: 2.5rem; border-radius: 15px; text-align: center; border: 2px solid #3B82F6; margin-top: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #3B82F6; margin-bottom: 1rem; font-weight: 800;">반갑습니다, {user_name}님! 👋</h2>
                <p style="font-size: 1.2rem; color: #333; margin-bottom: 1.5rem;"><strong>JobPocket</strong>이 여러분의 합격 여정을 함께합니다.</p>
                <div style="text-align: left; display: inline-block; margin-bottom: 2rem; color: #555; font-size: 1.05rem; line-height: 2;">
                    🚀 <b>내 스펙 기반:</b> 입력한 경험을 바탕으로 팩트 중심 초안 생성<br>
                    🤖 <b>듀얼 모델 지원:</b> GPT-4o-mini와 GPT-OSS-120B 선택 가능<br>
                    📝 <b>단계형 생성 안내:</b> 초안 생성부터 최종 정리까지 진행 상태 확인 가능
                </div>
            </div>
        """, unsafe_allow_html=True)

        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("🚀 대화 시작하기", use_container_width=True, type="primary"):
                st.session_state.show_welcome = False
                if not st.session_state.messages:
                    greeting = """안녕하세요! 👋
지원하시려는 **회사와 직무**, 그리고 **자기소개서 문항**을 편하게 남겨주세요. 

보관함에 등록해 두신 스펙을 바탕으로 **자소서 초안**을 작성해 드리겠습니다. 😊"""
                    st.session_state.messages.append({"role": "assistant", "content": greeting})
                    api_client.save_chat_message_api(user_email, "assistant", greeting)
                st.rerun()
        return

    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AI_AVATAR):
            if message["role"] == "assistant":
                render_assistant_message(message["content"], i)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("지원하실 회사와 직무, 자기소개서의 문항(ex.지원 동기, 포부, 회사 비전, 갈등 해결 등)을 작성해주세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        api_client.save_chat_message_api(user_email, "user", prompt)

        with st.chat_message("user", avatar=USER_AVATAR): st.markdown(prompt)

        with st.chat_message("assistant", avatar=AI_AVATAR):
            result_box = st.empty()
            try:
                response = generate_response_with_progress(
                    prompt=prompt, user_info=st.session_state.user_info, selected_model=st.session_state.selected_model
                )
                result_box.markdown(response)

                if "[자소서 초안]" in response:
                    try:
                        resume_text = response.split("[자소서 초안]")[1].split("[자소서 초안 평가]")[0].strip()
                        st.divider()
                        st.caption("📋 아래 박스 우측 상단의 아이콘을 눌러 자소서 본문만 쉽게 복사하세요.")
                        st.code(resume_text, language="plaintext")
                    except IndexError: pass

                st.session_state.messages.append({"role": "assistant", "content": response})
                api_client.save_chat_message_api(user_email, "assistant", response)

            except Exception as e:
                error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
                result_box.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                api_client.save_chat_message_api(user_email, "assistant", error_message)
        st.rerun()