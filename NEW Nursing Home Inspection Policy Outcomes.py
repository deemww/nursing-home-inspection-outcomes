import pandas as pd
import numpy as np
import streamlit as st

df = pd.read_csv("figure9_summary_raw.csv")

def interpolate(freq, pred, outcome_col):

    def interp_at(p):
        subset = df[df["predictability_numeric"] == p].sort_values("frequency")

        if p == 0:
            baseline_freq = 0.98
        else:
            baseline_freq = 0.99

        if abs(freq - baseline_freq) < 0.02:
            return subset.loc[
                (subset["frequency"] - baseline_freq).abs().idxmin(),
                outcome_col]

        return np.interp(freq,subset["frequency"].values,
            subset[outcome_col].values,left=subset[outcome_col].iloc[0],
            right=subset[outcome_col].iloc[-1])

    v0 = interp_at(0)      
    v50 = interp_at(50)    
    v100 = interp_at(100)  

    if pred <= 50:
        return v0 + (pred / 50) * (v50 - v0)
    else:
        return v50 + ((pred - 50) / 50) * (v100 - v50)

st.markdown(
    "<h1 style='text-align: center;'>Nursing Home Inspection Policy Outcomes</h1>",
    unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; color: #555;'>"
    "Explore how inspection frequency and predictability affect " \
    "lives saved, efficiency, and regulatory information."
    "</p>",unsafe_allow_html=True)

st.header("Policy controls")

st.subheader("Inspection frequency")
st.caption("How many inspections per facility per year?")

frequency = st.slider("",0.5, 1.5, 0.99, 0.01)

st.caption("Reference points: 0.74 (−25%), 0.99 (current), 1.25 (+25%)")

st.subheader("Inspection timing predictability")
st.caption("How predictable is inspection timing?")

predictability = st.slider("",0, 100, 50)

st.caption("0% = fully scheduled • 50% = current regime • 100% = fully random")


st.header("Policy outcomes")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Lives saved",
        f"{round(interpolate(frequency, predictability, 'lives_saved_annually'), 1)}",
        help="Annual reduction in patient deaths relative to no inspections")
    st.caption("per year")

with col2:
    st.metric(
        "Efficiency",
        f"{round(interpolate(frequency, predictability, 'lives_saved_per_1000'), 1)}",
        help="Lives saved per 1,000 inspections")
    st.caption("per 1,000 inspections")

with col3:
    st.metric(
        "Information",
        f"{round(interpolate(frequency, predictability, 'info_percent'), 1)}%",
        help="How much regulators learn about facility quality")
    st.caption("of maximum")

with col4:
    st.metric("Cost",
        f"{int(frequency * 15615):,}",
        help="Annual inspections nationwide")
    st.caption("inspections per year")
