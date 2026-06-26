# app.py
import streamlit as st

st.set_page_config(
    page_title="Tampa Mobility Gap Explorer",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚌 Tampa Mobility Gap Explorer")
st.subheader("Data-Driven Decision Support for Equitable Transit Investment")

st.markdown("""
---
### Welcome, Planners!
This dashboard is designed for the **City of Tampa Mobility Department (Tampa M.O.V.E.S.)**, the **Hillsborough TPO**, and regional transportation planning teams to turn demographic data and spatial analytics into actionable infrastructure investments.

Use this tool to bridge the gap between high-need communities and vital economic/social hubs.

#### 🧭 Use the Sidebar to Navigate:
* **1. Transit Equity Gap:** Identify current neighborhoods where social needs outpace the physical transit footprint.
* **2. Access to Opportunity:** Discover where new investments will have the highest impact on connecting residents to major job centers.
""")