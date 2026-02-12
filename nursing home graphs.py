import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",  # keep sidebar visible (no “off-screen” feel)
)

# =============================
# CSS: eliminate horizontal scroll + force charts to respect container width
# =============================
st.markdown(
    """
    <style>
      /* Hard kill any horizontal scrolling anywhere */
      html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; }

      /* Make the main content never exceed viewport width */
      [data-testid="stAppViewContainer"] > .main { max-width: 100vw; }

      /* Vega/Altair sometimes creates a min-width; force it to shrink-to-fit */
      div[data-testid="stVegaLiteChart"] { width: 100% !important; overflow-x: hidden !important; }
      div[data-testid="stVegaLiteChart"] > div { width: 100% !important; }
      .vega-embed { width: 100% !important; max-width: 100% !important; }
      .vega-embed summary { display: none; } /* hides the little '...' menu that can add width */

      /* Ensure column rows can wrap on narrower screens */
      @media (max-width: 1100px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Data
# =============================
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

    chart = (
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
        # Critical: tell Vega to fit the container (prevents min-width overflow)
        .properties(
            width="container",
            height=235,
            title=alt.TitleParams(
                text=chart_title,
                anchor="start",
                fontSize=14,
                fontWeight="normal",
                offset=10,
            ),
            padding={"top": 8, "left": 10, "right": 10, "bottom": 18},
        )
        .configure_autosize(type="fit", contains="padding")
        .configure_view(stroke=None)
    )
    return chart

# =============================
# Helper: get regime-specific frequency options
# =============================
def get_freq_options(predictability_numeric):
    opts = (
        df.loc[df["predictability_numeric"] == predictability_numeric, "frequency"]
        .sort_values()
        .tolist()
    )
    low, mid, high = sorted(opts)
    return low, mid, high

# =============================
# Session defaults (prevents radios from “jumping”)
# =============================
if "pred_choice" not in st.session_state:
    st.session_state["pred_choice"] = "Current regime (factual)"
if "freq_position" not in st.session_state:
    st.session_state["freq_position"] = "Current"  # one of: "−25%", "Current", "+25%"

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
# Sidebar controls
# =============================
with st.sidebar:
    st.markdown("## Policy controls")

    pred_options = [
        "Unpredictable (random)",
        "Current regime (factual)",
        "Perfectly predictable (scheduled)",
    ]
    pred_choice = st.radio(
        "Inspection timing predictability",
        pred_options,
        index=pred_options.index(st.session_state["pred_choice"]),
    )
    st.session_state["pred_choice"] = pred_choice

    pred_map = {
        "Unpredictable (random)": 100,
        "Current regime (factual)": 50,
        "Perfectly predictable (scheduled)": 0,
    }
    predictability = pred_map[pred_choice]

    low, mid, high = get_freq_options(predictability)

    freq_options = [
        f"−25% ({low:.2f})",
        f"Current ({mid:.2f})",
        f"+25% ({high:.2f})",
    ]

    pos_to_index = {"−25%": 0, "Current": 1, "+25%": 2}
    default_index = pos_to_index[st.session_state["freq_position"]]

    freq_choice = st.radio(
        "Inspection frequency",
        freq_options,
        index=default_index,
    )

    if freq_choice.startswith("−25%"):
        st.session_state["freq_position"] = "−25%"
        frequency = float(low)
    elif freq_choice.startswith("Current"):
        st.session_state["freq_position"] = "Current"
        frequency = float(mid)
    else:
        st.session_state["freq_position"] = "+25%"
        frequency = float(high)

# =============================
# Selected scenario
# =============================
scenario = scenario_label(predictability, frequency)

st.markdown(
    "<div style='text-align:center; margin-top:0.4rem; margin-bottom:0.85rem;'>"
    "<div style='color:#8b8b8b; font-size:0.95rem; margin-bottom:0.1rem;'>Selected policy scenario</div>"
    f"<div style='font-size:1.65rem; font-weight:800; line-height:1.1;'>{scenario}</div>"
    "</div>",
    unsafe_allow_html=True,
)

# =============================
# Selected row
# =============================
row = df[
    (df["predictability_numeric"] == predictability)
    & (df["frequency"] == frequency)
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

# 2x2 metrics (prevents the 1x4 row from forcing overflow)
m1, m2 = st.columns(2)
with m1:
    st.metric(
        "Lives saved",
        f"{float(row['lives_saved_annually']):.1f}",
        help="Annual reduction in patient deaths relative to no inspections",
    )
    st.caption("per year")

with m2:
    st.metric(
        "Efficiency",
        f"{float(row['lives_saved_per_1000']):.1f}",
        help="Lives saved per 1,000 inspections",
    )
    st.caption("per 1,000 inspections")

m3, m4 = st.columns(2)
with m3:
    st.metric(
        "Information",
        f"{float(row['info_percent']):.1f}%",
        help="How much regulators learn about facility quality",
    )
    st.caption("of maximum")

with m4:
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
