import pandas as pd
import numpy as np
import streamlit as st

df = pd.read_csv("figure9_summary_raw.csv")

def scenario_label(predictability, frequency):
    if predictability == 50:
        if frequency == 0.99:
            return "Current Regime"
        elif frequency > 0.99:
            return "Increase Frequency (↑ 25%)"
        else:
            return "Decrease Frequency (↓ 25%)"

    if predictability == 100:
        if frequency == 0.99:
            return "Unpredictable"
        elif frequency > 0.99:
            return "Unpredictable; Increased Frequency (↑ 25%)"
        else:
            return "Unpredictable; Decreased Frequency (↓ 25%)"

    if predictability == 0:
        if frequency == 0.98:
            return "Perfectly Predictable"
        elif frequency > 0.98:
            return "Perfectly Predictable; Increased Frequency (↑ 25%)"
        else:
            return "Perfectly Predictable; Decreased Frequency (↓ 25%)"

st.markdown(
    "<h1 style='text-align: center;'>Nursing Home Inspection Policy Outcomes</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; font-size: 1.1em; color: #555;'>"
    "Explore how inspection frequency and predictability affect "
    "lives saved, efficiency, and regulatory information."
    "</p>",
    unsafe_allow_html=True
)

st.header("Policy controls")
scenario_title = st.empty()

# Discrete predictability options (UI direction reversed per feedback)
st.subheader("Inspection timing predictability")
st.caption("How predictable is inspection timing?")

predictability_ui = st.select_slider(
    "",
    options=[0, 50, 100],
    value=50,
    format_func=lambda p: (
        "0% — Unpredictable (random)" if p == 0 else
        "50% — Current regime (factual)" if p == 50 else
        "100% — Perfectly predictable (scheduled)"
    )
)

# Map UI scale to paper/CSV coding:
# CSV: 0 = perfectly predictable, 50 = current, 100 = fully random
predictability = 100 - predictability_ui

# Discrete frequency options (only those available for the selected predictability regime)
st.subheader("Inspection frequency")
st.caption("How many inspections per facility per year?")

freq_options = (
    df.loc[df["predictability_numeric"] == predictability, "frequency"]
      .sort_values()
      .tolist()
)

# Pick the “current” frequency as default when possible (regime-specific baseline)
default_freq = 0.98 if predictability == 0 else 0.99
if default_freq in freq_options:
    frequency = st.select_slider("", options=freq_options, value=default_freq)
else:
    frequency = st.select_slider("", options=freq_options, value=freq_options[1])

low, mid, high = sorted(freq_options)
st.caption(
    f"−25% ({low:.2f})   •   Current ({mid:.2f})   •   +25% ({high:.2f})"
)

scenario_title.markdown(
    "<p style='text-align: center; color: #888; margin-bottom: 0;'>"
    "Selected policy scenario"
    "</p>"
    f"<h3 style='text-align: center; margin-top: 0;'>"
    f"{scenario_label(predictability, frequency)}"
    "</h3>",
    unsafe_allow_html=True
)
# Lookup the selected scenario row (no interpolation)
row = df[
    (df["predictability_numeric"] == predictability) &
    (df["frequency"] == frequency)
].iloc[0]

st.header("Policy outcomes")

st.caption(
    "Note: All outcomes are reported relative to a benchmark with no inspections. "
    "“Lives saved” reflects the annual reduction in patient deaths compared to a regime with zero inspections."
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Lives saved",
        f"{row['lives_saved_annually']:.1f}",
        help="Annual reduction in patient deaths relative to no inspections"
    )
    st.caption("per year")

with col2:
    st.metric(
        "Efficiency",
        f"{row['lives_saved_per_1000']:.1f}",
        help="Lives saved per 1,000 inspections"
    )
    st.caption("per 1,000 inspections")

with col3:
    st.metric(
        "Information",
        f"{row['info_percent']:.1f}%",
        help="How much regulators learn about facility quality"
    )
    st.caption("of maximum")

with col4:
    st.metric(
        "Total inspections",
        f"{int(frequency * 15615):,}",
        help="Annual inspections nationwide (frequency × 15,615 facilities)"
    )
    st.caption("inspections per year")
