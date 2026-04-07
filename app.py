import chainlit as cl
import asyncio
import os

# ==========================================
# 데이터 레이어 설정
# ==========================================
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

@cl.data_layer  
def setup_data_layer():
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///local_chat_history.db")

# ==========================================
# LLM 클라이언트 설정 (현재 UI 테스트를 위해 주석 처리됨)
# ==========================================
# from openai import AsyncOpenAI
# client = AsyncOpenAI(
#    api_key=os.environ.get("GROQ_API_KEY"),
#    base_url="https://api.groq.com/openai/v1"
# )

SYS_BOT = "안내 봇 (System)"
EXPERT_BOT = "시니어 면접관"

# ==========================================
# 채팅 시작
# ==========================================
@cl.on_chat_start
async def on_chat_start():
    settings = cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="model",
                label="💡 생성 모델 선택",
                values=[
                    "llama3-70b-8192",
                    "llama3-8b-8192",
                    "mixtral-8x7b-32768"
                ],
                initial_index=0,
            )
        ]
    )
    await settings.send()

    cl.user_session.set("model", "llama3-70b-8192")
    cl.user_session.set("step", 1)
    cl.user_session.set("draft_history", [])

    await cl.Message(
        content="""
## 🫧 ReGPT

지원자 상세 정보를 입력해주세요.

### 📝 입력 템플릿
- 목표 기업 및 직무
- 학력 및 배경
- 기술 스택
- 상세 경험
        """,
        author=SYS_BOT
    ).send()

# ==========================================
# 설정 변경
# ==========================================
@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("model", settings["model"])
    await cl.Message(
        content=f"⚙️ 모델 변경됨 → {settings['model']}",
        author=SYS_BOT
    ).send()

# ==========================================
# 메시지 처리
# ==========================================
@cl.on_message
async def on_message(message: cl.Message):
    step = cl.user_session.get("step")
    
    if step == 1:
        draft_history = cl.user_session.get("draft_history")
        draft_history.append({"role": "user", "content": message.content})
        cl.user_session.set("draft_history", draft_history)

        draft_msg = cl.Message(content="", author=SYS_BOT)
        await draft_msg.send()

        try:
            # 실 API 호출 대신 가짜 텍스트 스트리밍 (UI 테스트용)
            dummy_text = "이것은 API 키 없이 출력되는 가짜 이력서 초안입니다. UI가 잘 작동하는지 확인해보세요.\n\n- 목표: UI 테스트\n- 결과: 성공적"
            
            for char in dummy_text:
                await draft_msg.stream_token(char)
                await asyncio.sleep(0.02) # 글자가 타이핑되는 효과

            await draft_msg.update()

            draft_history.append({
                "role": "assistant",
                "content": draft_msg.content
            })
            cl.user_session.set("draft_history", draft_history)
            cl.user_session.set("draft_content", draft_msg.content)

            await cl.Message(
                content="초안 확인 후 선택하세요",
                author=SYS_BOT,
                actions=[
                    cl.Action(name="finalize_draft", value="finalize", label="⭐ 확정"),
                    cl.Action(name="continue_edit", value="continue", label="🔄 수정")
                ]
            ).send()

        except Exception as e:
            await cl.Message(
                content=f"❌ 오류: {str(e)}",
                author=SYS_BOT
            ).send()

    elif step == 2:
        await cl.Message(
            content="이미 평가 완료됨. 새 채팅 사용.",
            author=SYS_BOT
        ).send()

# ==========================================
# 초안 확정
# ==========================================
@cl.action_callback("finalize_draft")
async def on_finalize(action: cl.Action):
    cl.user_session.set("step", 2)

    await cl.Message(content="🔍 분석 시작...", author=SYS_BOT).send()
    expert_msg = cl.Message(content="", author=EXPERT_BOT)
    await expert_msg.send()

    try:
        # 실 API 호출 대신 가짜 텍스트 스트리밍 (UI 테스트용)
        dummy_feedback = "시니어 면접관의 가짜 분석 결과입니다.\n\n👍 강점: UI 구현력이 좋습니다.\n💡 개선점: API 연동 시 실제 키를 넣으세요."
        
        for char in dummy_feedback:
            await expert_msg.stream_token(char)
            await asyncio.sleep(0.02)

        await expert_msg.update()

    except Exception as e:
        await cl.Message(
            content=f"❌ 오류: {str(e)}",
            author=SYS_BOT
        ).send()

# ==========================================
# 수정 계속
# ==========================================
@cl.action_callback("continue_edit")
async def on_continue(action: cl.Action):
    await cl.Message(
        content="수정 내용 입력하세요.",
        author=SYS_BOT
    ).send()

    