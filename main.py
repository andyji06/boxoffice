import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 0. 페이지 기본 설정 및 스타일링
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="KOBIS 일별 박스오피스",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS로 약간의 여백 및 디자인 다듬기
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stMetric { background-color: #f8f9fa; padding: 12px; border-radius: 10px; border: 1px solid #e9ecef; }
    </style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 1. KOBIS API 데이터 캐싱 및 요청 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_daily_boxoffice(key: str, target_dt: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": target_dt}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# -----------------------------------------------------------------------------
# 2. 사이드바 - 날짜 선택 및 설정
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎬 박스오피스")
    st.caption("영화진흥위원회(KOBIS) API 연동")
    st.divider()

    kst_tz = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(kst_tz).date()
    yesterday = now_kst - datetime.timedelta(days=1)

    selected_date = st.date_input(
        label="📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        min_value=datetime.date(2004, 1, 1),
        help="오늘 날짜 데이터는 집계 전이므로 어제 날짜부터 조회 가능합니다.",
    )

    target_date_str = selected_date.strftime("%Y%m%d")
    display_date_str = selected_date.strftime("%Y년 %m월 %d일")

    st.info(f"📍 **조회 기준일**\n\n`{display_date_str}`")

# -----------------------------------------------------------------------------
# 3. API 키 검증
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "⚠️ **API 키를 찾을 수 없습니다.**\n\n"
        "`.streamlit/secrets.toml` 파일에 `KOBIS_KEY`를 설정해주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 4. 데이터 로드 및 에러 처리
# -----------------------------------------------------------------------------
try:
    data = fetch_daily_boxoffice(api_key, target_date_str)
except Exception as e:
    st.error(f"⚠️ **KOBIS API 서버 연결 실패**: `{e}`")
    st.stop()

if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
    st.error(f"⚠️ **KOBIS API 인증 오류**: `{fault_msg}`")
    st.stop()

boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(
        f"⚠️ **{display_date_str}**: 해당 날짜의 박스오피스 데이터가 존재하지 않습니다."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 5. 데이터 가공 (Data Processing)
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# 수치형 변환
numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# 순위 변환 서식
def format_rank_change(row):
    if row.get("rankOldAndNew") == "NEW":
        return "✨ NEW"
    inten = row["rankInten"]
    if inten > 0:
        return f"🔺 {inten}"
    elif inten < 0:
        return f"🔹 {abs(inten)}"
    return "-"


df["rankChange"] = df.apply(format_rank_change, axis=1)


# 천만/백만 관객 배지 표기
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >=
