
import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="CINEMA BOX OFFICE",
    layout="wide",
    page_icon="🎬"
)

# --------------------------------------------------
# 2. 디자인 테마
# --------------------------------------------------
st.markdown("""
<style>
/* 전체 배경 */
.stApp {
    background:
        radial-gradient(ellipse at top, #202b46 0%, transparent 55%),
        linear-gradient(135deg, #080b13, #11182a 55%, #080b13);
    color: #f3f5fa;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* 기본 글씨 */
p, label, li {
    color: #c6cede;
}

h1, h2, h3 {
    color: #ffffff !important;
}

h1 {
    font-weight: 900 !important;
    letter-spacing: -1.5px;
}

h2, h3 {
    font-weight: 800 !important;
}

/* 상단 영화관 배너 */
.hero {
    background: linear-gradient(120deg, #202a42, #111725 65%, #332817);
    border: 1px solid #4a422e;
    border-radius: 22px;
    padding: 30px;
    margin: 8px 0 25px 0;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.22);
}

.hero-label {
    color: #f5c451;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 4px;
}

.hero-title {
    color: #ffffff;
    font-size: clamp(27px, 4vw, 43px);
    font-weight: 900;
    margin-top: 10px;
    line-height: 1.25;
}

.hero-desc {
    color: #c0c9db;
    font-size: 15px;
    margin-top: 12px;
}

.gold {
    color: #f5c451;
}

/* 날짜 선택 */
div[data-testid="stDateInput"] input {
    background: #151d30 !important;
    color: white !important;
    border: 1px solid #39445e !important;
    border-radius: 10px !important;
}

/* 지표 카드 */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1d2940, #111827);
    border: 1px solid #34415c;
    border-radius: 17px;
    padding: 22px 20px;
    box-shadow: 0 7px 20px rgba(0, 0, 0, 0.15);
    transition: all 0.2s ease;
}

div[data-testid="stMetric"]:hover {
    border-color: #f5c451;
    transform: translateY(-3px);
}

div[data-testid="stMetricLabel"] {
    color: #b8c4da !important;
}

div[data-testid="stMetricValue"] {
    color: #f5c451 !important;
    font-weight: 850 !important;
}

/* 1위 영화 강조 카드 */
.movie-card {
    background: linear-gradient(120deg, #242d43, #141b2b);
    border: 1px solid #6b5730;
    border-radius: 18px;
    padding: 24px;
    margin: 12px 0 22px 0;
}

.movie-card-label {
    color: #f5c451;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
}

.movie-card-title {
    color: #ffffff;
    font-size: clamp(23px, 3vw, 34px);
    font-weight: 900;
    margin-top: 10px;
    overflow-wrap: anywhere;
}

.movie-card-info {
    color: #b8c4da;
    font-size: 14px;
    margin-top: 9px;
}

/* 섹션 제목 */
.section-heading {
    color: #f5c451;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 5px;
}

/* 표 */
div[data-testid="stDataFrame"] {
    border: 1px solid #34415c;
    border-radius: 13px;
    overflow: hidden;
}

/* 그래프 */
div[data-testid="stVegaLiteChart"],
div[data-testid="stArrowVegaLiteChart"] {
    background: #121a2b;
    border: 1px solid #303d56;
    border-radius: 16px;
    padding: 12px;
}

/* 버튼 */
.stButton > button {
    background: linear-gradient(100deg, #f5c451, #e7ad38);
    color: #101522;
    border: none;
    border-radius: 10px;
    font-weight: 800;
    min-height: 42px;
}

.stButton > button:hover {
    background: #ffdc80;
    color: #101522;
    border: none;
}

/* 알림 */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* 구분선 */
hr {
    border-color: #303a50 !important;
}

/* 하단 */
.footer {
    text-align: center;
    color: #7f8ba3;
    font-size: 12px;
    padding: 18px 0 5px 0;
    letter-spacing: 0.5px;
}

/* 모바일 화면 */
@media (max-width: 640px) {
    .block-container {
        padding: 1rem 1rem 2rem;
    }

    .hero {
        padding: 22px;
    }

    div[data-testid="stMetric"] {
        padding: 14px 12px;
    }
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 3. 상단 배너
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-label">CINEMA • DAILY CHART</div>
    <div class="hero-title">
        🎬 오늘의 영화,<br>
        <span class="gold">박스오피스 TOP 10</span>
    </div>
    <div class="hero-desc">
        대한민국 영화 흥행 순위와 관객수를 한눈에 확인하세요.
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 4. 날짜 선택
# --------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

st.markdown(
    '<div class="section-heading">📅 DATE SELECT</div>',
    unsafe_allow_html=True
)

selected_date = st.date_input(
    "조회할 날짜를 선택하세요",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1)
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"🔍 조회 기준일: {display_date_str}")

# --------------------------------------------------
# 5. API 키
# --------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "API 키를 찾을 수 없습니다. Streamlit Cloud의 "
        "App Settings → Secrets에 KOBIS_KEY를 등록해 주세요."
    )
    st.stop()

# --------------------------------------------------
# 6. API 데이터 요청
# --------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_daily_boxoffice(key: str, target_dt: str):
    url = (
        "https://www.kobis.or.kr/kobisopenapi/"
        "webservice/rest/boxoffice/"
        "searchDailyBoxOfficeList.json"
    )

    response = requests.get(
        url,
        params={"key": key, "targetDt": target_dt},
        timeout=15
    )
    response.raise_for_status()
    return response.json()


try:
    data = fetch_daily_boxoffice(api_key, target_date_str)

except requests.exceptions.Timeout:
    st.error("⏳ 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

except requests.exceptions.RequestException as e:
    st.error(f"⚠️ API 서버 연결 오류: {e}")
    st.stop()

except Exception as e:
    st.error(f"⚠️ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --------------------------------------------------
# 7. API 오류 및 데이터 확인
# --------------------------------------------------
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
    st.error(f"⚠️ KOBIS API 오류: {fault_msg}")
    st.stop()

boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(
        f"{display_date_str}에 해당하는 박스오피스 데이터가 없습니다."
    )
    st.stop()

# --------------------------------------------------
# 8. 데이터 전처리
# --------------------------------------------------
df = pd.DataFrame(daily_list)

numeric_cols = [
    "rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col], errors="coerce"
    ).fillna(0).astype(int)


def format_rank_change(row):
    if row.get("rankOldAndNew") == "NEW":
        return "✨ NEW"

    change = row["rankInten"]

    if change > 0:
        return f"🔺 {change}"
    elif change < 0:
        return f"🔻 {abs(change)}"
    return "—"


df["rankChange"] = df.apply(format_rank_change, axis=1)


def format_movie_title(row):
    title = row["movieNm"]

    if row["audiAcc"] >= 1_000_000:
        return f"{title} 🏆"

    return title


df["displayMovieNm"] = df.apply(format_movie_title, axis=1)

# --------------------------------------------------
# 9. 1위 영화 카드
# --------------------------------------------------
top_1 = df.iloc[0]

st.markdown(
    '<div class="section-heading">🏆 TODAY\'S NO.1</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="movie-card">
        <div class="movie-card-label">🥇 BOX OFFICE CHAMPION</div>
        <div class="movie-card-title">
            {top_1['displayMovieNm']}
        </div>
        <div class="movie-card-info">
            📅 기준일 {display_date_str}
            &nbsp; • &nbsp;
            🎞️ 개봉일 {top_1['openDt']}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🎟️ 일일 관객수",
        f"{top_1['audiCnt']:,}명"
    )

with col2:
    st.metric(
        "🏆 누적 관객수",
        f"{top_1['audiAcc']:,}명"
    )

with col3:
    st.metric(
        "📺 스크린 수",
        f"{top_1['scrnCnt']:,}개"
    )

st.markdown("---")

# --------------------------------------------------
# 10. 관객수 TOP 5 그래프
# --------------------------------------------------
st.markdown(
    '<div class="section-heading">📊 AUDIENCE RANKING</div>',
    unsafe_allow_html=True
)
st.subheader("관객수 TOP 5")
st.caption("선택한 날짜의 영화별 일일 관객수입니다.")

top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()

top_5_df.rename(
    columns={
        "movieNm": "영화명",
        "audiCnt": "일일 관객수"
    },
    inplace=True
)

top_5_df.set_index("영화명", inplace=True)
st.bar_chart(top_5_df)

st.markdown("---")

# --------------------------------------------------
# 11. 전체 순위표
# --------------------------------------------------
st.markdown(
    '<div class="section-heading">🎟️ FULL MOVIE CHART</div>',
    unsafe_allow_html=True
)
st.subheader("일별 박스오피스 전체 순위")

display_df = df[
    [
        "rank",
        "rankChange",
        "displayMovieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

display_df.columns = [
    "순위",
    "순위변동",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(
            format="%d위"
        ),
        "관객수": st.column_config.NumberColumn(
            format="%d명"
        ),
        "누적관객": st.column_config.NumberColumn(
            format="%d명"
        ),
        "스크린수": st.column_config.NumberColumn(
            format="%d개"
        )
    }
)

# --------------------------------------------------
# 12. 하단 안내
# --------------------------------------------------
st.markdown("---")

st.markdown("""
<div class="footer">
    🎬 CINEMA BOX OFFICE<br><br>
    DATA SOURCE · 영화진흥위원회 KOBIS Open API<br>
    매일 업데이트되는 영화 흥행 정보
</div>
""", unsafe_allow_html=True)
