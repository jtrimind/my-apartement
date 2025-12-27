import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Apartment Data Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #f8fafc;
    }
    /* Metric card styling - Light Mode */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    /* Label color - Darker for light mode */
    div[data-testid="stMetricLabel"] > div {
        color: #64748b !important;
        font-weight: 600;
        font-size: 0.9rem !important;
    }
    /* Value color - Dark blue/black for light mode */
    div[data-testid="stMetricValue"] > div {
        color: #1e293b !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    /* Header styling */
    h1, h2, h3 {
        color: #0f172a !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('apt_detail.csv')
    
    # Data Cleaning
    # Convert kaptUsedate to datetime (handle potential format issues)
    df['kaptUsedate'] = pd.to_datetime(df['kaptUsedate'], format='%Y%m%d', errors='coerce')
    df['built_year'] = df['kaptUsedate'].dt.year
    
    # Fill numeric NaNs
    df['kaptdaCnt'] = pd.to_numeric(df['kaptdaCnt'], errors='coerce').fillna(0)
    df['kaptTarea'] = pd.to_numeric(df['kaptTarea'], errors='coerce').fillna(0)
    df['kaptTopFloor'] = pd.to_numeric(df['kaptTopFloor'], errors='coerce').fillna(0)
    
    # Extract District (Gu) from kaptAddr
    def get_gu(addr):
        if pd.isna(addr): return "알수없음"
        parts = addr.split()
        if len(parts) >= 2:
            return parts[1]
        return "알수없음"
    
    df['district'] = df['kaptAddr'].apply(get_gu)
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# Sidebar
st.sidebar.title("🔍 Filters")
districts = sorted(df['district'].unique())
selected_districts = st.sidebar.multiselect("행정구역 (구)", districts, default=None)

year_range = st.sidebar.slider(
    "준공 연도 범위",
    int(df['built_year'].dropna().min()),
    int(df['built_year'].dropna().max()),
    (1980, 2025)
)

# Filter data
filtered_df = df.copy()
if selected_districts:
    filtered_df = filtered_df[filtered_df['district'].isin(selected_districts)]
filtered_df = filtered_df[(filtered_df['built_year'] >= year_range[0]) & (filtered_df['built_year'] <= year_range[1])]

# Main Dashboard
st.title("🏢 아파트 상세 데이터 분석 대시보드")
st.markdown("`apt_detail.csv` 데이터를 기반으로 한 종합 시각화 리포트입니다.")

# Row 1: Summary Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 아파트 수", f"{len(filtered_df):,} 개")
with col2:
    st.metric("평균 세대 수", f"{int(filtered_df['kaptdaCnt'].mean()) if not filtered_df.empty else 0:,} 세대")
with col3:
    if not filtered_df.empty:
        median_year = filtered_df['built_year'].median()
        current_year = datetime.now().year
        median_age = int(current_year - median_year)
        st.metric("연식 중앙값", f"{median_age} 년")
    else:
        st.metric("연식 중앙값", "N/A")

st.markdown("---")

# Row 2: Charts
tab1, tab2, tab3, tab4 = st.tabs(["🏠 아파트 유형", "📅 연도별 준공 현황", "🏗️ 건물 정보", "🏢 단지 규모"])

with tab1:
    st.subheader("🏠 아파트 유형 분포")
    type_counts = filtered_df['codeAptNm'].value_counts()
    fig_type = px.pie(
        values=type_counts.values, 
        names=type_counts.index, 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Safe,
        template="plotly_white"
    )
    st.plotly_chart(fig_type, use_container_width=True)

with tab2:
    st.subheader("📅 연도별 준공 현황")
    # Aggregate by year
    annual_stats = filtered_df.groupby('built_year').agg({
        'kaptName': 'count',
        'kaptdaCnt': 'sum'
    }).rename(columns={'kaptName': '아파트 수', 'kaptdaCnt': '세대 수'}).reset_index()

    fig_year = go.Figure()
    
    # Line for Apartment Count
    fig_year.add_trace(go.Scatter(
        x=annual_stats['built_year'], 
        y=annual_stats['아파트 수'],
        name='아파트 수',
        line=dict(color='#0ea5e9', width=3),
        mode='lines+markers'
    ))
    
    # Bar for Unit Count (Secondary axis)
    fig_year.add_trace(go.Bar(
        x=annual_stats['built_year'],
        y=annual_stats['세대 수'],
        name='세대 수',
        marker_color='rgba(244, 63, 94, 0.3)',
        yaxis='y2'
    ))

    fig_year.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="아파트 수", title_font=dict(color="#0ea5e9"), tickfont=dict(color="#0ea5e9"), rangemode='tozero'),
        yaxis2=dict(title="세대 수", title_font=dict(color="#f43f5e"), tickfont=dict(color="#f43f5e"), overlaying='y', side='right', showgrid=False, rangemode='tozero'),
        hovermode="x unified",
        margin=dict(t=30, b=0, l=0, r=0)
    )
    st.plotly_chart(fig_year, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🔥 난방 방식 분포")
        heat_counts = filtered_df['codeHeatNm'].value_counts()
        fig_heat = px.bar(
            x=heat_counts.index, 
            y=heat_counts.values,
            labels={'x': '난방 방식', 'y': '아파트 수'},
            color=heat_counts.index,
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with c2:
        st.subheader("⬆️ 최고 층수 분포")
        fig_floor = px.histogram(
            filtered_df, 
            x="kaptTopFloor", 
            nbins=30,
            template="plotly_white",
            color_discrete_sequence=['#6366f1']
        )
        fig_floor.update_layout(xaxis_title="층수", yaxis_title="건물 수")
        st.plotly_chart(fig_floor, use_container_width=True)

with tab4:
    st.subheader("🏗️ 주요 건설사별 아파트 수 (Top 20)")
    builder_counts = filtered_df['kaptBcompany'].value_counts().head(20)
    fig_builder = px.bar(
        y=builder_counts.index, 
        x=builder_counts.values,
        orientation='h',
        labels={'x': '아파트 수', 'y': '건설사'},
        template="plotly_white",
        color=builder_counts.values,
        color_continuous_scale='Blues'
    )
    fig_builder.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_builder, use_container_width=True)

# Data Table
with st.expander("📄 원본 데이터 보기"):
    st.dataframe(filtered_df[['kaptName', 'kaptAddr', 'codeAptNm', 'built_year', 'kaptdaCnt', 'kaptBcompany']])

st.markdown("""
---
Created by Antigravity 🚀
""")
