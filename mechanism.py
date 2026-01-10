import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.markdown(
    "<h1 style='text-align: center;'>Why Predictability Matters: Nursing Home Effort Over Time</h1>",
    unsafe_allow_html=True
)

st.header("Policy control")

st.subheader("Inspection timing predictability")
st.caption("How predictable is inspection timing?")

predictability = st.slider("", 0, 100, 50)
st.caption("0% = fully scheduled • 50% = current regime • 100% = fully random")

st.header("Mechanism")

st.caption(
    "When inspections are predictable, facilities reduce staffing after an inspection "
    "and increase it as the next inspection approaches. Random timing removes this incentive."
)

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
    "Random timing": effort_random
})

long_df = df.melt(
    id_vars="Weeks since last inspection",
    var_name="Inspection timing",
    value_name="Effort"
)

base = alt.Chart(long_df).mark_line(strokeWidth=3).encode(
    x=alt.X("Weeks since last inspection:Q", title="Weeks since last inspection"),
    y=alt.Y("Effort:Q", title="Effort (staffing level)", scale=alt.Scale(domain=[0.7, 1.3])),
    color=alt.Color(
        "Inspection timing:N",
        scale=alt.Scale(
            domain=["Predictable timing", "Random timing"],
            range=["#d62728", "#228B22"]
        )
    ),
    strokeDash=alt.StrokeDash(
        "Inspection timing:N",
        scale=alt.Scale(
            domain=["Predictable timing", "Random timing"],
            range=[[1, 0], [6, 4]]
        )
    )
)

labels = pd.DataFrame({
    "Weeks since last inspection": [30, 55, 40],
    "Effort": [0.88, 1.12, 1.00],
    "Label": ["Low effort", "Ramping up", "Consistent effort"]
})

label_layer = alt.Chart(labels).mark_text(
    color="#cccccc",
    fontSize=13
).encode(
    x="Weeks since last inspection:Q",
    y="Effort:Q",
    text="Label:N"
)

final_chart = base + label_layer

st.altair_chart(final_chart, use_container_width=True)
