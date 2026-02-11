import pandas as pd
import streamlit as st
import altair as alt

df = pd.read_csv("figure9_summary_raw.csv")

# -----------------------------
# Scenario label (Figure 9b col 1)
# -----------------------------
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

# -----------------------------
# Fixed y-axis limits (do not change when toggling)
# -----------------------------
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["frequency"].max() * 15615) * 1.10),
}

def single_bar_chart(value, x_label, y_domain, y_label, chart_title):
    d = pd.DataFrame({"metric": [x_label], "value": [float(value)]})
    chart = (
        alt.Chart(d)
        .mark_bar()
        .encode(
            x=alt.X(
                "metric:N",
                title=None,
                axis=alt.Axis(
                    labelAngle=0,
                    labelLimit=1000,   # prevent x label truncation
                    labelPadding=10
                ),
            ),
            y=alt.Y(
                "value:Q",
                title=y_label,
                scale=alt.Scale(domain=list(y_domain), nice=False),
            ),
            tooltip=[alt.Tooltip("value:Q", format=",.2f")],
        )
        .properties(
            height=240,  # slightly taller to avoid clipping
            title=alt.TitleParams(
                text=chart_title,
                anchor="start",
                fontSize=14,
                fontWeight="normal",
                offset=12,  # spacing between title and chart
            ),
            padding={"top": 10, "left": 10, "right": 10, "bottom": 20},
        )
    )
    return chart

# -----------------------------
# Page header
# -----------------------------
st.markdown(
    "<h1 style='text-align: center;'>Nursing Home Inspection Policy Outcomes</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size: 1.1em; color: #555;'>"
    "Explore how inspection frequency and predictability affect "
    "lives saved, efficiency, and regulatory information."
    "</p>",
    unsafe_allow_html=True,
)

# -----------------------------
# Policy controls (discrete only)
# -----------------------------
st.header("Policy controls")
scenario_title = st.empty()

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
    ),
)

# Map UI scale to CSV coding:
# CSV: 0 = perfectly predictable, 50 = current, 100 = fully random
predictability = 100 - predictability_ui

st.subheader("Inspection frequency")
st.caption("How many inspections per facility per year?")

freq_options = (
    df.loc[df["predictability_numeric"] == predictability, "frequency"]
    .sort_values()
    .tolist()
)

default_freq = 0.98 if predictability == 0 else 0.99
if default_freq in freq_options:
    frequency = st.select_slider("", options=freq_options, value=default_freq)
else:
    frequency = st.select_slider("", options=freq_options, value=freq_options[1])

low, mid, high = sorted(freq_options)
st.caption(f"−25% ({low:.2f})   •   Current ({mid:.2f})   •   +25% ({high:.2f})")

scenario_title.markdown(
    "<p style='text-align: center; color: #888; margin-bottom: 0;'>"
    "Selected policy scenario"
    "</p>"
    f"<h3 style='text-align: center; margin-top: 0;'>"
    f"{scenario_label(predictability, frequency)}"
    "</h3>",
    unsafe_allow_html=True,
)

# -----------------------------
# Selected row (no interpolation)
# -----------------------------
row = df[
    (df["predictability_numeric"] == predictability) &
    (df["frequency"] == frequency)
].iloc[0]

total_inspections = int(float(frequency) * 15615)

# -----------------------------
# Policy outcomes: keep boxes + add plots with fixed axes
# -----------------------------
st.header("Policy outcomes")

st.caption(
    "Note: All outcomes are reported relative to a benchmark with no inspections. "
    "“Lives saved” reflects the annual reduction in patient deaths compared to a regime with zero inspections."
)

# Metric boxes (kept)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Lives saved",
        f"{float(row['lives_saved_annually']):.1f}",
        help="Annual reduction in patient deaths relative to no inspections",
    )
    st.caption("per year")

with col2:
    st.metric(
        "Efficiency",
        f"{float(row['lives_saved_per_1000']):.1f}",
        help="Lives saved per 1,000 inspections",
    )
    st.caption("per 1,000 inspections")

with col3:
    st.metric(
        "Information",
        f"{float(row['info_percent']):.1f}%",
        help="How much regulators learn about facility quality",
    )
    st.caption("of maximum")

with col4:
    st.metric(
        "Total inspections",
        f"{total_inspections:,}",
        help="Annual inspections nationwide (frequency × 15,615 facilities)",
    )
    st.caption("inspections per year")

st.divider()

# Plots (fixed y-axes across toggles)
p1, p2 = st.columns(2)
with p1:
    st.altair_chart(
        single_bar_chart(
            float(row["lives_saved_annually"]),
            "Lives saved (annual)",
            Y_LIMS["lives_saved_annually"],
            "Lives saved",
            "Annual lives saved",
        ),
        use_container_width=True,
    )

with p2:
    st.altair_chart(
        single_bar_chart(
            float(row["lives_saved_per_1000"]),
            "Lives saved per 1,000",
            Y_LIMS["lives_saved_per_1000"],
            "Lives per 1,000 inspections",
            "Lives saved per 1,000 inspections",  
        ),
        use_container_width=True,
    )

p3, p4 = st.columns(2)
with p3:
    st.altair_chart(
        single_bar_chart(
            float(row["info_percent"]),
            "Information (%)",
            Y_LIMS["info_percent"],
            "Percent",
            "Regulatory information revealed",
        ),
        use_container_width=True,
    )

with p4:
    st.altair_chart(
        single_bar_chart(
            float(total_inspections),
            "Total inspections",
            Y_LIMS["total_inspections"],
            "Inspections",
            "Total inspections conducted",
        ),
        use_container_width=True,
    )
