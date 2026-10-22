import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 사이드바 (날짜 선택)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="장르 가변형 박스오피스", layout="wide", page_icon="🎬")

kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

st.sidebar.header("⚙️ CONTROL PANEL")

# 날짜 선택기 (최대 어제)
selected_date = st.sidebar.date_input(
    label="📅 조회 날짜 선택",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1)
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.sidebar.info(f"🎯 **TARGET DATE**\n{display_date_str}")

# -----------------------------------------------------------------------------
# 2. Streamlit Secrets에서 API Key 불러오기
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "⚠️ **KOBIS_KEY를 찾을 수 없습니다.**\n\n"
        "Streamlit Cloud의 **Secrets** 또는 `.streamlit/secrets.toml`에 `KOBIS_KEY`를 설정해 주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 요청
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_box_office(key, target_date):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": target_date}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

data = fetch_box_office(api_key, target_date_str)

if "error" in data:
    st.error(f"⚠️ **서버 연결 실패:** {data['error']}")
    st.stop()

if "faultInfo" in data:
    st.error(f"⚠️ **인증 오류:** {data['faultInfo'].get('message')}")
    st.stop()

boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(f"⚠️ **[{display_date_str}]**: 그날은 아직 집계 전입니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. 데이터 전처리
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

int_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in int_cols:
    df[col] = df[col].astype(int)

# -----------------------------------------------------------------------------
# 5. 🔥 1위 영화 장르/제목에 따른 동적 테마(Dynamic Theme) 적용
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]
top_1_title = str(top_1.get("movieNm", ""))
genre_text = str(top_1.get("genreAlt", "")) + " " + top_1_title

def get_dynamic_theme(text):
    if any(k in text for k in ["SF", "액션", "어벤져스", "히어로", "외계"]):
        return {
            "name": "히어로/SF 테마",
            "icon": "🤖",
            "bg": "#0b0e14",
            "accent": "#ff3333",
            "sub_accent": "#e6b800",
            "chart_color": "#ff3333"
        }
    elif any(k in text for k in ["공포", "스릴러", "미스터리", "호러"]):
        return {
            "name": "다크 스릴러 테마",
            "icon": "👻",
            "bg": "#0d0000",
            "accent": "#990000",
            "sub_accent": "#ff6666",
            "chart_color": "#990000"
        }
    elif any(k in text for k in ["애니메이션", "코미디", "전체관람가", "명탐정", "짱구", "포켓몬"]):
        return {
            "name": "팝 & 툰 테마",
            "icon": "🎈",
            "bg": "#121921",
            "accent": "#ffb703",
            "sub_accent": "#fb8500",
            "chart_color": "#ffb703"
        }
    elif any(k in text for k in ["멜로", "로맨스", "드라마"]):
        return {
            "name": "감성 시네마 테마",
            "icon": "🍿",
            "bg": "#1a0f1a",
            "accent": "#ffb3c1",
            "sub_accent": "#ff4d6d",
            "chart_color": "#ff4d6d"
        }
    else:
        return {
            "name": "골드 시네마 테마",
            "icon": "👑",
            "bg": "#0f172a",
            "accent": "#f59e0b",
            "sub_accent": "#38bdf8",
            "chart_color": "#f59e0b"
        }

theme = get_dynamic_theme(genre_text)

# 커스텀 CSS를 통한 안전한 테마 스타일 주입
css_code = f"""
<style>
    .stApp {{
        background-color: {theme['bg']};
        color: #f1f5f9;
    }}
    .dynamic-header {{
        font-family: 'Arial', sans-serif;
        color: {theme['accent']};
        text-shadow: 0 0 10px {theme['accent']};
        font-weight: 800;
    }}
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {theme['accent']};
        border-radius: 10px;
        padding: 15px;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {theme['sub_accent']} !important;
        font-weight: bold;
    }}
    div[data-testid="stMetricValue"] {{
        color: {theme['accent']} !important;
    }}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 메인 화면 출력
# -----------------------------------------------------------------------------
st.markdown(f"<h1 class='dynamic-header'>{theme['icon']} TODAY'S BOX OFFICE</h1>", unsafe_allow_html=True)
st.caption(f"🎨 **현재 맞춤 테마:** {theme['name']} (1위 영화 기반 자동 변경)")

# 순위 변환 서식
def format_rank_change(row):
    inten = row["rankInten"]
    if row.get("rankOldAndNew") == "NEW":
        return "🆕 NEW"
    elif inten > 0:
        return f"
