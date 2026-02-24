import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>

    [data-testid="stSidebar"] { background-color: #D9D9D9 !important; }

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

    html, body, [data-testid="stAppViewContainer"] * {
        font-family: "Gotham", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;}

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
# Scenario label
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
# Precompute columns + stable key
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
# Fixed y-axis limits
# =============================
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["total_inspections"].max()) * 1.10),
}

# =============================
# Sidebar option helpers
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
pred_to_label = {
    100: "Unpredictable (random)",
    50: "Current regime (status quo)",
    0: "Perfectly predictable (scheduled)",
}

def get_freq_options(predictability_numeric):
    opts = (
        df.loc[df["predictability_numeric"] == predictability_numeric, "frequency"]
        .sort_values()
        .tolist()
    )
    low, mid, high = sorted(opts)
    return low, mid, high

def sync_sidebar_from_selected_key(selected_key: str) -> None:
    r = df.loc[df["scenario_key"] == selected_key].iloc[0]
    pred = int(r["predictability_numeric"])
    freq = float(r["frequency"])

    st.session_state["pred_choice"] = pred_to_label[pred]

    low, mid, high = get_freq_options(pred)
    freq_options = [
        f"−25% ({low:.2f})",
        f"Current ({mid:.2f})",
        f"+25% ({high:.2f})",
    ]

    if freq == float(low):
        st.session_state["freq_position"] = "−25%"
        st.session_state["freq_choice"] = freq_options[0]
    elif freq == float(mid):
        st.session_state["freq_position"] = "Current"
        st.session_state["freq_choice"] = freq_options[1]
    else:
        st.session_state["freq_position"] = "+25%"
        st.session_state["freq_choice"] = freq_options[2]

# =============================
# Session defaults
# =============================
if "selected_key" not in st.session_state:
    low0, mid0, high0 = get_freq_options(50)
    st.session_state["selected_key"] = f"50_{round(float(mid0), 4)}"

if "pred_choice" not in st.session_state:
    st.session_state["pred_choice"] = "Current regime (status quo)"
if "freq_position" not in st.session_state:
    st.session_state["freq_position"] = "Current"
if "freq_choice" not in st.session_state:
    st.session_state["freq_choice"] = None

# Keep sidebar aligned with the selected key on load / rerun
sync_sidebar_from_selected_key(st.session_state["selected_key"])

# =============================
# Click-to-select plumbing (Streamlit selection state)
# =============================
SCENARIO_SELECT_PARAM = "scenario_select"

def extract_selected_key_from_event(event) -> str | None:
    """
    Streamlit returns a VegaLiteState-like object with a `.selection` attribute (and dict access).
    The selected data is under: event.selection[SCENARIO_SELECT_PARAM]
    and for a point selection on field 'scenario_key' it will include 'scenario_key'.
    """
    if not event:
        return None

    # event.selection is the documented location for selection state
    sel = None
    try:
        sel = event.selection
    except Exception:
        sel = event.get("selection") if hasattr(event, "get") else None

    if not sel:
        return None

    param_state = None
    try:
        param_state = sel.get(SCENARIO_SELECT_PARAM)
    except Exception:
        param_state = None

    if not param_state:
        return None

    val = param_state.get("scenario_key") if isinstance(param_state, dict) else None
    if val is None:
        return None

    if isinstance(val, list):
        return val[0] if val else None
    if isinstance(val, dict):
        return val.get("value")
    if isinstance(val, str):
        return val
    return None

def make_chart(df_all, metric_col, y_domain, y_label, chart_title, selected_key_for_style):
    click_sel = alt.selection_point(
        name=SCENARIO_SELECT_PARAM,
        fields=["scenario_key"],
        on="click",
        empty=True,
        clear="dblclick",
    )

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
            alt.datum.scenario_key == selected_key_for_style,
            alt.value("#800000"),
            alt.value("#c9c9c9"),
        ),
        stroke=alt.condition(
            alt.datum.scenario_key == selected_key_for_style,
            alt.value("#EAAA00"),
            alt.value(None),
        ),
        strokeWidth=alt.condition(
            alt.datum.scenario_key == selected_key_for_style,
            alt.value(10),
            alt.value(0),
        ),
        opacity=alt.condition(
            alt.datum.scenario_key == selected_key_for_style,
            alt.value(1.0),
            alt.value(0.55),
        ),
    )

    return (
        bars.add_params(click_sel)
        .properties(
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

def make_on_select_callback(chart_state_key: str):
    # Called BEFORE the script reruns; safe to mutate session_state for widgets.
    def _cb():
        event = st.session_state.get(chart_state_key)
        clicked = extract_selected_key_from_event(event)
        if clicked and clicked != st.session_state.get("selected_key"):
            st.session_state["selected_key"] = clicked
            sync_sidebar_from_selected_key(clicked)
    return _cb

def render_selectable_chart(chart, chart_state_key: str):
    # key=chart_state_key stores a read-only selection state in st.session_state[chart_state_key]
    st.altair_chart(
        chart,
        use_container_width=True,
        key=chart_state_key,
        on_select=make_on_select_callback(chart_state_key),
        selection_mode=SCENARIO_SELECT_PARAM,
    )

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
# Sidebar controls (still available)
# =============================
with st.sidebar:
    st.markdown("## Policy Controls")

    pred_choice = st.radio(
        "Inspection timing predictability",
        pred_options,
        key="pred_choice",
    )

    predictability_sidebar = pred_map[pred_choice]
    low, mid, high = get_freq_options(predictability_sidebar)

    freq_options = [
        f"−25% ({low:.2f})",
        f"Current ({mid:.2f})",
        f"+25% ({high:.2f})",
    ]

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

    if freq_choice.startswith("−25%"):
        st.session_state["freq_position"] = "−25%"
        frequency_sidebar = float(low)
    elif freq_choice.startswith("Current"):
        st.session_state["freq_position"] = "Current"
        frequency_sidebar = float(mid)
    else:
        st.session_state["freq_position"] = "+25%"
        frequency_sidebar = float(high)

    # Sidebar overrides the selection key too
    st.session_state["selected_key"] = f"{int(predictability_sidebar)}_{round(float(frequency_sidebar), 4)}"

# =============================
# Selected scenario (source of truth: selected_key)
# =============================
selected_key = st.session_state["selected_key"]
row = df.loc[df["scenario_key"] == selected_key].iloc[0]

predictability = int(row["predictability_numeric"])
frequency = float(row["frequency"])
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
        <div style='margin-top:0.5rem; font-size:0.9rem; color:rgba(0,0,0,0.6);'>
            Tip: Click a bar below to select that scenario (double-click blank space to clear).
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# Policy outcomes
# =============================
total_inspections = int(float(frequency) * 15615)

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

st.markdown(
    "<hr style='margin:0.5rem 0; border: none; border-top:1px solid rgba(0,0,0,0.15);'>",
    unsafe_allow_html=True,
)

# =============================
# Policy comparisons (clickable charts)
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
    render_selectable_chart(
        make_chart(
            df,
            "lives_saved_annually",
            Y_LIMS["lives_saved_annually"],
            "Lives saved",
            "Annual lives saved",
            selected_key,
        ),
        chart_state_key="chart_lives_saved_annually",
    )

with p2:
    render_selectable_chart(
        make_chart(
            df,
            "lives_saved_per_1000",
            Y_LIMS["lives_saved_per_1000"],
            "Lives per 1,000 inspections",
            "Efficiency (lives saved per 1,000 inspections)",
            selected_key,
        ),
        chart_state_key="chart_lives_saved_per_1000",
    )

p3, p4 = st.columns(2)
with p3:
    render_selectable_chart(
        make_chart(
            df,
            "info_percent",
            Y_LIMS["info_percent"],
            "Percent (%)",
            "Regulatory information revealed",
            selected_key,
        ),
        chart_state_key="chart_info_percent",
    )

with p4:
    render_selectable_chart(
        make_chart(
            df,
            "total_inspections",
            Y_LIMS["total_inspections"],
            "Inspections",
            "Total inspections conducted",
            selected_key,
        ),
        chart_state_key="chart_total_inspections",
    )
