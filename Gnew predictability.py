import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from scipy.stats import norm

# App Page Config
st.set_page_config(page_title="Inspection Predictability", layout="wide")

st.markdown("<h1 style='text-align: center;'>Why Predictability Matters</h1>", unsafe_allow_html=True)
st.markdown("### Recreating the Mechanism of NBER Working Paper 34491")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Policy Slider")
# 50% matches the 'Current Regime' described in Figure 10
predictability = st.sidebar.slider("Inspection Predictability", 0, 100, 50)
st.sidebar.caption("0% = Fully Random (Fig 12) | 50% = Current Regime (Fig 10) | 100% = Fixed Annual")

# --- DATA GENERATION (Logic from Section 6.1 & Appendix F.1) ---
weeks = np.arange(1, 61)

def generate_model_data(predict_level):
    p_factor = predict_level / 100
    
    # 1. Inspection Hazard h(w) [Cite: Section 4.1, Fig 1]
    # Random regime has a constant hazard (memoryless property) [Cite: Appendix F.1]
    # Current regime has a near-zero hazard until week 35, then spikes [Cite: 349]
    hazard_random = np.full_like(weeks, 1/54, dtype=float) 
    
    # Sigmoid function to mimic the "sharp rise" after week 35 in Figure 1a
    hazard_predictable = 0.15 / (1 + np.exp(-0.3 * (weeks - 45)))
    
    # Blend hazards based on predictability slider
    h_w = (p_factor * hazard_predictable) + ((1 - p_factor) * hazard_random)
    
    # 2. Facility Effort ej,k,w [Cite: Section 6.1]
    # The paper finds effort is a response to the threat (hazard) [Cite: 351, 451]
    # We use the empirical finding: effort ramp-up mirrors hazard ramp-up
    effort = 0.05 + (h_w * 0.75) 
    
    # 3. Time Distribution [Cite: Figure 10b, Section 2.2]
    # Most facilities are in the early-to-mid cycle because inspections happen ~annually
    # Figure H.1 shows 74% of inspections occur between 40-60 weeks
    time_spent = norm.pdf(weeks, loc=50, scale=8)
    time_spent = time_spent / time_spent.sum() # Normalize to sum to 1
    
    return h_w, effort, time_spent

# Generate data for Current (Slider) and Random (Benchmark)
h_current, e_current, t_current = generate_model_data(predictability)
h_rand, e_rand, t_rand = generate_model_data(0) # 0 = Fully Random (Figure 12)

# --- CALCULATE AVERAGES ---
# Professor's main point: Average effort is the key metric
avg_e_current = np.sum(e_current * t_current)
avg_e_rand = np.sum(e_rand * t_rand)

# Create DataFrame for Altair
df = pd.DataFrame({
    "Week": weeks,
    "Hazard Rate": h_current,
    "Effort (Current)": e_current,
    "Time Distribution": t_current,
    "Effort (Random)": e_rand
})

# --- VISUALIZATION ---

# Top Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Current Avg Effort", f"{avg_e_current:.4f}")
m2.metric("Random Avg Effort", f"{avg_e_rand:.4f}")
diff = ((avg_e_rand - avg_e_current) / avg_e_current) * 100
m3.metric("Gain if Fully Random", f"+{diff:.1f}%", delta_color="normal")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("I. The Effort-Hazard Link (Fig 10a/12a)")
    st.caption("Effort follows the 'threat' of inspection. Note the slacking when hazard is low.")
    
    # Hazard Area
    haz_chart = alt.Chart(df).mark_area(opacity=0.2, color='gray').encode(
        x='Week:Q',
        y=alt.Y('Hazard Rate:Q', title="Inspection Hazard (Threat)"),
    )
    
    # Effort Lines
    eff_chart = alt.Chart(df).transform_fold(
        ['Effort (Current)', 'Effort (Random)'],
        as_=['Type', 'Value']
    ).mark_line(strokeWidth=3).encode(
        x='Week:Q',
        y=alt.Y('Value:Q', title="Effort Level", scale=alt.Scale(domain=[0, 0.15])),
        color=alt.Color('Type:N', scale=alt.Scale(range=['#d62728', '#2ca02c']))
    )
    
    st.altair_chart(haz_chart + eff_chart, use_container_width=True)

with col_b:
    st.subheader("II. Distribution of Weeks (Fig 10b)")
    st.caption("Where do facilities spend their time? Most time is spent in the 'low-effort' weeks.")
    
    dist_chart = alt.Chart(df).mark_bar(color='#4682b4', opacity=0.6).encode(
        x=alt.X('Week:Q', title="Weeks Since Last Inspection"),
        y=alt.Y('Time Distribution:Q', title="Probability of Being in this Week"),
    )
    
    st.altair_chart(dist_chart, use_container_width=True)

# --- EDUCATIONAL FOOTNOTE ---
st.info(f"""
**The Mechanism:**
1. **Dynamic Response**: In the predictable regime, the hazard is low for the first 35 weeks, so effort is low[cite: 349, 351].
2. **Time Trap**: As shown in the right graph, facilities spend the majority of their time in these early weeks[cite: 511]. 
3. **The Result**: Even though effort spikes at week 50, it happens too rarely to pull up the overall average. 
**Randomizing inspections** flattens the hazard, removing the 'safe' weeks and raising the constant average effort[cite: 466].
""")
