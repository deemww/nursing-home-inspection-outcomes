import numpy as np
import pandas as pd
import streamlit as st

st.markdown(
    "<h1 style='text-align: center;'>Inspection Timing and Strategic Effort</h1>",
    unsafe_allow_html=True)

st.markdown(
    "<p style='text-align: center; font-size: 1.1em; color: #555;'>"
    "How predictability in inspection timing shapes how nursing homes allocate staffing over time."
    "</p>",
    unsafe_allow_html=True)

st.header("Policy control")

st.subheader("Inspection timing predictability")
st.caption("How predictable is inspection timing?")

predictability = st.slider("", 0, 100, 50)
st.caption("0% = fully scheduled • 50% = current regime • 100% = fully random")

st.header("Mechanism")

st.caption(
    "When inspections are predictable, facilities reduce staffing after an inspection "
    "and increase it as the next inspection approaches. Random timing removes this incentive.")

weeks = np.arange(0, 61)

strength = 1 - (predictability / 100)

baseline = 1.0
max_amp = 0.25
amp = max_amp * strength

shape = ((weeks - 30) / 30) ** 2
effort_predictable = baseline + amp * (2 * shape - 1)

effort_random = np.full_like(weeks, baseline, dtype=float)

df = pd.DataFrame({
    "Weeks since last inspection": weeks,
    "Predictable timing": effort_predictable,
    "Random timing": effort_random})

st.line_chart(
    df.set_index("Weeks since last inspection"),
    height=350)
