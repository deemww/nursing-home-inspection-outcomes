import pandas as pd
import streamlit as st
import altair as alt

# =============================
# Page config
# =============================
st.set_page_config(layout="wide")

# =============================
# Global CSS
# =============================
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #D9D9D9 !important; }

    /* Hide Altair/Vega-Lite chart action buttons (view data / export / open editor) */
    [data-testid="stVegaLiteChart"] .vega-actions { display: none !important; }

    /* ---- Gotham font faces ---- */
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Book.otf") format("opentype"); font-weight: 400; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-BookItalic.otf") format("opentype"); font-weight: 400; font-style: italic; }

    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Light.otf") format("opentype"); font-weight: 300; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-LightItalic.otf") format("opentype"); font-weight: 300; font-style: italic; }

    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Medium.otf") format("opentype"); font-weight: 500; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-MediumItalic.otf") format("opentype"); font-weight: 500; font-style: italic; }

    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Bold.otf") format("opentype"); font-weight: 700; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-BoldItalic.otf") format("opentype"); font-weight: 700; font-style: italic; }

    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Black.otf") format("opentype"); font-weight: 900; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-BlackItalic.otf") format("opentype"); font-weight: 900; font-style: italic; }

    /* ---- Apply Gotham everywhere in Streamlit UI ---- */
    html, body, [data-testid="stAppViewContainer"] * {
        font-family: "Gotham", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* ---- Sidebar section header ---- */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* ---- Sidebar widget label text ---- */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        margin-bottom: 0.25rem !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label span,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 1.15rem !important;
        line-height: 1.5 !important;
        margin: 0 !important;
    }

    /* Restore Material icon fonts */
    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] span,
    span.material-icons,
    span.material-icons-outlined,
    span.material-icons-round,
    span.material-icons-sharp,
    span.material-icons-two-tone,
    span.material-symbols-outlined,
    span.material-symbols-rounded,
    span.material-symbols-sharp,
    span[class^="material-symbols"],
    span[class*=" material-symbols"] {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    }

    /* ---- METRICS: bold label + value + caption text ---- */
    [data-testid="stMetricLabel"] p { font-weight: 700 !important; }
    [data-testid="stMetricValue"] { font-weight: 800 !important; }
    [data-testid="stMetricDelta"] { font-weight: 700 !important; }
    [data-testid="stCaptionContainer"] p { font-weight: 700 !important; }
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
# Precompute columns for 9-bar charts + stable selection key
# =============================
df["freq_round"] = df["frequency"].round(4)
df["scenario_key"] = (
    df["predictability_numeric"].astype(int).astype(str) + "_" + df["freq_round"].astype(str)
)
df["scenario_label"] = df.apply(
    lambda r: scenario_label(int(r["predictability_numeric"]), float(r["frequency"])),
    axis=1,
)

pred_order = {0: 0, 50: 1, 100: 2}
df["pred_order"] = df["predictability_numeric"].map(pred_order)
df = df.sort_values(["pred_order", "frequency"]).copy()
df["freq_rank"] = df.groupby("predictability_numeric").cumcount() + 1
df["x_order"] = df["pred_order"] * 10 + df["freq_rank"]

df["total_inspections"] = (df["frequency"] * 15615).round(0)

# =============================
# Fixed y-axis limits (constant across toggles)
# =============================
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["total_inspections"].max()) * 1.10),
}

def multi_bar_chart(df_all, metric_col, y_domain, y_label, chart_title, selected_key):
    base = alt.Chart(df_all).encode(
        x=alt.X(
            "scenario_label:N",
            title=None,
            sort=alt.SortField(field="x_order", order="ascending"),
            axis=alt.Axis(labels=False, ticks=False, domain=False),
        ),
        y=alt.Y(
            f"{metric_col}:Q",
            title=y_label,
            scale=alt.Scale(domain=list(y_domain), nice=False),
        ),
        tooltip=[
            alt.Tooltip("scenario_label:N", title="Scenario"),
            alt.Tooltip(f"{metric_col}:Q", format=",.2f", title=y_label),
        ],
    )

    bars = base.mark_bar(size=40, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        color=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#800000"),
            alt.value("#c9c9c9"),
        ),
        stroke=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#EAAA00"),
            alt.value(None),
        ),
        strokeWidth=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value(10),
            alt.value(0),
        ),
        opacity=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value(1.0),
            alt.value(0.55),
        ),
    )

    return (
        bars.properties(
            height=235,
            title=alt.TitleParams(
                text=chart_title,
                anchor="middle",
                fontSize=20,
                fontWeight="bold",
                offset=10,
            ),
            padding={"top": 8, "left": 10, "right": 10, "bottom": 5},
        )
        .configure(
            font="Gotham",
            axis=alt.AxisConfig(
                labelFont="Gotham",
                titleFont="Gotham",
                labelFontSize=14,
                titleFontSize=15.2,
                titleColor="#000000",
                labelColor="#000000",
                titleFontWeight="bold",
            ),
            title=alt.TitleConfig(font="Gotham", fontSize=20),
            legend=alt.LegendConfig(labelFont="Gotham", titleFont="Gotham"),
        )
    )

def get_freq_options(predictability_numeric):
    opts = (
        df.loc[df["predictability_numeric"] == predictability_numeric, "frequency"]
        .sort_values()
        .tolist()
    )
    low, mid, high = sorted(opts)
    return low, mid, high

# =============================
# Session defaults
# =============================
if "pred_choice" not in st.session_state:
    st.session_state["pred_choice"] = "Current regime (status quo)"
if "freq_position" not in st.session_state:
    st.session_state["freq_position"] = "Current"  # "−25%", "Current", "+25%"
# we will store the actual radio string in freq_choice; initialize lazily after we know options
if "freq_choice" not in st.session_state:
    st.session_state["freq_choice"] = None

# =============================
# Page header
# =============================
st.markdown(
    "<div style='text-align:center; margin-top:0.25rem;'>"
    "<h1 style='margin-bottom:0.25rem; color:#000000;'>Nursing Home Inspection Policy Outcomes</h1>"
    "<p style='font-size:1.25rem; font-weight:500; color:#000000; margin-top:0;'>"
    "Explore how inspection frequency and predictability affect lives saved, efficiency, and regulatory information."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)

# =============================
# Sidebar controls (FIXED: no jumping)
# =============================
pred_options = [
    "Unpredictable (random)",
    "Current regime (status quo)",
    "Perfectly predictable (scheduled)",
]
pred_map = {
    "Unpredictable (random)": 100,
    "Current regime (status quo)": 50,
    "Perfectly predictable (scheduled)": 0,
}

with st.sidebar:
    st.markdown("## Policy Controls")

    # Use key-based widget state; do not force index every rerun
    pred_choice = st.radio(
        "Inspection timing predictability",
        pred_options,
        key="pred_choice",
    )

    predictability = pred_map[pred_choice]
    low, mid, high = get_freq_options(predictability)

    freq_options = [
        f"−25% ({low:.2f})",
        f"Current ({mid:.2f})",
        f"+25% ({high:.2f})",
    ]

    # Ensure the stored freq_choice is valid for the current regime; otherwise set from freq_position
    pos_to_string = {
        "−25%": freq_options[0],
        "Current": freq_options[1],
        "+25%": freq_options[2],
    }
    if st.session_state["freq_choice"] not in freq_options:
        st.session_state["freq_choice"] = pos_to_string[st.session_state["freq_position"]]

    freq_choice = st.radio(
        "Inspection frequency",
        freq_options,
        key="freq_choice",
    )

    # Update stored position + set numeric frequency
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
# Selected scenario (main page)
# =============================
scenario = scenario_label(predictability, frequency)

st.markdown(
    f"""
    <div style='text-align:center; margin-top:0.4rem; margin-bottom:1.2rem;'>
        <div style='color:#000000; font-size:1.5rem; font-weight:700; margin-bottom:0.6rem;'>Selected Policy Scenario</div>
        <span style='
            display: inline-block;
            padding: 12px 24px;
            background-color: #800000;
            color: #ffffff;
            font-size: 1.6rem;
            font-weight: 800;
            border: 4px solid #EAAA00;
            border-radius: 12px;
            line-height: 1.1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            {scenario}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# Selected row (no interpolation)
# =============================
row = df[
    (df["predictability_numeric"] == predictability) & (df["frequency"] == frequency)
].iloc[0]

total_inspections = int(float(frequency) * 15615)
selected_key = f"{int(predictability)}_{round(float(frequency), 4)}"

# =============================
# Policy outcomes
# =============================
st.markdown("<h2 style='margin-bottom:0.25rem;'>Policy Outcomes</h2>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; font-size:0.85rem; color:rgba(0,0,0,0.6); margin-top:0.25rem;'>"
    "Note: All outcomes are reported relative to a benchmark with no inspections. "
    "“Lives saved” reflects the annual reduction in patient deaths compared to a regime with zero inspections."
    "</p>",
    unsafe_allow_html=True,
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
        "Inspection Efficiency",
        f"{float(row['lives_saved_per_1000']):.1f}",
        help="Lives saved per 1,000 inspections",
    )
    st.caption("per 1,000 inspections")

with col3:
    st.metric(
        "Regulatory information",
        f"{float(row['info_percent']):.1f}%",
        help="How much information inspections give regulators about a facility’s underlying quality, relative to no inspections.",
    )
    st.caption("about facility quality")

with col4:
    st.metric(
        "Total inspections",
        f"{total_inspections:,}",
        help="Annual inspections nationwide (frequency × 15,615 facilities)",
    )
    st.caption("inspections per year")

# Divider (tight spacing)
st.markdown(
    "<hr style='margin:0.5rem 0; border: none; border-top:1px solid rgba(0,0,0,0.15);'>",
    unsafe_allow_html=True,
)

# =============================
# Policy comparisons
# =============================
st.markdown("<h2 style='margin-bottom:0.25rem;'>Policy Comparisons</h2>", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align:center; font-size:0.85rem; color:rgba(0,0,0,0.6);'>"
    "Note: Each bar shows a different inspection policy. The highlighted bar corresponds to the selected policy shown above."
    "</p>",
    unsafe_allow_html=True,
)

p1, p2 = st.columns(2)
with p1:
    st.altair_chart(
        multi_bar_chart(
            df,
            "lives_saved_annually",
            Y_LIMS["lives_saved_annually"],
            "Lives saved",
            "Annual lives saved",
            selected_key,
        ),
        use_container_width=True,
    )

with p2:
    st.altair_chart(
        multi_bar_chart(
            df,
            "lives_saved_per_1000",
            Y_LIMS["lives_saved_per_1000"],
            "Lives per 1,000 inspections",
            "Efficiency (lives saved per 1,000 inspections)",
            selected_key,
        ),
        use_container_width=True,
    )

p3, p4 = st.columns(2)
with p3:
    st.altair_chart(
        multi_bar_chart(
            df,
            "info_percent",
            Y_LIMS["info_percent"],
            "Percent (%)",
            "Regulatory information revealed",
            selected_key,
        ),
        use_container_width=True,
    )

with p4:
    st.altair_chart(
        multi_bar_chart(
            df,
            "total_inspections",
            Y_LIMS["total_inspections"],
            "Inspections",
            "Total inspections conducted",
            selected_key,
        ),
        use_container_width=True,
    )
