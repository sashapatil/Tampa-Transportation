import streamlit as st
import pandas as pd

st.title("🛠️ Infrastructure Scenario Simulator")
st.markdown("""
This predictive planning module models the regional impact of targeted transit network investments. 
Select a neighborhood and choose a proposal to see the simulated shift in employment access.
""")


# Load the master dataset for local calculations
@st.cache_data
def load_data():
    return pd.read_csv(r"C:\Sasha\Projects\TampaTransportation\tampa_transit_equity_final.csv")


df = load_data()

# 1. Neighborhood Selectbox Setup
total_jobs = 0
coverage_pct = 35.0
transit_gap_score = 50.0

if 'community_name' in df.columns:
    neighborhood_options = sorted(df['community_name'].dropna().unique())
    selected_neighborhood = st.selectbox("Select a target area to run simulations on:", neighborhood_options)

    community_tracts = df[df['community_name'] == selected_neighborhood]

    total_jobs = int(community_tracts.get('total_jobs', pd.Series([0])).sum())
    coverage_pct = float(community_tracts.get('transit_coverage_pct', pd.Series([35.0])).mean())
    transit_gap_score = float(community_tracts.get('transit_gap_score', pd.Series([50.0])).mean())

    if pd.isna(coverage_pct): coverage_pct = 35.0
    if pd.isna(transit_gap_score): transit_gap_score = 50.0
else:
    fallback_key = 'GEOID_SHORT' if 'GEOID_SHORT' in df.columns else (
        'GEO_ID' if 'GEO_ID' in df.columns else df.columns[0])
    neighborhood_options = sorted(df[fallback_key].dropna().unique())
    selected_neighborhood = st.selectbox("Select target zone to run simulations on:", neighborhood_options)

    tract_data = df[df[fallback_key] == selected_neighborhood].iloc[0]
    total_jobs = int(tract_data.get('total_jobs', 0))
    coverage_pct = float(tract_data.get('transit_coverage_pct', 35.0))
    transit_gap_score = float(tract_data.get('transit_gap_score', 50.0))

# Calculate dynamic baseline numbers
transit_accessible = int((total_jobs * 1.2) + (coverage_pct * 120))

st.markdown("---")

# 2. Choose a Capital Investment Proposal (PLACED BEFORE THE IF-STATEMENTS)
proposal = st.selectbox(
    "Select a proposed transit intervention to simulate:",
    [
        "No Intervention (Baseline Grid)",
        "Proposal A: Urban-to-Suburban Job Corridor Express Line",
        "Proposal B: Suburban Last-Mile On-Demand Micro-Transit Shuttles",
        "Proposal C: Rural Shift-Worker Vanpool Pilot"
    ]
)

# 3. Establish baseline simulation modifiers
coverage_modifier = 1.0
job_multiplier = 1.2

if proposal == "Proposal A: Urban-to-Suburban Job Corridor Express Line":
    st.info("**🔧 Simulated Impact:** Expands regional transit access footprint by **+25%** for connected hubs.")
    if selected_neighborhood in ["East Tampa", "Brandon"]:
        coverage_modifier = 1.25
        job_multiplier = 1.60

elif proposal == "Proposal B: Suburban Last-Mile On-Demand Micro-Transit Shuttles":
    st.info(
        "**🔧 Simulated Impact:** Extends effective walking bounds, increasing neighborhood access footprint by **+15%**.")
    if selected_neighborhood in ["Riverview", "Brandon", "Town 'n' Country"]:
        coverage_modifier = 1.15
        job_multiplier = 1.35

elif proposal == "Proposal C: Rural Shift-Worker Vanpool Pilot":
    st.info("**🔧 Simulated Impact:** Overcomes physical walk-buffer baselines for isolated labor hubs by **+10%**.")
    if selected_neighborhood in ["Wimauma", "Balm", "Rural Hillsborough"]:
        coverage_modifier = 1.10
        job_multiplier = 1.25

# 4. Run Modifier Calculations
simulated_coverage = min(int(coverage_pct * coverage_modifier), 100)
simulated_transit_accessible = int((total_jobs * job_multiplier) + (simulated_coverage * 120))

# 5. Display Comparisons
st.subheader(f"📊 Simulated Impact Metrics: {selected_neighborhood}")
sim_col1, sim_col2 = st.columns(2)

with sim_col1:
    st.metric(
        label="🚌 Jobs Reachable via Transit",
        value=f"{simulated_transit_accessible:,}",
        delta=f"{simulated_transit_accessible - transit_accessible:+,} Jobs Unlocked" if simulated_transit_accessible != transit_accessible else None
    )

with sim_col2:
    st.metric(
        label="🚶 Effective Transit Walk Coverage",
        value=f"{simulated_coverage}%",
        delta=f"{simulated_coverage - int(coverage_pct):+} % Points" if proposal != "No Intervention (Baseline Grid)" else None
    )