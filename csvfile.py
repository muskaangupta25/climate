
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import pycountry
import plotly.express as px
import branca.colormap as cm

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

# Sidebar filters
st.sidebar.title("🌍 Filters")
selected_year = st.sidebar.selectbox("Select Year", years)
metric = st.sidebar.selectbox("Metric", [
    "Total Population", "Growth Rate", "Population Density (per sq km)",
    "Total Fertility Rate", "Life Expectancy at Birth"
])

df_year = df[df["year"] == selected_year]
metric_data = df_year[["country_code", metric]].dropna()
metric_map = dict(zip(metric_data["country_code"], metric_data[metric]))

# Create smooth colormap
vmin = df_year[metric].min()
vmax = df_year[metric].max()
colormap = cm.linear.YlGnBu_09.scale(vmin, vmax)
colormap.caption = f"{metric} Scale"
colormap.tick_format = lambda x: f"{x/1e6:.1f}M" if x > 1e6 else f"{x:,.0f}"

def style_function(feature):
    code = feature.get("id")
    val = metric_map.get(code)
    color = colormap(val) if val is not None else "#ccc"
    return {
        "fillColor": color,
        "color": "#333",
        "weight": 1,
        "fillOpacity": 0.6
    }

# Country View
if st.session_state.selected_country:
    code = st.session_state.selected_country
    name = iso3_to_name(code)
    st.title(f"📊 Stats for {name}")
    row = load_data()
    row = row[row["country_code"] == code].sort_values("year")

    st.subheader("📈 Select Graph Type and Metric")
    chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter"])
    numeric_cols = ["Total Population", "Life Expectancy at Birth", "Growth Rate",
                    "Population Density (per sq km)", "Total Fertility Rate"]
    x_axis = st.selectbox("X-axis", ["year"] + numeric_cols)
    y_axis = st.selectbox("Y-axis", numeric_cols)

    st.subheader(f"{chart_type} Chart for {name}")
    if chart_type == "Line":
        fig = px.line(row, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis} for {name}")
    elif chart_type == "Bar":
        fig = px.bar(row, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis} for {name}")
    elif chart_type == "Scatter":
        fig = px.scatter(row, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis} for {name}")
    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("🔁 Compare with another country"):
        code2 = st.selectbox("Select second country", [c for c in iso3_list if c != code])
        name2 = iso3_to_name(code2)
        row2 = df[df["country_code"] == code2].sort_values("year")
        st.subheader(f"📊 Comparison: {name} vs {name2}")
        combined = pd.concat([
            row[[x_axis, y_axis]].assign(Country=name),
            row2[[x_axis, y_axis]].assign(Country=name2)
        ])
        fig2 = px.line(combined, x=x_axis, y=y_axis, color="Country", title=f"{y_axis} Comparison")
        st.plotly_chart(fig2, use_container_width=True)

    if st.button("🔙 Back to Map"):
        st.session_state.selected_country = None
        st.rerun()
    st.stop()

# Map view
st.title("🌐 Climate vs. Capitalism – Global View")
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
import requests
geojson = requests.get(geojson_url).json()

for feature in geojson["features"]:
    code = feature.get("id")
    val = metric_map.get(code)
    feature["properties"]["metric"] = val if val is not None else "N/A"

folium.GeoJson(
    geojson,
    name="Countries",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["name", "metric"],
        aliases=["Country", metric],
        sticky=False
    ),
    control=False
).add_to(m)

colormap.add_to(m)
folium.LayerControl().add_to(m)

col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    map_data = st_folium(m, width=900, height=600)

last_draw = map_data.get("last_active_drawing") if map_data else None
if last_draw and "id" in last_draw:
    st.session_state.selected_country = last_draw["id"]
    st.rerun()
