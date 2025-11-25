import streamlit as st
import pandas as pd
from src.data_loader import load_and_validate
from src.kpi_engine import check_kpi_feasibility

# ------------------------------------------------------------------
# 1. Page Config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Strategic Sales Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------
# 2. Session State
# ------------------------------------------------------------------
if 'data_status' not in st.session_state:
    st.session_state['data_status'] = "waiting"
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'validation_report' not in st.session_state:
    st.session_state['validation_report'] = None

# ------------------------------------------------------------------
# 3. Sidebar
# ------------------------------------------------------------------
st.sidebar.title("🗂️ Data Input")
st.sidebar.caption("Upload your sales file to begin.")

data_source = st.sidebar.radio("Source", ["Sample Data", "Upload CSV"], index=0)

if data_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Drop CSV Here", type=['csv'], label_visibility="collapsed")
    if uploaded_file:
        if st.session_state.get('last_uploaded') != uploaded_file.name:
            with st.spinner("Processing Data..."):
                report = load_and_validate(uploaded_file)
                st.session_state['df'] = report.get('df')
                st.session_state['validation_report'] = report
                st.session_state['data_status'] = "loaded" if report['success'] else "error"
                st.session_state['last_uploaded'] = uploaded_file.name
else:
    if st.sidebar.button("Load Sample Data", type="primary", use_container_width=True):
        with st.spinner("Loading sample..."):
            report = load_and_validate('data/sample.csv')
            st.session_state['df'] = report.get('df')
            st.session_state['validation_report'] = report
            st.session_state['data_status'] = "loaded"

st.sidebar.divider()
st.sidebar.info("v1.0 | API-Ready Monolith")

# ------------------------------------------------------------------
# 4. Main Area
# ------------------------------------------------------------------
st.title("🚀 Strategic Sales Dashboard")

status = st.session_state['data_status']
report = st.session_state['validation_report']

if status == "waiting":
    st.info("👈 Use the sidebar to load your dataset.")
    st.markdown("""
    ### 📋 Capabilities
    - **Smart Detection**: Recognizes `Sales`, `Profit`, `Date`, etc. automatically.
    - **Data Guardrails**: Flags potential quality issues before analysis.
    - **Dynamic Insights**: Only enables modules supported by your data.
    """)

elif status == "error":
    st.error(f"❌ Error: {report.get('error')}")

elif status == "loaded":
    df = st.session_state['df']
    issues = report.get('quality_issues', [])
    feasibility = check_kpi_feasibility(report['found_cols'])
    
    # --- A. KPI Audit (Clean 2-Col Layout) ---
    with st.container(border=True):
        st.subheader("✅ Data Readiness Report")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("##### 🟢 Active Metrics")
            if feasibility['valid']:
                # Clean bullet list for active metrics
                for metric in feasibility['valid']:
                    st.markdown(f"✅ {metric}")
            else:
                st.warning("No metrics available.")
                
        with c2:
            st.markdown("##### 🔴 Unavailable")
            if feasibility['blocked']:
                for item in feasibility['blocked']:
                    missing = ", ".join(item['missing_columns'])
                    st.markdown(f"🚫 **{item['metric']}** (Needs: `{missing}`)")
            else:
                st.success("All systems go! No missing metrics.")

    # --- B. Quality Warnings ---
    if issues:
        with st.expander("⚠️ Data Quality Notices", expanded=False):
            for issue in issues:
                st.markdown(f"- {issue}")
    else:
        st.caption("✨ Data Quality looks good.")

    st.divider()
    st.success("🎉 Data Processed. Navigate to **'Executive Overview'** using the sidebar to view insights.")
    
    # Safe Preview
    with st.expander("🔎 View Raw Data"):
        st.dataframe(df.head(), use_container_width=True)