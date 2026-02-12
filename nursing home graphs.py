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
# Fixed y-axis limits (constant across toggles)
# -----------------------------
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["frequency"].max() * 15615) * 1.10),
}

def single_bar_chart(value, x_label, y_domain, y_label, chart_title):
    d = pd.DataFrame({"metric": [x_label], "value": [float(value)]})
    return (
        alt.Chart(d)
        .mark_bar(color="#800000", size=60, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "metric:N",
                title=None,
                axis=alt.Axis(labelAngle=0, labelLimit=1000, labelPadding=10, ticks=False),
            ),
            y=alt.Y(
                "value:Q",
                title=y_label,
                scale=alt.Scale(domain=list(y_domain), nice=False),
            ),
            tooltip=[alt.Tooltip("value:Q", format=",.2f")],
        )
        .properties(
            height=235,
            title=alt.TitleParams(text=chart_title, anchor="start", fontSize=14, fontWeight="normal", offset=10),
            padding={"top": 8, "left": 10, "right": 10, "bottom": 18},
        )
    )

# -----------------------------
# Page header
# -----------------------------
st.markdown(
    "<div style='text-align:center; margin-top:0.25rem;'>"
    "<h1 style='margin-bottom:0.25rem;'>Nursing Home Inspection Policy Outcomes</h1>"
    "<p style='font-size:1.05rem; color:#8b8b8b; margin-top:0;'>"
    "Explore how inspection frequency and predictability affect lives saved, efficiency, and regulatory information."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)

# -----------------------------
# Policy controls (set first)
# -----------------------------
st.markdown("<h2 style='margin-bottom:0.5rem;'>Policy controls</h2>", unsafe_allow_html=True)

c1, c2 = st.columns(2, vertical_alignment="top")

with c1:
    st.markdown(
        "<div style='font-weight:600; margin-bottom:0.25rem;'>Inspection timing predictability</div>",
        unsafe_allow_html=True,
    )
    pred_choice = st.radio(
        label="",
        options=[
            "Unpredictable (random)",
            "Current regime (factual)",
            "Perfectly predictable (scheduled)",
        ],
        index=1,
    )

# Map to CSV coding:
# CSV: 0 = perfectly predictable, 50 = current, 100 = fully random
pred_map = {
    "Unpredictable (random)": 100,
    "Current regime (factual)": 50,
    "Perfectly predictable (scheduled)": 0,
}
predictability = pred_map[pred_choice]

# Frequency options for chosen regime
freq_options = (
    df.loc[df["predictability_numeric"] == predictability, "frequency"]
    .sort_values()
    .tolist()
)
low, mid, high = sorted(freq_options)

with c2:
    st.markdown(
        "<div style='font-weight:600; margin-bottom:0.25rem;'>Inspection frequency</div>",
        unsafe_allow_html=True,
    )
    freq_choice = st.radio(
        label="",
        options=[
            f"−25% ({low:.2f})",
            f"Current ({mid:.2f})",
            f"+25% ({high:.2f})",
        ],
        index=1,
    )

freq_map = {
    f"−25% ({low:.2f})": low,
    f"Current ({mid:.2f})": mid,
    f"+25% ({high:.2f})": high,
}
frequency = float(freq_map[freq_choice])

# -----------------------------
# Selected policy scenario (moved ABOVE outcomes, but visually tied to controls)
# -----------------------------
scenario = scenario_label(predictability, frequency)
st.markdown(
    "<div style='text-align:center; margin-top:0.6rem; margin-bottom:0.85rem;'>"
    "<div style='color:#8b8b8b; font-size:0.95rem; margin-bottom:0.1rem;'>Selected policy scenario</div>"
    f"<div style='font-size:1.55rem; font-weight:700; line-height:1.1;'>{scenario}</div>"
    "</div>",
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
# Policy outcomes
# -----------------------------
st.markdown("<h2 style='margin-bottom:0.25rem;'>Policy outcomes</h2>", unsafe_allow_html=True)
st.caption(
    "Note: All outcomes are reported relative to a benchmark with no inspections. "
    "“Lives saved” reflects the annual reduction in patient deaths compared to a regime with zero inspections."
)

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
            "Efficiency (lives saved per 1,000 inspections)",
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
