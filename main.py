import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 테마 박스오피스", layout="wide", page_icon="🎬")

# -----------------------------------------------------------------------------
# 1. 영화 테마 자동 감지 및 Custom CSS 스타일 적용 함수
# -----------------------------------------------------------------------------
def apply_movie_theme(movie_title: str):
    """1위 영화 제목을 분석하여 분위기에 맞는 배경/스타일을 동적으로 전환합니다."""
    title_lower = movie_title.lower()
    
    # 테마 정의 (키워드, 배경 그라데이션, 포인트 색상, 테마 이모지, 메시지)
    if any(k in title_lower for k in ["범죄", "액션", "에이리언", "마녀", "샤이닝", "오컬트", "파묘", "악마", "죽음", "피", "괴물"]):
        theme = {
            "bg": "linear-gradient(135deg, #1f1c2c 0%, #928dab 100%)",
            "card_bg": "rgba(255, 255, 255, 0.08)",
            "text": "#ffffff",
            "accent": "#ff4b4b",
            "emoji": "👻💀",
            "tag": "스릴러 & 호러 & 미스터리 모드"
        }
    elif any(k in title_lower for k in ["사랑", "러브", "연애", "고백", "로맨스", "첫사랑", "너의", "그대"]):
        theme = {
            "bg": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)",
            "card_bg": "rgba(255, 255, 255, 0.65)",
            "text": "#2d3436",
            "accent": "#e84393",
            "emoji": "💖🌸",
            "tag": "달콤한 로맨스 & 감성 모드"
        }
    elif any(k in title_lower for k in ["어벤져스", "스파이더", "히어로", "전쟁", "스타", "워즈", "킹", "건", "미션", "시그널"]):
        theme = {
            "bg": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
            "card_bg": "rgba(255, 255, 255, 0.12)",
            "text": "#ffffff",
            "accent": "#00cec9",
            "emoji": "💥🚀",
            "tag": "블록버스터 & 액션 & SF 모드"
        }
    elif any(k in title_lower for k in ["짱구", "명탐정", "귀멸", "포켓몬", "디즈니", "픽사", "쿵푸", "인사이드", "슈퍼"]):
        theme = {
            "bg": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
            "card_bg": "rgba(255, 255, 255, 0.7)",
            "text": "#2d3436",
            "accent": "#ff7675",
            "emoji": "🎈🧸",
            "tag": "신나는 애니메이션 & 키덜트 모드"
        }
    else:
        # 기본 시네마틱 모드
        theme = {
            "bg": "linear-gradient(135deg, #141e30 0%, #243b55 100%)",
            "card_bg": "rgba(255, 255, 255, 0.1)",
            "text": "#ffffff",
            "accent": "#fbc531",
            "emoji": "🎬🍿",
            "tag": "클래식 시네마 모드"
        }

    # Streamlit 커스텀 CSS 주입
    css = f"""
    <style>
        .stApp {{
            background: {theme['bg']} !important;
            color: {theme['text']} !important;
        }}
        div[data-testid="stMetric"], div[data-testid="stForm"] {{
            background-color: {theme['card_bg']};
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        h1, h2, h3, p, span {{
            color: {theme['text']} !important;
        }}
        .theme-badge {{
            display: inline-block;
            padding: 6px 14px;
            background-color: {theme['accent']};
            color: white !important;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return theme

# -----------------------------------------------------------------------------
# 2. 날짜 선택기 (한국 시간 기준 어제 날짜 설정)
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

st.title("🎬 1위 영화 테마 실시간 바이브 박스오피스")

selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요:",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1),
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

# -----------------------------------------------------------------------------
# 3. Streamlit Secrets API 키 불러오기 및 데이터 요청
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error("⚠️ **API 키를 찾을 수 없습니다.** Secrets에 `KOBIS_KEY`를 등록해 주세요.")
    st.stop()

@st.cache_data(ttl=3600)
def fetch_daily_boxoffice(key: str, target_dt: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": target_dt}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

try:
    data = fetch_daily_boxoffice(api_key, target_date_str)
except Exception as e:
    st.error(f"⚠️ **KOBIS API 연결 실패:** `{e}`")
    st.stop()

boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(f"⚠️ **{display_date_str}**: 집계 전이거나 데이터가 존재하지 않습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. 데이터 전처리
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype
