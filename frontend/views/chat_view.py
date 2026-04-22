"""
[파일명: chat_view.py / chat_logic]
역할: JobPocket의 핵심 서비스인 'AI 자소서 채팅 인터뷰' 화면을 구성하고 관리합니다.
주요 기능:
1. AI 응답 데이터(초안, 평가 결과)를 정규표현식으로 파싱하여 UI에 최적화된 형태로 변환
2. 4단계(의도파악 -> 초안생성 -> 문장정제 -> 분량조절) AI 생성 프로세스 시각화
3. 보완 포인트 자동 생성 및 즉각적인 수정 요청 기능 제공
4. 좋아요/싫어요 피드백 수집 및 세션 상태(Session State) 기반의 UI 라우팅
"""

import re
import time
import streamlit as st
from utils import api_client

# 채팅창에 표시될 아바타 설정
AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"

# ---------------------------------------------------------
# [데이터 파싱 및 추출 헬퍼 함수]
# AI가 보낸 원문에서 특정 섹션(라벨, 본문, 평가)만 골라내는 역할
# ---------------------------------------------------------

def get_result_label(content: str) -> str:
    """
    메시지 상단의 [자소서 초안] 또는 [n차 수정안] 라벨을 추출합니다.
    - 파라미터: content (AI 응답 전체 텍스트)
    - 반환값: 라벨 문자열 (예: "자소서 초안")
    """
    match = re.search(r"^\[(.+?)\]", content.strip())
    return match.group(1) if match else ""


def get_last_assistant_result() -> str:
    """
    채팅 내역을 역순으로 뒤져 AI가 마지막으로 생성했던 자소서 결과물을 찾습니다.
    - 반환값: 마지막 자소서 내용 (없으면 빈 문자열)
    - UI 역할: 사용자가 '수정' 요청을 했을 때, 어떤 내용을 수정할지 기준점을 잡기 위해 사용합니다.
    """
    for msg in reversed(st.session_state.messages):
        if msg["role"] != "assistant":
            continue
        label = get_result_label(msg["content"])
        # 단순 인사가 아닌 '초안'이나 '수정안'인 경우만 유효한 결과로 간주합니다.
        if label == "자소서 초안" or label.endswith("수정안"):
            return msg["content"]
    return ""


def extract_resume_text(content: str) -> str:
    """
    AI 응답에서 평가 섹션을 제외한 '순수 자소서 본문'만 추출합니다.
    - 반환값: 자소서 본문 텍스트
    - UI 역할: '복사하기' 탭에 들어갈 내용이나 다음 수정의 입력값으로 사용합니다.
    """
    try:
        # 1. 라벨 제거
        title_match = re.search(r"^\[(.+?)\]\s*", content.strip())
        if not title_match:
            return content.strip()

        remaining = content.strip()[title_match.end():].lstrip()

        # 2. 수정안일 경우 포함되는 '반영 사항' 설명 부분 건너뛰기
        if remaining.startswith("반영 사항:"):
            lines = remaining.splitlines()
            remaining = "\n".join(lines[1:]).lstrip()

        # 3. 뒤에 붙는 [평가 및 코멘트] 섹션 잘라내기
        split_token = "[평가 및 코멘트]"
        if split_token in remaining:
            return remaining.split(split_token)[0].strip()

        return remaining.strip()
    except Exception:
        return content.strip()


def extract_evaluation_text(content: str) -> str:
    """
    AI 응답에서 [평가 및 코멘트] 이후의 내용만 추출합니다.
    """
    split_token = "[평가 및 코멘트]"
    if split_token not in content:
        return ""
    return content.split(split_token, 1)[1].strip()


def parse_evaluation_for_display(evaluation_text: str) -> dict:
    """
    평가 텍스트를 구조화된 딕셔너리로 변환합니다. (평가결과, 이유, 보완포인트 리스트)
    - UI 역할: '평가 카드' UI를 렌더링하기 위한 데이터 정제 과정입니다.
    """
    result = {"rating": "", "reason": "", "points": []}
    if not evaluation_text:
        return result

    lines = [line.strip() for line in evaluation_text.splitlines() if line.strip()]
    point_mode = False

    for line in lines:
        if line.startswith("평가 결과:"):
            result["rating"] = line.replace("평가 결과:", "").strip()
        elif line.startswith("이유:"):
            result["reason"] = line.replace("이유:", "").strip()
        elif line.startswith("보완 포인트"):
            point_mode = True
        elif point_mode and (line.startswith("-") or line.startswith("•")):
            result["points"].append(line.lstrip("-•").strip())

    return result


# ---------------------------------------------------------
# [자동 수정 요청(Quick Action) 맵핑]
# 사용자가 보완 포인트를 클릭했을 때 AI에게 전달할 프롬프트 생성
# ---------------------------------------------------------

def point_to_revision_prompt(point: str) -> str:
    """
    AI가 제시한 '보완 포인트' 문장을 구체적인 '수정 명령 프롬프트'로 변환합니다.
    - UI 역할: 사용자가 직접 타이핑하지 않아도 버튼 하나로 수정이 가능하게 돕습니다.
    """
    point = point.strip()

    # 주요 키워드에 따른 맞춤형 프롬프트 생성 로직
    if "첫 문장" in point:
        return "이 결과의 첫 문장이 더 선명하고 구체적으로 드러나도록 수정해줘."
    if "마지막 문단" in point:
        return "이 결과의 마지막 문단이 더 자연스럽고 현실적인 마무리가 되도록 수정해줘."
    if "지원동기" in point or "지원 이유" in point:
        return "이 결과에서 지원동기가 더 또렷하게 드러나도록 수정해줘."
    if "갈등" in point and ("방식" in point or "해결" in point):
        return "이 결과에서 갈등이 생긴 이유와 그것을 어떤 방식으로 조율하고 해결했는지가 더 분명히 드러나도록 수정해줘."
    if "경험" in point and "연결" in point:
        return "이 결과에서 내 경험과 지원 직무의 연결이 더 분명하게 드러나도록 수정해줘."
    if "직무" in point:
        return "이 결과가 지원 직무와 더 잘 맞아 보이도록 수정해줘."
    if "구체" in point:
        return "이 결과를 조금 더 구체적으로 보완해줘."
    if "담백" in point or "과장" in point:
        return "이 결과를 더 담백하고 과장 없는 문장으로 다듬어줘."
    if "분량" in point or "글자 수" in point or "700자" in point:
        return "이 결과를 글자 수 조건에 더 잘 맞도록 조정해줘."

    return f"다음 보완 포인트를 반영해서 수정해줘: {point}"


def build_change_summary_for_quick_action(prompt: str) -> str:
    """
    수정안 생성 시 상단에 표시될 '변경 요약' 문구를 생성합니다.
    """
    if "첫 문장" in prompt:
        return "첫 문장이 더 선명하게 보이도록 수정했습니다."
    if "사례" in prompt or "연결" in prompt:
        return "경험과 직무의 연결이 더 드러나도록 수정했습니다."
    if "더 담백하게" in prompt:
        return "문장을 조금 더 담백한 톤으로 다듬었습니다."
    if "700자" in prompt:
        return "요청한 글자 수에 맞춰 분량을 조정했습니다."
    if "지원동기" in prompt:
        return "지원 이유가 더 또렷하게 드러나도록 수정했습니다."
    if "마지막 문단" in prompt:
        return "마지막 문단을 중심으로 수정했습니다."
    if "구체적" in prompt or "구체" in prompt:
        return "핵심 문장을 조금 더 구체적으로 보완했습니다."
    if "직무" in prompt:
        return "지원 직무와의 연결이 더 분명하게 드러나도록 수정했습니다."
    return "요청하신 방향을 반영해 수정했습니다."


# ---------------------------------------------------------
# [UI 컴포넌트 렌더링 섹션]
# ---------------------------------------------------------

def render_evaluation_card(content: str, message_index: int):
    """
    AI가 준 평가 결과를 예쁜 카드 형태로 렌더링하고, 수정 버튼을 생성합니다.
    - UI 역할: 사용자가 자소서의 품질을 확인하고 부족한 부분을 바로 고칠 수 있게 유도합니다.
    """
    evaluation_text = extract_evaluation_text(content)
    parsed = parse_evaluation_for_display(evaluation_text)

    if not evaluation_text:
        return []

    rating = parsed.get("rating", "")
    reason = parsed.get("reason", "")
    points = parsed.get("points", [])

    st.markdown("### 평가 및 코멘트")

    if rating:
        st.markdown(f"**평가 결과:** {rating}")
    if reason:
        st.markdown(f"**이유:** {reason}")

    # 보완 포인트가 있다면 리스트와 '적용' 버튼을 나란히 배치
    if points:
        st.markdown("**보완 포인트**")
        for idx, point in enumerate(points):
            col_text, col_btn = st.columns([5, 1.2]) # 텍스트와 버튼 비율 조정
            with col_text:
                st.markdown(f"- {point}")
            with col_btn:
                prompt_text = point_to_revision_prompt(point)
                # 💡 Tip: Streamlit에서 반복문 안의 버튼은 고유한 'key'값이 필수입니다.
                if st.button(
                    "적용",
                    key=f"eval_btn_{message_index}_{idx}",
                    use_container_width=True,
                ):
                    # 버튼 클릭 시 즉시 실행하지 않고 '보류 중인 프롬프트'에 저장 후 리런하여 상단에서 처리합니다.
                    st.session_state.pending_prompt = prompt_text
                    st.rerun()

    return points


def render_assistant_message(content: str, message_index: int):
    """
    AI의 응답 메시지를 종류별(초안, 수정안, 일반 대화)로 구분하여 화면에 그립니다.
    - UI 역할: 복사 버튼(st.code), 구분선, 평가 카드, 좋아요/싫어요 버튼 등을 포함합니다.
    """
    label = get_result_label(content)
    is_result_message = label == "자소서 초안" or label.endswith("수정안")

    if is_result_message:
        title_line = f"[{label}]"
        body_text = extract_resume_text(content)

        # 1. 자소서 결과물 렌더링
        st.markdown(title_line)
        st.write("")
        st.markdown(body_text)

        # 2. 복사 편의 기능 (st.expander + st.code 조합)
        if label.endswith("수정안"):
            st.caption("📋 최신 수정본입니다. 아래 탭을 열어 본문만 쉽게 복사하세요.")
        else:
            st.caption("📋 아래 탭을 열어 자소서 본문만 쉽게 복사하세요.")

        with st.expander("📄 복사하기"):
            st.code(body_text, language="plaintext")

        st.divider()

        # 3. 하단 평가 카드 (보완 버튼 포함)
        render_evaluation_card(content, message_index)

        # 4. 만족도 피드백 버튼 (좋아요/싫어요)
        st.write("")
        feedback_title = "이 수정안이 마음에 드시나요?" if label.endswith("수정안") else "이 초안이 마음에 드시나요?"
        st.markdown(f"<div class='center-helper'>{feedback_title}</div>", unsafe_allow_html=True)

        feedback_key = f"feedback_{message_index}"
        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = None

        center_cols = st.columns([4, 1, 1, 4]) # 중앙 정렬을 위한 컬럼 배치

        if st.session_state[feedback_key] is None:
            with center_cols[1]:
                if st.button("👍", key=f"good_{message_index}", use_container_width=True):
                    st.session_state[feedback_key] = "good"
                    st.rerun()
            with center_cols[2]:
                if st.button("👎", key=f"bad_{message_index}", use_container_width=True):
                    st.session_state[feedback_key] = "bad"
                    st.rerun()
        else:
            # 평가가 완료된 경우 결과 표시
            if st.session_state[feedback_key] == "good":
                st.markdown("<div class='center-helper'>✓ 평가 완료: 👍</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='center-helper'>✓ 평가 완료: 👎</div>", unsafe_allow_html=True)
                st.info("어떤 부분이 아쉬웠는지 말씀해 주세요. 예: 첫 문장 구체화, 더 담백하게, 마지막 문단 수정")
    else:
        # 결과물이 아닌 일반 대화(인사말 등)는 마크다운으로 출력
        st.markdown(content)


def render_progress_card():
    """
    AI가 작업 중일 때 현재 단계를 시각적으로 보여주는 커스텀 카드입니다.
    """
    st.markdown("""
        <div class="progress-card">
            <b>진행 단계</b>
            1. 문항과 요청 정보 정리<br>
            2. 로컬 모델로 초안 생성 또는 기존 결과 분석<br>
            3. API 모델로 문장 정리 또는 수정 반영<br>
            4. 글자 수와 전체 흐름 최종 점검
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# [핵심 로직: AI 생성 프로세스]
# ---------------------------------------------------------

def is_revision_request(prompt: str) -> bool:
    """
    사용자의 입력이 새로운 자소서 요청인지, 기존 결과의 '수정' 요청인지 판별합니다.
    """
    revision_keywords = [
        "수정", "고쳐", "다듬", "줄여", "늘려", "바꿔", "다시 써",
        "마지막 문단", "첫 문장", "담백", "구체적", "지원동기",
        "톤", "문장", "700자", "500자", "1000자", "사례", "연결", "직무",
    ]
    return any(keyword in prompt for keyword in revision_keywords)


def generate_response_with_progress(prompt: str, user_info: tuple, selected_model: str):
    """
    4단계 멀티스텝 API 호출을 순차적으로 수행하고 화면에 진행 상황을 실시간으로 업데이트합니다.
    - UI 역할: st.empty()를 활용해 메시지를 계속 갈아끼우며 AI의 '사고 과정'을 보여줍니다.
    """
    status_box = st.empty() # 진행 상태 텍스트 영역
    step_box = st.empty()   # 진행 단계(n/4) 영역
    render_progress_card()  # 고정 안내판 표시

    # 직전 결과가 있는지 확인 (수정 모드 대비)
    last_result_full = get_last_assistant_result()
    last_result_body = extract_resume_text(last_result_full) if last_result_full else ""

    # --- [CASE 1: 기존 자소서 수정 모드] ---
    if last_result_body and is_revision_request(prompt):
        status_box.info("직전 결과를 바탕으로 수정 요청을 반영하고 있습니다.")
        step_box.caption("1/4 직전 결과와 수정 요청을 분석하고 있습니다.")
        time.sleep(0.15) # 사용자 경험을 위한 미세한 대기 시간

        status_box.info("요청한 방향에 맞춰 본문을 수정하고 있습니다.")
        step_box.caption("2/4 기존 결과를 기반으로 수정 중입니다.")
        # 백엔드 API 호출: 수정 로직 실행
        revised = api_client.revise_existing_draft_api(last_result_body, prompt, selected_model)

        status_box.info("수정된 문장을 더 자연스럽게 정리하고 있습니다.")
        step_box.caption("3/4 문장 흐름과 표현을 정리하고 있습니다.")
        refined = api_client.refine_with_api_api(revised, prompt, selected_model)

        status_box.info("최종 길이와 전체 흐름을 점검하고 있습니다.")
        step_box.caption("4/4 글자 수와 전체 흐름을 최종 점검하고 있습니다.")
        adjusted = api_client.fit_length_api(refined, prompt, selected_model)

        # 수정 차수 업데이트
        st.session_state.current_result_version += 1
        result_label = f"{st.session_state.current_result_version}차 수정안"
        change_summary = build_change_summary_for_quick_action(prompt)

        # 최종 응답 조립 (가이드 멘트 등 포함)
        final_response = api_client.build_final_response_api(
            adjusted, prompt, selected_model, result_label=result_label, change_summary=change_summary
        )
        status_box.success("수정안이 준비되었습니다.")
        step_box.empty()
        return final_response

    # --- [CASE 2: 신규 초안 생성 모드] ---
    status_box.info("입력 내용을 확인하고 있습니다.")
    step_box.caption("1/4 문항과 요청 정보를 정리하고 있습니다.")
    parsed = api_client.parse_request_api(prompt, selected_model)
    time.sleep(0.15)

    company_name = parsed.get("company") or "미기재"
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

    st.session_state.current_result_version = 0
    final_response = api_client.build_final_response_api(
        adjusted, prompt, selected_model, result_label="자소서 초안", change_summary=None
    )
    status_box.success("초안 생성이 완료되었습니다.")
    step_box.empty()
    return final_response


# ---------------------------------------------------------
# [메인 제어 로직]
# ---------------------------------------------------------

def process_prompt(prompt: str, user_email: str):
    """
    사용자 입력을 받아 처리하고 AI 응답을 생성한 뒤 DB에 저장하는 메인 루프입니다.
    """
    # 1. 사용자 메시지 세션 및 DB 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    api_client.save_chat_message_api(user_email, "user", prompt)

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # 2. 어시스턴트 메시지 생성 (진행 단계 시각화 포함)
    with st.chat_message("assistant", avatar=AI_AVATAR):
        result_box = st.empty()
        try:
            response = generate_response_with_progress(
                prompt=prompt,
                user_info=st.session_state.user_info,
                selected_model=st.session_state.selected_model,
            )
            result_box.markdown(response)
            # 3. AI 응답 세션 및 DB 저장
            st.session_state.messages.append({"role": "assistant", "content": response})
            api_client.save_chat_message_api(user_email, "assistant", response)

        except Exception as e:
            error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            result_box.error(error_message)
            st.info("잠시 후 다시 시도해 주세요.")
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            api_client.save_chat_message_api(user_email, "assistant", error_message)

    # 화면을 새로고침하여 바뀐 상태(피드백 버튼 등)를 적용합니다.
    st.rerun()


def get_chat_input_placeholder() -> str:
    """
    현재 대화 단계에 따라 채팅창 가이드 문구(Placeholder)를 동적으로 변경합니다.
    """
    last_result = get_last_assistant_result()
    if not last_result:
        return "지원 회사/직무/문항을 입력해 주세요!"
    label = get_result_label(last_result)
    if label == "자소서 초안":
        return "생성된 초안의 수정 방향을 말씀해 주세요!"
    if label.endswith("수정안"):
        return "추가 수정 방향이나 문장 변경 요청을 말씀해 주세요!"
    return "지원 회사/직무/문항을 입력하거나, 수정 방향을 말씀해 주세요!"


def chat_view():
    """
    [진입점] 전체 채팅 뷰 라우팅을 담당합니다. (환영 창 vs 실제 채팅창)
    """
    user_email = st.session_state.user_info[2]

    # 대화 기록이 없으면 환영 창(Welcome Box)을 보여줍니다.
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = not bool(st.session_state.messages)

    if st.session_state.show_welcome:
        # --- 환영 창 UI 섹션 ---
        user_name = st.session_state.user_info[0]
        st.markdown(f"""
            <div style="background-color: #F0F8FF; padding: 2.5rem; border-radius: 15px; text-align: center; border: 2px solid #3B82F6; margin-top: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #3B82F6; margin-bottom: 1rem; font-weight: 800;">반갑습니다, {user_name}님! 👋</h2>
                <p style="font-size: 1.2rem; color: #333; margin-bottom: 1.5rem;"><strong>JobPocket</strong>이 여러분의 합격 여정을 함께합니다.</p>
                <div style="text-align: left; display: inline-block; margin-bottom: 2rem; color: #555; font-size: 1.05rem; line-height: 2;">
                    🚀 <b>내 스펙 기반:</b> 입력한 경험을 바탕으로 팩트 중심 초안 생성<br>
                    🤖 <b>듀얼 모델 지원:</b> GPT-4o-mini와 GPT-OSS-120B 선택 가능<br>
                    📝 <b>대화형 수정:</b> 초안 생성 후 문장별 수정, 톤 변경, 길이 조정 가능
                </div>
            </div>
        """, unsafe_allow_html=True)

        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("🚀 대화 시작하기", use_container_width=True, type="primary"):
                st.session_state.show_welcome = False
                # 시작 버튼 클릭 시 AI의 첫 인사말 생성
                if not st.session_state.messages:
                    greeting = (
                        "안녕하세요! 지원하시려는 **회사와 직무**, 그리고 **자기소개서 문항**을 편하게 남겨주세요. "
                        "초안이 생성된 뒤에는 문장 수정, 톤 변경, 글자 수 조정도 이어서 도와드릴게요. 😊"
                    )
                    st.session_state.messages.append({"role": "assistant", "content": greeting})
                    api_client.save_chat_message_api(user_email, "assistant", greeting)
                st.rerun()
        return

    # --- 실제 채팅 메시지 렌더링 섹션 ---
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AI_AVATAR):
            if message["role"] == "assistant":
                render_assistant_message(message["content"], i)
            else:
                st.markdown(message["content"])

    # 💡 Tip: 평가 카드에서 '적용' 버튼을 눌러 예약된 프롬프트가 있다면 여기서 처리합니다.
    if st.session_state.pending_prompt:
        pending = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        process_prompt(pending, user_email)
        return

    # 채팅 입력창
    if prompt := st.chat_input(get_chat_input_placeholder()):
        process_prompt(prompt, user_email)