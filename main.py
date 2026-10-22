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
# 5. 🔥 1위 영화 장르에 따른 동적 테마(Dynamic Theme) 적용
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]
top_1_title = top_1["movieNm"]

# 1위 영화의 장르/이름 파악을 위한 텍스트 조건 검사
# KOBIS 데이터의 genreAlt 속성 활용 또는 제목 패턴 기반 자동 감지
genre_text = top_1.get("
