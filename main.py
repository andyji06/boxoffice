import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# -----------------------------------------------------------------------------
# 0. 아이언맨 (J.A.R.V.I.S.) 테마 및 스타일 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STARK BOX OFFICE HUB", layout="wide", page_icon="🤖")

# 커스텀 CSS (아이언맨 다크 테마: 골드 & 글루미 네온 레드/블루)
st.markdown("""
<style>
    /* 전체 배경 및 폰트 스타일 */
    .stApp {
        background-color: #0b0e14;
        color: #e0e6ed;
    }
    /* 타이틀 레전드 스타일 */
    .stark-header {
        font-family: 'Courier New', monospace;
        color: #ff3333;
        text-shadow: 0 0 10px #ff3333, 0 0 20px #e6b800;
        font-weight: 800;
        letter-spacing: 1.5px;
    }
    /* 카드 / 메트릭 컨테이너 스타일 */
    div[data-testid="stMetric"] {
        background: rgba(225, 29, 72, 0.08);
        border: 1px solid #ff3333;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 10px rgba(255, 51, 51, 0.2);
    }
    div[data-testid="stMetricLabel"] {
        color: #e6b800 !important;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-family: 'Consolas', monospace;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='stark-header'>🤖 STARK CINEMATIC BOX OFFICE</h1>", unsafe_allow_html=True)
st.caption("J.A.R.V.I.S. 프로토콜 분석 시스템: 영화진흥위원회(KOBIS) 연동")

# -----------------------------------------------------------------------------
# 1. 사이드바 - 날짜 선택 및 데이터 다운로드
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

st.sidebar.header("⚙️ CONTROL PANEL")

# 날짜 선택기
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
# 2. API Key 확인 및 불러오기
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "⚠️ **PROD API KEY NOT FOUND**\n\n"
        "Streamlit Cloud의 **Secrets** 메뉴에 `KOBIS_KEY`를 설정해 주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 요청 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # 캐싱으로 빠른 로딩 제공
def fetch_box_office(api_key, target_date, multi_stat=None):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": target_date,
    }
    if multi_stat:
        params["multiStatGb"] = multi_stat  # N: 상업, Y: 다양성(독립)

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

data = fetch_box_office(api_key, target_date_str)

# 에러 검증
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

# 정수형 변환
int_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in int_cols:
    df[col] = df[col].astype(int)

# 순위 변환 텍스트
def format_rank_change(row):
    inten = row["rankInten"]
    is_new = row.get("rankOldAndNew") == "NEW"
    
    if is_new:
        return "🆕 NEW"
    elif inten > 0:
        return f"🔺 {inten}"
    elif inten < 0:
        return f"🔹 {abs(inten)}"
    else:
        return "-"

df["순위변동"] = df.apply(format_rank_change, axis=1)

# 트로피(100만 이상) 아이콘 붙이기
df["표시영화명"] = df.apply(
    lambda r: f"{r['movieNm']} 🏆" if r["audiAcc"] >= 1_000_000 else r["movieNm"], 
    axis=1
)

# -----------------------------------------------------------------------------
# 5. 메인 레이아웃 (1위 영화 & 지표)
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.markdown(f"### ⚡ TOP TARGET: <span style='color:#e6b800;'>{top_1['표시영화명']}</span>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("일일 관객수", f"{top_1['audiCnt']:,} 명")
col2.metric("누적 관객수", f"{top_1['audiAcc']:,} 명")
col3.metric("스크린 수", f"{top_1['scrnCnt']:,} 개")
col4.metric("상영 횟수", f"{top_1['showCnt']:,} 회")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 상위 5편 막대 차트
# -----------------------------------------------------------------------------
st.subheader("📊 상위 5개 작품 일일 관객 수")
top_5_df = df.head(5)[["movieNm", "audiCnt"]].set_index("movieNm")
top_5_df.columns = ["일일 관객수"]
st.bar_chart(top_5_df, color="#ff3333")

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 박스오피스 데이터표 & 선택 상세 분석
# -----------------------------------------------------------------------------
st.subheader("📋 전체 박스오피스 리스트")

display_df = df[["rank", "순위변동", "표시영화명", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "변동", "영화명", "개봉일", "일일관객", "누적관객", "스크린수"]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(format="%d위"),
        "일일관객": st.column_config.NumberColumn(format="%d명"),
        "누적관객": st.column_config.NumberColumn(format="%d명"),
        "스크린수": st.column_config.NumberColumn(format="%d개"),
    }
)

# 데이터 다운로드 버튼 (사이드바)
csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
st.sidebar.download_button(
    label="📥 CSV 데이터 다운로드",
    data=csv_data,
    file_name=f"kobis_boxoffice_{target_date_str}.csv",
    mime="text/csv"
)

# -----------------------------------------------------------------------------
# 8. 영화 상세 정보 조회를 위한 검색 링크
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔎 영화 검색 및 상세 탐색")
selected_movie = st.selectbox("상세 정보를 검색할 영화를 선택하세요:", df["movieNm"].tolist())

if selected_movie:
    search_url = f"https://search.naver.com/search.naver?query=영화+{selected_movie}"
    st.markdown(f"👉 **[{selected_movie}]** 정보 검색하기: [네이버 검색 열기]({search_url})")
