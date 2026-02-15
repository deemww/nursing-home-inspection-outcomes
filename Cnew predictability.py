import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(page_title="Why Predictability Matters", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=DM+Sans:wght@400;500;700&display=swap');
    
    .main {
        font-family: 'DM Sans', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Crimson Pro', serif;
    }
    
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: #f5f1eb;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0dbd5;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #5d4e89;
        font-family: 'Crimson Pro', serif;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #6b6560;
        margin-top: 0.5rem;
    }
    
    .step-box {
        background: #f5f1eb;
        border-left: 4px solid #5d4e89;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center;'>Why Predictability Matters:<br>Nursing Home Inspection Timing</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b6560; font-size: 1.1rem; margin-bottom: 2rem;'>How the predictability of inspections shapes facility effort and patient outcomes</p>", unsafe_allow_html=True)

# Control panel
st.markdown("---")
st.subheader("Control Panel")

col1, col2 = st.columns([3, 1])

with col1:
    predictability = st.slider(
        "Inspection Timing Predictability",
        min_value=0,
        max_value=100,
        value=50,
        help="0% = Fully unpredictable (constant hazard) | 50% = Current regime | 100% = Fully predictable (scheduled)"
    )

with col2:
    st.markdown("<div style='padding-top: 1.5rem;'></div>", unsafe_allow_html=True)
    if predictability <= 25:
        regime_label = "**Unpredictable**"
    elif predictability <= 75:
        regime_label = "**Current Regime**"
    else:
        regime_label = "**Predictable**"
    st.markdown(f"Current: {regime_label}")

st.caption("**Fully Unpredictable** (0%): Constant hazard rate · **Current Regime** (50%): Cyclical inspections · **Fully Predictable** (100%): Scheduled date")

# Step selector
st.markdown("---")
st.subheader("Interactive Mechanism Explorer")

step_options = [
    "Step 1: Effort Levels by Week",
    "Step 2: Distribution of Weeks Since Inspection", 
    "Step 3: The Critical Interaction",
    "Step 4: Resulting Average Effort"
]

selected_step = st.radio(
    "Select explanation step:",
    options=range(len(step_options)),
    format_func=lambda x: step_options[x],
    horizontal=True
)

# Generate data
weeks = np.arange(0, 61)

def calculate_effort(weeks, predictability):
    """Calculate effort levels based on predictability"""
    strength = 1 - (predictability / 100)
    baseline = 0.05
    max_amp = 0.25
    amp = max_amp * strength
    
    shape = ((weeks - 30) / 30) ** 2
    effort = baseline + amp * (2 * shape - 1)
    return effort

def calculate_distribution(weeks, predictability):
    """Calculate distribution of weeks since inspection"""
    concentration = predictability / 100
    distribution = np.zeros_like(weeks, dtype=float)
    
    for i, w in enumerate(weeks):
        if w < 20:  # Revisit window
            distribution[i] = 0
        else:
            # Peak around week 52 for predictable, flatter for unpredictable
            peak_week = 52
            spread = 5 + (1 - concentration) * 15
            height = np.exp(-((w - peak_week) ** 2) / (2 * spread ** 2))
            
            # Add baseline for unpredictable (flatter distribution)
            distribution[i] = height * concentration + (1 - concentration) * 0.5
    
    # Normalize
    distribution = distribution / distribution.sum()
    return distribution

# Calculate efforts and distribution
effort_predictable = calculate_effort(weeks, 100)
effort_unpredictable = calculate_effort(weeks, 0)
effort_current = calculate_effort(weeks, predictability)
distribution = calculate_distribution(weeks, predictability)

# Calculate weighted averages
avg_effort_pred = np.sum(effort_predictable * distribution)
avg_effort_unpred = np.sum(effort_unpredictable * distribution)
effort_diff = ((avg_effort_unpred - avg_effort_pred) / avg_effort_pred) * 100

# Step explanations
step_explanations = [
    """
    **Under predictable inspections** (red line), facilities exert very low effort when inspection risk is minimal 
    (weeks 0-40) and dramatically increase effort only as the inspection becomes imminent.
    
    **Under unpredictable inspections** (green line), facilities maintain steady, moderate effort throughout 
    because they face constant inspection risk in every period.
    """,
    """
    The gray bars show how much time facilities spend at each point in the inspection cycle. Under the current regime, 
    **most weeks are spent in the low-effort periods** (weeks 20-45). The high-effort weeks (>45) are relatively rare.
    """,
    """
    This is the key mechanism: facilities spend most of their time in weeks where predictable inspections induce 
    LOW effort (below the green line). While effort spikes are high, they're infrequent. The unpredictable regime's 
    constant effort level exceeds the predictable regime's effort for most weeks.
    """,
    """
    Multiplying effort levels by the time spent in each week reveals that **average effort is significantly higher 
    under unpredictable inspections**. The predictable regime's dramatic effort spikes cannot compensate for the 
    long periods of minimal effort. This is why unpredictability saves more lives—it sustains higher average effort.
    """
]

# Display step explanation
st.markdown(f"<div class='step-box'>{step_explanations[selected_step]}</div>", unsafe_allow_html=True)

# Create visualization
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Step 1: Show effort lines
if selected_step >= 0:
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=effort_predictable,
            mode='lines',
            name='Predictable Regime',
            line=dict(
                color='#d32f2f',
                width=4 if selected_step == 0 else 3,
                dash='dot' if selected_step == 3 else 'solid'
            )
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=effort_unpredictable,
            mode='lines',
            name='Unpredictable Regime',
            line=dict(
                color='#2e7d32',
                width=4 if selected_step == 0 else 3,
                dash='dot' if selected_step == 3 else 'solid'
            )
        ),
        secondary_y=False
    )

# Step 2+: Show distribution
if selected_step >= 1:
    fig.add_trace(
        go.Bar(
            x=weeks,
            y=distribution * 0.4,  # Scale for visibility
            name='Time Spent in Each Week',
            marker=dict(
                color='rgba(93, 78, 137, 0.3)',
                line=dict(color='rgba(93, 78, 137, 0.6)', width=1)
            ),
            yaxis='y2'
        ),
        secondary_y=True
    )

# Step 4: Show weighted effort
if selected_step == 3:
    weighted_pred = effort_predictable * distribution * 10
    weighted_unpred = effort_unpredictable * distribution * 10
    
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=weighted_pred,
            mode='lines',
            name='Weighted Effort (Predictable)',
            line=dict(color='#d32f2f', width=4),
            fill='tozeroy',
            fillcolor='rgba(211, 47, 47, 0.2)'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=weighted_unpred,
            mode='lines',
            name='Weighted Effort (Unpredictable)',
            line=dict(color='#2e7d32', width=4),
            fill='tozeroy',
            fillcolor='rgba(46, 125, 50, 0.2)'
        ),
        secondary_y=False
    )

# Update layout
y_title = 'Weighted Effort' if selected_step == 3 else 'Effort Level (Std. Dev.)'
y_range = [0, 0.015] if selected_step == 3 else [-0.3, 0.35]

fig.update_xaxes(title_text="Weeks Since Last Inspection", showgrid=True, gridcolor='#e0e0e0')
fig.update_yaxes(title_text=y_title, secondary_y=False, showgrid=True, gridcolor='#e0e0e0', range=y_range)

if selected_step >= 1:
    fig.update_yaxes(title_text="Distribution", secondary_y=True, showgrid=False, range=[0, 0.5])

fig.update_layout(
    height=550,
    showlegend=True,
    legend=dict(
        x=0.01,
        y=0.99,
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='#e0e0e0',
        borderwidth=1
    ),
    paper_bgcolor='#ffffff',
    plot_bgcolor='#fafafa',
    font=dict(family='DM Sans, sans-serif'),
    margin=dict(l=60, r=60, t=20, b=60)
)

st.plotly_chart(fig, use_container_width=True)

# Key insight box
st.markdown("""
<div class='insight-box'>
    <h3>🎯 Key Insight</h3>
    <p style='font-size: 1.1rem; opacity: 0.95;'>
        The average effort is <strong>higher under unpredictable inspections</strong> because facilities must maintain 
        steady effort across all periods. Under predictable inspections, facilities concentrate effort in 
        high-risk weeks, but spend most of their time in low-effort periods—resulting in lower average effort overall.
    </p>
</div>
""", unsafe_allow_html=True)

# Statistics
st.markdown("### Summary Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-value'>{avg_effort_pred:.3f}</div>
        <div class='stat-label'>Average Effort<br><span style='color: #d32f2f; font-weight: 600;'>Predictable Regime</span></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-value'>{avg_effort_unpred:.3f}</div>
        <div class='stat-label'>Average Effort<br><span style='color: #2e7d32; font-weight: 600;'>Unpredictable Regime</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stat-card'>
        <div class='stat-value'>+{effort_diff:.1f}%</div>
        <div class='stat-label'>Effort Increase<br>from Unpredictability</div>
    </div>
    """, unsafe_allow_html=True)

# Additional context
st.markdown("---")
st.markdown("### About This Analysis")

st.markdown("""
This interactive visualization illustrates the key mechanism from "Predictably Unpredictable Inspections" 
(Gandhi, Olenski, and Shi, 2025). The research shows that:

- **Unpredictable inspections** induce 12.2% more lives saved compared to the current regime
- This is equivalent to a 12% increase in inspection frequency, but at zero additional cost
- The mechanism works by preventing facilities from strategically timing their effort provision

The model estimates that moving to unpredictable inspections could save an additional **103.9 lives per year** 
in U.S. nursing homes, while only minimally reducing informational value (by 1.5 percentage points).
""")

st.caption("Source: Gandhi, A., Olenski, A., & Shi, M. (2025). Predictably Unpredictable Inspections. NBER Working Paper No. 34491.")
