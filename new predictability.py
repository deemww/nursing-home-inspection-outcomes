import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'>Why Predictability Matters: Nursing Home Effort Over Time</h1>", unsafe_allow_html=True)

# -----------------------
# Controls
# -----------------------
st.sidebar.header("Policy control")
predictability = st.sidebar.slider("Inspection timing predictability", 0, 100, 50)
st.sidebar.caption("0% = fully scheduled • 50% = current regime • 100% = fully random")

story_step = st.sidebar.radio("Explanation step", [1, 2, 3], index=0)

weeks = np.arange(0, 61)

# -----------------------
# 1) Hazard functions (stylized but mechanism-correct)
# -----------------------
# strength = how "random" it is
rand_strength = predictability / 100.0

# Random regime: constant hazard
h_random = np.full_like(weeks, 0.06, dtype=float)  # tune as needed

# Predictable regime: near 0 early, ramps after ~35-40 weeks
# Use a smooth logistic ramp; mix with random hazard according to slider
def logistic(x): return 1 / (1 + np.exp(-x))

ramp = logistic((weeks - 42) / 4)  # ramps up around week ~42
h_predictable_core = 0.005 + 0.12 * ramp  # ~0.5% early -> up to ~12% late
h_predictable = (1 - rand_strength) * h_predictable_core + rand_strength * h_random

# Keep hazards in (0,1)
h_predictable = np.clip(h_predictable, 0.001, 0.5)
h_random = np.clip(h_random, 0.001, 0.5)

# -----------------------
# Convert hazard h(w) to "time share" pi(w)
# -----------------------
def time_share_from_hazard(h):
    # survival S(w) = P(no inspection through week w-1)
    S = np.ones_like(h, dtype=float)
    for w in range(1, len(h)):
        S[w] = S[w-1] * (1 - h[w-1])
    # fraction of time spent at each age w in a renewal process is proportional to S(w)
    pi = S / S.sum()
    return S, pi

S_pred, pi_pred = time_share_from_hazard(h_predictable)
S_rand, pi_rand = time_share_from_hazard(h_random)

# -----------------------
# 2) Effort-by-week functions (mechanism-correct)
# -----------------------
# Random: steady effort at some mean level
effort_random = np.full_like(weeks, 1.00, dtype=float)

# Predictable: low early (<40), high late (>40)
# Make it piecewise with a ramp-up, so it matches the written mechanism
low_level = 0.95
high_level = 1.10
ramp_eff = logistic((weeks - 42) / 4)  # ramp up around week ~42
effort_predictable = low_level + (high_level - low_level) * ramp_eff

# -----------------------
# 3) Implied averages and effort distributions
# -----------------------
avg_eff_pred = float((pi_pred * effort_predictable).sum())
avg_eff_rand = float((pi_rand * effort_random).sum())

# For "effort distribution", map weeks -> effort and weight by pi(w)
dist_pred = pd.DataFrame({"effort": effort_predictable, "weight": pi_pred})
dist_rand = pd.DataFrame({"effort": effort_random, "weight": pi_rand})

# -----------------------
# Build dataframes for charts
# -----------------------
df_eff = pd.DataFrame({
    "week": weeks,
    "Predictable regime": effort_predictable,
    "Random regime": effort_random
}).melt("week", var_name="regime", value_name="effort")

df_pi = pd.DataFrame({
    "week": weeks,
    "Predictable regime": pi_pred,
    "Random regime": pi_rand
}).melt("week", var_name="regime", value_name="time_share")

# -----------------------
# Step 1: Effort-by-week
# -----------------------
if story_step >= 1:
    st.subheader("Step 1 — Effort differs by weeks since inspection")

    chart_eff = alt.Chart(df_eff).mark_line(strokeWidth=3).encode(
        x=alt.X("week:Q", title="Weeks since last inspection"),
        y=alt.Y("effort:Q", title="Effort (index)", scale=alt.Scale(domain=[0.9, 1.15])),
        color=alt.Color("regime:N", title="Regime")
    )
    st.altair_chart(chart_eff, use_container_width=True)

# -----------------------
# Step 2: Time spent at each week-since (distribution)
# -----------------------
if story_step >= 2:
    st.subheader("Step 2 — Facilities spend most time in low-effort weeks under predictability")

    chart_pi = alt.Chart(df_pi).mark_area(opacity=0.5).encode(
        x=alt.X("week:Q", title="Weeks since last inspection"),
        y=alt.Y("time_share:Q", title="Share of time spent at week w"),
        color=alt.Color("regime:N", title="Regime")
    )
    st.altair_chart(chart_pi, use_container_width=True)

# -----------------------
# Step 3: Average effort comparison (the punchline)
# -----------------------
if story_step >= 3:
    st.subheader("Step 3 — Average effort is lower under predictable timing")

    st.write(f"Implied average effort (Predictable): {avg_eff_pred:.3f}")
    st.write(f"Implied average effort (Random): {avg_eff_rand:.3f}")

    # Optional: show effort distribution intuition via weighted histogram
    st.caption("Why: under predictability, high-effort weeks exist but get low weight (rare); most weight is on low-effort weeks.")
