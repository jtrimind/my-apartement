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
    # Load basic info
    try:
        df_basic = pd.read_csv('apt_basic.csv')
    except Exception:
        df_basic = pd.DataFrame(columns=['kaptCode'])
        
    # Load detail info
    try:
        df_detail = pd.read_csv('apt_detail.csv')
    except Exception:
        df_detail = pd.DataFrame(columns=['kaptCode'])
        
    # Merge on kaptCode
    if not df_basic.empty and not df_detail.empty:
        df = pd.merge(df_basic, df_detail, on='kaptCode', how='outer', suffixes=('', '_detail'))
        if 'kaptName_detail' in df.columns:
            df['kaptName'] = df['kaptName'].fillna(df['kaptName_detail'])
            df.drop(columns=['kaptName_detail'], inplace=True)
    elif not df_basic.empty:
        df = df_basic
    else:
        df = df_detail

    if df.empty:
        return pd.DataFrame(columns=['kaptCode', 'kaptName', 'district', 'built_year'])

    # Load brand scores
    try:
        df_brand = pd.read_csv('apt_brand.csv')
        brand_dict = dict(zip(df_brand['brand_name'], df_brand['score']))
    except Exception:
        brand_dict = {}

    def calculate_brand_score(name):
        if pd.isna(name) or not isinstance(name, str):
            return 2
        # Check for longest match first to handle e.g. '디에이치' vs '디에이치 아너힐즈' (if we had longer brands)
        # Sort brands by length descending
        sorted_brands = sorted(brand_dict.keys(), key=len, reverse=True)
        for brand in sorted_brands:
            if brand in name:
                return brand_dict[brand]
        return 2 # Default score

    df['brand_score'] = df['kaptName'].apply(calculate_brand_score)

    # Ensure required columns exist
    required_columns = [
        'kaptUsedate', 'kaptdaCnt', 'kaptTarea', 'kaptTopFloor', 
        'kaptdPcnt', 'kaptdPcntu', 'kaptAddr', 'codeAptNm', 
        'codeHeatNm', 'kaptBcompany', 'kaptName'
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None

    # Data Cleaning
    df['kaptUsedate'] = pd.to_datetime(df['kaptUsedate'], format='%Y%m%d', errors='coerce')
    df['built_year'] = df['kaptUsedate'].dt.year
    
    numeric_cols = ['kaptdaCnt', 'kaptTarea', 'kaptTopFloor', 'kaptdPcnt', 'kaptdPcntu']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['parking_per_unit'] = df.apply(
        lambda r: (r['kaptdPcnt'] + r['kaptdPcntu']) / r['kaptdaCnt'] if r['kaptdaCnt'] > 0 else 0,
        axis=1
    )
    
    def get_gu(addr):
        if pd.isna(addr) or not isinstance(addr, str): return "알수없음"
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

# Handle cases where built_year might be all NaT
if df['built_year'].dropna().empty:
    min_year, max_year = 1980, 2025
else:
    min_year = int(df['built_year'].dropna().min())
    max_year = int(df['built_year'].dropna().max())

year_range = st.sidebar.slider(
    "준공 연도 범위",
    min_year,
    max_year,
    (min_year, max_year)
)

# Filter data
filtered_df = df.copy()
if selected_districts:
    filtered_df = filtered_df[filtered_df['district'].isin(selected_districts)]
filtered_df = filtered_df[(filtered_df['built_year'] >= year_range[0]) & (filtered_df['built_year'] <= year_range[1])]

# Main Dashboard
st.title("🏢 아파트 상세 데이터 분석 대시보드")
st.markdown("`apt_basic.csv` 및 `apt_detail.csv` 데이터를 기반으로 한 종합 시각화 리포트입니다.")

# Row 1: Summary Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 아파트 수", f"{len(filtered_df):,} 개")
with col2:
    st.metric("평균 세대 수", f"{int(filtered_df['kaptdaCnt'].mean()) if not filtered_df.empty else 0:,} 세대")
with col3:
    if not filtered_df.empty and not filtered_df['built_year'].isna().all():
        median_year = filtered_df['built_year'].median()
        current_year = datetime.now().year
        median_age = int(current_year - median_year)
        st.metric("연식 중앙값", f"{median_age} 년")
    else:
        st.metric("연식 중앙값", "N/A")

st.markdown("---")

# Row 2: Charts
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 아파트 유형", "📅 연도별 준공 현황", "🏗️ 건물 정보", "🏢 단지 규모", "🎯 아파트 비교"])

with tab1:
    st.subheader("🏠 아파트 유형 분포")
    if not filtered_df.empty and 'codeAptNm' in filtered_df.columns:
        type_counts = filtered_df['codeAptNm'].value_counts()
        fig_type = px.pie(
            values=type_counts.values, 
            names=type_counts.index, 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe,
            template="plotly_white"
        )
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("표시할 아파트 유형 데이터가 없습니다.")

with tab2:
    st.subheader("📅 연도별 준공 현황")
    
    if not filtered_df.empty and not filtered_df['built_year'].isna().all():
        st.markdown("### 💡 Fun fact")
        
        # Calculate facts
        oldest_apt = filtered_df.loc[filtered_df['built_year'].idxmin()]
        newest_apt = filtered_df.loc[filtered_df['built_year'].idxmax()]
        
        median_year = filtered_df['built_year'].median()
        median_apt = filtered_df.iloc[(filtered_df['built_year'] - median_year).abs().argsort()[:1]].iloc[0]
        
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #64748b; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">👴 가장 오래된 아파트</p>
                <h4 style="margin: 0; color: #1e293b;">{oldest_apt['kaptName']}</h4>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(oldest_apt['built_year'])}년 준공</p>
            </div>
            """, unsafe_allow_html=True)
            
        with f_col2:
            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #0ea5e9; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">👶 가장 새로운 아파트</p>
                <h4 style="margin: 0; color: #1e293b;">{newest_apt['kaptName']}</h4>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(newest_apt['built_year'])}년 준공</p>
            </div>
            """, unsafe_allow_html=True)
            
        with f_col3:
            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #f43f5e; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">⚖️ 중간의 아파트</p>
                <h4 style="margin: 0; color: #1e293b;">{median_apt['kaptName']}</h4>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(median_apt['built_year'])}년 준공</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        annual_stats = filtered_df.groupby('built_year').agg({
            'kaptName': 'count',
            'kaptdaCnt': 'sum'
        }).rename(columns={'kaptName': '아파트 수', 'kaptdaCnt': '세대 수'}).reset_index()

        fig_year = go.Figure()
        fig_year.add_trace(go.Scatter(
            x=annual_stats['built_year'], 
            y=annual_stats['아파트 수'],
            name='아파트 수',
            line=dict(color='#0ea5e9', width=3),
            mode='lines+markers'
        ))
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
    else:
        st.info("준공 연도 데이터가 없습니다.")

with tab3:
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🔥 난방 방식 분포")
        if not filtered_df.empty and 'codeHeatNm' in filtered_df.columns:
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
        if not filtered_df.empty:
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
    if not filtered_df.empty and 'kaptBcompany' in filtered_df.columns:
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
    cols_to_show = ['kaptName', 'kaptAddr', 'codeAptNm', 'built_year', 'kaptdaCnt', 'kaptBcompany']
    available_cols = [c for c in cols_to_show if c in filtered_df.columns]
    st.dataframe(filtered_df[available_cols])

# Tab 5: Radar Chart
with tab5:
    st.subheader("🎯 아파트 백분위 비교")
    st.markdown("단지명을 검색하면 해당 아파트가 **전체 데이터 대비 어느 백분위**에 위치하는지 레이더 차트로 확인할 수 있습니다.")

    search_query = st.text_input("🔍 아파트 단지명 검색", placeholder="예: 래미안, 자이, 힐스테이트 ...")

    if search_query:
        matched = df[df['kaptName'].str.contains(search_query, case=False, na=False)]
        if matched.empty:
            st.warning(f"'{search_query}'에 해당하는 아파트를 찾을 수 없습니다.")
        else:
            apt_names = matched['kaptName'].tolist()
            selected_name = st.selectbox("아파트 선택", apt_names)
            selected = matched[matched['kaptName'] == selected_name].iloc[0]

            def percentile_rank(series, value):
                valid = series.dropna()
                if len(valid) == 0 or pd.isna(value):
                    return 0
                return round((valid < value).sum() / len(valid) * 100, 1)

            age_pct = percentile_rank(df['built_year'], selected['built_year'])
            unit_pct = percentile_rank(df['kaptdaCnt'], selected['kaptdaCnt'])
            parking_ratio = (selected['kaptdPcnt'] + selected['kaptdPcntu']) / selected['kaptdaCnt'] if selected['kaptdaCnt'] > 0 else 0
            parking_pct = percentile_rank(df['parking_per_unit'], parking_ratio)
            brand_pct = percentile_rank(df['brand_score'], selected['brand_score'])

            built_year_display = int(selected['built_year']) if not pd.isna(selected['built_year']) else '정보없음'
            unit_display = int(selected['kaptdaCnt']) if selected['kaptdaCnt'] > 0 else '정보없음'
            unit_display_str = f"{unit_display:,}세대" if isinstance(unit_display, int) else str(unit_display)

            st.markdown(f"""
            <div style="background:#ffffff; border-radius:12px; padding:20px; border:1px solid #e2e8f0;
                        box-shadow:0 4px 6px -1px rgba(0,0,0,0.07); margin-bottom:24px;">
                <h3 style="margin:0 0 8px 0; color:#0f172a;">{selected['kaptName']}</h3>
                <p style="margin:0; color:#64748b; font-size:0.95rem;">{selected.get('kaptAddr', '')}</p>
                <div style="display:flex; gap:24px; margin-top:14px; flex-wrap:wrap;">
                    <span style="color:#0ea5e9; font-weight:600;">📅 준공: {built_year_display}년</span>
                    <span style="color:#f43f5e; font-weight:600;">🏠 세대수: {unit_display_str}</span>
                    <span style="color:#6366f1; font-weight:600;">🏆 브랜드 점수: {selected['brand_score']}점</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            categories = ['연식 (신축도)', '세대 수', '세대당 주차대수', '브랜드 점수']
            values = [age_pct, unit_pct, parking_pct, brand_pct]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=selected_name,
                line=dict(color='#0ea5e9', width=2),
                fillcolor='rgba(14, 165, 233, 0.2)',
                marker=dict(size=8, color='#0ea5e9')
            ))

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        ticksuffix='%',
                        tickfont=dict(size=11),
                        gridcolor='#e2e8f0',
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=13, color='#1e293b')
                    ),
                    bgcolor='#f8fafc'
                ),
                template='plotly_white',
                showlegend=False,
                margin=dict(t=40, b=40, l=60, r=60),
                height=420
            )

            st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown("#### 📊 백분위 상세")
            total_parking = int(selected['kaptdPcnt'] + selected['kaptdPcntu'])
            parking_ratio_display = f"{parking_ratio:.2f}대/세대" if parking_ratio > 0 else '정보없음'
            pct_data = {
                '지표': categories,
                '해당 아파트 값': [
                    f"{built_year_display}년",
                    f"{unit_display:,}세대" if isinstance(unit_display, int) else str(unit_display),
                    parking_ratio_display,
                    f"{selected['brand_score']}점"
                ],
                '백분위': [f"{v:.1f}%" for v in values]
            }
            st.dataframe(pd.DataFrame(pct_data), use_container_width=True, hide_index=True)
    else:
        st.info("아파트 단지명을 입력하면 백분위 레이더 차트가 표시됩니다.")

st.markdown("""
---
Created by Antigravity 🚀
""")
