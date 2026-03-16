import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# =============================
# Styling
# =============================
st.markdown(
    """
    <style>
    /* ============================================================
       SIDEBAR — BFI Data Studio style
       White background, clean section labels, maroon accents
       ============================================================ */

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e4e4e4 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }

    /* Hide sidebar collapse button (shows broken icon text without Material Icons font) */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

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

    /* ---- Sidebar section labels (small uppercase BFI style) ---- */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.13em !important;
        text-transform: uppercase !important;
        color: #7c7c7c !important;
        border-bottom: 1px solid #e4e4e4 !important;
        padding-bottom: 8px !important;
        margin-bottom: 14px !important;
        margin-top: 4px !important;
    }

    /* ---- Widget labels (radio + slider) ---- */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.13em !important;
        text-transform: uppercase !important;
        color: #333333 !important;
        line-height: 1.2 !important;
        margin-bottom: 10px !important;
        border-bottom: 1px solid #e4e4e4 !important;
        padding-bottom: 8px !important;
    }

    /* ---- Radio: unselected ---- */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 6px 8px !important;
        border-radius: 4px !important;
        transition: background 0.12s !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #fcf8f5 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label span,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 1.0rem !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
        margin: 0 !important;
        color: #404040 !important;
        white-space: pre-wrap !important;
    }

    /* ---- Radio: selected — maroon text on warm tint bg ---- */
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #f5eded !important;
        border-radius: 4px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span,
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        font-weight: 700 !important;
        color: #800000 !important;
    }

    /* ---- METRICS ---- */
    [data-testid="stMetricLabel"] p { font-weight: 700 !important; }
    [data-testid="stMetricValue"] { font-weight: 800 !important; }
    [data-testid="stMetricDelta"] { font-weight: 700 !important; }
    [data-testid="stCaptionContainer"] p { font-weight: 700 !important; }

    /* ---- CSS hover tooltip for metric cards ---- */
    .bfi-help-wrap {
        position: relative;
        display: inline-block;
        vertical-align: middle;
        margin-left: 5px;
        top: -1px;
    }
    .bfi-help-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        border: 1.5px solid #aaaaaa;
        color: #aaaaaa;
        font-size: 0.6rem;
        font-weight: 700;
        cursor: help;
        line-height: 1;
        text-transform: none;
        letter-spacing: 0;
    }
    .bfi-help-popup {
        display: none;
        position: absolute;
        top: calc(100% + 4px);
        left: 0;
        transform: none;
        background: #222222;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 400;
        line-height: 1.45;
        padding: 7px 11px;
        border-radius: 4px;
        width: 200px;
        white-space: normal;
        text-align: left;
        z-index: 9999;
    }
    .bfi-help-wrap:hover .bfi-help-popup {
        display: block;
    }

    /* ============================================================
       INSPECTION FREQUENCY SLIDER STYLING
       Modern Streamlit uses role="slider" + utility classes (not rc-slider)
       ============================================================ */

    [data-testid="stSidebar"] [data-testid="stSlider"] {
        padding-bottom: 4px !important;
        margin-bottom: -1rem !important;
    }

    /* Hide default thumb value bubble */
    [data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
        display: none !important;
    }

    /* Hide default tick bar */
    [data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stSliderTickBar"] {
        display: none !important;
    }

    /* Handle — white fill, maroon ring (echoes radio button visual language) */
    [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
        background: #ffffff !important;
        border: 2.5px solid #800000 !important;
        width: 16px !important;
        height: 16px !important;
        box-shadow: none !important;
        border-radius: 50% !important;
        outline: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]:hover,
    [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]:focus {
        background: #f5eded !important;
        border: 2.5px solid #800000 !important;
        box-shadow: 0 0 0 3px rgba(128, 0, 0, 0.12) !important;
    }

    /* Track fill color is set via primaryColor in .streamlit/config.toml */

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

FREQ_LABELS = ["−25%", "Current", "+25%"]

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
    if isinstance(point, list):
        if not point:
            return None
        first = point[0]
        return first.get("scenario_key") if isinstance(first, dict) else None
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
    if isinstance(point, str):
        return point
    return None

# =============================
# Sidebar state sync
# =============================
def set_radios_from_selected_key(selected_key: str) -> None:
    r = df.loc[df["scenario_key"] == selected_key].iloc[0]
    pred = int(r["predictability_numeric"])
    freq = float(r["frequency"])
    st.session_state["pred_choice"] = pred_to_label[pred]
    low, mid, high = get_freq_options(pred)
    if freq == float(low):
        st.session_state["freq_choice"] = "−25%"
    elif freq == float(mid):
        st.session_state["freq_choice"] = "Current"
    else:
        st.session_state["freq_choice"] = "+25%"

def update_selected_key_from_sidebar():
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
# Chart click detection
# =============================
def get_new_chart_click() -> str | None:
    last_seen = st.session_state.get("last_seen_by_chart", {})
    for k in CHART_KEYS:
        clicked = parse_clicked_key_from_chart_state(st.session_state.get(k))
        if clicked and clicked != last_seen.get(k):
            return clicked
    return None

def mark_chart_clicks_as_seen():
    last_seen = st.session_state.get("last_seen_by_chart", {})
    for k in CHART_KEYS:
        last_seen[k] = parse_clicked_key_from_chart_state(st.session_state.get(k))
    st.session_state["last_seen_by_chart"] = last_seen

def apply_chart_click_if_any():
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

apply_chart_click_if_any()

# =============================
# Header
# =============================
st.markdown(
    """
    <div style='text-align:center; padding: 1.5rem 2rem 1.2rem; border-bottom: 1px solid #e4e4e4;'>
        <div style='font-size:0.68rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase;
                    color:#800000; margin-bottom:10px;'>
            BFI Data Studio &nbsp;·&nbsp; Policy Research
        </div>
        <h1 style='font-size:1.75rem; font-weight:800; color:#111111;
                   line-height:1.2; margin:0 auto 10px; max-width:640px;'>
            Nursing Home Inspection Policy Outcomes
        </h1>
        <p style='font-size:0.95rem; font-weight:400; color:#555555;
                  margin:0 auto; max-width:580px; line-height:1.6;'>
            Explore how inspection frequency and predictability affect lives saved,
            efficiency, and regulatory information.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# Sidebar controls
# =============================
with st.sidebar:
    # ── BFI-style maroon header block ──
    st.markdown(
        """
        <div style="
            background-color: #800000;
            margin: -1rem -1rem 1.25rem -1rem;
            padding: 14px 20px 12px 20px;
            text-align: center;
        ">
            <div style="
                font-size: 1.0rem;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 0.01em;
            ">Policy Controls</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.radio(
        "Inspection Predictability",
        pred_options,
        key="pred_choice",
        on_change=update_selected_key_from_sidebar,
    )

    pred_numeric = pred_map[st.session_state["pred_choice"]]
    low, mid, high = get_freq_options(pred_numeric)

    if st.session_state.get("freq_choice") not in FREQ_LABELS:
        st.session_state["freq_choice"] = "Current"
        update_selected_key_from_sidebar()

    # ── Inspection Frequency section label ──
    st.markdown(
        "<div style='font-size:0.85rem; font-weight:700; letter-spacing:0.13em; "
        "text-transform:uppercase; color:#333333; border-bottom:1px solid #e4e4e4; "
        "padding-bottom:8px; margin-top:20px; margin-bottom:10px; "
        "display:inline-block;'>Inspection Frequency</div>",
        unsafe_allow_html=True,
    )

    # ── Labels above slider ──
    selected_fc = st.session_state.get("freq_choice", "Current")
    labels_html = "".join([
        f"<span style='"
        f"color:{'#800000' if lbl == selected_fc else '#404040'};"
        f"font-weight:{'700' if lbl == selected_fc else '400'};"
        f"font-size:1.0rem;'>{lbl}</span>"
        for lbl in FREQ_LABELS
    ])
    st.markdown(
        f"<div style='display:flex; justify-content:space-between;"
        f" padding:0 6px; margin-bottom:4px;'>{labels_html}</div>",
        unsafe_allow_html=True,
    )

    # ── Slider ──
    st.select_slider(
        "Inspection frequency",
        options=FREQ_LABELS,
        key="freq_choice",
        on_change=update_selected_key_from_sidebar,
        label_visibility="collapsed",
    )

    # ── BFI-style callout: left maroon border, italic ──
    rates = {
        "−25%":    f"{low:.2f}",
        "Current": f"{mid:.2f}",
        "+25%":    f"{high:.2f}",
    }
    st.markdown(
        f"""
        <div style="
            border-left: 3px solid #800000;
            background-color: #fcf8f5;
            border-radius: 0 4px 4px 0;
            padding: 10px 14px;
            margin-top: 14px;
            font-size: 1.0rem;
            font-style: italic;
            color: #404040;
            line-height: 1.5;
        ">
            <strong style="font-style:normal; color:#800000;">{rates[selected_fc]}</strong>
            inspections per facility per year
        </div>
        """,
        unsafe_allow_html=True,
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
    <div style='
        text-align: center;
        padding: 14px 24px;
        background-color: #fcf8f5;
        border-top: 1px solid #e4e4e4;
        border-bottom: 1px solid #e4e4e4;
        margin-bottom: 1.2rem;
    '>
        <div style='font-size:0.78rem; font-weight:700; letter-spacing:0.13em;
                    text-transform:uppercase; color:#7c7c7c; margin-bottom:10px;'>
            Selected Scenario
        </div>
        <div style='
            display: inline-block;
            padding: 9px 26px;
            background-color: #800000;
            color: #ffffff;
            font-size: 1.15rem;
            font-weight: 700;
            border-radius: 3px;
            letter-spacing: 0.01em;
        '>
            {scenario}
        </div>
        <div style='font-size:0.82rem; color:#7c7c7c; margin-top:9px;'>
            Click any bar in a chart below to change scenario selection
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================
# Policy outcomes
# =============================
total_inspections = int(float(frequency) * 15615)

st.markdown(
    "<div style='font-size:0.82rem; font-weight:700; letter-spacing:0.13em; text-transform:uppercase; "
    "color:#800000; border-bottom:2px solid #800000; padding-bottom:4px; display:inline-block; "
    "margin-bottom:8px;'>Policy Outcomes</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:0.8rem; color:#7c7c7c; margin-top:0; margin-bottom:0.75rem; line-height:1.5;'>"
    "All outcomes are reported relative to a benchmark with no inspections. "
    "\u201cLives saved\u201d reflects the annual reduction in patient deaths compared to a regime with zero inspections."
    "</p>",
    unsafe_allow_html=True,
)

def metric_card(label, value, unit, help_text=""):
    tooltip = (
        f'<span class="bfi-help-wrap">'
        f'<span class="bfi-help-icon">?</span>'
        f'<span class="bfi-help-popup">{help_text}</span>'
        f'</span>'
        if help_text else ""
    )
    return f"""
    <div style="
        padding: 18px 20px 16px;
        background: #ffffff;
        border: 1px solid #e4e4e4;
        border-top: 3px solid #800000;
        border-radius: 2px;
        overflow: visible;
    ">
        <div style="font-size:0.88rem; font-weight:700; color:#333333; margin-bottom:8px;">
            {label}{tooltip}
        </div>
        <div style="font-size:2.2rem; font-weight:800; color:#111111;
                    line-height:1; margin-bottom:6px; letter-spacing:-0.01em;">
            {value}
        </div>
        <div style="font-size:0.8rem; color:#7c7c7c; font-style:italic;">
            {unit}
        </div>
    </div>
    """

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(metric_card(
        "Lives saved",
        f"{float(row['lives_saved_annually']):.1f}",
        "per year",
        "Annual reduction in patient deaths relative to no inspections",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card(
        "Inspection Efficiency",
        f"{float(row['lives_saved_per_1000']):.1f}",
        "per 1,000 inspections",
        "Lives saved per 1,000 inspections",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card(
        "Regulatory information",
        f"{float(row['info_percent']):.1f}%",
        "about facility quality",
        "How much information inspections give regulators about a facility's underlying quality, relative to no inspections.",
    ), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card(
        "Total inspections",
        f"{total_inspections:,}",
        "inspections per year",
        "Annual inspections nationwide (frequency × 15,615 facilities)",
    ), unsafe_allow_html=True)

st.markdown(
    "<hr style='margin:0.5rem 0; border: none; border-top:1px solid rgba(0,0,0,0.15);'>",
    unsafe_allow_html=True,
)

# =============================
# Vega-Lite bar chart specs (clickable) + sort toggle
# =============================
POINT_PARAM = "point_selection"

def vega_bar_spec(metric_col, y_domain, y_label, chart_title, selected_key_for_style, sort_by_magnitude_flag, label_expr=None):
    if sort_by_magnitude_flag:
        # Explicit sorted array — avoids Vega-Lite nominal sort ambiguity in layered specs
        sort_spec = (
            df.sort_values(metric_col, ascending=False)["scenario_key"].tolist()
        )
    else:
        sort_spec = {"field": "x_order", "order": "ascending"}
    if label_expr is None:
        label_expr = f"format(datum['{metric_col}'], ',.1f')"
    y_scale = {"domain": [float(y_domain[0]), float(y_domain[1])], "nice": False}
    y_axis = {
        "title": y_label,
        "titleFontWeight": 700,
        "titleFontSize": 13,
        "titleColor": "#333333",
        "titlePadding": 12,
        "labelFontSize": 12,
        "labelColor": "#555555",
        "gridColor": "#e8e8e8",
        "gridDash": [],
        "domainColor": "#e8e8e8",
        "tickColor": "#e8e8e8",
    }
    x_axis = {"labels": False, "ticks": False, "domain": False, "title": None, "grid": False}
    return {
        "title": {
            "text": chart_title,
            "anchor": "start",
            "fontSize": 15,
            "fontWeight": 700,
            "color": "#111111",
            "offset": 8,
        },
        "height": 260,
        "padding": {"top": 6, "left": 4, "right": 12, "bottom": 4},
        "layer": [
            {
                "params": [
                    {"name": POINT_PARAM, "select": {"type": "point", "fields": ["scenario_key"], "on": "click"}}
                ],
                "mark": {"type": "bar", "size": 28, "cornerRadiusTopLeft": 2, "cornerRadiusTopRight": 2},
                "encoding": {
                    "x": {"field": "scenario_key", "type": "nominal", "sort": sort_spec, "axis": x_axis},
                    "y": {"field": metric_col, "type": "quantitative", "scale": y_scale, "axis": y_axis},
                    "tooltip": [
                        {"field": "scenario_label", "type": "nominal", "title": "Scenario"},
                        {"field": metric_col, "type": "quantitative", "title": y_label, "format": ",.2f"},
                    ],
                    "color": {
                        "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": "#800000"},
                        "value": "#d6d2ce",
                    },
                    "opacity": {
                        "condition": {"test": f"datum.scenario_key === '{selected_key_for_style}'", "value": 1.0},
                        "value": 0.75,
                    },
                },
            },
            {
                "transform": [
                    {"calculate": label_expr, "as": "_label"},
                    {
                        "calculate": f"datum.scenario_key === '{selected_key_for_style}' ? datum._label : ''",
                        "as": "_visible_label",
                    },
                ],
                "mark": {
                    "type": "text",
                    "align": "center",
                    "baseline": "bottom",
                    "dy": -5,
                    "fontSize": 12,
                    "fontWeight": 700,
                    "color": "#800000",
                },
                "encoding": {
                    "x": {"field": "scenario_key", "type": "nominal", "sort": sort_spec, "axis": x_axis},
                    "y": {"field": metric_col, "type": "quantitative", "scale": y_scale},
                    "text": {"field": "_visible_label", "type": "nominal"},
                },
            },
        ] + ([] if sort_by_magnitude_flag else [
            {
                "transform": [
                    {
                        "calculate": "datum.freq_rank === 1 ? '−' : datum.freq_rank === 2 ? '=' : '+'",
                        "as": "_freq_sym",
                    }
                ],
                "mark": {
                    "type": "text",
                    "align": "center",
                    "baseline": "top",
                    "dy": 4,
                    "fontSize": 10,
                    "fontWeight": 600,
                    "color": "#444444",
                },
                "encoding": {
                    "x": {"field": "scenario_key", "type": "nominal", "sort": sort_spec},
                    "y": {"datum": 0, "type": "quantitative"},
                    "text": {"field": "_freq_sym", "type": "nominal"},
                },
            },
            {
                "transform": [
                    {"filter": "datum.freq_rank === 2"},
                    {
                        "calculate": (
                            "datum.predictability_numeric === 100 ? 'Unpredictable' : "
                            "datum.predictability_numeric === 50 ? 'Current Regime' : "
                            "'Perfectly Predictable'"
                        ),
                        "as": "_group_label",
                    },
                ],
                "mark": {
                    "type": "text",
                    "align": "center",
                    "baseline": "top",
                    "dy": 20,
                    "fontSize": 11,
                    "fontWeight": 700,
                    "color": "#333333",
                },
                "encoding": {
                    "x": {"field": "scenario_key", "type": "nominal", "sort": sort_spec},
                    "y": {"datum": 0, "type": "quantitative"},
                    "text": {"field": "_group_label", "type": "nominal"},
                },
            },
        ]),
        "config": {
            "font": "Gotham",
            "view": {"stroke": None},
            "axis": {"labelFont": "Gotham", "titleFont": "Gotham"},
            "title": {"font": "Gotham", "fontSize": 15, "fontWeight": 700},
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
st.markdown(
    "<div style='font-size:0.82rem; font-weight:700; letter-spacing:0.13em; text-transform:uppercase; "
    "color:#800000; border-bottom:2px solid #800000; padding-bottom:4px; display:inline-block; "
    "margin-bottom:8px;'>Policy Comparisons</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:0.8rem; color:#7c7c7c; margin-top:0; margin-bottom:0.75rem; line-height:1.5;'>"
    "Each bar shows a different inspection policy. The highlighted bar corresponds to the selected scenario above."
    "</p>",
    unsafe_allow_html=True,
)

if "sort_by_magnitude" not in st.session_state:
    st.session_state["sort_by_magnitude"] = False

sort_flag = st.toggle(
    "Sort bars by magnitude",
    key="sort_by_magnitude",
    help="Orders bars from largest to smallest value within each chart.",
)

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
            label_expr="format(datum.lives_saved_per_1000, ',.1f')",
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
            label_expr="format(datum.info_percent, '.1f') + '%'",
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
            label_expr="format(datum.total_inspections, ',.0f')",
        ),
        key="vega_total_inspections",
    )

st.markdown(
    """
    <div style='display:flex; justify-content:center; align-items:center; gap:6px; margin-top:0.6rem; flex-wrap:wrap;
                border:1px solid #dedede; border-radius:4px; padding:6px 14px; width:fit-content; margin-left:auto; margin-right:auto;'>
        <span style='font-size:0.72rem; color:#555555; font-weight:700; letter-spacing:0.08em;
                     text-transform:uppercase; margin-right:8px;'>
            Legend
        </span>
        <span style='color:#cccccc; font-size:0.7rem; margin-right:8px;'>|</span>
        <span style='font-size:0.72rem; color:#555555; font-style:italic; margin-right:6px;'>
            Inspection frequency:
        </span>
        <span style='font-size:0.72rem; color:#333333; display:flex; align-items:center; gap:5px;'>
            <span style='font-family:monospace; font-size:0.8rem; background:#dedede;
                         padding:1px 7px; border-radius:3px; color:#222; font-weight:600;'>−</span>
            −25%
        </span>
        <span style='color:#999999; font-size:0.7rem;'>·</span>
        <span style='font-size:0.72rem; color:#333333; display:flex; align-items:center; gap:5px;'>
            <span style='font-family:monospace; font-size:0.8rem; background:#dedede;
                         padding:1px 7px; border-radius:3px; color:#222; font-weight:600;'>=</span>
            Current
        </span>
        <span style='color:#999999; font-size:0.7rem;'>·</span>
        <span style='font-size:0.72rem; color:#333333; display:flex; align-items:center; gap:5px;'>
            <span style='font-family:monospace; font-size:0.8rem; background:#dedede;
                         padding:1px 7px; border-radius:3px; color:#222; font-weight:600;'>+</span>
            +25%
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)
