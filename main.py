import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/happykth/data/main/kobis_movies.csv"

st.set_page_config(page_title="영화 데이터 그래프 도감 2", page_icon="🎬", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_URL)

    # 개봉일: 여덟 자리 숫자(예: 20240131) -> 날짜
    df["openDt"] = pd.to_datetime(df["openDt"].astype(str), format="%Y%m%d", errors="coerce")

    # 장르: 세로막대(|)로 여러 개 적힌 경우 첫 번째 장르만 사용
    df["genre_main"] = (
        df["genre"]
        .fillna("미분류")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
        .replace("", "미분류")
    )
    return df


st.title("영화 데이터 그래프 도감 2 - 분포와 관계")
st.caption("1년간 박스오피스 10위권에 든 영화 가운데 이 기간에 개봉한 영화의 요약표를 바탕으로 합니다.")

try:
    movies = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

st.write(f"불러온 영화: **{len(movies):,}편**")

# ---------------------------------------------------------------
# 구역 1. 장르별 영화 편수 (도넛 그래프)
# ---------------------------------------------------------------
st.divider()
st.header("1. 장르별 영화 편수")

genre_counts = movies["genre_main"].value_counts().reset_index()
genre_counts.columns = ["장르", "편수"]

fig_genre = go.Figure(
    go.Pie(
        labels=genre_counts["장르"],
        values=genre_counts["편수"],
        hole=0.5,
        sort=False,  # 이미 편수 순으로 정렬되어 있음
        textinfo="label+percent",
        hovertemplate="%{label}<br>%{value}편 (%{percent})<extra></extra>",
    )
)
fig_genre.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    legend_title_text="장르",
    annotations=[
        dict(text=f"총 {len(movies)}편", x=0.5, y=0.5, font_size=20, showarrow=False)
    ],
)
st.plotly_chart(fig_genre, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 다음 구역이 들어갈 자리 (그래프를 추가할 때 아래 형식을 복사해 쓰세요)
# ---------------------------------------------------------------
# st.divider()
# st.header("2. 제목")
# st.plotly_chart(fig, use_container_width=True)
# st.markdown("**이 그래프로 알 수 있는 것**")
# st.info("여기에 한 문장을 적어 주세요.")
