import chainlit as cl

async def send_welcome_msg(username, profile):
    """자소서 첨삭 모드 진입 메시지"""
    content = f"## 🫧 JobPocket ({profile})\n반갑습니다, **{username}**님! 자소서 첨삭을 시작합니다. 분석할 내용을 입력해 주세요."
    await cl.Message(content=content, author="JobPocket").send()

async def send_action_buttons():
    """첨삭 초안 생성 후 선택 버튼"""
    await cl.Message(
        content="생성된 초안을 확인해 보세요.",
        author="JobPocket",
        actions=[
            cl.Action(name="finalize", payload={"v": "1"}, label="☑️ 확정"),
            cl.Action(name="edit_more", payload={"v": "0"}, label="🪄 추가 수정")
        ]
    ).send()