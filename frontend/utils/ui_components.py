import streamlit as st
import base64
import os

def apply_custom_css():
    st.markdown("""
        <style>
        /* 1. 하단 푸터 숨기기 */
        footer {visibility: hidden !important;}
        
        /* 2. 상단 헤더(stHeader) */
        
        /* 3. 우측에 거슬리는 요소만 아주 정밀하게 타격해서 삭제 */
        .stAppDeployButton {display: none !important;} /* Deploy 버튼 */
        [data-testid="stActionMenu"] {display: none !important;} /* 점 3개 메뉴 버튼 */
        
        /* 4. 메인 컨테이너 본문을 순정 헤더 아래로 안전하게 내리기 */
        .block-container { 
            padding-top: 3.5rem !important; /* 원래 있던 투명한 헤더 영역 아래로 로고 띠를 쑥 내립니다 */
            padding-bottom: 2rem !important; 
        }
        
        /* 5. 예쁜 커스텀 바 디자인 유지 (왼쪽 여백도 원래대로 원복) */
        .custom-navbar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid #CAD9F0;
        }
        .custom-navbar img { width: 55px; object-fit: contain; border-radius: 6px; }
        .custom-navbar h1 { margin: 0; padding: 0; font-size: 1.5rem; font-weight: 800; color: #31333F; line-height: 1; }

        /* 6. 사이드바 로고 상단 밀착 */
        [data-testid="stSidebarHeader"] {padding: 0px !important; margin: 0px !important;}
        [data-testid="stSidebarUserContent"] {padding-top: 1rem !important;}

        /* 7. 기존 UI 카드 스타일 유지 */
        .progress-card { padding: 0.9rem 1rem; border: 1px solid #E5E7EB; border-radius: 12px; background: #FAFAFA; margin-bottom: 0.8rem; line-height: 1.8; }
        .progress-card b { display: block; margin-bottom: 0.4rem; }
        </style>
    """, unsafe_allow_html=True)

def display_header(title: str):
    img_path = "public/logo_light.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""
            <div class="custom-navbar">
                <img src="data:image/png;base64,{encoded_string}" alt="Logo">
                <h1>{title}</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="custom-navbar"><h1>{title}</h1></div>
        """, unsafe_allow_html=True)