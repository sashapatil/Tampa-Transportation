# Tampa Mobility Gap Explorer

An interactive spatial decision-support dashboard built for regional transportation planners (such as Tampa M.O.V.E.S. and the Hillsborough TPO). This tool identifies micro-level geographic disparities where vulnerable demographic populations heavily outweigh the physical footprint of the public transit network.

---

## 🎯 Project Vision

* **Who uses it:** City of Tampa Mobility Department, Hillsborough TPO, and regional transit planners.
* **What they do:** Utilize highly granular mobility gap data to pinpoint underserved neighborhoods and prioritize areas for future route expansions, service frequency updates, or localized accessibility studies.
* **What changes:** Equitable distribution of public infrastructure, ensuring transit-dependent residents gain reliable, non-car infrastructure to support daily mobility.

---

## 🏗️ System Architecture & Methodology

The application breaks down complex GIS operations into an execution pipeline to ensure the frontend interface loads immediately.

### 1. Data Pipeline & Spatial Processing (`main.py`)
Instead of calculating heavy geometry on the fly, a background Python pipeline handles the core data fusion and spatial indexing:

* **Demographic Indexing:** Extracts micro-level vulnerability variables from the US Census American Community Survey (ACS) at the Census Tract level, including:
  * Households with zero vehicles available
  * Populations living below the poverty line
  * Seniors (Ages 65+)
  * Individuals with disabilities
* **Transit Walk-Coverage Buffer:** Projects spatial shapes into a local coordinate system (UTM Zone 17N / EPSG:32617) to calculate a true 1/4-mile walking buffer around every single HART bus stop and TECO Line Streetcar station across Hillsborough County.
* **The Mobility Gap Score:** Mathematically crosses the combined social need indicators against the localized transit walk-coverage percentage to output a normalized 0-100 friction scale.

### 2. Frontend (`app.py` & `pages/`)
* **Streamlit Web Framework:** Implements a dynamic multi-page navigation architecture via `st.navigation`, separating the user experience into logical executive, analytical, and predictive tracking phases.

---

## 📂 Repository Structure

```plaintext
├── app.py                         # Main application entrypoint & routing setup
├── main.py                        # Background GIS data processing pipeline
├── requirements.txt               # Global python dependency definitions
├── tampa_transit_equity_final.csv # Processed spatial tract stats & indicators
├── tampa_transit_equity_map.html  # Compiled standalone Leaflet interactive map
└── pages/
    ├── home_summary.py            # Project Hub: Executive Summary & Regional Priorities
    ├── transit_equity.py          # Metric 1: The Transit Equity Gap UI & Deep-Dive
    ├── opportunity_map.py         # Metric 2: Access to Opportunity (Jobs Realignment)
    └── simulator.py               # Planning Tool: Infrastructure Scenario Simulator