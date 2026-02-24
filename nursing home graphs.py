import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# =============================
# Styling
# =============================
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
        font-weight: 700 !important;
    }

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
# Sidebar options
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
pred_to_label = {100: pred_options[0], 50: pred_options[1], 0: pred_options[2]}

def get_freq_options(predictability_numeric):
    opts = (
        df.loc[df["predictability_numeric"] == predictability_numeric, "frequency"]
        .sort_values()
        .tolist()
    )
    low, mid, high = sorted(opts)
    return low, mid, high

# =============================
# Chart click parsing
# =============================
POINT_PARAM = "point_selection"
CHART_KEYS = [
    "vega_lives_saved_annually",
    "vega_lives_saved_per_1000",
    "vega_info_percent",
    "vega_total_inspections",
]

def parse_clicked_key_from_chart_state(chart_state) -> str | None:
    if not chart_state:
        return None

    sel = getattr(chart_state, "selection", None)
    if sel is None and isinstance(chart_state, dict):
        sel = chart_state.get("selection")

    if not sel or not isinstance(sel, dict):
        return None

    point = sel.get(POINT_PARAM)
    if point is None:
        return None

    # list of records
    if isinstance(point, list):
        if not point:
            return None
        first = point[0]
        return first.get("scenario_key") if isinstance(first, dict) else None

    # dict form
    if isinstance(point, dict):
        val = point.get("scenario_key")

        if isinstance(val, dict):
            if "value" in val:
                return val["value"]
            return val.get("scenario_key")

        if isinstance(val, list):
            return val[0] if val else None

        if isinstance(val, str):
            return val

        return None

    # direct string (rare)
    if isinstance(point, str):
        return point

    return None

# =============================
# Sidebar state sync
# =============================
def set_radios_from_selected_key(selected_key: str) -> None:
    """Safe ONLY before widgets are created."""
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
        st.session_state["freq_choice"] = freq_options[0]
    elif freq == float(mid):
        st.session_state["freq_choice"] = freq_options[1]
    else:
        st.session_state["freq_choice"] = freq_options[2]

def update_selected_key_from_sidebar():
    """
    Widget callback:
    - sidebar is source of truth
    - mark last_action so chart clicks are not re-applied
    """
    st.session_state["last_action"] = "sidebar"

    pred = pred_map[st.session_state["pred_choice"]]
    low, mid, high = get_freq_options(pred)

    fc = st.session_state["freq_choice"]
    if fc.startswith("−25%"):
        freq = float(low)
    elif fc.startswith("Current"):
        freq = float(mid)
    else:
        freq = float(high)

    st.session_state["selected_key"] = f"{int(pred)}_{round(float(freq), 4)}"

# =============================
# NEW: detect which chart changed (so all 4 charts can click-select)
# =============================
def get_new_chart_click() -> str | None:
    """
    Return the scenario_key from whichever chart has a NEW selection
    (different from what we saw last time). If multiple changed (rare),
    the first in CHART_KEYS order wins.
    """
    last_seen = st.session_state.get("last_seen_by_chart", {})
    for k in CHART_KEYS:
        clicked = parse_clicked_key_from_chart_state(st.session_state.get(k))
        if clicked and clicked != last_seen.get(k):
            return clicked
    return None

def mark_chart_clicks_as_seen():
    """Consume current chart selections by storing them as last-seen values."""
    last_seen = st.session_state.get("last_seen_by_chart", {})
    for k in CHART_KEYS:
        last_seen[k] = parse_clicked_key_from_chart_state(st.session_state.get(k))
    st.session_state["last_seen_by_chart"] = last_seen

def apply_chart_click_if_any():
    """
    MUST run before sidebar widgets are created.

    - If rerun came from sidebar, do not apply chart clicks.
      Just consume current chart selections so they can't override later.
    - Otherwise, apply the one NEW chart click (from any of the 4 charts).
    """
    if st.session_state.get("last_action") == "sidebar":
        mark_chart_clicks_as_seen()
        st.session_state["last_action"] = None
        return

    clicked = get_new_chart_click()
    if not clicked:
        return

    st.session_state["selected_key"] = clicked
    set_radios_from_selected_key(clicked)
    mark_chart_clicks_as_seen()

# =============================
# Session defaults
# =============================
if "selected_key" not in st.session_state:
    _, mid0, _ = get_freq_options(50)
    st.session_state["selected_key"] = f"50_{round(float(mid0), 4)}"

if "pred_choice" not in st.session_state or "freq_choice" not in st.session_state:
    set_radios_from_selected_key(st.session_state["selected_key"])

if "last_seen_by_chart" not in st.session_state:
    st.session_state["last_seen_by_chart"] = {k: None for k in CHART_KEYS}

# Apply any pending chart click BEFORE widgets
apply_chart_click_if_any()

# =============================
# Header
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
# Sidebar controls + sort toggle
# =============================
with st.sidebar:
    st.markdown("## Policy Controls")

    sort_by_magnitude = st.checkbox(
        "Sort bars by magnitude",
        value=False,
        help="If enabled, bars in each chart are ordered from largest to smallest value for that chart’s metric.",
        key="sort_by_magnitude",
    )

    st.radio(
        "Inspection timing predictability",
        pred_options,
        key="pred_choice",
        on_change=update_selected_key_from_sidebar,
    )

    pred_numeric = pred_map[st.session_state["pred_choice"]]
    low, mid, high = get_freq_options(pred_numeric)

    freq_options = [
        f"−25% ({low:.2f})",
        f"Current ({mid:.2f})",
        f"+25% ({high:.2f})",
    ]

    if st.session_state["freq_choice"] not in freq_options:
        st.session_state["freq_choice"] = freq_options[1]
        update_selected_key_from_sidebar()

    st.radio(
        "Inspection frequency",
        freq_options,
        key="freq_choice",
        on_change=update_selected_key_from_sidebar,
    )

# =============================
# Selected scenario (source of truth)
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
            Tip: Click a bar in any chart below to select that scenario.
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
# Vega-Lite bar chart specs (clickable) + sort toggle
# =============================
POINT_PARAM = "point_selection"

def vega_bar_spec(metric_col, y_domain, y_label, chart_title, selected_key_for_style, sort_by_magnitude_flag):
    if sort_by_magnitude_flag:
        sort_spec = {"field": metric_col, "order": "descending"}
    else:
        sort_spec = {"field": "x_order", "order": "ascending"}

    return {
        "title": {"text": chart_title, "anchor": "middle", "fontSize": 20, "fontWeight": "bold", "offset": 10},
        "height": 235,
        "padding": {"top": 8, "left": 10, "right": 10, "bottom": 5},
        "mark": {"type": "bar", "size": 40, "cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3},
        "params": [
            {"name": POINT_PARAM, "select": {"type": "point", "fields": ["scenario_key"], "on": "click"}}
        ],
        "encoding": {
            "x": {
                "field": "scenario_key",
                "type": "nominal",
                "sort": sort_spec,
                "axis": {"labels": False, "ticks": False, "domain": False, "title": None},
            },
            "y": {
                "field": metric_col,
                "type": "quantitative",
                "scale": {"domain": [float(y_domain[0]), float(y_domain[1])], "nice": False},
                "axis": {"title": y_label, "titleFontWeight": "bold"},
            },
            "tooltip": [
                {"field": "scenario_label", "type": "nominal", "title": "Scenario"},
                {"field": metric_col, "type": "quantitative", "title": y_label, "format": ",.2f"},
            ],
            "color": {
                "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": "#800000"},
                "value": "#c9c9c9",
            },
            "opacity": {
                "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": 1.0},
                "value": 0.55,
            },
            "stroke": {
                "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": "#EAAA00"},
                "value": None,
            },
            "strokeWidth": {
                "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": 10},
                "value": 0,
            },
        },
        "config": {
            "font": "Gotham",
            "axis": {
                "labelFont": "Gotham",
                "titleFont": "Gotham",
                "labelFontSize": 14,
                "titleFontSize": 15.2,
                "labelColor": "#000000",
                "titleColor": "#000000",
            },
            "title": {"font": "Gotham", "fontSize": 20},
            "legend": {"labelFont": "Gotham", "titleFont": "Gotham"},
        },
    }

def render_chart(df_in, spec, key):
    st.vega_lite_chart(
        df_in,
        spec,
        use_container_width=True,
        key=key,
        on_select="rerun",
        selection_mode=POINT_PARAM,
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

sort_flag = st.session_state.get("sort_by_magnitude", False)

p1, p2 = st.columns(2)
with p1:
    render_chart(
        df,
        vega_bar_spec(
            "lives_saved_annually",
            Y_LIMS["lives_saved_annually"],
            "Lives saved",
            "Annual lives saved",
            selected_key,
            sort_flag,
        ),
        key="vega_lives_saved_annually",
    )

with p2:
    render_chart(
        df,
        vega_bar_spec(
            "lives_saved_per_1000",
            Y_LIMS["lives_saved_per_1000"],
            "Lives per 1,000 inspections",
            "Efficiency (lives saved per 1,000 inspections)",
            selected_key,
            sort_flag,
        ),
        key="vega_lives_saved_per_1000",
    )

p3, p4 = st.columns(2)
with p3:
    render_chart(
        df,
        vega_bar_spec(
            "info_percent",
            Y_LIMS["info_percent"],
            "Percent (%)",
            "Regulatory information revealed",
            selected_key,
            sort_flag,
        ),
        key="vega_info_percent",
    )

with p4:
    render_chart(
        df,
        vega_bar_spec(
            "total_inspections",
            Y_LIMS["total_inspections"],
            "Inspections",
            "Total inspections conducted",
            selected_key,
            sort_flag,
        ),
        key="vega_total_inspections",
    )

# Optional debugging
# with st.expander("Debug"):
#     st.write("selected_key:", st.session_state["selected_key"])
#     st.write("last_action:", st.session_state.get("last_action"))
#     st.write("last_seen_by_chart:", st.session_state.get("last_seen_by_chart"))
#     for k in CHART_KEYS:
#         st.write(k, st.session_state.get(k))
