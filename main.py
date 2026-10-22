import datetime

import requests

import pandas as pd

import pytz

import streamlit as st



# 페이지 제목 및 레이아웃 설정

st.set_page_config(page_title="일별 박스오피스", layout="wide", page_icon="🎬")



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

        "Streamlit Cloud의 **App Settings > Secrets** 메뉴 또는 local .streamlit/secrets.toml에 아래와 같이 등록했는지 확인해 주세요.\n"

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

        f"- 상세 오류 내용: {e}"

    )

    st.stop()



# -----------------------------------------------------------------------------

# 4. API 응답 에러 검증 (faultInfo 응답 처리)

# -----------------------------------------------------------------------------

if "faultInfo" in data:

    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")

    st.error(

        f"⚠️ **KOBIS API 인증 오류가 발생했습니다.**\n\n"

        f"- 오류 메시지: {fault_msg}\n"

        f"- 등록된 KOBIS_KEY값이 정확한지 확인해 주세요."

    )

    st.stop()



# -----------------------------------------------------------------------------

# 5. 박스오피스 데이터 존재 여부 확인

# -----------------------------------------------------------------------------

boxoffice_result = data.get("boxOfficeResult", {})

daily_list = boxoffice_result.get("dailyBoxOfficeList", [])



if not daily_list:

    st.warning(f"⚠️ **{display_date_str}**: 해당 날짜는 아직 집계 전이거나 데이터가 없습니다.")

    st.stop()



# -----------------------------------------------------------------------------

# 6. 데이터 전처리 및 서식 적용

# -----------------------------------------------------------------------------

df = pd.DataFrame(daily_list)



# 수치형 컬럼 변환

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]

for col in numeric_cols:

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)



# 순위 증감 및 NEW 표시 로직

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



# 누적관객 100만 명 이상 영화명에 트로피(🏆) 이모지 추가

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

    st.metric(label="일일 관객수", value=f"{top_1['audiCnt']:,} 명")

with col2:

    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")

with col3:

    st.metric(label="스크린 수", value=f"{top_1['scrnCnt']:,} 개")



st.markdown("---")



# -----------------------------------------------------------------------------

# 8. 관객수 상위 5편 막대그래프

# -----------------------------------------------------------------------------

st.subheader("📊 관객수 상위 5개 영화")



top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()

top_5_df.rename(columns={"movieNm": "영화명", "audiCnt": "일일 관객수"}, inplace=True)

top_5_df.set_index("영화명", inplace=True)



st.bar_chart(top_5_df)



st.markdown("---")



# -----------------------------------------------------------------------------

# 9. 전체 박스오피스 순위표 (데이터프레임 출력)

# -----------------------------------------------------------------------------

st.subheader("📋 일별 박스오피스 전체 순위")



display_df = df[["rank", "rankChange", "displayMovieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()

display_df.columns = ["순위", "순위변동", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]



st.dataframe(

    display_df,

    use_container_width=True,

    hide_index=True,

    column_config={

        "순위": st.column_config.NumberColumn(format="%d위"),

        "관객수": st.column_config.NumberColumn(format="%,d명"),

        "누적관객": st.column_config.NumberColumn(format="%,d명"),

        "스크린수": st.column_config.NumberColumn(format="%,d개"),

    },

)
