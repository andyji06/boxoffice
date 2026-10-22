import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="일별 박스오피스", layout="wide")

st.title("🎬 일별 박스오피스 조회")
st.write("영화진흥위원회(KOBIS) API를 활용한 일별 박스오피스 순위입니다.")

# -----------------------------------------------------------------------------
# 1. 날짜 선택기 (한국 시간 기준 최대 '어제'까지만 선택 가능)
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz).date()
yesterday = now_kst - datetime.timedelta(days=1)

# 달력에서 조회할 날짜 선택 (기본값: 어제, 선택 가능 최대일: 어제)
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (오늘 날짜는 아직 집계 전입니다):",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1)  # KOBIS 데이터 제공 시작일 근처
)

target_date_str = selected_date.strftime("%Y%m%d")  # API용 YYYYMMDD 포맷
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"🔍 현재 조회 기준일: **{display_date_str}**")

# -----------------------------------------------------------------------------
# 2. Streamlit Secrets에서 API 키 불러오기
# -----------------------------------------------------------------------------
api_key = st.secrets.get("KOBIS_KEY")

if not api_key:
    st.error(
        "⚠️ **API 키를 찾을 수 없습니다.**\n\n"
        "Streamlit Cloud의 **App Settings > Secrets** 메뉴에서 아래와 같이 API 키를 등록했는지 확인해 주세요.\n"
        "```toml\n"
        'KOBIS_KEY = "발급받은_인증키"\n'
        "```"
    )
    st.stop()

# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 요청
# -----------------------------------------------------------------------------
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
params = {
    "key": api_key,
    "targetDt": target_date_str,
}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error(
        f"⚠️ **KOBIS API 서버 연결에 실패했습니다.**\n\n"
        f"- 인터넷 연결 상태나 네트워크 환경을 확인해 주세요.\n"
        f"- 상세 오류 내용: `{e}`"
    )
    st.stop()

# -----------------------------------------------------------------------------
# 4. API 응답 에러 검증 (faultInfo 응답 처리)
# -----------------------------------------------------------------------------
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
    st.error(
        f"⚠️ **KOBIS API 인증 오류가 발생했습니다.**\n\n"
        f"- 오류 메시지: `{fault_msg}`\n"
        f"- `.streamlit/secrets.toml` 또는 Streamlit Cloud의 **Secrets**에 입력된 `KOBIS_KEY`값이 정확한지 확인해 주세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 5. 박스오피스 데이터 존재 여부 확인
# -----------------------------------------------------------------------------
boxoffice_result = data.get("boxOfficeResult", {})
daily_list = boxoffice_result.get("dailyBoxOfficeList", [])

# 데이터가 비어 있을 때 요구사항 반영
if not daily_list:
    st.warning(f"⚠️ **{display_date_str}**: 그날은 아직 집계 전입니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리 및 요구사항 서식 적용
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# 숫자로 변환
df["rank"] = df["rank"].astype(int)
df["rankInten"] = df["rankInten"].astype(int)
df["audiCnt"] = df["audiCnt"].astype(int)
df["audiAcc"] = df["audiAcc"].astype(int)
df["scrnCnt"] = df["scrnCnt"].astype(int)

# 순위 증감(rankInten) 화살표 처리 함수
def format_rank_change(inten):
    if inten > 0:
        return f"🔺 {inten}"
    elif inten < 0:
        return f"🔹 {abs(inten)}"
    else:
        return "-"

df["rankChange"] = df["rankInten"].apply(format_rank_change)

# 누적관객 100만 명 이상 영화명에 트로피(🏆) 이모지 붙이기
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1_000_000:
        return f"{title} 🏆"
    return title

df["displayMovieNm"] = df.apply(format_movie_title, axis=1)

# -----------------------------------------------------------------------------
# 7. 1위 영화 주요 지표 카드 (Metrics)
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.subheader(f"🥇 1위: {top_1['displayMovieNm']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="일일 관객수",
        value=f"{top_1['audiCnt']:,} 명"
    )
with col2:
    st.metric(
        label="누적 관객수",
        value=f"{top_1['audiAcc']:,} 명"
    )
with col3:
    st.metric(
        label="스크린 수",
        value=f"{top_1['scrnCnt']:,} 개"
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 관객수 상위 5편 막대그래프
# -----------------------------------------------------------------------------
st.subheader("📊 관객수 상위 5개 영화")

top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()
top_5_df.rename(columns={"movieNm": "영화명", "audiCnt": "일일 관객수"}, inplace=True)

# 차트 출력을 위한 인덱스 지정
top_5_df.set_index("영화명", inplace=True)
st.bar_chart(top_5_df)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 전체 박스오피스 순위표 (데이터프레임 출력)
# -----------------------------------------------------------------------------
st.subheader("📋 일별 박스오피스 전체 순위")

# 화면 표시용 컬럼 추출 및 순서 정렬
display_df = df[["rank", "rankChange", "displayMovieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "순위변동", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

# 천 단위 콤마 서식 및 포맷팅을 적용하여 표 출력
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(format="%d위"),
        "관객수": st.column_config.NumberColumn(format="%d명"),
        "누적관객": st.column_config.NumberColumn(format="%d명"),
        "스크린수": st.column_config.NumberColumn(format="%d개"),
    }
)
