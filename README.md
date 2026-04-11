# 💼 JobPocket - AI 자소서 첨삭 어시스턴트 (MVP 1.0) - In Chainlit_Playground

> "당신의 경험을 완벽한 무기로."
> 10년 차 대기업 인사담당자 페르소나를 가진 AI가 지원자의 스펙을 분석하여 맞춤형 자소서 첨삭을 제공하는 하이브리드 챗봇 웹 서비스입니다.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Chainlit](https://img.shields.io/badge/Chainlit-F15A24?style=for-the-badge&logo=chainlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

## ✨ 주요 기능 (Features)

- **AI 맞춤형 자소서 첨삭:** LangChain과 GPT-4o-mini를 연동하여, 사용자가 입력한 학력/경력 기반의 전문적인 피드백을 실시간(Streaming)으로 제공합니다.
- **하이브리드 웹 아키텍처:** FastAPI로 구현된 인증(회원가입/로그인)용 랜딩 페이지와 Chainlit 기반의 챗봇 화면(`/chat`)을 완벽하게 라우팅 분리했습니다.
- **사용자 프로필 및 대화 유지:** SQLite를 활용하여 유저 스펙(학력, 경력 등)을 저장하고, 세션 및 과거 대화 내역(SQLAlchemyDataLayer)을 안전하게 관리합니다.
- **보안/인증 적용:** 이메일 중복 체크 및 SHA-256 단방향 암호화를 통한 안전한 비밀번호 관리를 지원합니다.

## 🏗 프로젝트 아키텍처 및 폴더 구조

```text
JobPocket/
├── main.py              # FastAPI 메인 서버 (랜딩/회원가입 라우팅 및 정적 파일 서빙)
├── app.py               # Chainlit 챗봇 본체 (웹소켓 통신 및 세션 관리)
├── chat_logic.py        # LangChain 핵심 파이프라인 (프롬프트 엔지니어링 및 AI 호출)
├── database.py          # SQLite DB 초기화 및 CRUD 로직 
├── auth.py              # 비밀번호 해싱 및 보안 유틸리티 모듈
├── templates/           # FastAPI용 HTML 템플릿 화면
│   ├── index.html       # 메인 랜딩 페이지 (대문)
│   └── signup.html      # 회원가입 폼
├── public/              # 정적 파일 보관소 (로고, 아바타 이미지 등)
└── .chainlit/           # Chainlit UI/UX 커스텀 설정 (라이트 모드 고정 등)