# import pandas as pd
# import geopandas as gpd
# import folium
# import branca
#
# # Paths
# shapefile_path = r"C:\Sasha\Projects\TampaTransportation\cb_2025_12_tract_500k\cb_2025_12_tract_500k.shp"
# hart_stops_path = r"C:\Sasha\Projects\TampaTransportation\HART_Stop_Locations\HART_Stop_Locations.shp"
#
# print("--- Step 1: Loading & Cleaning Census CSV Data Layers ---")
# # 1. Load the raw data layers
# vehicles_df = pd.read_csv("DP05_No_Vehicles.csv")
# demographics_df = pd.read_csv("DP02_Disability_SeniorCitizens.csv")
# income_df = pd.read_csv("DP03_Income.csv")
#
# # 2. Drop the metadata description row (Row Index 0)
# vehicles_df = vehicles_df.drop(0)
# demographics_df = demographics_df.drop(0)
# income_df = income_df.drop(0)
#
# # 3. Isolate the target columns and assign clean, descriptive names
# vehicles_clean = vehicles_df[['GEO_ID', 'DP04_0058PE']].rename(
#     columns={'DP04_0058PE': 'pct_no_vehicle'}
# )
# demo_clean = demographics_df[['GEO_ID', 'DP02_0015PE', 'DP02_0078PE']].rename(
#     columns={
#         'DP02_0015PE': 'pct_seniors',
#         'DP02_0078PE': 'pct_disability'
#     }
# )
# income_clean = income_df[['GEO_ID', 'DP03_0128PE']].rename(
#     columns={'DP03_0128PE': 'pct_below_poverty'}
# )
#
# # 4. Successive merges to build the tabular master dataset
# master_df = pd.merge(vehicles_clean, demo_clean, on='GEO_ID', how='inner')
# master_df = pd.merge(master_df, income_clean, on='GEO_ID', how='inner')
#
# # 5. Convert numeric columns from strings to floats for math steps
# numeric_cols = ['pct_no_vehicle', 'pct_seniors', 'pct_disability', 'pct_below_poverty']
# for col in numeric_cols:
#     master_df[col] = pd.to_numeric(master_df[col], errors='coerce')
#
# # Transform long GEO_ID to 11-digit short format to match the shapefile later
# master_df['GEOID_SHORT'] = master_df['GEO_ID'].str.replace('1400000US', '', regex=False)
# print("🎉 Tabular census metrics merged and converted successfully.")
#
#
# print("\n--- Step 2: Processing Spatial Geographic Layers ---")
# shapes = gpd.read_file(shapefile_path)
# # Filter for Hillsborough County right away (FIPS 057)
# hillsborough_shapes = shapes[shapes['COUNTYFP'] == '057'].copy()
#
# # Load the HART Bus Stop Points
# hart_stops = gpd.read_file(hart_stops_path)
#
# # Ensure they use matching local coordinate systems before running spatial operations
# hillsborough_shapes = hillsborough_shapes.to_crs(epsg=2237)
# hart_stops = hart_stops.to_crs(epsg=2237)
#
#
# print("\n--- Step 3: Spatial Join (Counting Bus Stops Per Neighborhood) ---")
# # Run a Spatial Join to drop points into polygons
# stops_in_tracts = gpd.sjoin(hart_stops, hillsborough_shapes, how="inner", predicate="within")
# stop_counts = stops_in_tracts.groupby('GEOID').size().reset_index(name='bus_stop_count')
#
#
# print("\n--- Step 4: Unifying Spatial Shapes, Demographics, and Transit Counts ---")
# # Merge geographic shapes with our cleaned census variables
# merged_gdf = hillsborough_shapes.merge(master_df, left_on='GEOID', right_on='GEOID_SHORT', how='inner')
#
# # Merge the calculated bus stop counts into the master spatial dataframe
# merged_gdf = merged_gdf.merge(stop_counts, on='GEOID', how='left')
# merged_gdf['bus_stop_count'] = merged_gdf['bus_stop_count'].fillna(0)
#
#
# print("\n--- Step 4.5: Calculating the Transit Equity Gap Score ---")
# # 1. Rank the 4 demand factors from 0 (lowest need) to 1 (highest need)
# merged_gdf['rank_vehicle'] = merged_gdf['pct_no_vehicle'].rank(pct=True)
# merged_gdf['rank_seniors'] = merged_gdf['pct_seniors'].rank(pct=True)
# merged_gdf['rank_disability'] = merged_gdf['pct_disability'].rank(pct=True)
# merged_gdf['rank_poverty'] = merged_gdf['pct_below_poverty'].rank(pct=True)
#
# # 2. Average them together to get a composite "Social Need Score" (0 to 1)
# merged_gdf['social_need_score'] = merged_gdf[['rank_vehicle', 'rank_seniors', 'rank_disability', 'rank_poverty']].mean(axis=1)
#
# # 3. Rank the transit supply from 0 (fewest bus stops) to 1 (most bus stops)
# merged_gdf['transit_supply_score'] = merged_gdf['bus_stop_count'].rank(pct=True)
#
# # 4. Calculate the GAP: Social Need Rank minus Transit Supply Rank
# merged_gdf['transit_gap_score'] = merged_gdf['social_need_score'] - merged_gdf['transit_supply_score']
#
# # 🚨 ADDED HERE: Normalize the score cleanly from 0 to 100 instead of -70 to 71
# min_raw = merged_gdf['transit_gap_score'].min()
# max_raw = merged_gdf['transit_gap_score'].max()
# merged_gdf['transit_gap_score'] = (((merged_gdf['transit_gap_score'] - min_raw) / (max_raw - min_raw)) * 100).round(1)
#
# print("🎯 Transit equity gap indices computed successfully (Rescaled 0-100).")
#
#
#
# print("\n--- Step 5: Spatial Join via Tract Centroids for Neighborhood Naming ---")
# cdp_url = "https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_12_place.zip"
# florida_places = gpd.read_file(cdp_url)
# county_communities = florida_places[['NAME', 'geometry']].rename(columns={'NAME': 'community_name'})
#
# # Match coordinate systems for the center point naming logic
# polygon_geometry = merged_gdf.geometry
# merged_gdf['centroid'] = merged_gdf.geometry.centroid
# merged_gdf = merged_gdf.set_geometry('centroid')
# county_communities = county_communities.to_crs(merged_gdf.crs)
#
# joined_gdf = gpd.sjoin(merged_gdf, county_communities, how='left', predicate='within')
# joined_gdf = joined_gdf.set_geometry(polygon_geometry)
# joined_gdf = joined_gdf.drop(columns=['centroid', 'index_right'], errors='ignore')
# joined_gdf['community_name'] = joined_gdf['community_name'].fillna('Rural Hillsborough County')
#
#
# print("\n--- Step 6: Exporting Cleaned Master Outputs ---")
# # Save the final flat CSV table (dropping geometry column for standard file format)
# joined_gdf.drop(columns='geometry', errors='ignore').to_csv("tampa_transit_equity_final.csv", index=False)
# print("💾 Master data table saved to: 'tampa_transit_equity_final.csv'")
#
# # Convert projection back to standard GPS coordinates for Folium mapping
# joined_gdf = joined_gdf.to_crs(epsg=4326)
#
# print("\n--- Step 7: Generating Interactive Multi-Layer Toggle Dashboard ---")
# # 1. Initialize map with NO default tile layer to keep our menu clean
# tampa_map = folium.Map(location=[27.9506, -82.4572], zoom_start=10, tiles=None)
#
# # 2. Lock the light grey map style as a permanent background element
# folium.TileLayer('cartodbpositron', name='Light Grey Map', control=False).add_to(tampa_map)
# folium.TileLayer('cartodbpositron', name="Baseline Data Layers", control=False, overlay=False).add_to(tampa_map)
#
# # 3. Setup configuration parameters with explicit color hex lists
# layers_config = [
#     {
#         "name": "1. Composite Transit Gap Score",
#         "col": "transit_gap_score",
#         "colors": ["#313695", "#74add1", "#e0f3f8", "#fee090", "#f46d43", "#a50026"],
#         "legend": "Transit Equity Gap Score (Higher Red = More Underserved)"
#     },
#     {
#         "name": "2. Households with No Vehicle (%)",
#         "col": "pct_no_vehicle",
#         "colors": ["#fff7ec", "#fee8c8", "#fdd49e", "#fdbb84", "#fc8d59", "#ef6548", "#d7301f", "#b30000", "#7f0000"],
#         "legend": "Households with No Vehicle Available (%)"
#     },
#     {
#         "name": "3. Senior Population (65+ %)",
#         "col": "pct_seniors",
#         "colors": ["#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#4a1486"],
#         "legend": "Percentage of Seniors (%)"
#     },
#     {
#         "name": "4. Population with Disability (%)",
#         "col": "pct_disability",
#         "colors": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
#         "legend": "Percentage of People with a Disability (%)"
#     },
#     {
#         "name": "5. Population in Poverty (%)",
#         "col": "pct_below_poverty",
#         "colors": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
#         "legend": "Percentage Below Poverty Line (%)"
#     },
#     {
#         "name": "6. Local Bus Stop Counts",
#         "col": "bus_stop_count",
#         "colors": ["#ffffe5", "#f7fcb9", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#006837", "#004529"],
#         "legend": "Raw Number of Local Bus Stops"
#     }
# ]
#
# # 4. Render demographic groupings as Native Mutually Exclusive Radio Buttons (overlay=False)
# for config in layers_config:
#     col_name = config["col"]
#
#     min_val = float(joined_gdf[col_name].min())
#     max_val = float(joined_gdf[col_name].max())
#
#     if min_val == max_val:
#         max_val += 1.0
#
#     color_scale = branca.colormap.LinearColormap(
#         colors=config["colors"],
#         vmin=min_val,
#         vmax=max_val
#     ).to_step(n=6)
#
#     color_scale.caption = config["legend"]
#
#     # Native base layers mean perfect radio buttons out-of-the-box
#     fg = folium.FeatureGroup(name=config["name"], overlay=False, show=(col_name == "transit_gap_score"))
#
#
#     def get_style(feature, col=col_name, scale=color_scale):
#         val = feature['properties'].get(col, None)
#         return {
#             'fillColor': scale(val) if val is not None else '#ffffff',
#             'color': '#333333',
#             'weight': 0.5,
#             'fillOpacity': 0.65
#         }
#
#
#     folium.GeoJson(
#         joined_gdf,
#         style_function=get_style,
#         highlight_function=lambda x: {'weight': 2, 'color': '#000000', 'fillOpacity': 0.8}
#     ).add_to(fg)
#
#     tampa_map.add_child(color_scale)
#     fg.add_to(tampa_map)
#
# # 5. Append physical bus stop points as an Independent Checkbox Overlay (overlay=True)
# hart_stops_map = gpd.read_file(hart_stops_path).to_crs(epsg=4326)
# stops_fg = folium.FeatureGroup(name="7. Physical Bus Stop Dots", overlay=True, show=False)
# folium.GeoJson(
#     hart_stops_map,
#     marker=folium.CircleMarker(radius=1.5, color=None, fill=True, fill_color="#1a5276", fill_opacity=0.45),
#     tooltip=folium.GeoJsonTooltip(fields=['stop_id', 'stop_name'], aliases=['Stop ID:', 'Stop Name:'])
# ).add_to(stops_fg)
# stops_fg.add_to(tampa_map)
#
# # 6. Render the Layer Control menu box to the upper right corner
# folium.LayerControl(position='topright', collapsed=False).add_to(tampa_map)
#
# # 🌟 THE GLOBAL HOVER ENGINE SCRIPT 🌟
# # This passes the GeoJSON spatial data directly to a frontend script that tracks your cursor
# # over the active layers, guaranteeing that the stats are always readable.
# geojson_data_json = joined_gdf.to_json()
#
# global_hover_script = f"""
# <script>
# document.addEventListener("DOMContentLoaded", function() {{
#     setTimeout(function() {{
#         // Identify Leaflet Map Instance
#         var mapInstance = null;
#         for (var key in window) {{
#             if (key.startsWith('map_') && window[key] instanceof L.Map) {{
#                 mapInstance = window[key];
#                 break;
#             }}
#         }}
#
#         if (!mapInstance) return;
#
#         // Load the tracking dataset geometries into memory
#         var geojsonData = {geojson_data_json};
#
#         // Build a single global floating tooltip element
#         var tooltipDiv = document.createElement('div');
#         tooltipDiv.style.position = 'fixed';
#         tooltipDiv.style.backgroundColor = 'white';
#         tooltipDiv.style.color = '#333333';
#         tooltipDiv.style.fontFamily = 'arial, sans-serif';
#         tooltipDiv.style.fontSize = '12px';
#         tooltipDiv.style.padding = '10px';
#         tooltipDiv.style.border = '1px solid #ccc';
#         tooltipDiv.style.borderRadius = '4px';
#         tooltipDiv.style.pointerEvents = 'none';
#         tooltipDiv.style.zIndex = '99999';
#         tooltipDiv.style.display = 'none';
#         tooltipDiv.style.boxShadow = '0px 2px 6px rgba(0,0,0,0.2)';
#         document.body.appendChild(tooltipDiv);
#
#         // Convert coordinates to matching lookup keys
#         var tractLayer = L.geoJson(geojsonData, {{
#             style: {{ fillOpacity: 0, weight: 0, opacity: 0 }},
#             onEachFeature: function(feature, layer) {{
#                 layer.on('mousemove', function(e) {{
#                     var props = feature.properties;
#
#                     // Format numeric lookups smoothly
#                     var gap = props.transit_gap_score !== null ? Number(props.transit_gap_score).toFixed(1) : 'N/A';
#                     var veh = props.pct_no_vehicle !== null ? Number(props.pct_no_vehicle).toFixed(1) : 'N/A';
#                     var sen = props.pct_seniors !== null ? Number(props.pct_seniors).toFixed(1) : 'N/A';
#                     var dis = props.pct_disability !== null ? Number(props.pct_disability).toFixed(1) : 'N/A';
#                     var pov = props.pct_below_poverty !== null ? Number(props.pct_below_poverty).toFixed(1) : 'N/A';
#                     var stops = props.bus_stop_count !== null ? props.bus_stop_count : '0';
#
#                     tooltipDiv.innerHTML =
#                         '<strong>Neighborhood:</strong> ' + props.community_name + '<br>' +
#                         '<strong>Zone ID:</strong> ' + props.NAMELSAD + '<br>' +
#                         '<hr style="margin: 4px 0; border: 0; border-top: 1px solid #eee;">' +
#                         '<strong>Transit Gap Score:</strong> ' + gap + '<br>' +
#                         '<strong>% No Vehicle:</strong> ' + veh + '%<br>' +
#                         '<strong>% Seniors (65+):</strong> ' + sen + '%<br>' +
#                         '<strong>% With Disability:</strong> ' + dis + '%<br>' +
#                         '<strong>% In Poverty:</strong> ' + pov + '%<br>' +
#                         '<strong>Local Bus Stops:</strong> ' + stops;
#
#                     tooltipDiv.style.left = (e.originalEvent.clientX + 15) + 'px';
#                     tooltipDiv.style.top = (e.originalEvent.clientX + 15) + 'px';
#                     tooltipDiv.style.top = (e.originalEvent.clientY + 15) + 'px';
#                     tooltipDiv.style.display = 'block';
#                 }});
#
#                 layer.on('mouseout', function() {{
#                     tooltipDiv.style.display = 'none';
#                 }});
#             }}
#         }}).addTo(mapInstance);
#
#         // Force our interactive lookup mesh to stay at the front of the tracking loop
#         mapInstance.on('baselayerchange overlayadd overlayremove', function() {{
#             tractLayer.bringToFront();
#         }});
#         tractLayer.bringToFront();
#
#     }}, 500);
# }});
# </script>
# """
# tampa_map.get_root().html.add_child(folium.Element(global_hover_script))
#
# # Explanatory Info Box Card Text (Unchanged)
# info_box_html = """
# <div style="
#     position: fixed;
#     bottom: 30px;
#     left: 30px;
#     width: 320px;
#     height: auto;
#     background-color: white;
#     font-family: Arial, sans-serif;
#     font-size: 13px;
#     color: #333333;
#     padding: 15px;
#     border-radius: 8px;
#     box-shadow: 0 0 15px rgba(0,0,0,0.2);
#     z-index: 9999;
#     line-height: 1.5;
# ">
#     <h4 style="margin-top: 0; margin-bottom: 8px; color: #a50026; font-size: 15px;">
#         Understanding the Transit Gap Score
#     </h4>
#     <p style="margin-bottom: 10px;">
#         This index identifies neighborhoods where the availability of physical transit infrastructure does not match community needs.
#     </p>
#     <strong>How it's calculated:</strong>
#     <ul style="padding-left: 20px; margin-top: 5px; margin-bottom: 10px;">
#         <li><strong>Demographic Demand:</strong> Combines density of seniors, residents with disabilities, households below the poverty line, and vehicle-less households.</li>
#         <li><strong>Transit Supply:</strong> Evaluated based on localized bus stop infrastructure counts.</li>
#     </ul>
#     <strong>Scale Interpretation:</strong><br>
#     <span style="color: #313695; font-weight: bold;">Low Scores (0-30):</span> Strong transit supply relative to community needs.<br>
#     <span style="color: #a50026; font-weight: bold;">High Scores (70-100):</span> Severe Equity Gap. Highly underserved zones requiring immediate service investment.
# </div>
# """
# tampa_map.get_root().html.add_child(folium.Element(info_box_html))
#
# output_html = "tampa_transit_equity_map.html"
# tampa_map.save(output_html)
# print(f"\n🎉 Success! Radio exclusivity locked and data tooltips permanently active. Saved to: '{output_html}'")

import pandas as pd
import geopandas as gpd
import folium
import branca

# Paths
shapefile_path = r"C:\Sasha\Projects\TampaTransportation\cb_2025_12_tract_500k\cb_2025_12_tract_500k.shp"
hart_stops_path = r"C:\Sasha\Projects\TampaTransportation\HART_Stop_Locations\HART_Stop_Locations.shp"

print("--- Step 1: Loading & Cleaning Census CSV Data Layers ---")
# 1. Load the raw data layers
vehicles_df = pd.read_csv("DP05_No_Vehicles.csv")
demographics_df = pd.read_csv("DP02_Disability_SeniorCitizens.csv")
income_df = pd.read_csv("DP03_Income.csv")

# 2. Drop the metadata description row (Row Index 0)
vehicles_df = vehicles_df.drop(0)
demographics_df = demographics_df.drop(0)
income_df = income_df.drop(0)

# 3. Isolate the target columns and assign clean, descriptive names
vehicles_clean = vehicles_df[['GEO_ID', 'DP04_0058PE']].rename(
    columns={'DP04_0058PE': 'pct_no_vehicle'}
)
demo_clean = demographics_df[['GEO_ID', 'DP02_0015PE', 'DP02_0078PE']].rename(
    columns={
        'DP02_0015PE': 'pct_seniors',
        'DP02_0078PE': 'pct_disability'
    }
)
income_clean = income_df[['GEO_ID', 'DP03_0128PE']].rename(
    columns={'DP03_0128PE': 'pct_below_poverty'}
)

# 4. Successive merges to build the tabular master dataset
master_df = pd.merge(vehicles_clean, demo_clean, on='GEO_ID', how='inner')
master_df = pd.merge(master_df, income_clean, on='GEO_ID', how='inner')

# 5. Convert numeric columns from strings to floats for math steps
numeric_cols = ['pct_no_vehicle', 'pct_seniors', 'pct_disability', 'pct_below_poverty']
for col in numeric_cols:
    master_df[col] = pd.to_numeric(master_df[col], errors='coerce')

# Transform long GEO_ID to 11-digit short format to match the shapefile later
master_df['GEOID_SHORT'] = master_df['GEO_ID'].str.replace('1400000US', '', regex=False)
print("🎉 Tabular census metrics merged and converted successfully.")


print("\n--- Step 2: Processing Spatial Geographic Layers ---")
shapes = gpd.read_file(shapefile_path)
# Filter for Hillsborough County right away (FIPS 057)
hillsborough_shapes = shapes[shapes['COUNTYFP'] == '057'].copy()

# Load the HART Bus Stop Points
hart_stops = gpd.read_file(hart_stops_path)

# Ensure they use matching local coordinate systems before running spatial operations
hillsborough_shapes = hillsborough_shapes.to_crs(epsg=2237)
hart_stops = hart_stops.to_crs(epsg=2237)


print("\n--- Step 3: Spatial Buffering (Calculating 1/4-Mile Service Area Coverage) ---")
# 1. Create a 1/4-mile buffer around every single bus stop (1/4 mile = 1,320 feet)
buffered_stops = hart_stops.copy()
buffered_stops['geometry'] = buffered_stops.buffer(1320)

# 2. Dissolve overlapping circles into a single massive unified walkshed polygon
# This prevents double-counting areas where multiple bus stops overlap
unified_walkshed = buffered_stops.unary_union

# 3. Calculate what percentage of each tract's area is covered by the transit walkshed
def get_coverage_percentage(row):
    # Get the intersection geometry between this specific neighborhood and our walkshed
    intersection = row.geometry.intersection(unified_walkshed)
    if intersection.is_empty:
        return 0.0
    # Calculate the area fraction and convert to percentage
    pct = (intersection.area / row.geometry.area) * 100
    return min(pct, 100.0) # Guard against minor floating-point math rounding overages

# Apply the intersection calculation directly to our projected Hillsborough shapes
hillsborough_shapes['transit_coverage_pct'] = hillsborough_shapes.apply(get_coverage_percentage, axis=1)


print("\n--- Step 4: Unifying Spatial Shapes, Demographics, and Transit Coverage ---")
# Merge geographic shapes (which now contain our coverage column) with our cleaned census variables
merged_gdf = hillsborough_shapes.merge(master_df, left_on='GEOID', right_on='GEOID_SHORT', how='inner')


print("\n--- Step 4.5: Calculating the Transit Equity Gap Score ---")
# 1. Rank the 4 demand factors from 0 (lowest need) to 1 (highest need)
merged_gdf['rank_vehicle'] = merged_gdf['pct_no_vehicle'].rank(pct=True)
merged_gdf['rank_seniors'] = merged_gdf['pct_seniors'].rank(pct=True)
merged_gdf['rank_disability'] = merged_gdf['pct_disability'].rank(pct=True)
merged_gdf['rank_poverty'] = merged_gdf['pct_below_poverty'].rank(pct=True)

# 2. Average them together to get a composite "Social Need Score" (0 to 1)
merged_gdf['social_need_score'] = merged_gdf[['rank_vehicle', 'rank_seniors', 'rank_disability', 'rank_poverty']].mean(axis=1)

# 3. Rank transit supply using our new area coverage metric (0 = no coverage, 1 = maximum coverage)
merged_gdf['transit_supply_score'] = merged_gdf['transit_coverage_pct'].rank(pct=True)

# 4. Calculate the GAP: Social Need Rank minus Transit Supply Rank
merged_gdf['transit_gap_score'] = merged_gdf['social_need_score'] - merged_gdf['transit_supply_score']

# Normalize the score cleanly from 0 to 100 instead of -70 to 71
min_raw = merged_gdf['transit_gap_score'].min()
max_raw = merged_gdf['transit_gap_score'].max()
merged_gdf['transit_gap_score'] = (((merged_gdf['transit_gap_score'] - min_raw) / (max_raw - min_raw)) * 100).round(1)

print("🎯 Transit equity gap indices computed successfully using area walkability metrics.")


print("\n--- Step 5: Spatial Join via Tract Centroids for Neighborhood Naming ---")
cdp_url = "https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_12_place.zip"
florida_places = gpd.read_file(cdp_url)
county_communities = florida_places[['NAME', 'geometry']].rename(columns={'NAME': 'community_name'})

# Match coordinate systems for the center point naming logic
polygon_geometry = merged_gdf.geometry
merged_gdf['centroid'] = merged_gdf.geometry.centroid
merged_gdf = merged_gdf.set_geometry('centroid')
county_communities = county_communities.to_crs(merged_gdf.crs)

joined_gdf = gpd.sjoin(merged_gdf, county_communities, how='left', predicate='within')
joined_gdf = joined_gdf.set_geometry(polygon_geometry)
joined_gdf = joined_gdf.drop(columns=['centroid', 'index_right'], errors='ignore')
joined_gdf['community_name'] = joined_gdf['community_name'].fillna('Rural Hillsborough County')


print("\n--- Step 6: Exporting Cleaned Master Outputs ---")
# Save the final flat CSV table (dropping geometry column for standard file format)
joined_gdf.drop(columns='geometry', errors='ignore').to_csv("tampa_transit_equity_final.csv", index=False)
print("💾 Master data table saved to: 'tampa_transit_equity_final.csv'")

# Convert projection back to standard GPS coordinates for Folium mapping
joined_gdf = joined_gdf.to_crs(epsg=4326)


print("\n--- Step 7: Generating Interactive Multi-Layer Toggle Dashboard ---")
# 1. Initialize map with NO default tile layer to keep our menu clean
tampa_map = folium.Map(location=[27.9506, -82.4572], zoom_start=10, tiles=None)

# 2. Lock the light grey map style as a permanent background element
folium.TileLayer('cartodbpositron', name='Light Grey Map', control=False).add_to(tampa_map)
folium.TileLayer('cartodbpositron', name="Baseline Data Layers", control=False, overlay=False).add_to(tampa_map)

# 3. Setup configuration parameters with explicit color hex lists
layers_config = [
    {
        "name": "1. Composite Transit Gap Score",
        "col": "transit_gap_score",
        "colors": ["#313695", "#74add1", "#e0f3f8", "#fee090", "#f46d43", "#a50026"],
        "legend": "Transit Equity Gap Score (Higher Red = More Underserved)"
    },
    {
        "name": "2. Households with No Vehicle (%)",
        "col": "pct_no_vehicle",
        "colors": ["#fff7ec", "#fee8c8", "#fdd49e", "#fdbb84", "#fc8d59", "#ef6548", "#d7301f", "#b30000", "#7f0000"],
        "legend": "Households with No Vehicle Available (%)"
    },
    {
        "name": "3. Senior Population (65+ %)",
        "col": "pct_seniors",
        "colors": ["#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#4a1486"],
        "legend": "Percentage of Seniors (%)"
    },
    {
        "name": "4. Population with Disability (%)",
        "col": "pct_disability",
        "colors": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
        "legend": "Percentage of People with a Disability (%)"
    },
    {
        "name": "5. Population in Poverty (%)",
        "col": "pct_below_poverty",
        "colors": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
        "legend": "Percentage Below Poverty Line (%)"
    },
    {
        "name": "6. Transit Walk Coverage (%)",
        "col": "transit_coverage_pct",
        "colors": ["#ffffe5", "#f7fcb9", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#006837", "#004529"],
        "legend": "Percentage of Neighborhood Area within 1/4 Mile of a Bus Stop"
    }
]

# 4. Render demographic groupings as Native Mutually Exclusive Radio Buttons (overlay=False)
for config in layers_config:
    col_name = config["col"]

    min_val = float(joined_gdf[col_name].min())
    max_val = float(joined_gdf[col_name].max())

    if min_val == max_val:
        max_val += 1.0

    color_scale = branca.colormap.LinearColormap(
        colors=config["colors"],
        vmin=min_val,
        vmax=max_val
    ).to_step(n=6)

    color_scale.caption = config["legend"]

    fg = folium.FeatureGroup(name=config["name"], overlay=False, show=(col_name == "transit_gap_score"))

    def get_style(feature, col=col_name, scale=color_scale):
        val = feature['properties'].get(col, None)
        return {
            'fillColor': scale(val) if val is not None else '#ffffff',
            'color': '#333333',
            'weight': 0.5,
            'fillOpacity': 0.65
        }

    folium.GeoJson(
        joined_gdf,
        style_function=get_style,
        highlight_function=lambda x: {'weight': 2, 'color': '#000000', 'fillOpacity': 0.8}
    ).add_to(fg)

    tampa_map.add_child(color_scale)
    fg.add_to(tampa_map)

# 5. Append physical bus stop points as an Independent Checkbox Overlay (overlay=True)
hart_stops_map = gpd.read_file(hart_stops_path).to_crs(epsg=4326)
stops_fg = folium.FeatureGroup(name="7. Physical Bus Stop Dots", overlay=True, show=False)
folium.GeoJson(
    hart_stops_map,
    marker=folium.CircleMarker(radius=1.5, color=None, fill=True, fill_color="#1a5276", fill_opacity=0.45),
    tooltip=folium.GeoJsonTooltip(fields=['stop_id', 'stop_name'], aliases=['Stop ID:', 'Stop Name:'])
).add_to(stops_fg)
stops_fg.add_to(tampa_map)

# 6. Render the Layer Control menu box to the upper right corner
folium.LayerControl(position='topright', collapsed=False).add_to(tampa_map)


# 🌟 THE GLOBAL HOVER ENGINE SCRIPT 🌟
# Updated variable keys to reference 'transit_coverage_pct' inside the hover script loop
geojson_data_json = joined_gdf.to_json()

global_hover_script = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
    setTimeout(function() {{
        var mapInstance = null;
        for (var key in window) {{
            if (key.startsWith('map_') && window[key] instanceof L.Map) {{
                mapInstance = window[key];
                break;
            }}
        }}

        if (!mapInstance) return;

        var geojsonData = {geojson_data_json};

        var tooltipDiv = document.createElement('div');
        tooltipDiv.style.position = 'fixed';
        tooltipDiv.style.backgroundColor = 'white';
        tooltipDiv.style.color = '#333333';
        tooltipDiv.style.fontFamily = 'arial, sans-serif';
        tooltipDiv.style.fontSize = '12px';
        tooltipDiv.style.padding = '10px';
        tooltipDiv.style.border = '1px solid #ccc';
        tooltipDiv.style.borderRadius = '4px';
        tooltipDiv.style.pointerEvents = 'none';
        tooltipDiv.style.zIndex = '99999';
        tooltipDiv.style.display = 'none';
        tooltipDiv.style.boxShadow = '0px 2px 6px rgba(0,0,0,0.2)';
        document.body.appendChild(tooltipDiv);

        var tractLayer = L.geoJson(geojsonData, {{
            style: {{ fillOpacity: 0, weight: 0, opacity: 0 }},
            onEachFeature: function(feature, layer) {{
                layer.on('mousemove', function(e) {{
                    var props = feature.properties;

                    var gap = props.transit_gap_score !== null ? Number(props.transit_gap_score).toFixed(1) : 'N/A';
                    var veh = props.pct_no_vehicle !== null ? Number(props.pct_no_vehicle).toFixed(1) : 'N/A';
                    var sen = props.pct_seniors !== null ? Number(props.pct_seniors).toFixed(1) : 'N/A';
                    var dis = props.pct_disability !== null ? Number(props.pct_disability).toFixed(1) : 'N/A';
                    var pov = props.pct_below_poverty !== null ? Number(props.pct_below_poverty).toFixed(1) : 'N/A';
                    var stops = props.transit_coverage_pct !== null ? Number(props.transit_coverage_pct).toFixed(1) : '0.0';

                    tooltipDiv.innerHTML =
                        '<strong>Neighborhood:</strong> ' + props.community_name + '<br>' +
                        '<strong>Zone ID:</strong> ' + props.NAMELSAD + '<br>' +
                        '<hr style="margin: 4px 0; border: 0; border-top: 1px solid #eee;">' +
                        '<strong>Transit Gap Score:</strong> ' + gap + '<br>' +
                        '<strong>% No Vehicle:</strong> ' + veh + '%<br>' +
                        '<strong>% Seniors (65+):</strong> ' + sen + '%<br>' +
                        '<strong>% With Disability:</strong> ' + dis + '%<br>' +
                        '<strong>% In Poverty:</strong> ' + pov + '%<br>' +
                        '<strong>Transit Walk Coverage:</strong> ' + stops + '%';

                    tooltipDiv.style.left = (e.originalEvent.clientX + 15) + 'px';
                    tooltipDiv.style.top = (e.originalEvent.clientY + 15) + 'px';
                    tooltipDiv.style.display = 'block';
                }});

                layer.on('mouseout', function() {{
                    tooltipDiv.style.display = 'none';
                }});
            }}
        }}).addTo(mapInstance);

        mapInstance.on('baselayerchange overlayadd overlayremove', function() {{
            tractLayer.bringToFront();
        }});
        tractLayer.bringToFront();

    }}, 500);
}});
</script>
"""
tampa_map.get_root().html.add_child(folium.Element(global_hover_script))


# Explanatory Info Box Card Text (Updated reference text to note Walk Coverage)
info_box_html = """
<div style="
    position: fixed;
    bottom: 30px;
    left: 30px;
    width: 320px;
    height: auto;
    background-color: white;
    font-family: Arial, sans-serif;
    font-size: 13px;
    color: #333333;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(0,0,0,0.2);
    z-index: 9999;
    line-height: 1.5;
">
    <h4 style="margin-top: 0; margin-bottom: 8px; color: #a50026; font-size: 15px;">
        Understanding the Transit Gap Score
    </h4>
    <p style="margin-bottom: 10px;">
        This index identifies neighborhoods where the availability of physical transit infrastructure does not match community needs.
    </p>
    <strong>How it's calculated:</strong>
    <ul style="padding-left: 20px; margin-top: 5px; margin-bottom: 10px;">
        <li><strong>Demographic Demand:</strong> Combines density of seniors, residents with disabilities, households below the poverty line, and vehicle-less households.</li>
        <li><strong>Transit Supply:</strong> Measures what percentage of the neighborhood's total area is within a 5-minute walk (1/4 mile) of a bus stop. </li>
    </ul>
    <strong>Scale Interpretation:</strong><br>
    <span style="color: #313695; font-weight: bold;">Low Scores (0-30):</span> Strong transit supply relative to community needs.<br>
    <span style="color: #a50026; font-weight: bold;">High Scores (70-100):</span> Severe Equity Gap. Highly underserved zones requiring immediate service investment.
</div>
"""
tampa_map.get_root().html.add_child(folium.Element(info_box_html))

output_html = "tampa_transit_equity_map.html"
tampa_map.save(output_html)
print(f"\n🎉 Success! Script compiled smoothly with new walkability coverage backend logic. Dashboard output generated: '{output_html}'")

