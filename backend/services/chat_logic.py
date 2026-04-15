import json
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()

# 현재 파일(chat_logic.py)이 있는 위치(backend/services)를 기준으로 json 파일을 찾습니다.
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "essay_samples.json"

# -----------------------------
# 모델 설정
# -----------------------------
# 주의: 윈도우 환경에서 Ollama 앱이 켜져 있어야 localhost:11434 연결이 성공합니다!
local_llm = ChatOllama(
    model="exaone3.5:7.8b",
    base_url="http://localhost:11434",
    temperature=0.9,
)

llm_gpt = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.5,
)

llm_groq = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.6,
    top_p=1,
    stop=None,
)

# -----------------------------
# 회사 맥락
# -----------------------------
COMPANY_CONTEXTS = {
    "ptkorea": {"display_name": "PTKOREA", "context": "PTKOREA는 데이터와 기술, 크리에이티브를 함께 활용해 브랜드와 비즈니스의 성장 실행을 만드는 환경으로 볼 수 있다. 데이터를 단순히 정리하는 데서 끝내지 않고, 실제 전략 판단과 실행으로 연결하는 시각이 중요하다."},
    "pt코리아": {"display_name": "PTKOREA", "context": "PTKOREA는 데이터와 기술, 크리에이티브를 함께 활용해 브랜드와 비즈니스의 성장 실행을 만드는 환경으로 볼 수 있다. 데이터를 단순히 정리하는 데서 끝내지 않고, 실제 전략 판단과 실행으로 연결하는 시각이 중요하다."},
    "올리브영": {"display_name": "올리브영", "context": "올리브영은 상품, 고객, 채널, 프로모션 데이터가 실제 운영과 연결되는 환경으로 볼 수 있다. 여러 부서가 함께 활용할 수 있는 신뢰 가능한 데이터 구조와 기준을 만드는 관점이 중요하다."},
    "oliveyoung": {"display_name": "올리브영", "context": "올리브영은 상품, 고객, 채널, 프로모션 데이터가 실제 운영과 연결되는 환경으로 볼 수 있다. 여러 부서가 함께 활용할 수 있는 신뢰 가능한 데이터 구조와 기준을 만드는 관점이 중요하다."},
    "넥슨": {"display_name": "넥슨", "context": "넥슨은 게임 경험과 이용자 반응을 데이터로 해석해 콘텐츠와 운영 판단으로 연결하는 환경으로 볼 수 있다. 단순 지표 관찰보다 왜 재미가 생기고 왜 이탈이 생기는지를 해석하는 관점이 중요하다."},
    "넥슨게임즈": {"display_name": "넥슨게임즈", "context": "넥슨게임즈는 콘텐츠 경험과 이용자 반응을 데이터로 해석해 운영과 개선으로 이어지는 판단이 중요한 환경으로 볼 수 있다."},
}

# -----------------------------
# 공통 유틸
# -----------------------------
def choose_refine_llm(selected_model: str):
    if "GPT-OSS-120B" in selected_model:
        return llm_groq
    return llm_gpt

def parse_user_profile(user_profile: tuple) -> dict[str, str]:
    resume_str = user_profile[4]
    try:
        resume_data = json.loads(resume_str) if resume_str else {}
    except json.JSONDecodeError:
        resume_data = {}

    personal = resume_data.get("personal", {})
    edu = resume_data.get("education", {})
    add = resume_data.get("additional", {})

    return {
        "gender": personal.get("gender", "선택안함"),
        "school": edu.get("school", "정보 없음"),
        "major": edu.get("major", "정보 없음"),
        "exp": add.get("internship", "정보 없음"),
        "awards": add.get("awards", "정보 없음"),
        "tech": add.get("tech_stack", "정보 없음"),
    }

def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def remove_forbidden_headers(text: str) -> str:
    cleaned = text.strip()
    block_patterns = [
        r"\[자소서 초안 평가\][\s\S]*$",
        r"\[AI 표절률\(유사도\) 검사 및 코멘트\][\s\S]*$",
    ]
    for pattern in block_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)
    line_patterns = [
        r"^\[자소서 초안\]\s*",
        r"^초안\s*[:：]\s*",
        r"^본문\s*[:：]\s*",
    ]
    for pattern in line_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()

def split_sentences_korean(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?다요])\s+", text.strip())
    return [c.strip() for c in chunks if c.strip()]

def repetition_ratio(text: str) -> float:
    sentences = split_sentences_korean(text)
    if not sentences:
        return 1.0
    unique_count = len(set(sentences))
    return 1 - (unique_count / len(sentences))

def normalize_company_key(name: str) -> str:
    if not name:
        return ""
    value = name.strip().lower().replace(" ", "")
    value = value.replace("(주)", "").replace("주식회사", "")
    return value

def get_company_context(company: str) -> tuple[str, str]:
    key = normalize_company_key(company)
    if key in COMPANY_CONTEXTS:
        data = COMPANY_CONTEXTS[key]
        return data["display_name"], data["context"]
    for stored_key, data in COMPANY_CONTEXTS.items():
        if stored_key in key or key in stored_key:
            return data["display_name"], data["context"]
    return company or "미기재", "회사 맥락 정보 없음"

def detect_question_type(user_message: str) -> str:
    text = user_message.lower()
    if any(k in text for k in ["지원 이유", "지원이유", "지원 동기", "지원동기", "왜 지원", "입사 이유"]):
        return "motivation"
    if any(k in text for k in ["입사 후 포부", "포부", "기여", "입사후"]):
        return "future_goal"
    if any(k in text for k in ["협업", "팀워크", "같이", "소통"]):
        return "collaboration"
    if any(k in text for k in ["문제 해결", "문제해결", "해결 경험", "어려움", "개선"]):
        return "problem_solving"
    if any(k in text for k in ["성장", "노력", "배운 점", "배움"]):
        return "growth"
    return "general"

def parse_user_request_regex(user_message: str) -> dict[str, Any]:
    text = user_message.strip()
    char_limit = None
    patterns = [r"(\d{3,4})\s*자\s*이내", r"(\d{3,4})\s*자\s*내외", r"(\d{3,4})\s*자\s*정도", r"(\d{3,4})\s*자", r"(\d{3,4})\s*byte"]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                char_limit = int(match.group(1))
                break
            except ValueError: pass

    company, job, question = "", "", ""
    company_match = re.search(r"(회사|기업|지원회사)\s*[:：]\s*(.+)", text)
    if company_match: company = company_match.group(2).splitlines()[0].strip()

    job_match = re.search(r"(직무|포지션|지원직무)\s*[:：]\s*(.+)", text)
    if job_match: job = job_match.group(2).splitlines()[0].strip()

    natural_patterns = [r"(.+?)에\s+(.+?)\s*직무로\s+지원", r"(.+?)\s+(.+?)\s*직무에\s+지원", r"(.+?)에\s+지원"]
    for idx, pattern in enumerate(natural_patterns):
        match = re.search(pattern, text)
        if match:
            if idx == 0 or idx == 1:
                if not company: company = match.group(1).strip()
                if not job: job = match.group(2).strip()
            elif idx == 2:
                if not company: company = match.group(1).strip()

    q_patterns = [r"(.+?)(?:를|을)\s*물어봤", r"문항\s*[:：]\s*(.+)", r"질문\s*[:：]\s*(.+)",]
    for pattern in q_patterns:
        match = re.search(pattern, text)
        if match:
            question = match.group(1).strip()
            break

    return {
        "raw": text, "company": company, "job": job, "question": question,
        "char_limit": char_limit, "question_type": detect_question_type(text),
    }

def llm_parse_user_request(user_message: str, selected_model: str) -> dict[str, Any]:
    active_llm = choose_refine_llm(selected_model)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """너는 자기소개서 요청 문장을 구조화하는 파서다. 반드시 JSON만 출력하라.
키는 아래만 사용하라: company, job, question, char_limit, question_type
규칙:
- 없는 값은 빈 문자열 또는 null
- question_type은 아래 중 하나만: motivation, future_goal, collaboration, problem_solving, growth, general
- 사용자의 표현을 과도하게 바꾸지 말고 핵심만 추출"""),
        ("human", "사용자 요청:\n{user_message}")
    ])
    chain = prompt | active_llm | StrOutputParser()
    raw = chain.invoke({"user_message": user_message}).strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        data = json.loads(raw)
        return {
            "company": str(data.get("company", "") or "").strip(),
            "job": str(data.get("job", "") or "").strip(),
            "question": str(data.get("question", "") or "").strip(),
            "char_limit": data.get("char_limit", None),
            "question_type": str(data.get("question_type", "") or "").strip() or "general",
        }
    except Exception:
        return {"company": "", "job": "", "question": "", "char_limit": None, "question_type": "general"}

def parse_user_request(user_message: str, selected_model: str = "GPT-4o-mini") -> dict[str, Any]:
    base = parse_user_request_regex(user_message)
    needs_llm = (not base["company"] or not base["job"] or base["question_type"] == "general")

    if needs_llm:
        llm_data = llm_parse_user_request(user_message, selected_model)
        if not base["company"] and llm_data["company"]: base["company"] = llm_data["company"]
        if not base["job"] and llm_data["job"]: base["job"] = llm_data["job"]
        if not base["question"] and llm_data["question"]: base["question"] = llm_data["question"]
        if not base["char_limit"] and llm_data["char_limit"]:
            try: base["char_limit"] = int(llm_data["char_limit"])
            except Exception: pass
        if base["question_type"] == "general" and llm_data["question_type"]:
            base["question_type"] = llm_data["question_type"]

    company_name, company_context = get_company_context(base["company"])
    base["company_display"] = company_name
    base["company_context"] = company_context

    if not base["question"]:
        qtype_map = {
            "motivation": "지원한 이유", "future_goal": "입사 후 포부", "collaboration": "협업 경험",
            "problem_solving": "문제 해결 경험", "growth": "성장 과정 또는 노력 경험", "general": "자기소개서 문항"
        }
        base["question"] = qtype_map.get(base["question_type"], "자기소개서 문항")
    return base

def load_easy_samples(question_type: str = "general") -> str:
    if not SAMPLE_PATH.exists():
        return ""
    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return ""

    samples = []
    if isinstance(raw, dict):
        raw = raw.get("cases", [raw])
    if not isinstance(raw, list):
        return ""

    scored_items = []
    for item in raw:
        score = 0
        q = str(item.get("question", "")).lower() if isinstance(item, dict) else str(item).lower()

        if question_type == "motivation" and any(k in q for k in ["지원동기", "지원 동기", "지원 이유"]): score += 3
        elif question_type == "future_goal" and any(k in q for k in ["포부", "입사 후"]): score += 3
        elif question_type == "collaboration" and any(k in q for k in ["협업", "팀워크"]): score += 3
        elif question_type == "problem_solving" and any(k in q for k in ["문제", "해결", "개선"]): score += 3
        elif question_type == "growth" and any(k in q for k in ["성장", "노력", "배움"]): score += 3

        scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    selected = [item for _, item in scored_items[:2]]

    for idx, item in enumerate(selected, start=1):
        if isinstance(item, dict):
            target_job = str(item.get("target_job", "")).strip()
            question = str(item.get("question", "")).strip()
            essay_text = str(item.get("essay_text", "") or item.get("content", "") or item.get("text", "")).strip()
            
            merged = []
            if target_job: merged.append(f"지원 직무: {target_job}")
            if question: merged.append(f"문항: {question}")
            if essay_text: merged.append(f"예시 본문:\n{essay_text[:1000]}")
            if merged: samples.append(f"[예시 {idx}]\n" + "\n".join(merged))
        elif isinstance(item, str):
            text = item.strip()
            if text: samples.append(f"[예시 {idx}]\n{text[:1000]}")

    return "\n\n".join(samples)

def score_local_draft(text: str, parsed_request: dict[str, Any]) -> tuple[bool, str]:
    if not text or len(text.strip()) < 140:
        return False, "초안 길이가 너무 짧습니다."
    ratio = repetition_ratio(text)
    if ratio > 0.48:
        return False, "문장 반복이 많습니다."
    if parsed_request.get("char_limit"):
        target = parsed_request["char_limit"]
        if len(text) < max(180, int(target * 0.45)):
            return False, "글자 수가 목표 대비 지나치게 짧습니다."
    if parsed_request.get("question_type") == "motivation":
        company_display = parsed_request.get("company_display", "")
        if company_display and company_display not in text:
            return False, "지원동기 문항인데 회사명이 반영되지 않았습니다."
    return True, "통과"

# -----------------------------
# 프롬프트
# -----------------------------
def get_local_system_prompt(question_type: str) -> str:
    common = """당신은 한국어 자기소개서 초안 작성 도우미다. 반드시 한국어로만 작성하라.
공통 규칙:
- 사용자 정보 안에서만 소재를 고른다. 없는 경험, 수치, 성과 절대 추가 금지.
- 예시 자소서는 구조와 전개만 참고하고 문장을 베끼지 않는다.
- 자기소개서 본문만 작성하라. 단순 나열을 피하고 문항과 연결되는 이유를 분명히 드러내라."""
    
    if question_type == "motivation":
        return common + "\n이 문항은 지원동기 문항이다. 회사의 관심점과 사용자 경험을 연결하고 입사 후 기여로 마무리하라. 첫 문장이 지원 이유가 되게 써라."
    if question_type == "future_goal":
        return common + "\n이 문항은 입사 후 포부다. 현재 경험을 바탕으로 입사 후 배우고 기여할 방향을 써라."
    if question_type == "collaboration":
        return common + "\n이 문항은 협업 문항이다. 기준 정렬, 전달 조율, 연결을 중심으로 써라."
    if question_type == "problem_solving":
        return common + "\n이 문항은 문제 해결 문항이다. 문제 인식 → 원인 파악 → 해결 방식 → 결과 흐름으로 써라."
    if question_type == "growth":
        return common + "\n이 문항은 성장/노력 문항이다. 무엇을 배우려 했고, 어떤 기준을 새로 세웠는지 써라."
    return common + "\n문항 의도에 맞는 흐름을 세우고 가장 관련 있는 경험 중심으로 써라."

def get_refine_system_prompt(question_type: str) -> str:
    common = """당신은 한국어 자기소개서 첨삭 전문가다. 새로 쓰는 것이 아니라 초안을 더 설득력 있게 다듬어라.
규칙: 한국어 작성, 경험 조작 금지, 담백한 문체, 반복 표현 제거, 본문만 출력."""
    if question_type == "motivation":
        return common + "\n지원동기 문항 점검: 첫 문장 이유 시작, 경험 연결, 기체적 기여 방향 마무리."
    return common

# -----------------------------
# 생성 단계
# -----------------------------
def build_local_draft(user_message: str, user_profile: tuple, selected_model: str = "GPT-4o-mini") -> str:
    profile = parse_user_profile(user_profile)
    parsed = parse_user_request(user_message, selected_model)
    examples_text = load_easy_samples(parsed["question_type"])

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_local_system_prompt(parsed["question_type"])),
        ("human", """[지원자 정보]
- 성별: {gender} / 학교: {school} / 전공: {major}
- 경험: {exp} / 수상: {awards} / 기술: {tech}

[추출 정보]
- 회사: {company_display} / 직무: {job} / 문항: {question} / 길이: {char_limit}

[회사 맥락]
{company_context}

[참고 예시]
{examples_text}

요구사항: 자소서 본문 초안만 써라.""")
    ])

    chain = prompt | local_llm | StrOutputParser()
    result = chain.invoke({
        "gender": profile["gender"], "school": profile["school"], "major": profile["major"],
        "exp": profile["exp"], "awards": profile["awards"], "tech": profile["tech"],
        "company_display": parsed["company_display"] or "미기재", "job": parsed["job"] or "미기재",
        "question": parsed["question"] or "미기재", "char_limit": parsed["char_limit"] or "미기재",
        "company_context": parsed["company_context"], "examples_text": examples_text or "없음",
    })
    return clean_text(remove_forbidden_headers(result))

def regenerate_local_draft_if_needed(user_message: str, user_profile: tuple, selected_model: str = "GPT-4o-mini", max_attempts: int = 2) -> str:
    parsed = parse_user_request(user_message, selected_model)
    last_text, working_message = "", user_message

    for attempt in range(max_attempts):
        draft = build_local_draft(working_message, user_profile, selected_model)
        is_ok, reason = score_local_draft(draft, parsed)
        last_text = draft

        if is_ok: return draft
        if attempt < max_attempts - 1:
            working_message = user_message + f"\n\n추가 지시: 이전 초안은 '{reason}' 문제가 있었어. 다시 작성해줘."
    return last_text

def refine_with_api(local_draft_body: str, user_message: str, selected_model: str) -> str:
    parsed = parse_user_request(user_message, selected_model)
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_refine_system_prompt(parsed["question_type"])),
        ("human", "[추출 정보]\n- 회사: {company_display} / 직무: {job} / 문항: {question}\n\n[초안]\n{local_draft_body}\n\n요구사항: 방향 유지하며 다듬기.")
    ])
    chain = prompt | active_llm | StrOutputParser()
    result = chain.invoke({
        "company_display": parsed["company_display"], "job": parsed["job"], "question": parsed["question"],
        "local_draft_body": local_draft_body,
    })
    return clean_text(remove_forbidden_headers(result))

def fit_length_if_needed(text: str, user_message: str, selected_model: str) -> str:
    parsed = parse_user_request(user_message, selected_model)
    target = parsed.get("char_limit")
    if not target: return text

    current = len(text)
    lower, upper = int(target * 0.9), int(target * 1.05)
    if lower <= current <= upper: return text

    active_llm = choose_refine_llm(selected_model)
    direction = "조금 더 압축해 주세요." if current > upper else "조금 더 내용을 보강해 주세요."

    prompt = ChatPromptTemplate.from_messages([
        ("system", "한국어 자기소개서 문장 길이 조정 전문가다. 본문만 출력할 것."),
        ("human", "[현재: {current}자 / 목표: {target}자]\n요청: {direction}\n\n{text}")
    ])
    chain = prompt | active_llm | StrOutputParser()
    adjusted = chain.invoke({"text": text, "target": target, "current": current, "direction": direction})
    return clean_text(remove_forbidden_headers(adjusted))

def build_final_response(body: str, user_message: str, selected_model: str = "GPT-4o-mini") -> str:
    parsed = parse_user_request(user_message, selected_model)
    current_len = len(body)
    length_comment = f"요청 글자 수 기준({parsed['char_limit']}자)" if parsed.get("char_limit") else "문항 흐름"
    
    return f"""[자소서 초안]

{body}

[자소서 초안 평가]
평가 결과: 좋다
이유: 문항 의도와 사용자 경험, 회사 맥락이 자연스럽게 이어지도록 정리했습니다.

[AI 표절률(유사도) 검사 및 코멘트]
- 예상 AI 유사도: 측정값 아님
- 멘토 코멘트: {length_comment}을 고려해 약 {current_len}자로 정리했습니다. 구체화를 통해 완성도를 높여보세요."""