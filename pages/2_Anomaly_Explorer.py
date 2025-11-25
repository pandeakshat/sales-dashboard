import streamlit as st
import plotly.express as px
from src.anomaly_engine import (
    detect_anomalies, 
    analyze_root_causes, 
    get_anomaly_breakdown, 
    get_top_anomalous_products
)

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Anomaly Explorer")
st.title("🔍 Anomaly Detection Engine")

# Check Data
if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Data not loaded. Please go to the Home page and upload a CSV.")
    st.stop()

df = st.session_state['df']

# -----------------------------------------------------------------------------
# 2. Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Model Tuning")
    
    contamination = st.slider(
        "Sensitivity Threshold", 
        min_value=0.01, 
        max_value=0.15, 
        value=0.05, 
        step=0.01,
        help="Higher values make the model more sensitive, flagging more points as anomalies."
    )
    
    st.info(f"Scanning for the top **{contamination*100:.0f}%** statistical outliers based on Sales, Profit, and Discount patterns.")

# -----------------------------------------------------------------------------
# 3. Run Logic Engine
# -----------------------------------------------------------------------------
# Step 1: Detect
raw_anomalies = detect_anomalies(df, contamination=contamination)

# Step 2: Analyze Root Cause
analyzed_anomalies = analyze_root_causes(raw_anomalies, df)

# -----------------------------------------------------------------------------
# 4. Top Level Metrics
# -----------------------------------------------------------------------------
c1, c2, c3 = st.columns(3)

# Count
c1.metric("Anomalies Detected", f"{len(analyzed_anomalies)}")

# Financial Risk (Sum of negative profits in the anomaly set)
risk_val = 0
if not analyzed_anomalies.empty and 'Profit' in analyzed_anomalies.columns:
    risk_val = analyzed_anomalies[analyzed_anomalies['Profit'] < 0]['Profit'].sum()

c2.metric("Financial Risk (Losses)", f"${abs(risk_val):,.0f}", delta="Potential Savings", delta_color="inverse")

# Impact %
impact_pct = len(analyzed_anomalies) / len(df) if len(df) > 0 else 0
c3.metric("Dataset Impact", f"{impact_pct:.1%}")

st.divider()

# -----------------------------------------------------------------------------
# 5. Micro View: Scatter Plot & Root Cause Pie
# -----------------------------------------------------------------------------
st.subheader("📍 Anomaly Scatter Map")
col_chart, col_root = st.columns([3, 1])

with col_chart:
    # Prepare Plot Data (Combine Normal + Anomaly)
    plot_df = df.copy()
    plot_df['Type'] = 'Normal'
    plot_df['Severity'] = 0.05 # Default small size for normal points
    
    if not analyzed_anomalies.empty:
        plot_df.loc[analyzed_anomalies.index, 'Type'] = 'Anomaly'
        plot_df.loc[analyzed_anomalies.index, 'Severity'] = analyzed_anomalies['Severity']

    # Scatter Plot
    fig = px.scatter(
        plot_df, 
        x="Sales", 
        y="Profit", 
        color="Type",
        size="Severity", 
        size_max=25, # Controls how big the bubbles get
        color_discrete_map={"Normal": "#f3f4f6", "Anomaly": "#ef4444"},
        hover_data=["Product Name", "Category", "Severity"],
        title="Sales vs Profit (Size = Severity)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_root:
    # Pie Chart of Root Causes
    if not analyzed_anomalies.empty and 'Main_Factor' in analyzed_anomalies.columns:
        st.markdown("**Primary Drivers**")
        drivers = analyzed_anomalies['Main_Factor'].value_counts().reset_index()
        drivers.columns = ['Factor', 'Count']
        
        fig_d = px.pie(drivers, names='Factor', values='Count', hole=0.4)
        fig_d.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_d, use_container_width=True)
    else:
        st.info("No anomalies to analyze.")

st.divider()

# -----------------------------------------------------------------------------
# 6. Macro View: Systemic Issues (Heatmap & Table)
# -----------------------------------------------------------------------------
st.subheader("📊 Systemic Analysis")

tab1, tab2 = st.tabs(["🗺️ Regional Heatmap", "🏆 Top Offender Products"])

with tab1:
    # 1. Get Aggregated Data
    breakdown = get_anomaly_breakdown(analyzed_anomalies)
    
    if not breakdown.empty:
        # 2. Pivot for Heatmap
        heatmap_data = breakdown.pivot(index='Category', columns='Region', values='Count').fillna(0)
        
        # 3. Plot
        fig_heat = px.imshow(
            heatmap_data, 
            labels=dict(x="Region", y="Category", color="Count"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale="Reds",
            text_auto=True,
            aspect="auto"
        )
        fig_heat.update_layout(title="Concentration of Anomalies by Region & Category")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Not enough data or missing Region/Category columns.")

with tab2:
    # 1. Get Top Products
    top_products = get_top_anomalous_products(analyzed_anomalies, top_n=10)
    
    if not top_products.empty:
        st.markdown("**Products with highest anomaly frequency**")
        
        # 2. Display Table with Formatting
        # We assume 'Total_Loss' is negative, so we format nicely
        st.dataframe(
            top_products.style.background_gradient(subset=['Anomaly_Count'], cmap='Reds')
            .format({
                "Total_Loss": "${:,.0f}", 
                "Avg_Severity": "{:.2f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No anomalies found.")