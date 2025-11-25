import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from src.forecast_engine import train_model, generate_forecast, calculate_elasticity
from src.anomaly_engine import detect_anomalies

st.set_page_config(layout="wide", page_title="Forecast Studio")
st.title("🔮 Advanced Forecast Studio")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ No data loaded. Please upload a CSV on the home page.")
    st.stop()
    
df = st.session_state['df']

# ==============================================================================
# 1. SIDEBAR CONFIGURATION
# ==============================================================================
with st.sidebar:
    st.header("1. Data Scope")
    
    # A. Target Metric
    target = st.selectbox("Metric to Forecast", ["Sales", "Profit", "Quantity"])
    
    # B. Segmentation (Category/Region)
    st.markdown("**Segmentation**")
    segment_col = st.selectbox("Filter By", ["None", "Category", "Region"])
    
    segment_val = None
    if segment_col != "None":
        # Dynamic dropdown based on selection
        options = df[segment_col].unique()
        segment_val = st.selectbox(f"Select {segment_col}", options)
    
    # C. Noise Reduction
    st.markdown("**Data Cleaning**")
    remove_anomalies = st.checkbox("Exclude Anomalies from Training", value=False)
    
    st.divider()
    
    st.header("2. Strategic Scenario")
    days = st.slider("Forecast Horizon (Days)", 30, 180, 90)
    
    # D. The Discount Lever (FIXED)
    # We use integers (-50 to 50) for the slider, then divide by 100 for math
    st.markdown("**Discount Strategy**")
    st.caption("Adjust the average discount to see impact on demand.")
    
    discount_change_pct = st.slider(
        "Change Discount Rate", 
        min_value=-50, 
        max_value=50, 
        value=0, 
        step=1, 
        format="%+d%%" # Displays as +5%, -10%
    )
    # Convert integer (5) to float (0.05)
    discount_delta = discount_change_pct / 100.0

# ==============================================================================
# 2. DATA PREPARATION
# ==============================================================================
active_df = df.copy()

# Apply Segment Filter
if segment_val:
    active_df = active_df[active_df[segment_col] == segment_val]

# Apply Anomaly Filter
if remove_anomalies:
    with st.spinner("Removing outliers..."):
        anomalies = detect_anomalies(active_df)
        if not anomalies.empty:
            active_df = active_df.drop(anomalies.index)

# Calculate Elasticity (Specific to this segment!)
elasticity = calculate_elasticity(active_df)

# ==============================================================================
# 3. FORECAST MODELING
# ==============================================================================
st.subheader(f"Projected {target}: {segment_val if segment_val else 'Global'}")

# Train Model
with st.spinner(f"Training AI model for {len(active_df)} records..."):
    model = train_model(active_df, target_col=target)

if model is None:
    st.error("⚠️ Not enough data points to generate a reliable forecast for this selection.")
    st.stop()

# Generate Forecast
forecast = generate_forecast(model, days, elasticity, discount_delta)

# ==============================================================================
# 4. VISUALIZATION
# ==============================================================================

# A. Impact Metrics
base_pred = forecast[forecast['ds'] > model.history['ds'].max()]['yhat'].sum()
scenario_pred = forecast[forecast['ds'] > model.history['ds'].max()]['yhat_scenario'].sum()

delta_val = scenario_pred - base_pred
delta_pct = (delta_val / base_pred) * 100 if base_pred != 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Forecast Horizon", f"{days} Days")
col2.metric("Elasticity Score", f"{elasticity:.2f}", help="Sensitivity: 1.0 means 1% discount = 1% sales lift.")
col3.metric("Projected Total", f"{scenario_pred:,.0f}")
col4.metric("Scenario Impact", f"{delta_val:+,.0f}", f"{delta_pct:+.1f}%")

# B. Main Chart
fig = go.Figure()

# Historical Dots
fig.add_trace(go.Scatter(
    x=model.history['ds'], y=model.history['y'], mode='markers', 
    name='Historical Actuals', marker=dict(color='gray', opacity=0.3, size=3)
))

# Baseline Line (Grey Dashed)
fig.add_trace(go.Scatter(
    x=forecast['ds'], y=forecast['yhat'], mode='lines', 
    name='Baseline Trend', line=dict(dash='dash', color='gray')
))

# Scenario Line (Blue Solid)
fig.add_trace(go.Scatter(
    x=forecast['ds'], y=forecast['yhat_scenario'], mode='lines', 
    name=f'Scenario ({discount_change_pct:+}%)', 
    line=dict(color='#2563eb', width=3)
))

# Confidence Interval
fig.add_trace(go.Scatter(
    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
    fill='toself', name='Uncertainty Range', 
    line=dict(color='rgba(0,0,0,0)'), fillcolor='rgba(37, 99, 235, 0.1)', showlegend=False
))

fig.update_layout(
    title=f"Forecast Analysis: {segment_val if segment_val else 'All Segments'}",
    hovermode="x unified",
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# C. Explanation
st.info(
    f"ℹ️ **How this works:** The model detected a Price Elasticity of **{elasticity:.2f}** for {segment_val if segment_val else 'this dataset'}. "
    f"Simulating a **{discount_change_pct:+d}%** change in discount results in a **{delta_pct:+.1f}%** shift in {target}."
)