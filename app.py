import os
import sqlite3
import hashlib
import asyncio
from typing import Optional
from dotenv import load_dotenv

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

load_dotenv()

SYS_BOT = "JobPocket"

# ==========================================
# 1. 데이터 레이어 (대화 기록 DB)
# ==========================================
@cl.data_layer  
def setup_data_layer():
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///local_chat_history.db")

# ==========================================
# 2. 사용자 인증 (SQLite 연동)
# ==========================================
@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    # SQLite 연결 (init_user_db.py로 생성한 DB)
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT password, role FROM users WHERE username = ?', (username, ))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password, role = result
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if hashed_password == stored_password:
            return cl.User(
                identifier=username, 
                metadata={"role": role, "provider": "credentials"}
            )
    return None

# ==========================================
# 3. 모델 선택 토글
# ==========================================
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

# ==========================================
# 4. 채팅 시작 로직
# ==========================================
@cl.on_chat_start
async def on_chat_start():
    # 🌟 핵심 방어 로직: 이미 초기화된 세션이면 여기서 함수를 종료(return)합니다.
    if cl.user_session.get("is_initialized"):
        return 
        
    # 초기화가 안 된 상태라면 플래그를 True로 켭니다.
    cl.user_session.set("is_initialized", True)

    # 로그인한 사용자 정보 가져오기
    app_user = cl.user_session.get("user")
    
    # 세션 상태 초기화
    chat_profile = cl.user_session.get("chat_profile")
    cl.user_session.set("model", chat_profile)
    cl.user_session.set("step", 1)
    cl.user_session.set("draft_history", [])

    # 환영 메시지
    welcome_message = f"""
## 🫧 JobPocket ({chat_profile})
반갑습니다, **{app_user.identifier}**님!

지원자 상세 정보를 입력해주세요. 
저는 안내 및 이력서 첨삭을 도와드릴 시스템입니다.
    """
    
    await cl.Message(content=welcome_message, author=SYS_BOT).send()

# ==========================================
# 5. 메시지 처리 로직 (UI 시나리오)
# ==========================================
@cl.on_message
async def on_message(message: cl.Message):
    step = cl.user_session.get("step")
    
    if step == 1:
        draft_history = cl.user_session.get("draft_history")
        draft_history.append({"role": "user", "content": message.content})
        
        draft_msg = cl.Message(content="", author=SYS_BOT)
        await draft_msg.send()

        try:
            # 💡 향후 여기에 LCEL Chain (ChatOpenAI 등) 로직을 결합하면 됩니다.
            dummy_text = "이것은 가짜 이력서 초안입니다. UI 테스트 중입니다.\n\n- 목표: UI 테스트\n- 결과: 성공적"
            
            for char in dummy_text:
                await draft_msg.stream_token(char)
                await asyncio.sleep(0.01)

            await draft_msg.update()
            draft_history.append({"role": "assistant", "content": draft_msg.content})
            cl.user_session.set("draft_history", draft_history)

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

# ==========================================
# 6. 버튼 액션 콜백
# ==========================================
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