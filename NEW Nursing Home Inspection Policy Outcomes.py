import pandas as pd
import numpy as np
import streamlit as st

df = pd.read_csv("figure9_summary_raw.csv")

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

# Discrete predictability options (exactly as in the table)
st.subheader("Inspection timing predictability")
st.caption("How predictable is inspection timing?")
predictability = st.select_slider(
    "",
    options=[0, 50, 100],
    value=50,
    format_func=lambda p: (
        "0% (scheduled)" if p == 0 else
        "50% (current)" if p == 50 else
        "100% (random)"
    )
)

# Discrete frequency options (only those available for the selected predictability)
st.subheader("Inspection frequency")
st.caption("How many inspections per facility per year?")

freq_options = (
    df.loc[df["predictability_numeric"] == predictability, "frequency"]
      .sort_values()
      .tolist()
)

# Pick the “current” frequency as default when possible
default_freq = 0.98 if predictability == 0 else 0.99
if default_freq in freq_options:
    frequency = st.select_slider("", options=freq_options, value=default_freq)
else:
    frequency = st.select_slider("", options=freq_options, value=freq_options[1])

# Optional: show the reference points you actually have
st.caption(f"Available options for this regime: {', '.join([str(x) for x in freq_options])}")

# Lookup the selected scenario row (no interpolation)
row = df[
    (df["predictability_numeric"] == predictability) &
    (df["frequency"] == frequency)
].iloc[0]

st.header("Policy outcomes")

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
