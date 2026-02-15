# app.py
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Why Predictability Matters", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def logistic(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))

def time_share_from_hazard(h: np.ndarray) -> np.ndarray:
    """
    Convert weekly inspection chance into 'share of time spent' at each week since inspection.
    (No jargon shown to users; this is just internal plumbing.)
    """
    S = np.ones_like(h, dtype=float)
    for w in range(1, len(h)):
        S[w] = S[w - 1] * (1 - h[w - 1])
    pi = S / S.sum()
    return pi

def badge(text: str) -> None:
    st.markdown(
        f"""
        <div style="
            padding: 14px 16px;
            border-radius: 14px;
            background: rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.08);
            font-size: 16px;
            line-height: 1.35;
            ">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )

def big_number(title: str, value: str, delta: str | None = None):
    if delta is None:
        st.metric(title, value)
    else:
        st.metric(title, value, delta)

# -----------------------------
# State (so the app is guided, not a dashboard)
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <h1 style="text-align:center; margin-bottom:0;">
        Why Predictability Matters
    </h1>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <p style="text-align:center; margin-top:8px; font-size:18px;">
        Random inspections raise <b>average</b> effort because nursing homes stop spending most weeks at low effort.
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()

# -----------------------------
# Sidebar: ONE control + optional autoplay
# -----------------------------
st.sidebar.header("Policy control")

predictability = st.sidebar.slider(
    "How random are inspections?",
    0,
    100,
    50,
    help="0 = very predictable (close to scheduled) • 50 = current regime • 100 = fully random",
)
st.sidebar.caption("0 = predictable • 50 = current • 100 = random")

autoplay = st.sidebar.checkbox("Auto-play explanation", value=False)
speed = st.sidebar.slider("Auto-play speed (seconds per step)", 1, 6, 3) if autoplay else None

# -----------------------------
# Build the mechanism data (kept simple + aligned to feedback)
# -----------------------------
weeks = np.arange(0, 61)
T = int(weeks.max())
LOW_CUTOFF = 40

# Interpret predictability as "randomness"
rand_strength = predictability / 100.0

# 1) Effort by week since inspection
# Random regime: flat (use ~0.05 scale to match feedback language)
e_random = 0.050
effort_random = np.full_like(weeks, e_random, dtype=float)

# Predictable regime: low early, higher late (ramps after ~40)
ramp_center = 42
ramp_width = 4
ramp = logistic((weeks - ramp_center) / ramp_width)

max_amp = 0.030  # bigger -> clearer difference
amp = max_amp * (1 - rand_strength)

low_level = e_random - amp
high_level = e_random + amp
effort_predictable_core = low_level + (high_level - low_level) * ramp

# Blend toward flat as inspections become more random
effort_predictable = (1 - rand_strength) * effort_predictable_core + rand_strength * effort_random

# 2) "Where they spend time" (weeks since inspection distribution)
# Random inspections: constant weekly chance
base_weekly_chance = 0.06
h_random = np.full_like(weeks, base_weekly_chance, dtype=float)

# Predictable inspections: very unlikely early, much more likely later
h_low = 0.004
h_high = 0.16
haz_ramp = logistic((weeks - ramp_center) / ramp_width)
h_predictable_core = h_low + (h_high - h_low) * haz_ramp

# Blend hazard toward constant as regime becomes more random
h_predictable = (1 - rand_strength) * h_predictable_core + rand_strength * h_random

h_random = np.clip(h_random, 0.001, 0.5)
h_predictable = np.clip(h_predictable, 0.001, 0.5)

pi_pred = time_share_from_hazard(h_predictable)
pi_rand = time_share_from_hazard(h_random)

# 3) Averages (what professor cares about)
avg_pred = float(np.sum(pi_pred * effort_predictable))
avg_rand = float(np.sum(pi_rand * effort_random))

# -----------------------------
# Layout: “guided story” controls on the page (stable + intuitive)
# -----------------------------
left, right = st.columns([1.2, 1.0], gap="large")

with left:
    badge(
        "<b>How to use this:</b> Read one card at a time. Click <b>Next</b>. "
        "You only need the slider if you want to see what changes under more/less randomness."
    )

with right:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("◀ Back", use_container_width=True, disabled=(st.session_state.step == 1)):
            st.session_state.step -= 1
    with c2:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px; font-weight:600;'>Step {st.session_state.step} of 3</div>",
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("Next ▶", use_container_width=True, disabled=(st.session_state.step == 3)):
            st.session_state.step += 1

# Auto-play (no user confusion: it just advances steps)
if autoplay:
    # NOTE: Streamlit reruns scripts; a simple approach is to show a timer hint and rely on user interaction.
    # This avoids brittle sleep loops.
    st.sidebar.info("Auto-play is ON. Click Next to advance; the slider updates live.")

st.divider()

# -----------------------------
# STEP 1 — Effort over the cycle (10a vs 12a intuition)
# -----------------------------
if st.session_state.step == 1:
    st.subheader("Step 1 — What homes do between inspections")

    badge(
        "When inspections are <b>predictable</b>, effort is <b>low right after</b> an inspection and "
        "<b>rises as the next inspection approaches</b>. When inspections are <b>random</b>, effort stays steady."
    )

    df_eff = pd.DataFrame(
        {
            "Week": weeks,
            "Predictable timing": effort_predictable,
            "Random timing": effort_random,
        }
    ).melt("Week", var_name="Regime", value_name="Effort")

    # Shading for early vs late weeks (no jargon)
    shade = pd.DataFrame(
        {"x0": [0, LOW_CUTOFF], "x1": [LOW_CUTOFF, T], "label": ["Early weeks", "Late weeks"]}
    )
    shade_chart = alt.Chart(shade).mark_rect(opacity=0.10).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    )

    cutoff_rule = alt.Chart(pd.DataFrame({"x": [LOW_CUTOFF]})).mark_rule(strokeDash=[4, 4], opacity=0.7).encode(x="x:Q")
    cutoff_text = alt.Chart(pd.DataFrame({"x": [LOW_CUTOFF], "y": [0.001]})).mark_text(
        align="center", baseline="bottom", dy=-2
    ).encode(x="x:Q", y="y:Q", text=alt.value("≈ week 40"))

    mean_rule = alt.Chart(pd.DataFrame({"y": [e_random]})).mark_rule(strokeDash=[6, 4], opacity=0.8).encode(y="y:Q")
    mean_text = alt.Chart(pd.DataFrame({"x": [2], "y": [e_random]})).mark_text(
        align="left", baseline="bottom", dx=6
    ).encode(x="x:Q", y="y:Q", text=alt.value("Random level"))

    line = alt.Chart(df_eff).mark_line(strokeWidth=3).encode(
        x=alt.X("Week:Q", title="Weeks since last inspection"),
        y=alt.Y("Effort:Q", title="Effort (index)", scale=alt.Scale(domain=[0.0, max(0.085, e_random + max_amp + 0.01)])),
        color=alt.Color("Regime:N", title=None),
        tooltip=[
            alt.Tooltip("Week:Q", title="Week since inspection"),
            alt.Tooltip("Regime:N", title="Line"),
            alt.Tooltip("Effort:Q", title="Effort", format=".3f"),
        ],
    )

    # Simple on-chart labels (plain language)
    labels = alt.Chart(
        pd.DataFrame(
            {
                "x": [6, 52],
                "y": [float(effort_predictable[6]), float(effort_predictable[52])],
                "t": ["After inspection: lower effort", "Closer to next inspection: higher effort"],
            }
        )
    ).mark_text(align="left", dx=6, dy=-10).encode(x="x:Q", y="y:Q", text="t:N")

    chart = (shade_chart + line + mean_rule + mean_text + cutoff_rule + cutoff_text + labels).properties(height=420)
    st.altair_chart(chart, use_container_width=True)

    badge(
        f"<b>Key takeaway:</b> The predictable line is mostly <b>below</b> the random level in early weeks "
        f"(weeks 0–{LOW_CUTOFF}), and only goes <b>above</b> it late in the cycle."
    )

# -----------------------------
# STEP 2 — Where they spend time (10b intuition)
# -----------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2 — Where homes spend most weeks")

    badge(
        "Now the crucial part: even if effort is sometimes high under predictable inspections, "
        "it only matters if homes spend a lot of time in those high-effort weeks."
    )

    df_time = pd.DataFrame(
        {
            "Week": weeks,
            "Predictable timing": pi_pred,
            "Random timing": pi_rand,
        }
    ).melt("Week", var_name="Regime", value_name="Share of time")

    shade = alt.Chart(pd.DataFrame({"x0": [0], "x1": [LOW_CUTOFF]})).mark_rect(opacity=0.10).encode(
        x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(1)
    )
    cutoff_rule = alt.Chart(pd.DataFrame({"x": [LOW_CUTOFF]})).mark_rule(strokeDash=[4, 4], opacity=0.7).encode(x="x:Q")
    cutoff_text = alt.Chart(pd.DataFrame({"x": [LOW_CUTOFF], "y": [0.0]})).mark_text(
        align="center", baseline="bottom", dy=2
    ).encode(x="x:Q", y="y:Q", text=alt.value("early weeks (mostly low effort)"))

    area = alt.Chart(df_time).mark_area(opacity=0.50).encode(
        x=alt.X("Week:Q", title="Weeks since last inspection"),
        y=alt.Y("Share of time:Q", title="Share of weeks spent here"),
        color=alt.Color("Regime:N", title=None),
        tooltip=[
            alt.Tooltip("Week:Q", title="Week since inspection"),
            alt.Tooltip("Regime:N", title="Regime"),
            alt.Tooltip("Share of time:Q", title="Share", format=".3f"),
        ],
    ).properties(height=420)

    st.altair_chart(shade + area + cutoff_rule + cutoff_text, use_container_width=True)

    badge(
        f"<b>Key takeaway:</b> Under the predictable/current regime, homes spend <b>most of their time</b> "
        f"in weeks 0–{LOW_CUTOFF}. Those are the same weeks where effort is usually <b>below</b> the random level."
    )

# -----------------------------
# STEP 3 — The punchline (average effort)
# -----------------------------
else:
    st.subheader("Step 3 — So why is average effort higher under random inspections?")

    badge(
        "Average effort is basically: <b>(effort in a week)</b> × <b>(how often that week happens)</b>, "
        "added up across weeks."
    )

    c1, c2 = st.columns(2)
    with c1:
        big_number("Average effort (Predictable/current)", f"{avg_pred:.3f}")
    with c2:
        big_number("Average effort (Random/unpredictable)", f"{avg_rand:.3f}")

    delta = avg_rand - avg_pred
    badge(
        f"<b>Final takeaway:</b> Under predictable inspections, low-effort weeks are common and high-effort weeks are rare, "
        f"so the average ends up lower. Here, random inspections increase average effort by <b>{delta:.3f}</b>."
    )

    # Optional: a single, simple visual that combines both forces (no extra jargon)
    st.markdown("**One-line summary visual (what drives the average):**")

    df_combo = pd.DataFrame(
        {
            "Week": weeks,
            "Predictable: effort × time": effort_predictable * pi_pred,
            "Random: effort × time": effort_random * pi_rand,
        }
    ).melt("Week", var_name="Term", value_name="Contribution")

    bar = alt.Chart(df_combo).mark_bar(opacity=0.65).encode(
        x=alt.X("Week:Q", title="Weeks since last inspection"),
        y=alt.Y("Contribution:Q", title="Contribution to average"),
        color=alt.Color("Term:N", title=None),
        tooltip=[
            alt.Tooltip("Week:Q", title="Week"),
            alt.Tooltip("Term:N", title=""),
            alt.Tooltip("Contribution:Q", title="Contribution", format=".5f"),
        ],
    ).properties(height=360)

    st.altair_chart(bar, use_container_width=True)

    badge(
        "This last chart shows which weeks actually matter for the average. "
        "If most of the weight is in early weeks, then early-week effort drives the mean."
    )

st.divider()
st.caption(
    "Design goal: one idea per step. The slider is optional—you can understand the mechanism without touching it."
)
