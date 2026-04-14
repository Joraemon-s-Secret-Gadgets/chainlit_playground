# chat_logic.py
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()  
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def generate_ai_feedback_stream(user_message: str, user_profile: tuple):
    resume_str = user_profile[4]
    
    try:
        resume_data = json.loads(resume_str) if resume_str else {}
    except json.JSONDecodeError:
        resume_data = {}

    # 데이터 추출 (학점, 마스터자소서 제외됨)
    personal = resume_data.get("personal", {})
    edu = resume_data.get("education", {})
    add = resume_data.get("additional", {})
    
    gender = personal.get("gender", "선택안함")
    school = edu.get("school", "정보 없음")
    major = edu.get("major", "정보 없음")
    exp = add.get("internship", "정보 없음")
    awards = add.get("awards", "정보 없음")
    tech = add.get("tech_stack", "정보 없음")

    # 🌟 대화형 인터뷰 프롬프트로 전면 수정
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 10년 차 대기업 최고 인사담당자이자 1:1 자소서 전담 멘토입니다.
아래는 지원자의 기본 하드 스펙(Hard Spec)입니다.

[지원자 팩트 체크]
- 인적사항: 성별({gender})
- 학력: {school} {major}
- 직무 경험: {exp}
- 수상 및 스펙: {awards}
- 기술 스택: {tech}

[대화 및 작성 지침 - ⭐️매우 중요⭐️]
1. 사용자가 "OO기업 OO직무 자소서 써줘"라고 처음 요청했을 때, 지원 동기나 구체적인 경험(성취, 갈등해결 등)이 포함되어 있지 않다면 **절대 바로 자소서를 완성하지 마세요.**
2. 대신, 면접관의 시선에서 아주 친절하게 **"경험 도출용 티키타카 질문"**을 1~2개 던지세요.
   - 예시: "OO기업 지원을 응원합니다! 완벽한 자소서를 위해, 혹시 {tech}를 활용했던 프로젝트 중 가장 큰 성취를 이룬 경험이나, 팀원과 갈등을 해결했던 에피소드가 있다면 편하게 단어나 개조식으로 던져주세요!"
3. 사용자가 키워드나 짧은 문장으로 자신의 스토리를 대답하면, 그제서야 지원자의 스펙과 엮어서 **[전문가 수정본]** 자소서를 마크다운으로 완벽하게 작성해 주세요.
4. 자소서를 작성한 후에는, 어떤 점을 강조했는지 짧게 코멘트해 주세요.
5. 대화는 항상 멘토처럼 따뜻하되, 글의 퀄리티는 날카롭고 전문적이어야 합니다."""),
        ("user", "{user_message}")
    ])

    chain = prompt | llm | StrOutputParser()

    for chunk in chain.stream({
        "gender": gender,
        "school": school, "major": major,
        "exp": exp, "awards": awards, "tech": tech,
        "user_message": user_message
    }):
        yield chunk