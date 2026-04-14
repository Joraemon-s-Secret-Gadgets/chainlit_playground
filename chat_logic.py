import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()  

# 1. 두 모델을 독립적으로 선언 (덮어쓰기 방지)
llm_gpt = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_groq = ChatGroq(
    model='openai/gpt-oss-120b',
    temperature=1.0,
    top_p=1,
    # stream=False 옵션은 langchain의 .stream()을 방해하므로 제거함
    stop=None
)

# 2. 매개변수에 selected_model 추가
def generate_ai_feedback_stream(user_message: str, user_profile: tuple, selected_model: str = "GPT-4o-mini"):
    resume_str = user_profile[4]
    
    try:
        resume_data = json.loads(resume_str) if resume_str else {}
    except json.JSONDecodeError:
        resume_data = {}

    personal = resume_data.get("personal", {})
    edu = resume_data.get("education", {})
    add = resume_data.get("additional", {})
    
    gender = personal.get("gender", "선택안함")
    school = edu.get("school", "정보 없음")
    major = edu.get("major", "정보 없음")
    exp = add.get("internship", "정보 없음")
    awards = add.get("awards", "정보 없음")
    tech = add.get("tech_stack", "정보 없음")

    prompt = ChatPromptTemplate.from_messages([
   ("system", """당신은 10년 차 대기업 최고 인사담당자이자 1:1 자소서 전담 멘토입니다.
아래는 지원자의 기본 하드 스펙(Hard Spec)입니다.

[지원자 팩트 체크]
- 인적사항: 성별({gender})
- 학력: {school} {major}
- 직무 경험: {exp}
- 수상 및 스펙: {awards}
- 기술 스택: {tech}

[대화 및 작성 지침 - 매우 중요]
1. 무조건 초안부터 즉시 작성 (질문으로 대화 가로막기 절대 금지!):
   - 사용자가 기업, 직무, 문항을 제시하며 자소서 작성을 요청하면, 정보가 부족하다고 느끼더라도 "질문부터 드리겠습니다"라며 멈추지 마세요.
   - 반드시 주어진 [지원자 팩트 체크] 정보와 사용자의 요청 내용만으로 뼈대를 구성하여 [자소서 초안]을 즉시 출력하세요.
   - 단, 허위 사실이나 에피소드를 임의로 지어내지 말고, 주어진 팩트 안에서 논리적으로 포장하세요.

2. 자소서 분량 및 구조 강제 규칙 (글자 수 미달 방지):
   - 사용자가 제시한 문항의 의도에 맞게 글의 흐름을 구성하되, 반드시 아래의 4단 구조와 할당된 글자 수를 꽉 채워서 작성하세요.
     * 서론 (문항에 대한 핵심 답변 요약) : 150자 ~ 200자
     * 본론 1 (관련된 첫 번째 팩트 기반 에피소드 및 STAR 기법 적용) : 300자 ~ 350자
     * 본론 2 (관련된 두 번째 팩트 기반 에피소드 및 성과 수치화) : 300자 ~ 350자
     * 결론 (입사 후 포부 및 기여 방안) : 150자 ~ 200자 
   - [자체 검수] 작성을 마친 후 자체적으로 분량을 확인하여 900자가 안 된다고 판단되면, 본론의 Action(행동) 부분에 기술적 디테일이나 문제 해결 과정을 구체적으로 덧붙여 분량을 반드시 늘리세요.

3. 문체 및 표현 제약:
   - 맞춤법을 완벽히 지키며, 특수문자(*, # 등 마크다운 기호)는 절대 사용하지 마세요. 오직 평문으로만 작성하세요.
   - '체감', '다양한', '~~했습니다', '~을(를) 넘어' 등 AI 특유의 기계적이고 추상적인 어휘를 철저히 배제하세요.

4. 최종 출력 포맷 (반드시 아래 3가지 항목을 순서대로 출력할 것):

[자소서 초안]
(이곳에 마크다운 기호 없이 자소서 본문을 텍스트로만 출력)

[자소서 초안 평가]
평가 결과: (좋다 / 나쁘다 중 택 1 하여 명시하고, 그 이유를 1~2줄로 예리하게 분석)

[AI 표절률(유사도) 검사 및 코멘트]
- 예상 AI 유사도: (0~100% 사이의 수치, 예: 15%)
- 멘토 코멘트: (초안에서 팩트가 부족하여 부득이하게 빈약하게 작성된 부분을 짚어주며, "더 완벽한 글을 위해 ~~부분의 구체적인 에피소드를 알려주시면 반영해 드리겠습니다"라고 역질문하여 피드백을 유도하세요.)
"""),
    ("user", "{user_message}")
])

    # 3. 모델 선택 분기
    active_llm = llm_groq if "GPT-OSS-120B" in selected_model else llm_gpt
    chain = prompt | active_llm | StrOutputParser()

    for chunk in chain.stream({
        "gender": gender,
        "school": school, "major": major,
        "exp": exp, "awards": awards, "tech": tech,
        "user_message": user_message
    }):
        yield chunk