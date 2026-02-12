import pandas as pd
import streamlit as st
import altair as alt

df = pd.read_csv("figure9_summary_raw.csv")

# =============================
# Scenario label (Figure 9b col 1)
# =============================
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

# =============================
# Fixed y-axis limits (constant across toggles)
# =============================
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

# =============================
# UI helpers
# =============================
REGIME_OPTIONS = {
    "Unpredictable (random)": 100,
    "Current regime (factual)": 50,
    "Perfectly predictable (scheduled)": 0,
}

def regime_mid_frequency(predictability):
    opts = (
        df.loc[df["predictability_numeric"] == predictability, "frequency"]
        .sort_values()
        .tolist()
    )
    low, mid, high = sorted(opts)
    return low, mid, high

def card_html(title, subtitle, selected=False):
    # Dark-theme friendly card styling; no fragile widget CSS overrides
    bg = "rgba(255,255,255,0.06)" if selected else "rgba(255,255,255,0.03)"
    border = "1px solid rgba(255,255,255,0.22)" if selected else "1px solid rgba(255,255,255,0.10)"
    badge = (
        "<span style='font-size:0.75rem; padding:0.15rem 0.45rem; border-radius:999px; "
        "background:rgba(128,0,0,0.35); border:1px solid rgba(128,0,0,0.65);'>Selected</span>"
        if selected else ""
    )

    return f"""
    <div style="
        background:{bg};
        border:{border};
        border-radius:14px;
        padding:14px 14px 12px 14px;
        min-height:110px;
    ">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
        <div style="font-weight:700; font-size:1.05rem; line-height:1.2;">{title}</div>
        {badge}
      </div>
      <div style="margin-top:6px; color:rgba(255,255,255,0.72); font-size:0.95rem; line-height:1.25;">
        {subtitle}
      </div>
    </div>
    """

# =============================
# Defaults
# =============================
if "regime_label" not in st.session_state:
    st.session_state["regime_label"] = "Current regime (factual)"
if "freq_choice" not in st.session_state:
    st.session_state["freq_choice"] = "Current"

# =============================
# Page header
# =============================
st.markdown(
    "<div style='text-align:center; margin-top:0.25rem;'>"
    "<h1 style='margin-bottom:0.25rem;'>Nursing Home Inspection Policy Outcomes</h1>"
    "<p style='font-size:1.05rem; color:#8b8b8b; margin-top:0;'>"
    "Explore how inspection frequency and predictability affect lives saved, efficiency, and regulatory information."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)

# =============================
# DESIGN DIRECTION 1:
# "Policy scenario cards" (primary) + frequency modifier (secondary)
# =============================
st.markdown("<h2 style='margin-bottom:0.4rem;'>Policy scenario</h2>", unsafe_allow_html=True)
st.caption("Select the inspection timing regime (as in Figure 9b), then adjust inspection frequency.")

# --- Cards row
cols = st.columns(3, vertical_alignment="top")
for i, label in enumerate(REGIME_OPTIONS.keys()):
    pred_val = REGIME_OPTIONS[label]
    low, mid, high = regime_mid_frequency(pred_val)

    # Card text: regime explanation + the “current” frequency for that regime
    if label.startswith("Unpredictable"):
        subtitle = f"Random inspection timing<br><span style='opacity:0.95;'>Baseline frequency: {mid:.2f} inspections per facility-year</span>"
    elif label.startswith("Current"):
        subtitle = f"Factual (current) timing regime<br><span style='opacity:0.95;'>Baseline frequency: {mid:.2f} inspections per facility-year</span>"
    else:
        subtitle = f"Scheduled (perfectly predictable) timing<br><span style='opacity:0.95;'>Baseline frequency: {mid:.2f} inspections per facility-year</span>"

    selected = (st.session_state["regime_label"] == label)

    with cols[i]:
        st.markdown(card_html(label, subtitle, selected=selected), unsafe_allow_html=True)
        # Action row
        if not selected:
            if st.button("Select", key=f"select_{i}", use_container_width=True):
                st.session_state["regime_label"] = label
                st.session_state["freq_choice"] = "Current"
        else:
            st.caption(" ")

# --- Secondary control: frequency modifier
predictability = REGIME_OPTIONS[st.session_state["regime_label"]]
low, mid, high = regime_mid_frequency(predictability)

st.markdown("<h3 style='margin-top:0.8rem; margin-bottom:0.2rem;'>Inspection frequency</h3>", unsafe_allow_html=True)
freq_choice = st.radio(
    label="",
    options=["−25%", "Current", "+25%"],
    index=["−25%", "Current", "+25%"].index(st.session_state["freq_choice"]),
    horizontal=True,
)
st.session_state["freq_choice"] = freq_choice
st.caption(f"−25% = {low:.2f} • Current = {mid:.2f} • +25% = {high:.2f} inspections per facility-year")

freq_map = {"−25%": low, "Current": mid, "+25%": high}
frequency = float(freq_map[freq_choice])

# --- Scenario callout (centered)
scenario = scenario_label(predictability, frequency)
st.markdown(
    "<div style='text-align:center; margin-top:0.6rem; margin-bottom:0.85rem;'>"
    "<div style='color:#8b8b8b; font-size:0.95rem; margin-bottom:0.1rem;'>Selected policy scenario</div>"
    f"<div style='font-size:1.55rem; font-weight:800; line-height:1.1;'>{scenario}</div>"
    "</div>",
    unsafe_allow_html=True,
)

# =============================
# Selected row (no interpolation)
# =============================
row = df[
    (df["predictability_numeric"] == predictability) &
    (df["frequency"] == frequency)
].iloc[0]

total_inspections = int(float(frequency) * 15615)

# =============================
# Policy outcomes
# =============================
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
