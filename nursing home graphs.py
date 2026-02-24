import pandas as pd
import streamlit as st
import altair as alt

# 1. Page Configuration
st.set_page_config(layout="wide")

# 2. Custom CSS (Styles for fonts, sidebar, and metrics)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #D9D9D9 !important; }

    /* ---- Gotham font faces ---- */
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Book.otf") format("opentype"); font-weight: 400; font-style: normal; }
    @font-face { font-family: "Gotham"; src: url("assets/fonts/gotham/Gotham-Bold.otf") format("opentype"); font-weight: 700; font-style: normal; }

    html, body, [data-testid="stAppViewContainer"] * {
        font-family: "Gotham", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size: 1.6rem !important; font-weight: 700 !important;}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size: 1.35rem !important; font-weight: 700 !important; }
    
    [data-testid="stMetricLabel"] p { font-weight: 700 !important; }
    [data-testid="stMetricValue"] { font-weight: 800 !important; }
    [data-testid="stCaptionContainer"] p { font-weight: 700 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Data Loading and Precomputing
@st.cache_data
def load_and_prep_data():
    df = pd.read_csv("figure9_summary_raw.csv")
    
    def scenario_label(predictability, frequency):
        if predictability == 50:
            if frequency == 0.99: return "Current Regime"
            return "Increase Frequency (↑ 25%)" if frequency > 0.99 else "Decrease Frequency (↓ 25%)"
        if predictability == 100:
            if frequency == 0.99: return "Unpredictable"
            return "Unpredictable; Increased Frequency (↑ 25%)" if frequency > 0.99 else "Unpredictable; Decreased Frequency (↓ 25%)"
        if predictability == 0:
            if frequency == 0.98: return "Perfectly Predictable"
            return "Perfectly Predictable; Increased Frequency (↑ 25%)" if frequency > 0.98 else "Perfectly Predictable; Decreased Frequency (↓ 25%)"
        return "Unknown"

    df["freq_round"] = df["frequency"].round(4)
    df["scenario_key"] = df["predictability_numeric"].astype(int).astype(str) + "_" + df["freq_round"].astype(str)
    df["scenario_label"] = df.apply(lambda r: scenario_label(int(r["predictability_numeric"]), float(r["frequency"])), axis=1)

    pred_order = {0: 0, 50: 1, 100: 2}
    df["pred_order"] = df["predictability_numeric"].map(pred_order)
    df = df.sort_values(["pred_order", "frequency"]).copy()
    df["freq_rank"] = df.groupby("predictability_numeric").cumcount() + 1
    df["x_order"] = df["pred_order"] * 10 + df["freq_rank"]
    df["total_inspections"] = (df["frequency"] * 15615).round(0)
    return df

df = load_and_prep_data()

# Fixed Y-Axis Limits
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["total_inspections"].max()) * 1.10),
}

# 4. Chart Function with Click Interaction Logic
def multi_bar_chart(df_all, metric_col, y_domain, y_label, chart_title, selected_key):
    # Selection object for clicking
    click_selection = alt.selection_point(fields=['scenario_key'], on='click', toggle=False)

    base = alt.Chart(df_all).encode(
        x=alt.X("scenario_label:N", title=None, sort=alt.SortField(field="x_order", order="ascending"),
                axis=alt.Axis(labels=False, ticks=False, domain=False)),
        y=alt.Y(f"{metric_col}:Q", title=y_label, scale=alt.Scale(domain=list(y_domain), nice=False)),
        tooltip=[
            alt.Tooltip("scenario_label:N", title="Scenario"),
            alt.Tooltip(f"{metric_col}:Q", format=",.2f", title=y_label),
        ],
        # Important: pass scenario_key to the chart so it can be used for selection
        detail="scenario_key:N"
    ).add_params(click_selection)

    bars = base.mark_bar(size=40, cornerRadiusTopLeft=3, cornerRadiusTopRight=3, cursor='pointer').encode(
        color=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#800000"), # Maroon for selected
            alt.value("#c9c9c9"), # Grey for others
        ),
        stroke=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#EAAA00"), # Gold border for selected
            alt.value(None),
        ),
        strokeWidth=alt.condition(alt.datum.scenario_key == selected_key, alt.value(6), alt.value(0)),
        opacity=alt.condition(alt.datum.scenario_key == selected_key, alt.value(1.0), alt.value(0.55)),
    )

    return bars.properties(height=235, title=alt.TitleParams(text=chart_title, anchor="middle", fontSize=20, fontWeight="bold"))

# 5. Sidebar and State Initialization
pred_map = {
    "Unpredictable (random)": 100,
    "Current regime (status quo)": 50,
    "Perfectly predictable (scheduled)": 0,
}
inv_pred_map = {v: k for k, v in pred_map.items()}

if "pred_choice" not in st.session_state:
    st.session_state["pred_choice"] = "Current regime (status quo)"
if "freq_position" not in st.session_state:
    st.session_state["freq_position"] = "Current"

# Helper for frequencies
def get_freq_options(pred_num):
    return sorted(df.loc[df["predictability_numeric"] == pred_num, "frequency"].tolist())

# Sidebar Logic
with st.sidebar:
    st.markdown("## Policy Controls")
    pred_choice = st.radio("Inspection timing predictability", list(pred_map.keys()), key="pred_choice")
    
    predictability = pred_map[pred_choice]
    low, mid, high = get_freq_options(predictability)
    freq_options = [f"−25% ({low:.2f})", f"Current ({mid:.2f})", f"+25% ({high:.2f})"]
    
    # Sync frequency position to labels
    pos_map = {"−25%": freq_options[0], "Current": freq_options[1], "+25%": freq_options[2]}
    current_label = pos_map[st.session_state["freq_position"]]
    
    freq_choice = st.radio("Inspection frequency", freq_options, key="f_widget", index=freq_options.index(current_label))
    
    if freq_choice.startswith("−25%"):
        st.session_state["freq_position"] = "−25%"
        frequency = low
    elif freq_choice.startswith("Current"):
        st.session_state["freq_position"] = "Current"
        frequency = mid
    else:
        st.session_state["freq_position"] = "+25%"
        frequency = high

# 6. Main Dashboard UI
st.markdown("<h1 style='text-align:center;'>Nursing Home Inspection Policy Outcomes</h1>", unsafe_allow_html=True)

selected_key = f"{int(predictability)}_{round(float(frequency), 4)}"
row = df[df["scenario_key"] == selected_key].iloc[0]

# Selection Hero Box
st.markdown(f"""
    <div style='text-align:center; margin-bottom:1.5rem;'>
        <div style='font-size:1.5rem; font-weight:700;'>Selected Policy Scenario</div>
        <div style='display:inline-block; padding:12px 24px; background-color:#800000; color:#fff; font-size:1.6rem; font-weight:800; border:4px solid #EAAA00; border-radius:12px;'>
            {row['scenario_label']}
        </div>
    </div>
""", unsafe_allow_html=True)

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Lives saved", f"{row['lives_saved_annually']:.1f}", help="Annual reduction in deaths")
m2.metric("Efficiency", f"{row['lives_saved_per_1000']:.1f}", help="Lives saved per 1,000 inspections")
m3.metric("Regulatory information", f"{row['info_percent']:.1f}%")
m4.metric("Total inspections", f"{int(row['total_inspections']):,}")

st.markdown("---")
st.markdown("<h2 style='text-align:center;'>Policy Comparisons</h2>", unsafe_allow_html=True)
st.caption("Click any bar in the charts below to select a different policy scenario.")

# 7. Grid of 4 Interactive Charts
chart_data = [
    ("lives_saved_annually", "Annual lives saved"),
    ("lives_saved_per_1000", "Efficiency (Lives per 1,000)"),
    ("info_percent", "Regulatory information revealed"),
    ("total_inspections", "Total inspections conducted")
]

# Display charts in 2x2 grid
for i in range(0, 4, 2):
    cols = st.columns(2)
    for j in range(2):
        metric, title = chart_data[i+j]
        with cols[j]:
            c_obj = multi_bar_chart(df, metric, Y_LIMS[metric], title, title, selected_key)
            
            # The key for on_select must be unique per chart
            res = st.altair_chart(c_obj, use_container_width=True, on_select="rerun", key=f"chart_{metric}")

            # Capture clicks
            if res and res.get("selection") and res["selection"].get("scenario_key"):
                new_key = res["selection"]["scenario_key"][0]
                new_pred = int(new_key.split("_")[0])
                new_freq = float(new_key.split("_")[1])
                
                # Update Session State
                st.session_state["pred_choice"] = inv_pred_map[new_pred]
                opts = get_freq_options(new_pred)
                if abs(new_freq - opts[0]) < 0.001: st.session_state["freq_position"] = "−25%"
                elif abs(new_freq - opts[1]) < 0.001: st.session_state["freq_position"] = "Current"
                else: st.session_state["freq_position"] = "+25%"
                
                st.rerun()
