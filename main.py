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
        basic_cols = ['kaptCode', 'kaptName', 'kaptAddr', 'kaptUsedate', 'kaptdaCnt', 'kaptTarea', 'kaptTopFloor', 'codeAptNm', 'codeHeatNm', 'kaptBcompany']
        df_basic = pd.read_csv('apt_basic.csv', usecols=lambda c: c in basic_cols)
    except Exception:
        df_basic = pd.DataFrame(columns=['kaptCode'])
        
    # Load detail info
    try:
        detail_cols = ['kaptCode', 'kaptName', 'kaptdPcnt', 'kaptdPcntu', 'subwayLine', 'subwayStation', 'kaptdWtimesub']
        df_detail = pd.read_csv('apt_detail.csv', usecols=lambda c: c in detail_cols, low_memory=False)
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
            return 1
        # Check for longest match first to handle e.g. '디에이치' vs '디에이치 아너힐즈' (if we had longer brands)
        # Sort brands by length descending
        sorted_brands = sorted(brand_dict.keys(), key=len, reverse=True)
        for brand in sorted_brands:
            if brand in name:
                return brand_dict[brand]
        return 1 # Default score

    df['brand_score'] = df['kaptName'].apply(calculate_brand_score)

    # Load override data
    try:
        sub_override = pd.read_csv('apt_subway_override.csv')
        df = pd.merge(df, sub_override, on='kaptCode', how='left')
    except Exception:
        pass

    # Load school data
    try:
        school_data = pd.read_csv('apt_school_mapped.csv')
        df = pd.merge(df, school_data, on='kaptCode', how='left')
    except Exception:
        pass

    try:
        sub_df = pd.read_csv('subway_score.csv', encoding='utf-8')
        subway_weights = dict(zip(sub_df['subwayLine'], sub_df['weight']))
    except:
        subway_weights = {}

    def calculate_station_score(row):
        time_str = row.get('kaptdWtimesub', None)
        subways = str(row.get('subwayLine', ''))

        base_score = 1
        if 'subwayDist' in row and pd.notna(row['subwayDist']):
            dist = float(row['subwayDist'])
            if dist <= 250:
                base_score = 5 # 5분이내
            elif dist <= 500:
                base_score = 4 # 10분이내
            elif dist <= 750:
                base_score = 3 # 15분이내
            elif dist <= 1000:
                base_score = 2 # 20분이내
            else:
                base_score = 1
        else:
            mapping = {
                '5분이내': 5,
                '5~10분이내': 4,
                '10~15분이내': 3,
                '15~20분이내': 2
            }
            base_score = mapping.get(time_str, 1) if pd.notna(time_str) else 1

        multiplier = 1.0
        if subways and subways != 'nan':
            lines = [l.strip() for l in subways.split(',')]
            weights = [subway_weights.get(l, 1.0) for l in lines]
            if weights:
                multiplier = max(weights)
        
        return base_score * multiplier

    df['station_score'] = df.apply(calculate_station_score, axis=1)

    def calculate_school_score(row):
        dist = row.get('schul_dstnc')
        if pd.isna(dist):
            return 1
        dist = float(dist)
        if dist <= 250:
            return 5
        elif dist <= 500:
            return 4
        elif dist <= 750:
            return 3
        elif dist <= 1000:
            return 2
        else:
            return 1

    df['school_score'] = df.apply(calculate_school_score, axis=1)

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
    
    def get_city(addr):
        if pd.isna(addr) or not isinstance(addr, str): return "알수없음"
        parts = addr.split()
        if len(parts) >= 1:
            return parts[0]
        return "알수없음"

    def get_gu(addr):
        if pd.isna(addr) or not isinstance(addr, str): return "알수없음"
        parts = addr.split()
        if len(parts) >= 2:
            return parts[1]
        return "알수없음"
    
    df['city'] = df['kaptAddr'].apply(get_city)
    df['district'] = df['kaptAddr'].apply(get_gu)

    # Load area and price data
    try:
        df_p = pd.read_csv('apt_price_mapped.csv', usecols=['kaptCode', 'exclusive_area', 'min_price', 'max_price'])
        df_p['exclusive_area'] = pd.to_numeric(df_p['exclusive_area'], errors='coerce')
        df_p['min_price'] = pd.to_numeric(df_p['min_price'], errors='coerce')
        df_p['max_price'] = pd.to_numeric(df_p['max_price'], errors='coerce')
        
        df_area_cln = df_p.dropna(subset=['exclusive_area'])
        agg_area = df_area_cln.groupby('kaptCode')['exclusive_area'].agg(['unique', 'min', 'max']).reset_index()
        agg_area.rename(columns={'unique': 'areas', 'min': 'min_area', 'max': 'max_area'}, inplace=True)
        agg_area['areas'] = agg_area['areas'].apply(lambda x: sorted(list(x)))
        df = pd.merge(df, agg_area, on='kaptCode', how='left')

        df_price_cln = df_p.dropna(subset=['min_price', 'max_price'])
        agg_price = df_price_cln.groupby('kaptCode').agg({'min_price': 'min', 'max_price': 'max'}).reset_index()
        agg_price['min_price'] = agg_price['min_price'] / 100000000.0
        agg_price['max_price'] = agg_price['max_price'] / 100000000.0
        df = pd.merge(df, agg_price, on='kaptCode', how='left')
        
        # area-price pairs for linked filtering
        df_ap_cln = df_p.dropna(subset=['exclusive_area', 'max_price']).copy()
        df_ap_cln['price_억원'] = df_ap_cln['max_price'] / 100000000.0
        agg_ap = df_ap_cln.groupby('kaptCode').apply(
            lambda x: list(zip(x['exclusive_area'], x['price_억원'])),
            include_groups=False
        ).reset_index(name='area_price_list')
        df = pd.merge(df, agg_ap, on='kaptCode', how='left')
    except Exception:
        pass # Leave areas/price columns out if file not found
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# Sidebar
st.sidebar.title("🔍 Filters")

cities = sorted(df['city'].unique())
selected_cities = st.sidebar.multiselect("시/도", cities, default=None)

# District options depend on selected cities
if selected_cities:
    available_districts_df = df[df['city'].isin(selected_cities)]
else:
    available_districts_df = df

districts = sorted(available_districts_df['district'].unique())
selected_districts = st.sidebar.multiselect("행정구역 (구/군)", districts, default=None)

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

SLIDER_MAX_UNIT = 2000

unit_range = st.sidebar.slider(
    f"세대 수 범위 (최대 선택 시 {SLIDER_MAX_UNIT}세대 이상)",
    min_value=0,
    max_value=SLIDER_MAX_UNIT,
    value=(0, SLIDER_MAX_UNIT),
    step=50
)

if 'min_area' in df.columns and not df['min_area'].dropna().empty:
    min_a = int(df['min_area'].dropna().min())
    max_a = int(df['max_area'].dropna().max())
else:
    min_a, max_a = 0, 300

if 'area_range' not in st.session_state:
    st.session_state.area_range = (min_a, max_a)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 전용면적 빠른 선택")
col_area_1, col_area_2 = st.sidebar.columns(2)
col_area_3, col_area_4 = st.sidebar.columns(2)
col_area_5, col_area_6 = st.sidebar.columns(2)

if col_area_1.button("전체", width="stretch"):
    st.session_state.area_range = (min_a, max_a)
if col_area_2.button("초소형 (~40㎡)", width="stretch"):
    st.session_state.area_range = (min_a, 40)
if col_area_3.button("소형 (40~50㎡)", width="stretch"):
    st.session_state.area_range = (40, 50)
if col_area_4.button("중소형 (50~60㎡)", width="stretch"):
    st.session_state.area_range = (50, 60)
if col_area_5.button("중형 (60~85㎡)", width="stretch"):
    st.session_state.area_range = (60, 85)
if col_area_6.button("대형 (85㎡~)", width="stretch"):
    st.session_state.area_range = (85, max_a)

area_range = st.sidebar.slider(
    "전용면적 직접 선택 (㎡)",
    min_a,
    max_a,
    key="area_range"
)

SLIDER_MAX_PRICE = 50.0

if 'min_price' in df.columns and not df['min_price'].dropna().empty:
    min_p = float(df['min_price'].dropna().min())
    max_p = SLIDER_MAX_PRICE
else:
    min_p, max_p = 0.0, SLIDER_MAX_PRICE

if 'price_range' not in st.session_state:
    st.session_state.price_range = (min_p, max_p)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 공시가격 빠른 선택")
col_price_1, col_price_2, col_price_3 = st.sidebar.columns(3)

if col_price_1.button("전체", key="btn_p_all", width="stretch"):
    st.session_state.price_range = (min_p, max_p)
if col_price_2.button("6억 이하", key="btn_p_6", help="장기주택저당차입금 이자상환액 소득공제 기준", width="stretch"):
    st.session_state.price_range = (min_p, min(6.0, max_p))
if col_price_3.button("12억 이하", key="btn_p_12", help="종합부동산세 비과세 기준", width="stretch"):
    st.session_state.price_range = (min_p, min(12.0, max_p))

price_range = st.sidebar.slider(
    f"공시가격 직접 선택 (최대 선택 시 {SLIDER_MAX_PRICE}억원 이상)",
    float(min_p),
    float(max_p),
    key="price_range",
    step=0.1
)

st.sidebar.markdown("---")
# Subway Line Filter
if 'subwayLine' in df.columns:
    all_subway_lines = set()
    for item in df['subwayLine'].dropna():
        for line in str(item).split(','):
            all_subway_lines.add(line.strip())
    sorted_subway_lines = sorted(list(all_subway_lines))
else:
    sorted_subway_lines = []

selected_subway_lines = st.sidebar.multiselect("지하철 호선", sorted_subway_lines, default=None)

st.sidebar.markdown("---")
school_options = ["전체", "도보 0m (완전 초품아)", "도보 250m 이내", "도보 500m 이내", "도보 750m 이내", "도보 1km 이내"]
selected_school_dist = st.sidebar.selectbox("초등학교 도보 거리 (초품아)", school_options, index=0)

# Filter data
filtered_df = df.copy()
if selected_cities:
    filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
if selected_districts:
    filtered_df = filtered_df[filtered_df['district'].isin(selected_districts)]
filtered_df = filtered_df[(filtered_df['built_year'] >= year_range[0]) & (filtered_df['built_year'] <= year_range[1])]

if unit_range[1] >= SLIDER_MAX_UNIT:
    filtered_df = filtered_df[filtered_df['kaptdaCnt'] >= unit_range[0]]
else:
    filtered_df = filtered_df[(filtered_df['kaptdaCnt'] >= unit_range[0]) & (filtered_df['kaptdaCnt'] <= unit_range[1])]

is_area_filtered = 'areas' in df.columns and (area_range[0] > min_a or area_range[1] < max_a)
is_price_filtered = 'min_price' in df.columns and (price_range[0] > min_p or price_range[1] < max_p)
effective_price_max = float('inf') if price_range[1] >= max_p else price_range[1]

if is_area_filtered or is_price_filtered:
    def check_conditions(row):
        if 'area_price_list' in row and isinstance(row['area_price_list'], list):
            ap_list = row['area_price_list']
            if len(ap_list) == 0:
                return False
                
            # Filter by area first
            matching_ap = []
            for area, price in ap_list:
                if area_range[0] <= area <= area_range[1]:
                    matching_ap.append((area, price))
                    
            if not matching_ap:
                return False
                
            # Find max price for each matched area
            area_max_prices = {}
            for area, price in matching_ap:
                if area not in area_max_prices or price > area_max_prices[area]:
                    area_max_prices[area] = price
                    
            if is_price_filtered:
                if not is_area_filtered:
                    overall_max_price = max(area_max_prices.values()) if area_max_prices else 0
                    return price_range[0] <= overall_max_price <= effective_price_max
                
                for max_price in area_max_prices.values():
                    if price_range[0] <= max_price <= effective_price_max:
                        return True
                return False
                
            return True
            
        else:
            a_ok_overall = True
            p_ok_overall = True
            
            if is_area_filtered:
                areas = row.get('areas')
                if isinstance(areas, list):
                    a_ok_overall = any(area_range[0] <= a <= area_range[1] for a in areas)
                else:
                    a_ok_overall = False
                    
            if is_price_filtered:
                max_p_val = row.get('max_price')
                if not is_area_filtered:
                    if pd.notna(max_p_val):
                        p_ok_overall = (price_range[0] <= max_p_val <= effective_price_max)
                    else:
                        p_ok_overall = False
                else:
                    min_p_val = row.get('min_price')
                    if pd.notna(min_p_val) and pd.notna(max_p_val):
                        p_ok_overall = not (max_p_val < price_range[0] or min_p_val > effective_price_max)
                    else:
                        p_ok_overall = False
                    
            return a_ok_overall and p_ok_overall

    filtered_df = filtered_df[filtered_df.apply(check_conditions, axis=1)]

if selected_subway_lines and 'subwayLine' in df.columns:
    def has_selected_subway(subway_str, selected_lines):
        if pd.isna(subway_str) or not isinstance(subway_str, str): return False
        apartment_lines = [l.strip() for l in subway_str.split(',')]
        # Check if any selected line is in the apartment's connected lines
        return any(line in apartment_lines for line in selected_lines)
    
    filtered_df = filtered_df[filtered_df['subwayLine'].apply(lambda x: has_selected_subway(x, selected_subway_lines))]

if selected_school_dist != "전체" and 'schul_dstnc' in df.columns:
    dist_map = {
        "도보 0m (완전 초품아)": 0,
        "도보 250m 이내": 250,
        "도보 500m 이내": 500,
        "도보 750m 이내": 750,
        "도보 1km 이내": 1000
    }
    max_dist = dist_map.get(selected_school_dist, 10000)
    filtered_df = filtered_df[pd.to_numeric(filtered_df['schul_dstnc'], errors='coerce') <= max_dist]

# Buy me a coffee button (Sidebar Footer)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<a href="https://www.buymeacoffee.com/kimbndt" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" >
</a>
<br><br>
<span style="font-size: 0.8em; color: gray;">불쌍한 개발자에게 도움을!</span>
""", unsafe_allow_html=True)

# Main Dashboard
st.title("🏢 아파트 상세 데이터 분석 대시보드")
st.markdown("""
**데이터 소스:**
- **공공데이터포털**: 아파트 목록 및 상세 정보 (API)
- **국토교통부**: 주택 공시가격 정보
- **국가교통 데이터 오픈마켓**: 역세권 실거래 및 초등학교 도보통학권 정보
- **자체 데이터**: 브랜드 점수 및 지하철 노선 가중치
""")

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
tab1, tab2, tab3, tab4 = st.tabs(["🎯 아파트 비교", "📅 연도별 준공 현황", "🏢 단지 규모 현황", "📄 필터링 데이터 목록"])

with tab1:
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
                if value >= valid.max():
                    return 100.0
                return round((valid < value).sum() / len(valid) * 100, 1)

            age_pct = percentile_rank(df['built_year'], selected['built_year'])
            unit_pct = percentile_rank(df['kaptdaCnt'], selected['kaptdaCnt'])
            parking_ratio = (selected['kaptdPcnt'] + selected['kaptdPcntu']) / selected['kaptdaCnt'] if selected['kaptdaCnt'] > 0 else 0
            parking_pct = percentile_rank(df['parking_per_unit'], parking_ratio)
            brand_pct = percentile_rank(df['brand_score'], selected['brand_score'])
            station_pct = percentile_rank(df['station_score'], selected['station_score'])
            school_pct = percentile_rank(df['school_score'], selected['school_score'])

            built_year_display = int(selected['built_year']) if not pd.isna(selected['built_year']) else '정보없음'
            unit_display = int(selected['kaptdaCnt']) if selected['kaptdaCnt'] > 0 else '정보없음'
            unit_display_str = f"{unit_display:,}세대" if isinstance(unit_display, int) else str(unit_display)
            
            if 'subwayStation' in selected and pd.notna(selected['subwayStation']) and 'subwayDist' in selected and pd.notna(selected['subwayDist']):
                station_time = f"{selected['subwayStation']} ({int(selected['subwayDist'])}m)"
            else:
                station_time = selected['kaptdWtimesub'] if not pd.isna(selected['kaptdWtimesub']) else '정보없음'
            subway_line_str = str(selected['subwayLine']) if 'subwayLine' in selected and pd.notna(selected['subwayLine']) else ""
            if subway_line_str.lower() == 'nan' or not subway_line_str.strip():
                subway_line_str = ""
            station_display = f"{station_time} ({subway_line_str})" if subway_line_str else station_time

            areas_str = "정보없음"
            if 'areas' in selected and isinstance(selected['areas'], list) and len(selected['areas']) > 0:
                areas_str = ", ".join([f"{a:g}㎡" for a in selected['areas']])
                if len(selected['areas']) > 5:
                    areas_str = ", ".join([f"{a:g}㎡" for a in selected['areas'][:5]]) + " ..."

            price_str = "정보없음"
            if 'min_price' in selected and not pd.isna(selected['min_price']):
                if selected['min_price'] == selected['max_price']:
                    price_str = f"{selected['min_price']:.1f}억원"
                else:
                    price_str = f"{selected['min_price']:.1f}억 ~ {selected['max_price']:.1f}억원"

            school_display = "정보없음"
            if 'schul_nm' in selected and pd.notna(selected['schul_nm']) and 'schul_dstnc' in selected and pd.notna(selected['schul_dstnc']):
                school_display = f"{selected['schul_nm']} ({int(selected['schul_dstnc'])}m)"

            st.markdown(f"""
            <div style="background:#ffffff; border-radius:12px; padding:20px; border:1px solid #e2e8f0;
                        box-shadow:0 4px 6px -1px rgba(0,0,0,0.07); margin-bottom:24px;">
                <h3 style="margin:0 0 8px 0; color:#0f172a;">{selected['kaptName']}</h3>
                <p style="margin:0; color:#64748b; font-size:0.95rem;">{selected.get('kaptAddr', '')}</p>
                <div style="display:flex; gap:24px; margin-top:14px; flex-wrap:wrap;">
                    <span style="color:#0ea5e9; font-weight:600;">📅 준공: {built_year_display}년</span>
                    <span style="color:#f43f5e; font-weight:600;">🏠 세대수: {unit_display_str}</span>
                    <span style="color:#8b5cf6; font-weight:600;">📐 면적: {areas_str}</span>
                    <span style="color:#eab308; font-weight:600;">💰 공시가: {price_str}</span>
                    <span style="color:#6366f1; font-weight:600;">🏆 브랜드 점수: {selected['brand_score']}점</span>
                    <span style="color:#10b981; font-weight:600;">🚇 역세권: {station_display}</span>
                    <span style="color:#ec4899; font-weight:600;">🏫 초품아: {school_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            categories = ['연식 (신축도)', '세대 수', '세대당 주차대수', '브랜드 점수', '역세권 점수', '초품아 점수']
            values = [age_pct, unit_pct, parking_pct, brand_pct, station_pct, school_pct]

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

            st.plotly_chart(fig_radar, width="stretch")

            st.markdown("#### 📊 백분위 상세")
            total_parking = int(selected['kaptdPcnt'] + selected['kaptdPcntu'])
            parking_ratio_display = f"{parking_ratio:.2f}대/세대" if parking_ratio > 0 else '정보없음'
            pct_data = {
                '지표': categories,
                '해당 아파트 값': [
                    f"{built_year_display}년",
                    f"{unit_display:,}세대" if isinstance(unit_display, int) else str(unit_display),
                    parking_ratio_display,
                    f"{selected['brand_score']}점",
                    station_display,
                    school_display
                ],
                '백분위': [f"{v:.1f}%" for v in values]
            }
            st.dataframe(pd.DataFrame(pct_data), width="stretch", hide_index=True)
            with st.expander("📄 원본 데이터 보기"):
                st.markdown("선택된 아파트의 원본 데이터 상세 정보입니다.")
                # Transpose the data to make it easier to read column by column
                selected_df = selected.to_frame(name='값').reset_index().rename(columns={'index': '항목'})
                st.dataframe(selected_df, width="stretch", hide_index=True)

    else:
        st.info("아파트 단지명을 입력하면 백분위 레이더 차트가 표시됩니다.")

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
        st.plotly_chart(fig_year, width="stretch")
    else:
        st.info("준공 연도 데이터가 없습니다.")

# Data Table
with tab3:
    st.subheader("🏢 단지 규모 분포 (세대수별 아파트 수)")
    if not filtered_df.empty and 'kaptdaCnt' in filtered_df.columns:
        valid_df = filtered_df[filtered_df['kaptdaCnt'] > 0]
        
        if not valid_df.empty:
            st.markdown("### 💡 Fun fact")
            
            # Calculate facts
            largest_apt = valid_df.loc[valid_df['kaptdaCnt'].idxmax()]
            smallest_apt = valid_df.loc[valid_df['kaptdaCnt'].idxmin()]
            
            median_units = valid_df['kaptdaCnt'].median()
            median_apt = valid_df.iloc[(valid_df['kaptdaCnt'] - median_units).abs().argsort()[:1]].iloc[0]
            
            u_col1, u_col2, u_col3 = st.columns(3)
            
            with u_col1:
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">👑 가장 큰 단지</p>
                    <h4 style="margin: 0; color: #1e293b;">{largest_apt['kaptName']}</h4>
                    <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(largest_apt['kaptdaCnt']):,} 세대</p>
                </div>
                """, unsafe_allow_html=True)
                
            with u_col2:
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #f59e0b; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">🐣 가장 작은 단지</p>
                    <h4 style="margin: 0; color: #1e293b;">{smallest_apt['kaptName']}</h4>
                    <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(smallest_apt['kaptdaCnt']):,} 세대</p>
                </div>
                """, unsafe_allow_html=True)
                
            with u_col3:
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #6366f1; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="margin-bottom: 5px; color: #64748b; font-size: 0.8rem; font-weight: 600;">⚖️ 중간 규모 단지</p>
                    <h4 style="margin: 0; color: #1e293b;">{median_apt['kaptName']}</h4>
                    <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9rem;">{int(median_apt['kaptdaCnt']):,} 세대</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

        # Create bins for better visualization of unit counts
        bins = [0, 200, 500, 1000, 2000, 3000, max(filtered_df['kaptdaCnt'].max(), 3000)+1]
        labels = ['200세대 이하', '200~500세대', '500~1000세대', '1000~2000세대', '2000~3000세대', '3000세대 이상']
        
        filtered_df['unit_group'] = pd.cut(filtered_df['kaptdaCnt'], bins=bins, labels=labels, right=False)
        unit_counts = filtered_df['unit_group'].value_counts().reindex(labels)
        
        fig_units = px.bar(
            x=unit_counts.index,
            y=unit_counts.values,
            labels={'x': '세대수 구간', 'y': '아파트 수 (단지)'},
            template="plotly_white",
            color_discrete_sequence=['#10b981']
        )
        
        fig_units.update_layout(
            xaxis_title="세대수 구간",
            yaxis_title="아파트 수",
            bargap=0.2,
            margin=dict(t=40, b=40, l=40, r=40)
        )
        
        # Add labels on top of bars
        fig_units.update_traces(texttemplate='%{y}', textposition='outside')
        
        st.plotly_chart(fig_units, width="stretch")
    else:
        st.info("세대수 데이터를 표시할 수 없습니다.")

with tab4:
    st.subheader("📄 필터링된 데이터 목록")
    st.markdown("현재 사이드바 필터 조건에 해당하는 아파트 데이터 전체 목록입니다.")
    cols_to_show = ['kaptName', 'built_year', 'kaptdaCnt', 'codeAptNm', 'district', 'kaptAddr', 'kaptBcompany']
    available_cols = [c for c in cols_to_show if c in filtered_df.columns]
    
    st.dataframe(filtered_df[available_cols], width="stretch", hide_index=True)

st.markdown("""
---
Created by Antigravity 🚀
""")
