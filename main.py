import datetime
from urllib.parse import quote_plus

import pandas as pd
import pytz
import requests
import streamlit as st

st.set_page_config(page_title="CINEMA BOX", page_icon="🎬", layout="wide")

# CSS는 반드시 문자열 안에 작성합니다.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp {
        background: radial-gradient(circle at 85% 0%, rgba(110,45,190,.18), transparent 30%),
                    linear-gradient(180deg, #10111a 0%, #0b0c12 100%);
        color: #f5f5fa;
    }
    [data-testid="stSidebar"] { background: #141520; border-right: 1px solid #282a3a; }
    .hero {
        padding: 32px; border-radius: 22px; margin-bottom: 22px;
        background: linear-gradient(115deg, #262044, #171827 55%, #321a3c);
        border: 1px solid rgba(255,255,255,.10);
    }
    .eyebrow { color: #c7a7ff; font-size: .82rem; font-weight: 800; letter-spacing: .18em; }
    .hero h1 { color: white; font-size: clamp(2rem, 4vw, 3.2rem); margin: 8px 0; }
    .hero p { color: #c7c7d8; margin-bottom: 0; }
    div[data-testid="stMetric"] { background: #171925; border: 1px solid #2a2d40; padding: 16px; border-radius: 16px; }
    .stButton > button, .stLinkButton > a { border-radius: 12px; font-weight: 700; }
    hr { border-color: #292b3c; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">YOUR DAILY MOVIE GUIDE</div>
      <h1>🎬 CINEMA BOX</h1>
      <p>오늘의 영화 트렌드를 발견하고, 포스터와 예고편까지 만나보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_daily_boxoffice(api_key: str, target_dt: str) -> dict:
    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )
    response = requests.get(
        url, params={"key": api_key, "targetDt": target_dt}, timeout=15
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_tmdb_movie(movie_title: str, tmdb_key: str) -> dict:
    search_response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={
            "api_key": tmdb_key,
            "query": movie_title,
            "language": "ko-KR",
            "include_adult": "false",
        },
        timeout=12,
    )
    search_response.raise_for_status()
    results = search_response.json().get("results", [])
    if not results:
        return {}
    match = next(
        (item for item in results if item.get("title", "").strip().lower() == movie_title.strip().lower()),
        results[0],
    )
    details_response = requests.get(
        f"https://api.themoviedb.org/3/movie/{match['id']}",
        params={
            "api_key": tmdb_key,
            "language": "ko-KR",
            "append_to_response": "videos",
        },
        timeout=12,
    )
    details_response.raise_for_status()
    return details_response.json()

