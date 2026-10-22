import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="영화관 박스오피스 & 매점", layout="wide", page_icon="🍿")

# -----------------------------------------------------------------------------
# 1. 영화관 분위기 동적 테마 설정 함수 (CSS 주입)
# -----------------------------------------------------------------------------
def apply_cinema_theme(movie_title: str):
    title_lower = movie_title.lower()
    
    # 1위 영화 키워드 기반 영화관 컨셉 테마 분기
    if any(k in title_lower for k in ["범죄", "액션", "마녀", "스릴러", "파묘", "괴물", "악마", "죽음", "피"]):
        # [다크 상영관 모드] - 딥 블랙 & 붉은 네온
        theme = {
            "bg": "linear-gradient(135deg, #090a0f 0%, #171926 100%)",
            "card_bg": "rgba(255, 30, 80, 0.08)",
            "card_border": "#ff1e50",
            "text": "#ffffff",
            "accent": "#ff1e50",
            "emoji": "🎬 🍷",
            "tag": "다크 서스펜스 상영관 모드"
        }
    elif any(k in title_lower for k in ["어벤져스", "스파이더", "히어로", "전쟁", "스타", "워즈", "킹", "건", "미션", "SF"]):
        # [IMAX / SF 상영관 모드] - 블루 네온 & 사이버 시네마
        theme = {
            "bg": "linear-gradient(135deg, #050b14 0%, #0a192f 100%)",
            "card_bg": "rgba(0, 210, 255, 0.08)",
            "card_border": "#00d2ff",
            "text": "#ffffff",
            "accent": "#00d2ff",
            "emoji": "🌌 🚀",
            "tag": "IMAX 레이저 시네마 모드"
        }
    elif any(k in title_lower for k in ["짱구", "명탐정", "귀멸", "포켓몬", "디즈니", "픽사", "쿵푸", "인사이드", "코미디", "사랑"]):
        # [팝콘 & 로맨틱 콤보 모드] - 따뜻한 카라멜 팝콘 느낌
        theme = {
            "bg": "linear-gradient(135deg, #1f1a14 0%, #3a2e21 100%)",
            "card_bg": "rgba(255, 180, 0, 0.1)",
            "card_border": "#ffb400",
            "text": "#fff8e7",
            "accent": "#ffb400",
            "emoji": "🍿 🥤",
            "tag": "카라멜 팝콘 & 콤보 상영관 모드"
        }
    else:
        # [클래식 레드카펫 모드] - 전통적인 고급 영화관 느낌
        theme = {
            "bg": "linear-gradient(135deg, #120006 0%, #2a0812 100%)",
            "card_bg": "rgba(220, 53, 69, 0.1)",
            "card_border": "#dc3545",
            "text": "#ffffff",
            "accent": "#ff4d4d",
            "emoji": "🎟️ 🍿",
            "tag": "클래식 시네마 프리미엄 모드"
        }

    # Streamlit 커스텀 CSS
    css = f"""
    <style>
        .stApp {{
            background: {theme['bg']} !important;
            color: {theme['text']} !important;
        }}
        div[data-testid="stMetric"], div[data-testid="stForm"] {{
            background-color: {theme['card_bg']};
            border: 1px solid {theme['card_border']};
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        h1, h2, h3, p, span, label {{
            color: {theme['text']} !important;
        }}
        .cinema-badge {{
            display: inline-block;
            padding: 6px 16px;
            background-color: {theme['accent']};
            color: #ffffff !important;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.95rem;
            margin-bottom: 15px;
            box-shadow: 0 0 10px {theme['accent']};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return theme

# -----------------------------------------------------------------------------
# 2. 날짜 선택기 (한국 시간 기준 최대 '어제'까지만 선택 가능)
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

st.title("🍿 CGV·메가박스 감성 일별 박스오피스")

selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (오늘 날짜는 집계 전입니다):",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1),
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

# -----------------------------------------------------------------------------
# 3. Streamlit Secrets API 키 불러오기 & 요청
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "⚠️ **API 키를 찾을 수 없습니다.**\n\n"
        "Streamlit Cloud의 **App Settings > Secrets** 메뉴 또는 local `.streamlit/secrets.toml`에 아래와 같이 등록했는지 확인해 주세요.\n"
        "```toml\n"
        'KOBIS_KEY = "발급받은_인증키"\n'
        "```"
    )
    st
