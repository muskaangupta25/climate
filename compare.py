import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

def compare_climate_vs_capitalism(df):
    st.title("📉 Compare Climate Metrics vs. Capitalism Metrics")

    st.markdown("This section allows you to explore relationships between governance/economic freedom indicators and climate-related waste and recycling metrics across countries.")

    capitalism_metrics = [
        "Property Rights", "Government Integrity", "Judicial Effectiveness",
        "Tax Burden", "Government Spending", "Fiscal Health",
        "Business Freedom", "Labor Freedom", "Investment Freedom", "Financial Freedom"
    ]

    climate_metrics = [
        "Recycling Score", "Waste Management Score",
        "Overall Sustainable Development Goal Score"
    ]

    st.subheader("🛠️ Choose Metrics")
    col1, col2 = st.columns(2)
    with col1:
        x_metric = st.selectbox("Select a Capitalism Metric (X-axis)", capitalism_metrics)
    with col2:
        y_metric = st.selectbox("Select a Climate Metric (Y-axis)", climate_metrics)


    df_scatter = df[[x_metric, y_metric, "Name", "year"]].dropna()
    if df_scatter.empty:
        st.warning("Not enough data for this animated scatter plot.")
    else:
        fig1 = px.scatter(df_scatter, x=x_metric, y=y_metric, hover_name="Name",
                          animation_frame="year", title=f"{y_metric} vs. {x_metric} Over Time")
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("### 📊 Static Scatter Plot")
    static_scatter_df = df[[x_metric, y_metric, "Name", "year"]].dropna()
    if static_scatter_df.empty:
        st.info("Not enough data for this pair.")
    else:
        fig2 = px.scatter(static_scatter_df, x=x_metric, y=y_metric,
                          hover_name="Name", color="year",
                          title=f"{y_metric} vs {x_metric}")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🏆 Country Rankings")

    year_choice = st.selectbox("Select Year for Rankings", sorted(df["year"].dropna().unique()))
    rank_df = df[df["year"] == year_choice][["Name", x_metric, y_metric]].dropna()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Top 10 by {y_metric}")
        st.dataframe(rank_df.sort_values(y_metric, ascending=False).head(10))

    with col2:
        st.subheader(f"Top 10 by {x_metric}")
        st.dataframe(rank_df.sort_values(x_metric, ascending=False).head(10))