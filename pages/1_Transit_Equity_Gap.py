# pages/1_Transit_Equity_Gap.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Transit Equity Gap", layout="wide")

st.title("📍 Metric 1: The Transit Equity Gap")
st.write("Identifying neighborhoods where social need heavily outweighs physical transit footprint.")

# --- SECTION 1: FULL-WIDTH INTERACTIVE MAP ---
st.markdown("### Interactive Map")

try:
    with open("tampa_transit_equity_map.html", 'r', encoding='utf-8') as f:
        html_data = f.read()

    # Removing columns here lets the map expand to the full width of the dashboard
    components.html(html_data, height=700, scrolling=True)

except FileNotFoundError:
    st.error("Could not find 'tampa_transit_equity_map.html'. Please make sure it's in the project root.")

st.markdown("---")

# --- SECTION 2: NEIGHBORHOOD SEARCH & PROFILE (UNDER MAP) ---
st.markdown("### 📋 Neighborhood Deep-Dive")

try:
    df = pd.read_csv("tampa_transit_equity_final.csv")

    neighborhoods = sorted(df['community_name'].dropna().unique())
    selected = st.selectbox("Select a Community Focus Area to inspect:", neighborhoods)

    # Filter and calculate metrics
    sub_df = df[df['community_name'] == selected]
    avg_gap = sub_df['transit_gap_score'].mean()
    avg_no_veh = sub_df['pct_no_vehicle'].mean()
    avg_pov = sub_df['pct_below_poverty'].mean()

    # Present metrics in a clean, multi-column row underneath the map
    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(label="Average Mobility Gap Score", value=f"{avg_gap:.1f}/100")
    with m2:
        st.metric(label="No Vehicle Available", value=f"{avg_no_veh:.1f}%", delta="Households")
    with m3:
        st.metric(label="Living Below Poverty Line", value=f"{avg_pov:.1f}%", delta="Population")

except FileNotFoundError:
    st.info("Run your main processing script to populate the 'tampa_transit_equity_final.csv' profile stats here.")