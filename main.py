import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="일별 박스오피스", layout="wide", page_icon="🎬")

# -----------------------------------------------------------------------------
# 0. 커스텀 CSS (1위 영화 히어로 카드를 위한 스타일링)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* 1위 히어로 배너 스타일 */
    .hero-container {
        background: linear-gradient(135deg, #1f1c2c 0%, #928DAB 100%);
        border: 2px solid #FFD700;
        border-radius: 16px;
        padding: 28px 24px;
        box-shadow: 0 10px 25px rgba(255, 215, 0, 0.25);
        color: #FFFFFF;
        margin-bottom: 25px;
        text-align: center;
    }
    .hero-badge {
        background-color: #FFD700;
        color: #111111;
        font-weight: 800;
        font-size: 0.95rem;
        padding: 6px 16px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 12px;
        letter-spacing: 1px;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 10px 0;
        text-shadow: 0 0 12px rgba(255, 215, 0, 0.6);
        color: #FFFFFF;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #FFE57F;
        font-weight: 600;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎬 일별 박스오피스 조회")
st.write("영화진흥위원회(KOBIS) API를 활용한 일별 박스오피스 순위 서비스입니다.")

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

# -----------------------------------------------------------------------------
# 4. API 응답 에러 검증 (faultInfo 응답 처리)
# -----------------------------------------------------------------------------
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
    st.
