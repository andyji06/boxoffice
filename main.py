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
    
    /* 기본 텍스트, 라벨, 캐션 글자색을 하얀색/밝은 톤으로 보정 */
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
        color: #FFE57F;
        font-weight: 600;
    }

    /* Metric 카드 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #161A23 !important;
        border: 1px solid #2A2F3D !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetricLabel"] label {
        color: #AAAAAA !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #FFD700 !important;
        font-weight: 700 !important;
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
# 2. Streamlit Secrets에서 API 키 불러오기 및 유효성 검사
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.warning(
        "⚠️ **API 키가 등록되지 않았습니다.**\n\n"
        "1. **Local 실행 시**: 프로젝트 폴더 내 `.streamlit/secrets.toml` 파일에 아래와 같이 추가해주세요.\n"
        "```toml\n"
        'KOBIS_KEY = "발급받은_인증키"\n'
        "```\n"
        "2. **Streamlit Cloud 대시보드**: 우측 하단 **Manage app > Settings > Secrets** 메뉴에 키를 저장해주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 캐싱 및 요청 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # 1시간 캐싱
def fetch_daily_boxoffice(key: str, target_dt: str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": target_dt}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

try:
    data = fetch_daily_boxoffice(api_key, target_date_str)
except Exception as e:
    st.error(f"⚠️ **KOBIS API 서버 연결 실패:** `{e}`")
    st.stop()

# -----------------------------------------------------------------------------
# 4. API 응답 에러 검증
# -----------------------------------------------------------------------------
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
    st.error(f"⚠️ **KOBIS API 인증 오류:** `{fault_msg}` (등록된 KOBIS_KEY를 확인하세요)")
    st.stop()

# -----------------------------------------------------------------------------
# 5. 박스오피스 데이터 존재 여부 확인
# -----------------------------------------------------------------------------
boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.info(f"ℹ️ **{display_date_str}**: 해당 날짜는 집계 전이거나 데이터가 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

def format_rank_change(row):
    if row.get("rankOldAndNew") == "NEW":
        return "✨ NEW"
    inten = row["rankInten"]
    if inten > 0:
        return f"🔺 {inten}"
    elif inten < 0:
        return f"🔹 {abs(inten)}"
    else:
        return "-"

df["rankChange"] = df.apply(format_rank_change, axis=1)

def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1_000_000:
        return f"{title} 🏆"
    return title

df["displayMovieNm"] = df.apply(format_movie_title, axis=1)

# -----------------------------------------------------------------------------
# 7. 👑 1위 영화 히어로 카드
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.balloons()

audi_acc = top_1["audiAcc"]
if audi_acc >= 10_000_000:
    milestone_tag = "💎 1,000만 관객 돌파 대
