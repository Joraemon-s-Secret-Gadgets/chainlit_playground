import streamlit as st
import base64
import os

def apply_custom_css():
    # 1. 로고 이미지 가져오기
    img_path = "public/logo_light.png"
    if not os.path.exists(img_path):
        img_path = os.path.join("frontend", "public", "logo_light.png")
    
    encoded_string = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()

    # 2. 확실한 CSS 주입 (수학적 중앙 계산)
    st.markdown(f"""
        <style>
        footer {{visibility: hidden !important;}}
        .stAppDeployButton {{display: none !important;}}
        [data-testid="stActionMenu"] {{display: none !important;}}
        
        /* 1. 순정 헤더(하얀 띠) 투명화 */
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            box-shadow: none !important;
        }}

        /* 2. 화면 전체를 덮는 고정 배경 바 */
        .ultimate-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 70px;
            background-color: rgba(255, 255, 255, 0.98) !important;
            border-bottom: 2px solid #CAD9F0;
            z-index: 999;
            pointer-events: none;
        }}

        /* 3. 로고와 텍스트 알맹이 (기본: 화면 정중앙) */
        .header-content {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: flex;
            align-items: center;
            gap: 12px;
            pointer-events: auto;
            /* 🔥 사이드바 열고 닫을 때 로고가 스무스하게 중앙을 찾아가는 애니메이션 */
            transition: left 0.3s ease-in-out;
        }}

        /* 🔥 4. 핵심 마법: 사이드바가 '열려있을 때'만 오른쪽으로 168px 밀어줌 (사이드바 336px의 절반) */
        section[data-testid="stSidebar"][aria-expanded="true"] + section.main .header-content {{
            left: calc(50% + 168px) !important;
        }}

        .header-content img {{ 
            width: 35px;
            height: 35px;
            object-fit: contain; 
            border-radius: 6px; 
        }}
        
        .header-content h1 {{ 
            margin: 0; 
            padding: 0; 
            font-size: 1.4rem; 
            font-weight: 800; 
            color: #31333F; 
            line-height: 1; 
        }}

        /* 사이드바 여는 버튼 보호 (위로 끌어올림) */
        [data-testid="stSidebarCollapsedControl"] {{
            z-index: 999999 !important;
        }}

        /* 본문이 헤더에 가리지 않게 넉넉한 여백 확보 */
        .block-container {{ 
            padding-top: 5.5rem !important;
            padding-bottom: 2rem !important; 
        }}

        /* 기존 유지 CSS */
        [data-testid="stSidebarHeader"] {{padding: 0px !important; margin: 0px !important;}}
        [data-testid="stSidebarUserContent"] {{
            padding-top: 1rem !important;
            display: flex;
            flex-direction: column;
            height: 100%;
        }}
        .sidebar-bottom-spacer {{ flex-grow: 1; min-height: 50px; }}
        .progress-card {{ padding: 0.9rem 1rem; border: 1px solid #E5E7EB; border-radius: 12px; background: #FAFAFA; margin-bottom: 0.8rem; line-height: 1.8; }}
        .progress-card b {{ display: block; margin-bottom: 0.4rem; }}
        .followup-box {{ padding: 1rem 1.2rem; border: 1px solid #E5E7EB; border-radius: 12px; background: #FCFCFD; margin-top: 0.8rem; line-height: 1.8; }}
        .evaluation-card {{ padding: 1rem 1.2rem; border: 1px solid #E5E7EB; border-radius: 12px; background: #F8FAFC; margin-top: 1rem; margin-bottom: 1rem; line-height: 1.8; }}
        .center-helper {{ text-align: center; }}
        .muted-caption {{ color: #666; font-size: 0.95rem; }}
        </style>
        
        <div class="ultimate-header">
            <div class="header-content">
                {f'<img src="data:image/png;base64,{encoded_string}" alt="Logo">' if encoded_string else ''}
                <h1>JobPocket</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_header(title: str):
    pass