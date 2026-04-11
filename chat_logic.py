import chainlit as cl
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser 

# 1. LLM 모델 초기화 (API 키는 .env에서 자동 로드)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

async def generate_ai_feedback(user_message: str, user_profile: tuple):
    """
    유저의 프로필과 메시지를 받아 AI 자소서 첨삭 결과를 스트리밍합니다.
    """
    # 2. DB에서 가져온 유저 프로필 파싱
    # user_profile 구조: (username, password, email, reset_token, edu, exp, awd, role)
    edu = user_profile[4] if user_profile[4] else "정보 없음"
    exp = user_profile[5] if user_profile[5] else "정보 없음"
    awd = user_profile[6] if user_profile[6] else "정보 없음"

    # 3. 프롬프트 엔지니어링 (시스템 프롬프트 설계)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 10년 차 대기업 인사담당자이자 깐깐하지만 친절한 자소서 컨설턴트입니다.
지원자의 기본 스펙을 참고하여, 작성한 자소서 초안을 프로페셔널하게 첨삭해 주세요.

[지원자 기본 스펙]
- 학력: {edu}
- 경력: {exp}
- 수상 및 자격증: {awd}

[답변 작성 지침]
1. 먼저 지원자의 글에서 잘된 점과 보완할 점을 1~2줄로 따뜻하게 피드백해 주세요.
2. 직무 역량과 경험이 돋보이도록 문장을 다듬어 **[전문가 수정본]**을 제시해 주세요.
3. 마크다운 포맷을 사용하여 가독성 좋게 출력해 주세요."""),
        ("user", "다음 자소서 내용을 첨삭해 주세요:\n\n{user_message}")
    ])

    # 4. 랭체인(LangChain) 파이프라인 연결
    chain = prompt | llm | StrOutputParser()

    # 5. 체인릿(Chainlit) UI에 실시간 스트리밍 출력
    msg = cl.Message(content="")
    await msg.send() # 빈 메시지를 먼저 화면에 띄움

    # AI가 단어를 생성할 때마다 화면에 타닥타닥 쏘아줌
    async for chunk in chain.astream({
        "edu": edu, 
        "exp": exp, 
        "awd": awd, 
        "user_message": user_message
    }):
        await msg.stream_token(chunk)

    await msg.update() # 출력 완료 표시
    return True