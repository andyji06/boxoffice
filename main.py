import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="어제의 박스오피스", layout="wide")

st.title("🎬 어제의 박스오피스")
st.write("영화진흥위원회(KOBIS) API를 활용한 일별 박스오피스 순위입니다.")

# -----------------------------------------------------------------------------
# 1. 한국 시간(KST) 기준 어제 날짜 계산 (배포 서버 시계 차이 해결)
# -----------------------------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz)
yesterday = now_kst - datetime.timedelta(days=1)
target_date_str = yesterday.strftime("%Y%m%d")  # YYYYMMDD 포맷
display_date_str = yesterday.strftime("%Y년 %m월 %d일")

st.caption(f"📅 기준일: **{display_date_str}**")

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
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # HTTP status가 200이 아닐 경우 예외 발생
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

if not daily_list:
    st.warning(
        f"⚠️ **{display_date_str}의 박스오피스 데이터가 비어 있습니다.**\n\n"
        "- 아직 영화진흥위원회에서 집계를 마치지 않았거나 데이터 준비 중일 수 있습니다.\n"
        "- 잠시 후 다시 시도해 보세요."
    )
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리 (문자열 -> 숫자 변환)
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

# API 응답 숫자가 모두 문자열이므로 정수형(int)으로 변환
df["rank"] = df["rank"].astype(int)
df["audiCnt"] = df["audiCnt"].astype(int)
df["audiAcc"] = df["audiAcc"].astype(int)
df["scrnCnt"] = df["scrnCnt"].astype(int)

# -----------------------------------------------------------------------------
# 7. 1위 영화 주요 지표 카드 (Metrics)
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.subheader(f"🥇 1위: {top_1['movieNm']}")

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

# 화면 표시용 컬럼 추출 및 이름 변경
display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

# 천 단위 콤마(,) 서식 적용하여 표 출력
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
