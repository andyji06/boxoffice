import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(
    page_title="시네마 일별 박스오피스",
    layout="wide",
    page_icon="🎬"
)

# -----------------------------------------------------------------------------
# 0. 커스텀 CSS (다크 테마 텍스트 가독성 및 UI 개선)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* 전체 배경색 지정 */
    .stApp {
        background-color: #0E1117;
    }
    
    /* 기본 텍스트, 라벨, 캡션 글자색 보정 */
    .stApp p, .stApp label, .stApp span, div[data-testid="stMarkdownContainer"] p {
        color: #E0E0E0 !important;
    }
    
    /* 제목 및 헤더 강조 */
    h1 {
        color: #FFD700 !important;
        font-weight: 800 !important;
        text-shadow: 0px 0px 15px rgba(255, 215, 0, 0.4);
    }
    
    h2, h3 {
        color: #FFFFFF !important;
    }

    /* 날짜 선택기 Input Box 가독성 확보 */
    div[data-baseweb="input"] {
        background-color: #161A23 !important;
        border-radius: 8px !important;
        border: 1px solid #33394B !important;
    }
    div[data-baseweb="input"] input {
        color: #FFFFFF !important;
    }

    /* 1위 히어로 배너 */
    .hero-container {
        background: linear-gradient(135deg, #1A1C29 0%, #0D0F18 100%);
        border: 2px solid #FFD700;
        border-radius: 16px;
        padding: 32px 24px;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.2);
        color: #FFFFFF;
        margin-top: 15px;
        margin-bottom: 25px;
        text-align: center;
    }
    .hero-badge {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
        color: #000000;
        font-weight: 900;
        font-size: 0.9rem;
        padding: 6px 18px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 12px;
        letter-spacing: 1px;
    }
    .hero-title {
        font-size: 2.6rem;
        font-weight: 900;
        margin: 8px 0;
        color: #FFFFFF;
        text-shadow: 0 0 16px rgba(255, 215, 0, 0.5);
    }
    .hero-sub {
        font-size: 1.1rem;
