import chainlit as cl
import asyncio
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

# 1. 데이터 레이어 (DB 활성화)

@cl.data_layer  
def setup_data_layer():
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///local_chat_history.db")

# 2. 사용자 인증

@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    return cl.User(identifier=username)

SYS_BOT = "doraemon"

# 3. 모델 선택 토글 (아이콘 경로 수정 완료)

@cl.set_chat_profiles
async def chat_profile():
    model_icon_path = "/public/models.png" 

    return [
        cl.ChatProfile(
            name="llama3-70b-8192",
            markdown_description="고성능 Llama 3 모델",
            icon=model_icon_path  
        ),
        cl.ChatProfile(
            name="llama3-8b-8192",
            markdown_description="경량화 Llama 3 모델",
            icon=model_icon_path  
        ),
        cl.ChatProfile(
            name="mixtral-8x7b-32768",
            markdown_description="Mixtral 모델",
            icon=model_icon_path  
        )
    ]

# 4. 채팅 시작 로직

@cl.on_chat_start
async def on_chat_start():
    # 선택된 프로필 설정
    chat_profile = cl.user_session.get("chat_profile")
    cl.user_session.set("model", chat_profile)
    cl.user_session.set("step", 1)
    cl.user_session.set("draft_history", [])

    # 시작할 때 큰 이미지를 보여주고 싶다 ? 해제
    # welcome_image = cl.Image(path="./public/models.png", name="welcome", display="inline")

    await cl.Message(
        content=f"## 🫧 ReGPT ({chat_profile})\n\n지원자 상세 정보를 입력해주세요. 저는 안내 및 이력서 첨삭을 도와드릴 시스템입니다.",
        author=SYS_BOT,
        # elements=[welcome_image] # 이미지를 크게 띄우고 싶을 때 
    ).send()

# 5. 메시지 처리 로직

@cl.on_message
async def on_message(message: cl.Message):
    step = cl.user_session.get("step")
    
    if step == 1:
        draft_history = cl.user_session.get("draft_history")
        draft_history.append({"role": "user", "content": message.content})
        
        draft_msg = cl.Message(content="", author=SYS_BOT)
        await draft_msg.send()

        try:
            dummy_text = "이것은 가짜 이력서 초안입니다. UI 테스트 중입니다.\n\n- 목표: UI 테스트\n- 결과: 성공적"
            
            for char in dummy_text:
                await draft_msg.stream_token(char)
                await asyncio.sleep(0.01)

            await draft_msg.update()
            draft_history.append({"role": "assistant", "content": draft_msg.content})
            cl.user_session.set("draft_history", draft_history)

            # 액션 버튼 전송
            await cl.Message(
                content="초안 확인 후 선택하세요",
                author=SYS_BOT,
                actions=[
                    cl.Action(name="finalize_draft", payload={"action": "finalize"}, label="☑️ 확정"),
                    cl.Action(name="continue_edit", payload={"action": "continue"}, label="🪄 수정")
                ]
            ).send()

        except Exception as e:
            await cl.Message(content=f"❌ 오류 발생: {str(e)}", author=SYS_BOT).send()

# 6. 버튼 액션 콜백

@cl.action_callback("finalize_draft")
async def on_finalize(action: cl.Action):
    cl.user_session.set("step", 2)
    await cl.Message(content="🔍 분석 및 첨삭 시작...", author=SYS_BOT).send()
    
    expert_msg = cl.Message(content="", author=SYS_BOT)
    await expert_msg.send()

    dummy_feedback = "👍 강점: UI 구현력이 좋습니다.\n💡 개선점: 실제 LLM API 연동을 추가하세요."
    for char in dummy_feedback:
        await expert_msg.stream_token(char)
        await asyncio.sleep(0.01)
    await expert_msg.update()

@cl.action_callback("continue_edit")
async def on_continue(action: cl.Action):
    await cl.Message(content="수정 내용을 입력해 주세요.", author=SYS_BOT).send()