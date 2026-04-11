# app.py
import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from database import get_user
from auth import hash_pw
from chat_logic import generate_ai_feedback 

# ==========================================
#  1. 모델 선택 토글 및 채팅 아이콘
# ==========================================
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="gpt-4o-mini",
            markdown_description="빠르고 똑똑한 기본 AI",
            icon="/public/models.png"
        ),
        cl.ChatProfile(
            name="gpt-4o", 
            markdown_description="심도있는 분석이 가능한 고성능 AI",
            icon="/public/models.png"
        )
    ]

# ==========================================
# 2. 데이터 레이어 (과거 대화 기록 저장)
# ==========================================
@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///local_chat_history.db")

# ==========================================
# 3. 로그인 인증 (DB 검증)
# ==========================================
@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    user_info = get_user(username)
    if user_info:
        stored_pw = user_info[1]
        if hash_pw(password) == stored_pw:
            return cl.User(identifier=username, metadata={"role": "user"})
    return None

# ==========================================
# 4. 채팅방 입장 시 환영 인사
# ==========================================
@cl.on_chat_start
async def start():
    if cl.user_session.get("is_initialized"): 
        return
    cl.user_session.set("is_initialized", True)
    
    user = cl.user_session.get("user")
    
    # 현재 선택된 모델의 이름 가져오기
    profile = cl.user_session.get("chat_profile") 
    
    await cl.Message(
        content=f"환영합니다 **{user.identifier}**님! 🎉\n\n현재 **[{profile}]** 모델로 설정되어 있습니다.\n작성해 두신 자소서 초안을 편하게 붙여넣어 주세요. 제가 전문적인 시각으로 첨삭해 드리겠습니다!"
    ).send()

# ==========================================
# 5. 핵심: 유저 메시지 처리 및 AI 연동
# ==========================================
@cl.on_message
async def main(message: cl.Message):
    user = cl.user_session.get("user")
    user_info = get_user(user.identifier) 
    
    await generate_ai_feedback(message.content, user_info)
    
    await cl.Message(
        content="🪄 **수정하고 싶은 부분이 더 있으신가요?**\n(예: '직무 역량을 더 강조해 줘', '분량을 조금 더 줄여줘' 등 편하게 말씀해 주세요!)"
    ).send()