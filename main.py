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
# 0. 극장 시네마틱(Dark & Gold) 커스텀 CSS 테마
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* 앱 전체 배경 및 기본 글자 색상 */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* 헤더 및 메인 타이틀 커스텀 */
    h1 {
        color: #FFD700 !important;
        font-weight: 800 !important;
        text-shadow: 0px 0px 15px rgba(255, 215, 0, 0.4);
    }
    
    h2, h3 {
        color: #F5F5F5 !important;
    }

    /* 1위 히어로 배너 (시네마 골드 하이라이트) */
    .hero-container {
        background: linear-gradient(135deg, #1A1C29 0%, #0D0F18 100%);
        border: 2px solid #FFD700;
        border-radius: 16px;
        padding: 32px 24px;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.2);
        color: #FFFFFF;
        margin-bottom: 25px;
        text-align: center;
        position: relative;
        overflow: hidden;
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
        color: #FFE57F;
        font-weight: 600;
    }

    /* Metric 카드 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #161A23;
        border: 1px solid #2A2F3D;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #AAAAAA !important;
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎬 일별 박스오피스 조회")
st.write("영화진흥위원회(KOBIS) API 기반의 극장 순위 및 흥행 지표 정보 서비스입니다.")

# -----------------------------------------------------------------------------
# 1. 날짜 선택기 (한국 시간 기준 최대 '어제'까지만 선택 가능)
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (오늘 날짜는 아직 집계 전입니다):",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1),
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"🔍 현재 조회 기준일: **{display_date_str}**")

# -----------------------------------------------------------------------------
# 2. Streamlit Secrets에서 API 키 불러오기
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
    st.stop()

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 캐싱 및 요청 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # 1시간 동안 조회 결과 캐싱
def fetch_daily_boxoffice(key: str, target_dt: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": target_dt}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

try:
    data = fetch_daily_boxoffice(api_key, target_date_str)
except Exception as e:
    st.error(
        f"⚠️ **KOBIS API 서버 연결에 실패했습니다.**\n\n"
        f"- 상세 오류 내용: `{e}`"
    )
    st.stop()

# ----------------
