import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
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

    /* ---- Sidebar styling ---- */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        margin-bottom: 0.25rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# Data
# =============================
# Ensure your CSV file is in the same directory
df = pd.read_csv("figure9_summary_raw.csv")

# =============================
# Scenario label logic
# =============================
def scenario_label(predictability, frequency):
    if predictability == 50:
        if frequency == 0.99: return "Current Regime"
        elif frequency > 0.99: return "Increase Frequency (↑ 25%)"
        else: return "Decrease Frequency (↓ 25%)"
    if predictability == 100:
        if frequency == 0.99: return "Unpredictable"
        elif frequency > 0.99: return "Unpredictable; Increased Frequency (↑ 25%)"
        else: return "Unpredictable; Decreased Frequency (↓ 25%)"
    if predictability == 0:
        if frequency == 0.98: return "Perfectly Predictable"
        elif frequency > 0.98: return "Perfectly Predictable; Increased Frequency (↑ 25%)"
        else: return "Perfectly Predictable; Decreased Frequency (↓ 25%)"

# Precompute columns
df["freq_round"] = df["frequency"].round(4)
df["scenario_key"] = df["predictability_numeric"].astype(int).astype(str) + "_" + df["freq_round"].astype(str)
df["scenario_label"] = df.apply(lambda r: scenario_label(int(r["predictability_numeric"]), float(r["frequency"])), axis=1)

# Sorting logic
pred_order = {0: 0, 50: 1, 100: 2}
df["pred_order"] = df["predictability_numeric"].map(pred_order)
df = df.sort_values(["pred_order", "frequency"]).copy()
df["freq_rank"] = df.groupby("predictability_numeric").cumcount() + 1
df["x_order"] = df["pred_order"] * 10 + df["freq_rank"]
df["total_inspections"] = (df["frequency"] * 15615).round(0)

# Y Limits
Y_LIMS = {
    "lives_saved_annually": (0, float(df["lives_saved_annually"].max()) * 1.10),
    "lives_saved_per_1000": (0, float(df["lives_saved_per_1000"].max()) * 1.10),
    "info_percent": (0, 100),
    "total_inspections": (0, float(df["total_inspections"].max()) * 1.10),
}

# =============================
# Chart Function with "3D Pop" effect
# =============================
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

    # Simulation of 3D depth using stroke (borders) and conditional opacity
    bars = base.mark_bar(
        size=40, 
        cornerRadiusTopLeft=4, 
        cornerRadiusTopRight=4
    ).encode(
        color=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#800000"),  # Maroon for selected
            alt.value("#d9d9d9"),  # Lighter grey for background
        ),
        stroke=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value("#4a0000"),  # Darker border for "depth"
            alt.value(None)
        ),
        strokeWidth=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value(2),
            alt.value(0)
        ),
        opacity=alt.condition(
            alt.datum.scenario_key == selected_key,
            alt.value(1.0),
            alt.value(0.4),  # Faded background bars
        ),
    )

    return (
        bars.properties(
            height=235,
            title=alt.TitleParams(
                text=chart_title, anchor="start", fontSize=14, fontWeight="normal", offset=10
            ),
            padding={"top": 8, "left": 10, "right": 10, "bottom": 5},
        )
        .configure(font="Gotham")
        .configure_axis(labelFont="Gotham", titleFont="Gotham")
        .configure_view(strokeOpacity=0) # Remove chart border for cleaner look
    )

# =============================
# Sidebar and App Logic
# =============================
with st.sidebar:
    st.markdown("## Policy Controls")
    pred_options = ["Unpredictable (random)", "Current regime (factual)", "Perfectly predictable (scheduled)"]
    if "pred_choice" not in st.session_state: st.session_state["pred_choice"] = "Current regime (factual)"
    pred_choice = st.radio("Inspection timing predictability", pred_options, index=pred_options.index(st.session_state["pred_choice"]))
    st.session_state["pred_choice"] = pred_choice
    
    pred_map = {"Unpredictable (random)": 100, "Current regime (factual)": 50, "Perfectly predictable (scheduled)": 0}
    predictability = pred_map[pred_choice]
    
    # Frequency logic
    subset = df[df["predictability_numeric"] == predictability]
    low, mid, high = sorted(subset["frequency"].unique())
    freq_options = [f"−25% ({low:.2f})", f"Current ({mid:.2f})", f"+25% ({high:.2f})"]
    if "freq_position" not in st.session_state: st.session_state["freq_position"] = "Current"
    pos_to_idx = {"−25%": 0, "Current": 1, "+25%": 2}
    freq_choice = st.radio("Inspection frequency", freq_options, index=pos_to_idx[st.session_state["freq_position"]])
    
    if freq_choice.startswith("−25%"): 
        st.session_state["freq_position"] = "−25%"; frequency = low
    elif freq_choice.startswith("Current"): 
        st.session_state["freq_position"] = "Current"; frequency = mid
    else: 
        st.session_state["freq_position"] = "+25%"; frequency = high

# Header
st.markdown("<h1 style='text-align:center;'>Nursing Home Inspection Policy Outcomes</h1>", unsafe_allow_html=True)
scenario = scenario_label(predictability, frequency)
st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><span style='color:#8b8b8b;'>Selected policy:</span><br><b>{scenario}</b></div>", unsafe_allow_html=True)

# Metrics
row = df[(df["predictability_numeric"] == predictability) & (df["frequency"] == frequency)].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lives saved", f"{row['lives_saved_annually']:.1f}")
c2.metric("Efficiency", f"{row['lives_saved_per_1000']:.1f}")
c3.metric("Information", f"{row['info_percent']:.1f}%")
c4.metric("Total inspections", f"{int(frequency * 15615):,}")

st.divider()
st.caption("Each bar represents a different policy. The highlighted '3D' bar corresponds to your selection.")

# Display Charts
selected_key = f"{int(predictability)}_{round(float(frequency), 4)}"
p1, p2 = st.columns(2)
with p1: st.altair_chart(multi_bar_chart(df, "lives_saved_annually", Y_LIMS["lives_saved_annually"], "Lives saved", "Annual lives saved", selected_key), use_container_width=True)
with p2: st.altair_chart(multi_bar_chart(df, "lives_saved_per_1000", Y_LIMS["lives_saved_per_1000"], "Lives saved/1k", "Efficiency", selected_key), use_container_width=True)

p3, p4 = st.columns(2)
with p3: st.altair_chart(multi_bar_chart(df, "info_percent", Y_LIMS["info_percent"], "Percent", "Information Revealed", selected_key), use_container_width=True)
with p4: st.altair_chart(multi_bar_chart(df, "total_inspections", Y_LIMS["total_inspections"], "Inspections", "Total Conducted", selected_key), use_container_width=True)
