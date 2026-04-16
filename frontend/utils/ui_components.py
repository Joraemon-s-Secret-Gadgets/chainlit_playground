import streamlit as st
import base64
import os

def apply_custom_css():
    st.markdown("""
        <style>
        footer {visibility: hidden !important;}
        .stAppDeployButton {display: none !important;}
        [data-testid="stActionMenu"] {display: none !important;}

        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }

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

        [data-testid="stSidebarHeader"] {padding: 0px !important; margin: 0px !important;}
        [data-testid="stSidebarUserContent"] {padding-top: 1rem !important;}

        .progress-card {
            padding: 0.9rem 1rem;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            background: #FAFAFA;
            margin-bottom: 0.8rem;
            line-height: 1.8;
        }
        .progress-card b { display: block; margin-bottom: 0.4rem; }

        .followup-box {
            padding: 1rem 1.2rem;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            background: #FCFCFD;
            margin-top: 0.8rem;
            line-height: 1.8;
        }

        .evaluation-card {
            padding: 1rem 1.2rem;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            background: #F8FAFC;
            margin-top: 1rem;
            margin-bottom: 1rem;
            line-height: 1.8;
        }

        .center-helper {
            text-align: center;
        }

        .muted-caption {
            color: #666;
            font-size: 0.95rem;
        }
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
