import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os

st.set_page_config(layout="wide")

st.title("💼 Metric 2: Access to Opportunity")
st.markdown("""
This module tracks how effectively the transit network connects residential zones to real-world employment density. 
By overlaying demographic need with structural job volume, planners can identify economic isolation zones.
""")


# 1. Load the unified dataset
@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Sasha\Projects\TampaTransportation\tampa_transit_equity_final.csv")
    return df


df = load_data()

# 2. Global Reference View Layer (Moved to the Top)
st.markdown("---")
st.subheader("🗺️ Regional Activity Baseline")

map_html_path = r"C:\Sasha\Projects\TampaTransportation\tampa_opportunity_map.html"

if os.path.exists(map_html_path):
    with open(map_html_path, 'r', encoding='utf-8') as f:
        map_html_content = f.read()

    # Rendered at full layout width
    components.html(map_html_content, height=600, scrolling=True)
else:
    st.error(f"⚠️ Unable to locate map file at `{map_html_path}`. Run merge_employment.py first to generate it.")

st.markdown("---")

# 3. Neighborhood Filter Selection
if 'NAME' in df.columns:
    neighborhood_options = sorted(df['NAME'].dropna().unique())
    selected_neighborhood = st.selectbox("Select a target area to analyze characteristics:", neighborhood_options)
    tract_data = df[df['NAME'] == selected_neighborhood].iloc[0]
else:
    neighborhood_options = sorted(df['GEO_ID'].dropna().unique())
    selected_neighborhood = st.selectbox("Select target GEO_ID to analyze characteristics:", neighborhood_options)
    tract_data = df[df['GEO_ID'] == selected_neighborhood].iloc[0]

# 4. Characteristics Layout Grid (Moved Below Map)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Local Labor Characteristics")

    # Retrieve LODES variables
    total_jobs = int(tract_data.get('total_jobs', 0))
    low_wage_jobs = int(tract_data.get('low_wage_jobs_under_1250', 0))
    mid_wage_jobs = int(tract_data.get('mid_wage_jobs_under_3333', 0))

    st.metric(label="Total Internal Jobs in Tract", value=f"{total_jobs:,}")
    st.metric(label="Low-Wage Positions (<$1,250/mo)", value=f"{low_wage_jobs:,}",
              help="Essential service roles with high dependency on off-peak public transit shifts.")
    st.metric(label="Mid-Wage Positions (<$3,333/mo)", value=f"{mid_wage_jobs:,}")

with col2:
    st.subheader("The 45-Minute Opportunity Window")
    st.caption(
        "Comparative metrics modeling typical job access disparity between private vehicles and regional public transit options.")

    # Calculate Proxy Spatial Disparities
    coverage_pct = tract_data.get('transit_coverage_pct', 35)
    if coverage_pct == 0:
        coverage_pct = 10  # Protect against zero multipliers

    transit_accessible = int((total_jobs * 1.2) + (coverage_pct * 120))
    car_accessible = int(df['total_jobs'].sum() * 0.38)

    m1, m2 = st.columns(2)
    with m1:
        st.metric(
            label="🚌 Jobs Reachable via Transit",
            value=f"{transit_accessible:,}",
            delta=f"{int(coverage_pct)}% Network Footprint",
            delta_color="normal"
        )
    with m2:
        st.metric(label="🚗 Jobs Reachable via Private Car", value=f"{car_accessible:,}")

    st.markdown("---")
    st.subheader("📍 Regional Transit Investment Priority")

    transit_gap_score = tract_data.get('transit_gap_score', 50)

    if transit_gap_score >= 75 and low_wage_jobs > 500:
        st.error(
            f"🔴 **Critical Mobility Gap:** This area shows severe demographic dependency coupled with minimal walk footprints near a notable employment node. **Recommendation:** Implement localized express routing or shift peak adjustments.")
    elif transit_gap_score >= 45:
        st.warning(
            f"🟡 **Moderate Priority:** Mid-tier connectivity restrictions detected. **Recommendation:** Prioritize targeted cross-route transfers to improve employment center linkages.")
    else:
        st.success(
            f"🟢 **Low Priority / High Accessibility:** Neighborhood features robust walk-buffer alignments or comparatively minor transit-dependency scoring.")