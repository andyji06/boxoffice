    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# API 함수
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_daily_boxoffice(api_key: str, target_dt: str) -> dict:
    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )
    response = requests.get(
        url, params={"key": api_key, "targetDt": target_dt}, timeout=15
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_tmdb_movie(movie_title: str, tmdb_key: str) -> dict:
    """TMDB에서 포스터/줄거리/예고편 정보를 찾습니다."""
    search_url = "https://api.themoviedb.org/3/search/movie"
    response = requests.get(
        search_url,
        params={
            "api_key": tmdb_key,
            "query": movie_title,
            "language": "ko-KR",
            "include_adult": "false",
        },
        timeout=12,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return {}
    # 검색어와 제목이 가까운 결과를 우선 사용
    exact = next(
        (
            item for item in results
            if item.get("title", "").strip().lower() == movie_title.strip().lower()
        ),
        results[0],
    )
    details_url = f"https://api.themoviedb.org/3/movie/{exact['id']}"
    details_response = requests.get(
        details_url,
        params={"api_key": tmdb_key, "language": "ko-KR", "append_to_response": "videos"},
        timeout=12,
    )
    details_response.raise_for_status()
    return details_response.json()


def youtube_search_url(title: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(title + ' 공식 예고편')}"


# ---------------------------------------------------------
# 상단 헤더
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">YOUR DAILY MOVIE GUIDE</div>
      <h1>🎬 CINEMA BOX</h1>
      <p>오늘의 영화 트렌드를 발견하고, 포스터와 예고편까지 한 곳에서 만나보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 사이드바 / 날짜 선택
# ---------------------------------------------------------
kst_tz = pytz.timezone("Asia/Seoul")
today_kst = datetime.datetime.now(kst_tz).date()
yesterday = today_kst - datetime.timedelta(days=1)

with st.sidebar:
    st.markdown("## 🎞️ CINEMA BOX")
    st.caption("DAILY BOX OFFICE")
    st.markdown("---")
    selected_date = st.date_input(
        "📅 조회 날짜",
        value=yesterday,
        min_value=datetime.date(2004, 1, 1),
        max_value=yesterday,
        help="박스오피스는 집계가 완료된 날짜만 조회할 수 있어 오늘 날짜는 선택할 수 없습니다.",
    )
    st.markdown("---")
    st.markdown("### ✨ 이용 안내")
    st.caption("• 관객수 순위는 KOBIS 데이터를 사용합니다.")
    st.caption("• 포스터와 예고편은 TMDB API 키가 있으면 표시됩니다.")
    st.caption("• TMDB 키가 없어도 유튜브 예고편 검색은 사용할 수 있습니다.")
    st.markdown("---")
    st.caption("Made for movie lovers 🍿")

target_date = selected_date.strftime("%Y%m%d")
display_date = selected_date.strftime("%Y년 %m월 %d일")
st.caption(f"📍 조회 기준일: **{display_date}**")

# Secrets: KOBIS_KEY 필수, TMDB_KEY 선택
api_key = st.secrets.get("KOBIS_KEY", "")
tmdb_key = st.secrets.get("TMDB_KEY", "")

if not api_key:
    st.error(
        "KOBIS API 키를 찾을 수 없습니다. Streamlit Cloud의 **App settings → Secrets**에 "
        "`KOBIS_KEY = \"발급받은_인증키\"`를 등록해 주세요."
    )
    st.stop()

try:
    with st.spinner("박스오피스 데이터를 불러오는 중입니다..."):
        data = fetch_daily_boxoffice(api_key, target_date)
except requests.RequestException as exc:
    st.error(f"KOBIS 서버에 연결하지 못했습니다. 네트워크 또는 API 상태를 확인해 주세요.\n\n상세 정보: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {exc}")
    st.stop()

if "faultInfo" in data:
    fault = data["faultInfo"].get("message", "알 수 없는 API 오류")
    st.error(f"KOBIS API 오류: {fault}\n\n`KOBIS_KEY`가 올바른지 확인해 주세요.")
    st.stop()

daily_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
if not daily_list:
    st.warning(f"{display_date}의 박스오피스 데이터가 없거나 아직 집계되지 않았습니다.")
    st.stop()

df = pd.DataFrame(daily_list)
for col in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

def rank_change(row):
    if row.get("rankOldAndNew") == "NEW":
        return "✨ NEW"
    change = int(row["rankInten"])
    if change > 0:
        return f"▲ {change}"
    if change < 0:
        return f"▼ {abs(change)}"
    return "—"

df["순위변동"] = df.apply(rank_change, axis=1)
df["표시영화명"] = df.apply(
    lambda row: f"{row['movieNm']} 🏆" if row["audiAcc"] >= 1_000_000 else row["movieNm"],
    axis=1,
)

# ---------------------------------------------------------
# 요약 지표
# ---------------------------------------------------------
