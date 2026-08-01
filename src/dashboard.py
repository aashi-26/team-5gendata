
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Karnataka Math Competency Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COMPETENCY_GROUP = {
    "Q1": "Number Sense", "Q2": "Place Value", "Q3": "Number Sense", "Q4": "Number Sense",
    "Q5": "Addition", "Q6": "Addition",
    "Q7": "Subtraction", "Q8": "Subtraction",
    "Q9": "Multiplication", "Q10": "Multiplication", "Q11": "Multiplication",
    "Q12": "Division", "Q13": "Division", "Q14": "Division",
    "Q15": "Fraction",
    "Q16": "Measurement", "Q17": "Measurement", "Q18": "Measurement",
    "Q19": "Shapes", "Q20": "Shapes",
}


@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE_DIR, "combined_with_scores.csv"))
    severity = pd.read_csv(
        os.path.join(BASE_DIR, "district_severity_ranked.csv")
    )
    return df, severity


df, severity = load_data()

st.sidebar.header("Filter")
district_options = ["All Districts"] + sorted(df["District"].unique().tolist())
selected_district = st.sidebar.selectbox("District", district_options)

filtered_df = df if selected_district == "All Districts" else df[df["District"] == selected_district]

st.title("Karnataka Math Competency Dashboard")
st.caption("Grades 4-6, 2022-23 · Akshara Foundation assessment data")

group_scores = {}
for group in set(COMPETENCY_GROUP.values()):
    cols = [q for q, g in COMPETENCY_GROUP.items() if g == group]
    group_scores[group] = filtered_df[cols].mean(axis=1).mean() * 100
group_series = pd.Series(group_scores).sort_values()

weakest_name, weakest_score = group_series.index[0], group_series.iloc[0]
strongest_name, strongest_score = group_series.index[-1], group_series.iloc[-1]
severity_gap_value = strongest_score - weakest_score

col1, col2, col3, col4 = st.columns(4)
col1.metric("Students Shown", f"{len(filtered_df):,}")
col2.metric("Weakest Competency", weakest_name, delta=f"{weakest_score:.1f}%", delta_color="off")
col3.metric("Strongest Competency", strongest_name, delta=f"{strongest_score:.1f}%", delta_color="off")
col4.metric("Severity Gap", f"{severity_gap_value:.1f} pts",
            help="Gap between strongest and weakest competency group accuracy")

st.divider()

st.subheader(f"Competency Accuracy — {selected_district}")
fig_bar = px.bar(
    x=group_series.values, y=group_series.index, orientation="h",
    labels={"x": "Accuracy (%)", "y": "Competency Group"},
    color=group_series.values,
    color_continuous_scale="RdYlGn",
)
fig_bar.update_layout(coloraxis_showscale=False, height=400)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

if selected_district == "All Districts":
    left, right = st.columns(2)

    with left:
        st.subheader("District Severity Ranking")
        fig_severity = px.bar(
            severity.sort_values("severity_gap"),
            x="severity_gap", y="District", orientation="h",
            color="weakest_group",
            labels={"severity_gap": "Severity Gap (pts)"},
        )
        fig_severity.update_layout(height=700)
        st.plotly_chart(fig_severity, use_container_width=True)

    with right:
        st.subheader("District x Competency Heatmap")
        group_scores_all = {}
        for group in set(COMPETENCY_GROUP.values()):
            cols = [q for q, g in COMPETENCY_GROUP.items() if g == group]
            group_scores_all[group] = df[cols].mean(axis=1) * 100
        group_df_all = pd.DataFrame(group_scores_all)
        group_df_all["District"] = df["District"]
        district_group_avg = group_df_all.groupby("District").mean(numeric_only=True)

        fig_heat = go.Figure(data=go.Heatmap(
            z=district_group_avg.values,
            x=district_group_avg.columns,
            y=district_group_avg.index,
            colorscale="RdYlGn",
            zmin=30, zmax=90,
            colorbar=dict(title="Accuracy %"),
        ))
        fig_heat.update_layout(height=700)
        st.plotly_chart(fig_heat, use_container_width=True)

    st.subheader("Full District Severity Table")
    st.dataframe(severity, use_container_width=True)

st.divider()

with st.expander("View filtered raw data"):
    st.dataframe(filtered_df, use_container_width=True)