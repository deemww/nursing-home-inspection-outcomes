# app.py
# Streamlit app: paper-accurate mechanism (Figure 10a/10b/12a) with a zero-background UI.
# Main view = “100 weeks as dots” (intuitive).
# “Paper check” view = effort path + distribution of weeks-since + effort distribution (matches paper objects).

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Why Predictability Matters", layout="wide")

# -----------------------------
# Constants from paper text
# -----------------------------
CYCLE_WEEKS = 53          # ~ one inspection every 53 weeks (paper: ~0.99/year ≈ 53 weeks)
REVISIT_WEEKS = 20        # paper discusses revisit window and robustness to eliminating w<=20
DOTS_PER_REGIME = 100     # intuitive “100-week” view

# -----------------------------
# Helpers
# -----------------------------
def logistic(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))

def expected_cycle_length_from_hazard(h: np.ndarray, horizon: int = 400) -> float:
    """
    Approx E[L] = sum_{w>=0} S(w), where S(w)=P(L > w).
    For discrete-time inspection hazard h(w)=P(inspection occurs at week w | reached w).
    """
    S = 1.0
    EL = 0.0
    for w in range(horizon):
        EL += S
        hw = float(h[w] if w < len(h) else h[-1])  # extend with last value
        S *= (1.0 - hw)
        if S < 1e-10:
            break
    return EL

def scale_hazard_to_target_length(shape: np.ndarray, target_len: float) -> np.ndarray:
    """
    Takes a nonnegative hazard 'shape' (not necessarily in [0,1]) and finds a scalar m
    such that hazard h = clip(m*shape, 0, 0.999) yields expected cycle length ~ target_len.
    Uses monotone bisection on m.
    """
    shape = np.asarray(shape, dtype=float)
    shape = np.clip(shape, 0.0, None)

    # If shape is all zeros, can't scale; fall back to flat hazard
    if float(shape.max()) == 0.0:
        return np.full_like(shape, 1.0 / target_len, dtype=float)

    lo, hi = 0.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        h_mid = np.clip(mid * shape, 0.0, 0.999)
        EL = expected_cycle_length_from_hazard(h_mid)
        if EL > target_len:
            lo = mid  # hazard too small -> cycles too long -> increase m
        else:
            hi = mid
    return np.clip(hi * shape, 0.0, 0.999)

def time_share_from_hazard(h: np.ndarray, horizon: int = 400) -> np.ndarray:
    """
    Long-run share of time spent at each week-since-inspection w is proportional to survival S(w).
    pi(w) ∝ S(w). (This is exactly the object behind Figure 10a/10b/12a overlays.)
    """
    S_vals = []
    S = 1.0
    for w in range(horizon):
        S_vals.append(S)
        hw = float(h[w] if w < len(h) else h[-1])
        S *= (1.0 - hw)
        if S < 1e-10:
            break
    S_arr = np.array(S_vals, dtype=float)
    pi = S_arr / S_arr.sum()
    return pi

def effort_scheduled_like(w: np.ndarray, low: float, high: float, center: float, width: float) -> np.ndarray:
    """
    Minimal effort for most of cycle, concentrated near scheduled inspection (paper: predictable regime).
    """
    ramp = logistic((w - center) / width)
    return low + (high - low) * ramp

def effort_unpredictable_like(w: np.ndarray, level: float) -> np.ndarray:
    """
    Modest constant effort (paper: unpredictable regime).
    """
    return np.full_like(w, level, dtype=float)

def shade_revisit_layer(xmax: int, height: int = 260) -> alt.Chart:
    return alt.Chart(pd.DataFrame({"x0": [0], "x1": [xmax]})).mark_rect(opacity=0.10).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    ).properties(height=height)

def sample_weeks(pi: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    w_support = np.arange(len(pi))
    return rng.choice(w_support, size=n, replace=True, p=pi)

def dot_grid_df(effort_samples: np.ndarray, regime_name: str) -> pd.DataFrame:
    n = len(effort_samples)
    cols = 10
    rows = int(np.ceil(n / cols))
    xs = np.tile(np.arange(cols), rows)[:n]
    ys = np.repeat(np.arange(rows), cols)[:n]
    # y inverted for nicer grid
    return pd.DataFrame(
        {
            "x": xs,
            "y": (rows - 1) - ys,
            "effort": effort_samples,
            "regime": regime_name,
        }
    )

def effort_bin(series: pd.Series) -> pd.Series:
    # 3 bins for “no background” users
    q1 = series.quantile(0.33)
    q2 = series.quantile(0.66)
    return pd.cut(series, bins=[-np.inf, q1, q2, np.inf], labels=["Low", "Medium", "High"])

# -----------------------------
# Title (plain English)
# -----------------------------
st.markdown(
    "<h1 style='text-align:center; margin-bottom:0;'>Why Predictability Matters</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; margin-top:8px; font-size:18px;'>"
    "Random inspections raise <b>average</b> effort because high-effort weeks stop being rare."
    "</p>",
    unsafe_allow_html=True,
)
st.divider()

# -----------------------------
# Sidebar controls (simple)
# -----------------------------
st.sidebar.header("Controls")

predictability = st.sidebar.slider(
    "Predictability",
    0,
    100,
    50,
    help="0 = fully scheduled (most predictable) • 100 = flat hazard (unpredictable), frequency held fixed (~1 per 53 weeks).",
)
st.sidebar.caption("Paper extremes: scheduled hazard vs flat hazard (Figure 12).")

show_paper_check = st.sidebar.checkbox("Show paper-check panels (10a/10b/12a view)", value=False)

seed = st.sidebar.number_input("Random seed (for dot sampling)", min_value=0, max_value=9999, value=7, step=1)

# -----------------------------
# Build hazard: interpolate between scheduled and flat, then (re)scale to keep frequency fixed
# Paper:
# - Unpredictable: constant hazard h(w)=hbar
# - Scheduled: h(w)=0 for w<53 and h(53)=1 (per notes)
# We'll implement scheduled as a spike near week 53 (discrete). For computations, we include a 1 at w=53.
# For mixed regimes, we blend shapes then scale to keep E[L]≈53.
# -----------------------------
horizon = 300
w_full = np.arange(horizon)

# Scheduled hazard: inspection happens in the same week each cycle
h_sched = np.zeros(horizon, dtype=float)
h_sched[CYCLE_WEEKS] = 1.0  # exactly scheduled

# Flat hazard: constant chance each week; choose level to target E[L]≈53
h_flat = np.full(horizon, 1.0 / CYCLE_WEEKS, dtype=float)

# “Predictability” slider:
# p=0 -> scheduled, p=100 -> flat
p = predictability / 100.0

# Blend shapes but keep “scheduled spike” structure present when p small.
# We do:
#   shape = (1-p)*sched_like + p*flat_like
# then rescale non-spike part to target length, while preserving spike at week 53 when (1-p) is dominant.
shape = (1.0 - p) * h_sched + p * h_flat

# If p < 1, the spike is present but diluted; scaling could distort it.
# Approach: keep the spike component fixed relative to (1-p), and scale the rest to hit target length.
spike = np.zeros_like(shape)
spike[CYCLE_WEEKS] = (1.0 - p) * 1.0
rest = np.clip(shape - spike, 0.0, None)

# Scale rest so that the combined hazard has expected length ~53 (spike contributes automatically).
# If spike already forces exact length near 53 for low p, scaling will have minimal effect.
rest_scaled = scale_hazard_to_target_length(rest + 1e-12, CYCLE_WEEKS)  # +eps to avoid zero-shape issues
h = np.clip(spike + rest_scaled, 0.0, 0.999)

# Time-share distribution pi(w): where homes spend time (Figure 10a/10b overlays)
pi = time_share_from_hazard(h, horizon=horizon)

# -----------------------------
# Build effort policy e(w) consistent with paper narrative:
# - Unpredictable: modest constant effort
# - Scheduled: minimal effort for most of cycle, concentrated near inspection
# Also: revisit window shading; we do NOT change behavior there (we simply visually mark it).
# -----------------------------
# Levels are “index-like” and only need to preserve the paper ordering:
# predictable has very low effort for most weeks, spikes near end; unpredictable has steady modest effort.
e_unpred_level = 0.05
e_sched_low = 0.01
e_sched_high = 0.12

# Scheduled-like effort
e_sched = effort_scheduled_like(w_full, low=e_sched_low, high=e_sched_high, center=CYCLE_WEEKS - 6, width=2.5)

# Unpredictable effort
e_unpred = effort_unpredictable_like(w_full, level=e_unpred_level)

# Mixed effort (predictability affects incentives): interpolate effort policies
e = (1.0 - p) * e_sched + p * e_unpred

# -----------------------------
# Two regimes to compare (what user sees)
# Left: current chosen predictability (mixed)
# Right: fully unpredictable (paper’s flat hazard)
# This makes the “average effort higher under random” comparison explicit.
# -----------------------------
pi_mixed = pi
e_mixed = e

pi_unpred = time_share_from_hazard(h_flat, horizon=horizon)
e_unpred_policy = e_unpred

avg_mixed = float(np.sum(pi_mixed * e_mixed))
avg_unpred = float(np.sum(pi_unpred * e_unpred_policy))

# -----------------------------
# Intuitive main view: “100 weeks as dots”
# -----------------------------
st.subheader("What a typical year looks like (each dot is a week)")

c1, c2 = st.columns([1, 1], gap="large")

rng = np.random.default_rng(int(seed))

weeks_mixed = sample_weeks(pi_mixed, DOTS_PER_REGIME, rng)
weeks_unpred = sample_weeks(pi_unpred, DOTS_PER_REGIME, rng)

eff_mixed_samples = e_mixed[weeks_mixed]
eff_unpred_samples = e_unpred_policy[weeks_unpred]

df_dots = pd.concat(
    [
        dot_grid_df(eff_mixed_samples, "Predictable / current-ish"),
        dot_grid_df(eff_unpred_samples, "Random / unpredictable"),
    ],
    ignore_index=True,
)

# Bin effort into Low/Medium/High for readability
df_dots["level"] = effort_bin(df_dots["effort"])

dot_chart = alt.Chart(df_dots).mark_circle(size=120).encode(
    x=alt.X("x:Q", axis=None),
    y=alt.Y("y:Q", axis=None),
    color=alt.Color("level:N", title="Effort this week"),
    column=alt.Column("regime:N", title=None),
    tooltip=[
        alt.Tooltip("regime:N", title="Regime"),
        alt.Tooltip("effort:Q", title="Effort", format=".3f"),
        alt.Tooltip("level:N", title="Level"),
    ],
).properties(height=220)

with c1:
    st.metric("Average effort (Predictable / current-ish)", f"{avg_mixed:.3f}")

with c2:
    st.metric("Average effort (Random / unpredictable)", f"{avg_unpred:.3f}")

st.altair_chart(dot_chart, use_container_width=True)

st.markdown(
    "<div style='font-size:16px; line-height:1.35; padding:10px 12px; "
    "border-radius:12px; background:rgba(0,0,0,0.04); border:1px solid rgba(0,0,0,0.08);'>"
    "<b>How to read this:</b> If most dots are “Low” on the left but not on the right, "
    "then average effort is lower under predictability even if a few weeks are very high."
    "</div>",
    unsafe_allow_html=True,
)

# -----------------------------
# Paper-check view (optional): shows the actual paper objects behind the dots
# - Effort path e(w) + distribution of w (pi) overlay idea (Figure 10a / 12a panels a,b)
# - Distribution of effort implied by weighting e(w) by pi(w) (Figure 10b / 12c)
# -----------------------------
if show_paper_check:
    st.divider()
    st.subheader("Paper-check panels (mechanism components)")

    # Panel A: effort by week since inspection (two regimes)
    df_eff = pd.DataFrame(
        {
            "Week since last inspection (w)": np.arange(len(pi_mixed)),
            "Predictable/current-ish": e_mixed[: len(pi_mixed)],
            "Random/unpredictable": e_unpred_policy[: len(pi_unpred)],
        }
    ).melt("Week since last inspection (w)", var_name="Regime", value_name="Effort")

    base_eff = alt.Chart(df_eff).mark_line(strokeWidth=3).encode(
        x=alt.X("Week since last inspection (w):Q", title="Weeks since last inspection"),
        y=alt.Y("Effort:Q", title="Effort", scale=alt.Scale(domain=[0.0, float(max(e_sched_high, e_unpred_level) * 1.15)])),
        color=alt.Color("Regime:N", title=None),
        tooltip=[
            alt.Tooltip("Week since last inspection (w):Q", title="w"),
            alt.Tooltip("Regime:N", title="Regime"),
            alt.Tooltip("Effort:Q", title="Effort", format=".3f"),
        ],
    ).properties(height=260)

    # Shade revisit window (paper notes show gray areas)
    revisit = alt.Chart(pd.DataFrame({"x0": [0], "x1": [REVISIT_WEEKS]})).mark_rect(opacity=0.12).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    ).properties(height=260)

    st.altair_chart(revisit + base_eff, use_container_width=True)
    st.caption(f"Gray shading marks the revisit window (w ≤ {REVISIT_WEEKS}), consistent with the paper’s discussion.")

    # Panel B: distribution of weeks since inspection (pi(w))
    df_pi = pd.DataFrame(
        {
            "w": np.arange(len(pi_mixed)),
            "Predictable/current-ish": pi_mixed,
            "Random/unpredictable": pi_unpred[: len(pi_mixed)],
        }
    ).melt("w", var_name="Regime", value_name="Share of time at w")

    base_pi = alt.Chart(df_pi).mark_area(opacity=0.5).encode(
        x=alt.X("w:Q", title="Weeks since last inspection"),
        y=alt.Y("Share of time at w:Q", title="Share of time"),
        color=alt.Color("Regime:N", title=None),
        tooltip=[
            alt.Tooltip("w:Q", title="w"),
            alt.Tooltip("Regime:N", title="Regime"),
            alt.Tooltip("Share of time at w:Q", title="Share", format=".4f"),
        ],
    ).properties(height=260)

    st.altair_chart(revisit + base_pi, use_container_width=True)
    st.caption("This is the second force in the mechanism: predictable regimes concentrate time in early-cycle weeks.")

    # Panel C: implied effort distribution (weight e(w) by pi(w)) — matches the paper logic of right-skew
    def weighted_effort_samples(pi_arr: np.ndarray, e_arr: np.ndarray, n: int, rng_: np.random.Generator) -> np.ndarray:
        ww = sample_weeks(pi_arr, n, rng_)
        return e_arr[ww]

    N_hist = 8000
    samp_mixed = weighted_effort_samples(pi_mixed, e_mixed, N_hist, rng)
    samp_unpred = weighted_effort_samples(pi_unpred, e_unpred_policy, N_hist, rng)

    df_hist = pd.DataFrame(
        {
            "Effort": np.concatenate([samp_mixed, samp_unpred]),
            "Regime": (["Predictable/current-ish"] * N_hist) + (["Random/unpredictable"] * N_hist),
        }
    )

    hist = alt.Chart(df_hist).mark_bar(opacity=0.55).encode(
        x=alt.X("Effort:Q", bin=alt.Bin(maxbins=40), title="Effort"),
        y=alt.Y("count():Q", title="Frequency (weighted sample)"),
        color=alt.Color("Regime:N", title=None),
        tooltip=[alt.Tooltip("count():Q", title="Count")],
    ).properties(height=260)

    st.altair_chart(hist, use_container_width=True)
    st.caption("This corresponds to the paper’s point: predictable regimes can have rare high-effort weeks but many low-effort weeks (right-skew).")

# -----------------------------
# Footer: one-sentence mechanism (no jargon)
# -----------------------------
st.divider()
st.caption(
    "Mechanism: predictable timing creates low-effort weeks after inspection and high-effort weeks near inspection; "
    "if most weeks are low-effort, the average is lower than under random timing."
)
