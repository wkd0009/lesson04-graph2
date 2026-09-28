import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

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
# 구역 2. 장르 안의 영화별 총 관객 (트리맵)
# ---------------------------------------------------------------
st.divider()
st.header("2. 장르별 영화 총 관객 트리맵")

tree_df = movies.dropna(subset=["total_audi"])
tree_df = tree_df[tree_df["total_audi"] > 0]

fig_tree = px.treemap(
    tree_df,
    path=[px.Constant("전체"), "genre_main", "movieNm"],
    values="total_audi",
)
fig_tree.update_traces(
    hovertemplate="%{label}<br>총 관객 %{value:,}명<extra></extra>",
    textinfo="label",
)
fig_tree.update_layout(margin=dict(t=20, b=20, l=20, r=20))
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 구역 3. 총 관객 히스토그램
# ---------------------------------------------------------------
st.divider()
st.header("3. 총 관객 분포 (히스토그램)")

audi = movies.dropna(subset=["total_audi"])
NBINS = 30
lo, hi = float(audi["total_audi"].min()), float(audi["total_audi"].max())
bin_size = (hi - lo) / NBINS

fig_hist = px.histogram(
    audi,
    x="total_audi",
    nbins=NBINS,
    labels={"total_audi": "총 관객(명)", "count": "영화 편수"},
)
# 아래 문구에서 계산하는 구간과 그래프의 막대 구간을 똑같이 맞춤
fig_hist.update_traces(xbins=dict(start=lo, end=hi, size=bin_size))
fig_hist.update_layout(
    xaxis_title="총 관객(명)",
    yaxis_title="영화 편수",
    bargap=0.05,
    margin=dict(t=20, b=20, l=20, r=20),
)
st.plotly_chart(fig_hist, use_container_width=True)

# 가장 많은 영화가 몰려 있는 구간
counts, edges = np.histogram(audi["total_audi"], bins=NBINS, range=(lo, hi))
peak = int(counts.argmax())
peak_lo, peak_hi = edges[peak], edges[peak + 1]
peak_n = int(counts[peak])
peak_share = peak_n / len(audi) * 100

# 총 관객이 가장 많은 영화
top = audi.loc[audi["total_audi"].idxmax()]

st.markdown("**이 그래프로 알 수 있는 것**")
st.info(
    f"영화가 가장 많이 몰린 구간은 총 관객 {peak_lo:,.0f}명 ~ {peak_hi:,.0f}명으로 "
    f"{peak_n}편({peak_share:.1f}%)이고, "
    f"관객이 가장 많은 영화는 '{top['movieNm']}'({top['total_audi']:,.0f}명)입니다."
)

# ---------------------------------------------------------------
# 구역 4. 개봉일 스크린수와 총 관객 (산점도)
# ---------------------------------------------------------------
st.divider()
st.header("4. 개봉일 스크린수와 총 관객의 관계")

scatter_df = movies.dropna(subset=["first_scrn", "total_audi"])

fig_scatter = px.scatter(
    scatter_df,
    x="first_scrn",
    y="total_audi",
    color="genre_main",
    hover_name="movieNm",  # 마우스를 올리면 영화명이 맨 위에 보임
    hover_data={
        "genre_main": False,
        "first_scrn": ":,",
        "total_audi": ":,",
    },
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객(명)",
        "genre_main": "장르",
    },
)
fig_scatter.update_traces(marker=dict(size=9, opacity=0.8))
fig_scatter.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text="장르")
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 구역 5. 장르별 총 관객 (박스플롯, 10편 이상인 장르만)
# ---------------------------------------------------------------
st.divider()
st.header("5. 장르별 총 관객 분포 (상자 그림)")
st.caption("영화가 10편 이상인 장르만 보여 줍니다.")

box_df = movies.dropna(subset=["total_audi"])
box_counts = box_df["genre_main"].value_counts()
box_genres = box_counts[box_counts >= 10].index.tolist()  # 편수 많은 순
box_df = box_df[box_df["genre_main"].isin(box_genres)]

fig_box = px.box(
    box_df,
    x="genre_main",
    y="total_audi",
    color="genre_main",
    points="outliers",  # 상자 밖으로 튀는 점만 표시
    hover_name="movieNm",  # 튀는 점에 마우스를 올리면 영화명이 보임
    hover_data={"genre_main": False, "total_audi": ":,"},
    category_orders={"genre_main": box_genres},
    labels={"genre_main": "장르", "total_audi": "총 관객(명)"},
)
fig_box.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
st.plotly_chart(fig_box, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 구역 6. 스크린수·총 관객·첫 주 관객 (버블 그래프)
# ---------------------------------------------------------------
st.divider()
st.header("6. 스크린수와 총 관객, 첫 주 관객까지 (버블 그래프)")
st.caption("4번 산점도에 점 크기(첫 주 관객)를 더한 그래프입니다.")

bubble_df = movies.dropna(subset=["first_scrn", "total_audi", "first_week_audi"])
bubble_df = bubble_df[bubble_df["first_week_audi"] > 0]  # 크기는 0보다 커야 그릴 수 있음

fig_bubble = px.scatter(
    bubble_df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    size_max=45,
    color="genre_main",
    hover_name="movieNm",
    hover_data={
        "genre_main": False,
        "first_scrn": ":,",
        "total_audi": ":,",
        "first_week_audi": ":,",
    },
    labels={
        "first_scrn": "개봉일 스크린수(개)",
        "total_audi": "총 관객(명)",
        "first_week_audi": "첫 주 관객(명)",
        "genre_main": "장르",
    },
)
fig_bubble.update_traces(marker=dict(opacity=0.6, line=dict(width=0.5, color="white")))
fig_bubble.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text="장르")
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 구역 7. 제작 국가에서 장르로 (선버스트)
# ---------------------------------------------------------------
st.divider()
st.header("7. 제작 국가별 장르 구성 (선버스트)")
st.caption("안쪽 고리는 제작 국가, 바깥쪽 고리는 그 나라 영화의 장르예요. 칸의 크기는 영화 편수입니다.")

sun_df = movies.copy()
sun_df["nation"] = sun_df["nation"].fillna("미상").astype(str).str.strip().replace("", "미상")
sun_df["편수"] = 1  # 영화 한 편을 1로 세어 칸 크기로 씀

fig_sun = px.sunburst(
    sun_df,
    path=["nation", "genre_main"],
    values="편수",
)
fig_sun.update_traces(
    hovertemplate="%{label}<br>%{value}편<extra></extra>",
    textinfo="label",
)
fig_sun.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=650)
st.plotly_chart(fig_sun, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 구역 8. 월별 개봉 편수와 총 관객 (막대 + 선)
# ---------------------------------------------------------------
st.divider()
st.header("8. 어느 달에 개봉한 영화가 많고, 관객은 얼마나 들었을까?")

month_df = movies.dropna(subset=["openDt"]).copy()
month_df["개봉월"] = month_df["openDt"].dt.to_period("M")
monthly = month_df.groupby("개봉월").agg(
    편수=("movieCd", "count"),
    총관객=("total_audi", "sum"),
)
# 개봉작이 한 편도 없는 달도 0으로 채워서 빠짐없이 보여 줌
all_months = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M")
monthly = monthly.reindex(all_months, fill_value=0)
month_labels = monthly.index.astype(str)  # 예: 2026-03

fig_month = make_subplots(specs=[[{"secondary_y": True}]])
fig_month.add_trace(
    go.Bar(
        x=month_labels,
        y=monthly["편수"],
        name="개봉 편수",
        hovertemplate="%{x}<br>개봉 %{y}편<extra></extra>",
    ),
    secondary_y=False,
)
fig_month.add_trace(
    go.Scatter(
        x=month_labels,
        y=monthly["총관객"],
        name="총 관객 합계",
        mode="lines+markers",
        hovertemplate="%{x}<br>총 관객 합계 %{y:,}명<extra></extra>",
    ),
    secondary_y=True,
)
fig_month.update_xaxes(title_text="개봉월", type="category")
fig_month.update_yaxes(title_text="개봉 편수(편)", secondary_y=False)
fig_month.update_yaxes(title_text="총 관객 합계(명)", secondary_y=True)
fig_month.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    legend=dict(orientation="h", y=1.08, x=0),
)
st.plotly_chart(fig_month, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.info("여기에 한 문장을 적어 주세요.")

# ---------------------------------------------------------------
# 다음 구역이 들어갈 자리 (그래프를 추가할 때 아래 형식을 복사해 쓰세요)
# ---------------------------------------------------------------
# st.divider()
# st.header("9. 제목")
# st.plotly_chart(fig, use_container_width=True)
# st.markdown("**이 그래프로 알 수 있는 것**")
# st.info("여기에 한 문장을 적어 주세요.")
