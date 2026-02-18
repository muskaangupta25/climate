
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import pycountry
import plotly.express as px
import branca.colormap as cm
import numpy as np
import requests

st.set_page_config(layout="wide")

@st.cache_data
def load_data(path="data/final_dataset.csv"):
    df = pd.read_csv(path, low_memory=False)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "country_code"])
    df["year"] = df["year"].astype(int)
    keep_codes = df["country_code"].dropna().unique()[:50]
    return df[df["country_code"].isin(keep_codes)]

def iso3_to_name(code):
    try:
        return pycountry.countries.get(alpha_3=code).name
    except:
        return code

df = load_data()
years = sorted(df["year"].dropna().unique())
iso3_list = df["country_code"].dropna().unique()

if "selected_country" not in st.session_state:
    st.session_state.selected_country = None

st.sidebar.title("🌍 Filters")
metric = st.sidebar.selectbox("Metric", [
    "Total Population", "Growth Rate", "Population Density (per sq km)",
    "Total Fertility Rate", "Life Expectancy at Birth"
])

col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    selected_year = st.slider("📅 Select Year", min_value=int(min(years)), max_value=int(max(years)), value=int(min(years)), step=1)

df_year = df[df["year"] == selected_year]
metric_data = df_year[["country_code", metric]].dropna()
metric_map = dict(zip(metric_data["country_code"], metric_data[metric]))

vmin = df_year[metric].min()
vmax = df_year[metric].max()
log_vmin = np.log10(vmin + 1)
log_vmax = np.log10(vmax + 1)
colormap = cm.linear.YlGnBu_09.scale(log_vmin, log_vmax)
colormap.caption = f"{metric} ({selected_year}, log scale)"
colormap.tick_format = lambda x: f"{10**x:,.0f}"

def style_function(feature):
    code = feature.get("id")
    val = metric_map.get(code)
    log_val = np.log10(val + 1) if val is not None else None
    color = colormap(log_val) if log_val is not None else "#ccc"
    return {"fillColor": color, "color": "#333", "weight": 1, "fillOpacity": 0.6}

if st.session_state.selected_country:
    code = st.session_state.selected_country
    name = iso3_to_name(code)
    st.title(f"📊 Stats for {name}")
    row = df[df["country_code"] == code].sort_values("year")
    chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter"])
    numeric_cols = ["Total Population", "Life Expectancy at Birth", "Growth Rate", "Population Density (per sq km)", "Total Fertility Rate"]
    x_axis = st.selectbox("X-axis", ["year"] + numeric_cols)
    y_axis = st.selectbox("Y-axis", numeric_cols)

    if chart_type == "Line":
        fig = px.line(row, x=x_axis, y=y_axis)
    elif chart_type == "Bar":
        fig = px.bar(row, x=x_axis, y=y_axis)
    elif chart_type == "Scatter":
        fig = px.scatter(row, x=x_axis, y=y_axis)
    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("🔁 Compare with another country"):
        code2 = st.selectbox("Select second country", [c for c in iso3_list if c != code])
        name2 = iso3_to_name(code2)
        row2 = df[df["country_code"] == code2].sort_values("year")
        combined = pd.concat([
            row[[x_axis, y_axis]].assign(Country=name),
            row2[[x_axis, y_axis]].assign(Country=name2)
        ])
        fig2 = px.line(combined, x=x_axis, y=y_axis, color="Country") if chart_type == "Line" else                px.bar(combined, x=x_axis, y=y_axis, color="Country") if chart_type == "Bar" else                px.scatter(combined, x=x_axis, y=y_axis, color="Country")
        st.plotly_chart(fig2, use_container_width=True)

    if st.button("🔙 Back to Map"):
        st.session_state.selected_country = None
        st.rerun()
    st.stop()

st.title("🌐 Climate vs. Capitalism – Global View")
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
geojson = requests.get("https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json").json()

for feature in geojson["features"]:
    code = feature.get("id")
    val = metric_map.get(code)
    feature["properties"]["metric"] = val if val is not None else "N/A"

folium.GeoJson(
    geojson,
    name="Countries",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["name", "metric"], aliases=["Country", metric])
).add_to(m)

colormap.add_to(m)

m.get_root().html.add_child(folium.Element("""
<style>
.legend {
    position: absolute !important;
    bottom: 10px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    z-index: 9999 !important;
    background: white;
    padding: 6px 12px;
    border-radius: 4px;
    box-shadow: 0 0 4px rgba(0,0,0,0.2);
}
</style>
"""))

with col2:
    map_data = st_folium(m, width=900, height=600)

last_draw = map_data.get("last_active_drawing") if map_data else None
if last_draw and "id" in last_draw:
    st.session_state.selected_country = last_draw["id"]
    st.rerun()
