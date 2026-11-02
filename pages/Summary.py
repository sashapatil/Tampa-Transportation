import streamlit as st

st.title("🚌 Hillsborough County Transit Equity & Economic Access Study")
st.caption("A data-driven framework for optimized transit infrastructure deployment.")

st.markdown("---")

# 1. The Core Pitch
st.error("""
### ⏱️ The 30-Second Executive Summary
Hillsborough County’s physical employment hubs are geographically isolated from our highest-need, transit-dependent communities. This dashboard bridges that gap. By combining multi-variable demographic demand with micro-level transit footprints, we expose structural **Spatial Mismatches**—identifying exactly where transit investments will yield the highest socioeconomic return.
""")

st.markdown("---")

# 2. Neighborhood-Specific Diagnostic Breakdown

st.subheader("📍 Priority Geographic Focus Areas")

# Create three columns to show the full spectrum of Hillsborough's geography
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 🔴 The Urban Equity Core
    * **Target Zones:** *East Tampa, Sulphur Springs, University Square*
    * **The Mismatch:** Extreme demographic dependency (high poverty, low vehicle ownership) paired with fractured pedestrian access networks.
    * **Planning Action:** Prioritize for high-frequency Bus Rapid Transit (BRT) corridors, immediate sidewalk network infill, and shelter enhancements.
    """)

with col2:
    st.markdown("""
    #### 🟠 Suburban Commuter Deserts
    * **Target Zones:** *Brandon, Riverview, Town 'n' Country*
    * **The Mismatch:** Rapidly expanding low-to-mid wage retail, fulfillment, and logistical job centers that remain completely car-dependent.
    * **Planning Action:** Implement point-to-point express commuter shuttles, workplace vanpools, and regional employment hub line extensions.
    """)

with col3:
    st.markdown("""
    #### 🟤 Rural Structural Isolation
    * **Target Zones:** *Wimauma, Balm, Lithia, Rural Hillsborough*
    * **The Mismatch:** Complete absence of transit infrastructure ($0\%$ coverage) impacting isolated, lower-wage agricultural and shift workers.
    * **Planning Action:** Traditional fixed-route transit is inefficient here. Implement **On-Demand Micro-Transit zones**, flexible micro-shuttles, or regional Park-and-Ride anchors.
    """)
st.markdown("---")

# 3. Prescriptive Guide for Using the App
st.subheader("💡 How to Utilize This Tool")
st.markdown("""
1. **Explore Regional Inequity (Page 2):** Use the Social Need map to isolate exactly where high concentrations of vehicle-less households overlap with low walk-coverage scores.
2. **Identify Blocked Opportunity Hubs (Page 3):** Use the Access to Opportunity map to cross-reference low-wage job centers with current bus stop geometry. Look for deep-red job clusters that lack dark blue stop dots.
""")