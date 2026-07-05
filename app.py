import streamlit as st

# 1. Point Streamlit to where your individual script files live
home_page = st.Page("pages/Summary.py", title="Executive Summary", icon="🏠")
equity_page = st.Page("pages/1_Transit_Equity_Gap.py", title="Metric 1: Transit Equity", icon="🗺️")
opp_page = st.Page("pages/2_Access_to_Opportunity.py", title="Metric 2: Opportunity Access", icon="💼")
sim_page = st.Page("pages/simulator.py", title="Infrastructure Simulator", icon="🛠️")

# 2. Build the structured navigation categories for your sidebar
pg = st.navigation({
    "Project Overview": [home_page],
    "Data Dashboards": [equity_page, opp_page],
    "Planning Tools": [sim_page]
})

# 3. Run the app
pg.run()