import pandas as pd
import geopandas as gpd
import folium
import branca
import numpy as np

# Paths
shapefile_path = r"C:\Sasha\Projects\TampaTransportation\cb_2025_12_tract_500k\cb_2025_12_tract_500k.shp"
hart_stops_path = r"C:\Sasha\Projects\TampaTransportation\HART_Stop_Locations\HART_Stop_Locations.shp"

print("--- Step 1: Aggregating LODES Data ---")
df_lodes = pd.read_csv(rf"C:\Sasha\Projects\TampaTransportation\Workplace_SI03_JT05_2023.csv", dtype={'w_geocode': str})

# Ensure the IDs are treated purely as stripped strings
df_lodes['clean_tract_id'] = df_lodes['w_geocode'].astype(str).str.strip().str.slice(0, 11)

tract_jobs = df_lodes.groupby('clean_tract_id')[['C000', 'CE01', 'CE02']].sum().reset_index()
tract_jobs = tract_jobs.rename(columns={
    'C000': 'total_jobs',
    'CE01': 'low_wage_jobs_under_1250',
    'CE02': 'mid_wage_jobs_under_3333'
})

print("\n--- Step 2: Unifying with Tabular Master Data ---")
df_existing = pd.read_csv(r"C:\Sasha\Projects\TampaTransportation\tampa_transit_equity_final.csv")

# Wipe out any legacy or broken job columns from previous attempts
cols_to_overwrite = ['total_jobs', 'low_wage_jobs_under_1250', 'mid_wage_jobs_under_3333']
df_existing = df_existing.drop(columns=[col for col in cols_to_overwrite if col in df_existing.columns],
                               errors='ignore')

# Standardize the join key using the exact logic from your original main.py
if 'GEOID_SHORT' in df_existing.columns:
    df_existing['clean_tract_id'] = df_existing['GEOID_SHORT'].astype(str).str.strip()
else:
    df_existing['clean_tract_id'] = df_existing['GEO_ID'].astype(str).str.replace('1400000US', '',
                                                                                  regex=False).str.strip()

# Run the left merge
df_final = pd.merge(df_existing, tract_jobs, on='clean_tract_id', how='left')

# Count how many tracts actually found matching job data before filling zeros
matched_count = df_final['total_jobs'].notna().sum()
print(
    f"📊 Match Verification: {matched_count} out of {len(df_final)} Hillsborough tracts successfully linked to LODES job data!")

# Now fill the remaining unmatched tracts safely with 0
df_final[cols_to_overwrite] = df_final[cols_to_overwrite].fillna(0)

# Save the updated master table
df_final.to_csv(r"C:\Sasha\Projects\TampaTransportation\tampa_transit_equity_final.csv", index=False)

print("\n--- Step 3: Compiling Page 2 Spatial Interactive Map ---")
shapes = gpd.read_file(shapefile_path)
hillsborough_shapes = shapes[shapes['COUNTYFP'] == '057'].copy()
hillsborough_shapes['GEOID'] = hillsborough_shapes['GEOID'].astype(str).str.strip()

# Merge shapes with our fresh final dataframe
joined_gdf = hillsborough_shapes.merge(df_final, left_on='GEOID', right_on='clean_tract_id', how='inner')
joined_gdf = joined_gdf.to_crs(epsg=4326)

# Setup Folium Map with NO default tile layer to support LayerControl smoothly
opportunity_map = folium.Map(location=[27.9506, -82.4572], zoom_start=10, tiles=None)
folium.TileLayer('cartodbpositron', name='Light Grey Map', control=False).add_to(opportunity_map)
folium.TileLayer('cartodbpositron', name="Employment Context", control=False, overlay=False).add_to(opportunity_map)

# Find your true max value dynamically
max_jobs = int(joined_gdf['total_jobs'].max())
if max_jobs <= 0:
    max_jobs = 6096

# Define the exact sequential hex colors matching your theme
color_list = ["#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#de2d26", "#a50f15"]

# Base layer FeatureGroup (Radio Group setup)
# Base layer FeatureGroup (Radio Group setup)
fg = folium.FeatureGroup(name="1. Employment Centers Density", overlay=False, show=True)


# 🗺️ Map your raw numbers cleanly to the color bins
def get_style(feature):
    val = feature['properties'].get('total_jobs', None)

    if val is None or pd.isna(val):
        color = '#ffffff'
    elif val <= 50:
        color = color_list[0]
    elif val <= 200:
        color = color_list[1]
    elif val <= 500:
        color = color_list[2]
    elif val <= 1500:
        color = color_list[3]
    elif val <= 4000:
        color = color_list[4]
    else:
        color = color_list[5]  # Captures all massive 6,000+ job hubs

    return {
        'fillColor': color,
        'color': '#444444',
        'weight': 0.6,
        'fillOpacity': 0.7
    }


folium.GeoJson(
    joined_gdf,
    style_function=get_style,
    highlight_function=lambda x: {'weight': 2.5, 'color': '#000000', 'fillOpacity': 0.85}
).add_to(fg)
fg.add_to(opportunity_map)

# 🚌 5. Append physical bus stop points as an Independent Checkbox Overlay (overlay=True)
print("🚌 Layering physical bus stop footprint coordinates...")
hart_stops_map = gpd.read_file(hart_stops_path).to_crs(epsg=4326)
stops_fg = folium.FeatureGroup(name="2. Physical Bus Stop Dots", overlay=True, show=False)

folium.GeoJson(
    hart_stops_map,
    # 🌟 FIXED: Changed color from None to an explicit navy blue border so dots are clearly visible
    marker=folium.CircleMarker(
        radius=2,
        color="#0b3c5d",
        weight=1,
        fill=True,
        fill_color="#1d2731",
        fill_opacity=0.6
    ),
    tooltip=folium.GeoJsonTooltip(fields=['stop_id', 'stop_name'], aliases=['Stop ID:', 'Stop Name:'])
).add_to(stops_fg)
stops_fg.add_to(opportunity_map)

# 🛠️ Render the Layer Control checkbox block to the upper right corner first
folium.LayerControl(position='topright', collapsed=False).add_to(opportunity_map)

# 🎨 Injecting the Custom HTML Legend Card (MOVED TO THE TOP LEFT CORNER)
html_legend = f"""
<div style="
    position: fixed; 
    top: 20px; 
    left: 55px; 
    width: 420px; 
    height: auto; 
    background-color: white; 
    z-index: 9999; 
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11px; 
    padding: 12px 15px; 
    border-radius: 6px; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
">
    <strong style="font-size: 12px; display: block; margin-bottom: 8px; color: #333333;">
        Total Physical Jobs within Census Tract
    </strong>
    <div style="display: flex; width: 100%; height: 14px; margin-bottom: 4px;">
        <div style="flex: 1; background-color: #fee5d9;"></div>
        <div style="flex: 1; background-color: #fcbba1;"></div>
        <div style="flex: 1; background-color: #fc9272;"></div>
        <div style="flex: 1; background-color: #fb6a4a;"></div>
        <div style="flex: 1; background-color: #de2d26;"></div>
        <div style="flex: 1; background-color: #a50f15;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; width: 100%; color: #555555; padding: 0 2px;">
        <span style="width: 30px; text-align: left;">0</span>
        <span style="width: 40px; text-align: center;">50</span>
        <span style="width: 40px; text-align: center;">200</span>
        <span style="width: 40px; text-align: center;">500</span>
        <span style="width: 40px; text-align: center;">1.5k</span>
        <span style="width: 40px; text-align: center;">4k</span>
        <span style="width: 50px; text-align: right;">{max_jobs:,}</span>
    </div>
</div>
"""
opportunity_map.get_root().html.add_child(folium.Element(html_legend))

# Interactive JavaScript hover engine layer
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
                    var total = props.total_jobs !== null ? Number(props.total_jobs).toLocaleString() : '0';
                    var low = props.low_wage_jobs_under_1250 !== null ? Number(props.low_wage_jobs_under_1250).toLocaleString() : '0';
                    var mid = props.mid_wage_jobs_under_3333 !== null ? Number(props.mid_wage_jobs_under_3333).toLocaleString() : '0';
                    var cov = props.transit_coverage_pct !== null ? Number(props.transit_coverage_pct).toFixed(1) : '0.0';

                    tooltipDiv.innerHTML =
                        '<strong>Community:</strong> ' + props.community_name + '<br>' +
                        '<strong>Tract:</strong> ' + props.NAMELSAD + '<br>' +
                        '<hr style="margin: 4px 0; border: 0; border-top: 1px solid #eee;">' +
                        '<strong>💼 Total Jobs:</strong> ' + total + '<br>' +
                        '<strong>💵 Low-Wage Jobs:</strong> ' + low + '<br>' +
                        '<strong>💵 Mid-Wage Jobs:</strong> ' + mid + '<br>' +
                        '<strong>🚌 Walk Coverage:</strong> ' + cov + '%';

                    tooltipDiv.style.left = (e.originalEvent.clientX + 15) + 'px';
                    tooltipDiv.style.top = (e.originalEvent.clientY + 15) + 'px';
                    tooltipDiv.style.display = 'block';
                }});
                layer.on('mouseout', function() {{ tooltipDiv.style.display = 'none'; }});
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
opportunity_map.get_root().html.add_child(folium.Element(global_hover_script))

output_html = "tampa_opportunity_map.html"
opportunity_map.save(output_html)
print(f"🎉 Success! Generated map footprint layer at '{output_html}'")