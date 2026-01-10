import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.markdown(
    "<h1 style='text-align: center;'>Why Predictability Matters: Nursing Home Effort Over Time</h1>",
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

chart = alt.Chart(df).transform_fold(
    ["Predictable timing", "Random timing"],
    as_=["variable", "value"]
).mark_line(strokeWidth=3).encode(
    x=alt.X("Weeks since last inspection:Q", title="Weeks since last inspection"),
    y=alt.Y(
        "value:Q",
        title="Effort (staffing level)",
        scale=alt.Scale(domain=[0.7, 1.3])
    ),
    color=alt.Color(
        "variable:N",
        title="Inspection timing",
        scale=alt.Scale(
            domain=["Predictable timing", "Random timing"],
            range=["#d62728", "#228B22"]  # red, green
        )
    ),
    strokeDash=alt.StrokeDash(
        "variable:N",
        scale=alt.Scale(
            domain=["Predictable timing", "Random timing"],
            range=[[1, 0], [6, 4]]   # solid, dashed
        )
    )
)

st.altair_chart(chart, use_container_width=True)
