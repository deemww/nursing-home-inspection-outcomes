# app.py
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Why Predictability Matters", layout="wide")

# -----------------------------
# Title + subtitle
# -----------------------------
st.markdown(
    "<h1 style='text-align:center; margin-bottom:0;'>Why Predictability Matters</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; margin-top:6px; font-size:18px;'>"
    "Random inspections raise <b>average</b> effort not because effort is always higher, "
    "but because nursing homes stop spending most weeks at low effort."
    "</p>",
    unsafe_allow_html=True,
)

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Policy control")

predictability = st.sidebar.slider(
    "Inspection timing predictability",
    min_value=0,
    max_value=100,
    value=50,
    help="0% = fully scheduled (highly predictable) • 50% = current regime • 100% = fully random",
)
st.sidebar.caption("0% = fully scheduled • 50% = current regime • 100% = fully random")

step = st.sidebar.radio(
    "Explain the intuition (step-by-step)",
    options=[1, 2, 3],
    format_func=lambda x: {
        1: "Step 1 — What homes do over the cycle",
        2: "Step 2 — Where they spend their time",
        3: "Step 3 — Why the average is higher under random",
    }[x],
    index=0,
)

show_effort_hist = st.sidebar.checkbox("Show effort distribution (optional)", value=False)

# -----------------------------
# Core timeline
# -----------------------------
weeks = np.arange(0, 61)
T = weeks.max()
x = weeks / T

def logistic(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))

# -----------------------------
# Mechanism pieces (stylized but matches the feedback logic)
# 1) Effort-by-week e(w)
# 2) Time share pi(w) from hazard h(w)
# -----------------------------

# "Randomness strength" (100 = fully random)
rand_strength = predictability / 100.0

# (A) Effort curves
# Random/unpredictable regime: steady effort
# Use a level around 0.05 to mirror the feedback language.
e_random_mean = 0.05
effort_random = np.full_like(weeks, e_random_mean, dtype=float)

# Predictable regime: low early, high late (ramp after ~40)
# Make the ramp shape respond to predictability:
#   - More predictable -> bigger cycle (lower early, higher late)
#   - More random -> flatter toward the random mean
ramp_center = 42
ramp_width = 4
ramp = logistic((weeks - ramp_center) / ramp_width)

# Amplitude shrinks as predictability increases (more random -> smaller cycle)
max_amp = 0.03  # tune if you want stronger visual separation
amp = max_amp * (1 - rand_strength)

low_level = e_random_mean - amp
high_level = e_random_mean + amp
effort_predictable_core = low_level + (high_level - low_level) * ramp

# Blend toward flat effort as the regime becomes more random
effort_predictable = (1 - rand_strength) * effort_predictable_core + rand_strength * effort_random

# (B) Hazard curves -> time share distribution of "weeks since inspection"
# Random hazard: constant each week (memoryless)
base_h = 0.06
h_random = np.full_like(weeks, base_h, dtype=float)

# Predictable hazard: very low early, ramps up late
h_low = 0.005
h_high = 0.14
haz_ramp = logistic((weeks - ramp_center) / ramp_width)
h_predictable_core = h_low + (h_high - h_low) * haz_ramp

# Blend hazard as predictability increases (more random -> closer to constant hazard)
h_predictable = (1 - rand_strength) * h_predictable_core + rand_strength * h_random

h_random = np.clip(h_random, 0.001, 0.5)
h_predictable = np.clip(h_predictable, 0.001, 0.5)

def time_share_from_hazard(h: np.ndarray) -> np.ndarray:
    """
    Convert weekly hazard h(w) into a time-share distribution pi(w).
    In a renewal process, the fraction of time spent at 'age' w is proportional to survival S(w).
    """
    S = np.ones_like(h, dtype=float)
    for w in range(1, len(h)):
        S[w] = S[w - 1] * (1 - h[w - 1])
    pi = S / S.sum()
    return pi

pi_pred = time_share_from_hazard(h_predictable)
pi_rand = time_share_from_hazard(h_random)

# Average effort implied by weighting effort by time share
avg_pred = float(np.sum(pi_pred * effort_predictable))
avg_rand = float(np.sum(pi_rand * effort_random))

# -----------------------------
# Shared styling helpers
# -----------------------------
LOW_WEEK_CUTOFF = 40

def shaded_region(x0: int, x1: int, label: str):
    return alt.Chart(pd.DataFrame({"x0": [x0], "x1": [x1], "label": [label]})).mark_rect(
        opacity=0.12
    ).encode(
        x=alt.X("x0:Q"),
        x2="x1:Q",
        y=alt.value(0),
        y2=alt.value(1),
    )

def vline(xpos: int):
    return alt.Chart(pd.DataFrame({"x": [xpos]})).mark_rule(strokeDash=[4, 4]).encode(x="x:Q")

# -----------------------------
# Step 1: Effort by week since inspection
# -----------------------------
if step >= 1:
    st.subheader("Step 1 — What homes do over the inspection cycle")

    st.write(
        "When inspections are predictable, facilities **reduce effort after an inspection** "
        "and **increase effort as the next inspection approaches**. "
        "Under random inspections, effort stays roughly steady."
    )

    df_eff = pd.DataFrame(
        {
            "Week": weeks,
            "Predictable inspections": effort_predictable,
            "Random inspections": effort_random,
        }
    ).melt("Week", var_name="Regime", value_name="Effort")

    # Background shading: low-effort region (<40) and high-effort region (>=40)
    shade_low = alt.Chart(pd.DataFrame({"x0": [0], "x1": [LOW_WEEK_CUTOFF]})).mark_rect(opacity=0.10).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    )
    shade_high = alt.Chart(pd.DataFrame({"x0": [LOW_WEEK_CUTOFF], "x1": [T]})).mark_rect(opacity=0.06).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    )

    base = alt.Chart(df_eff).encode(
        x=alt.X("Week:Q", title="Weeks since last inspection", scale=alt.Scale(domain=[0, T])),
        y=alt.Y("Effort:Q", title="Effort", scale=alt.Scale(domain=[0.0, max(0.08, e_random_mean + max_amp + 0.01)])),
        color=alt.Color("Regime:N", title=None),
    )

    lines = base.mark_line(strokeWidth=3)

    mean_rule = alt.Chart(pd.DataFrame({"y": [e_random_mean]})).mark_rule(strokeDash=[6, 4]).encode(
        y="y:Q"
    )

    mean_label = alt.Chart(pd.DataFrame({"x": [2], "y": [e_random_mean]})).mark_text(
        align="left", baseline="bottom", dx=6
    ).encode(x="x:Q", y="y:Q", text=alt.value("Random regime mean"))

    cutoff_rule = alt.Chart(pd.DataFrame({"x": [LOW_WEEK_CUTOFF]})).mark_rule(strokeDash=[4, 4]).encode(x="x:Q")

    cutoff_label = alt.Chart(pd.DataFrame({"x": [LOW_WEEK_CUTOFF], "y": [0.002]})).mark_text(
        align="center", baseline="bottom", dy=-2
    ).encode(x="x:Q", y="y:Q", text=alt.value("≈ week 40"))

    annotations = alt.Chart(
        pd.DataFrame(
            {
                "x": [6, 52],
                "y": [float(effort_predictable[6]), float(effort_predictable[52])],
                "text": ["After inspection → effort is low", "Before next inspection → effort spikes"],
            }
        )
    ).mark_text(align="left", dx=6, dy=-10).encode(x="x:Q", y="y:Q", text="text:N")

    chart_eff = (
        (shade_low + shade_high)
        .properties(width="container", height=380)
        + lines
        + mean_rule
        + mean_label
        + cutoff_rule
        + cutoff_label
        + annotations
    ).resolve_scale(y="shared")

    st.altair_chart(chart_eff, use_container_width=True)

    st.caption(
        "Interpretation: In the predictable regime, effort is below the random mean in early weeks "
        f"(weeks < {LOW_WEEK_CUTOFF}) and above it mainly later in the cycle."
    )

# -----------------------------
# Step 2: Distribution of weeks since inspection (time share)
# -----------------------------
if step >= 2:
    st.subheader("Step 2 — Where facilities spend their time")

    st.write(
        "The key is not just how effort changes over the cycle, but **how often** facilities are in each part of the cycle. "
        "Under predictable timing, they spend most weeks in the early, low-effort region."
    )

    df_pi = pd.DataFrame(
        {
            "Week": weeks,
            "Predictable inspections": pi_pred,
            "Random inspections": pi_rand,
        }
    ).melt("Week", var_name="Regime", value_name="Share of time")

    shade_low2 = alt.Chart(pd.DataFrame({"x0": [0], "x1": [LOW_WEEK_CUTOFF]})).mark_rect(opacity=0.10).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    )
    cutoff_rule2 = alt.Chart(pd.DataFrame({"x": [LOW_WEEK_CUTOFF]})).mark_rule(strokeDash=[4, 4]).encode(x="x:Q")

    chart_pi = (
        (shade_low2 + cutoff_rule2)
        + alt.Chart(df_pi)
        .mark_area(opacity=0.45)
        .encode(
            x=alt.X("Week:Q", title="Weeks since last inspection", scale=alt.Scale(domain=[0, T])),
            y=alt.Y("Share of time:Q", title="Share of time at week w"),
            color=alt.Color("Regime:N", title=None),
        )
    ).properties(height=320)

    st.altair_chart(chart_pi, use_container_width=True)

    st.caption(
        f"Under predictable timing, mass concentrates in weeks < {LOW_WEEK_CUTOFF} (low-effort weeks). "
        "Under random timing, the distribution is less concentrated in the early weeks."
    )

# -----------------------------
# Step 3: Average effort (the punchline)
# -----------------------------
if step >= 3:
    st.subheader("Step 3 — Why average effort is higher under random inspections")

    st.write(
        "Average effort is a **weighted average**: effort in each week multiplied by how often facilities are in that week."
    )

    # Display as clear, “punchline” numbers
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Average effort (Predictable/current)", f"{avg_pred:.3f}")
    with c2:
        st.metric("Average effort (Random/unpredictable)", f"{avg_rand:.3f}")

    st.write(
        f"Under predictable inspections, facilities spend **most weeks** in the early part of the cycle "
        f"(weeks < {LOW_WEEK_CUTOFF}), where effort is **below** the random mean. "
        "High-effort weeks exist, but they are rare—so the predictable regime ends up with a lower average."
    )

    # Optional: show effort distribution intuition (weighted histogram)
    if show_effort_hist:
        st.markdown("**Optional — Effort distribution (weighted by time spent in each week)**")

        # Create weighted samples (approx) for a simple histogram
        # This is purely for visualization; it helps show right-skew under predictability.
        rng = np.random.default_rng(0)
        N = 5000
        samp_pred_weeks = rng.choice(weeks, size=N, p=pi_pred)
        samp_rand_weeks = rng.choice(weeks, size=N, p=pi_rand)

        samp_pred_eff = effort_predictable[samp_pred_weeks]
        samp_rand_eff = effort_random[samp_rand_weeks]

        df_hist = pd.DataFrame(
            {
                "Effort": np.concatenate([samp_pred_eff, samp_rand_eff]),
                "Regime": (["Predictable/current"] * N) + (["Random/unpredictable"] * N),
            }
        )

        hist = alt.Chart(df_hist).mark_bar(opacity=0.55).encode(
            x=alt.X("Effort:Q", bin=alt.Bin(maxbins=30), title="Effort"),
            y=alt.Y("count():Q", title="Frequency (weighted sample)"),
            color=alt.Color("Regime:N", title=None),
        ).properties(height=320)

        st.altair_chart(hist, use_container_width=True)
        st.caption(
            "Under predictable timing, the distribution tends to be right-skewed: many low-effort weeks, few high-effort weeks."
        )

# -----------------------------
# Footer: one-line recap (always useful)
# -----------------------------
st.divider()
st.write(
    "Recap: Predictability creates an effort cycle (low early, high late), but facilities spend most time in the low-effort part of that cycle—so the average is lower than under random inspections."
)
