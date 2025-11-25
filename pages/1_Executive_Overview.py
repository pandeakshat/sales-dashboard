import streamlit as st
import plotly.express as px
from src.kpi_engine import calculate_kpis, get_monthly_trend, get_ranked_performers
from src.data_loader import filter_data # Ensure this is imported or defined in data_loader

st.set_page_config(layout="wide")
st.title("📊 Executive Overview")

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("Data not loaded. Please go to the Home page and upload a file.")
    st.stop()

df = st.session_state['df']

# --- Sidebar: Global Filters ---
with st.sidebar:
    st.header("Global Filters")
    # Determine valid filters based on columns
    valid_regions = df['Region'].unique() if 'Region' in df.columns else []
    valid_cats = df['Category'].unique() if 'Category' in df.columns else []
    
    regions = st.multiselect("Region", valid_regions, default=valid_regions)
    categories = st.multiselect("Category", valid_cats, default=valid_cats)

# Apply Global Filters (Using the filter_data function from src)
# Note: You might need to ensure src.data_loader has filter_data. 
# If not, a simple local filter works for now:
filtered_df = df.copy()
if regions and 'Region' in df.columns:
    filtered_df = filtered_df[filtered_df['Region'].isin(regions)]
if categories and 'Category' in df.columns:
    filtered_df = filtered_df[filtered_df['Category'].isin(categories)]

# ==============================================================================
# 1. KPI CARDS
# ==============================================================================
metrics = calculate_kpis(filtered_df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Sales", f"${metrics['total_sales']:,.0f}", f"{metrics['yoy_growth']:.1f}% YoY")
c2.metric("Total Profit", f"${metrics['total_profit']:,.0f}")
c3.metric("Profit Margin", f"{metrics['profit_margin']:.1f}%")
# New Loss Metric
c4.metric("Total Loss", f"${metrics['total_loss']:,.0f}", delta="- Loss", delta_color="inverse")
c5.metric("Order Count", f"{metrics['order_count']:,}")

st.markdown("---")

# ==============================================================================
# 2. MAIN TREND
# ==============================================================================
st.subheader("📈 Monthly Performance")
trend_df = get_monthly_trend(filtered_df)
if not trend_df.empty:
    fig_trend = px.line(
        trend_df, x='Month_Year', y=['Sales', 'Profit'], 
        markers=True, title="Sales & Profit Trends",
        color_discrete_map={"Sales": "#2563eb", "Profit": "#16a34a"}
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Trend data unavailable (Missing Date or Sales columns).")

st.markdown("---")

# ==============================================================================
# 3. PERFORMANCE ANALYZER (Split Layout)
# ==============================================================================
st.subheader("🏆 Performance Analyzer")

# Create the 2-column layout: [Controls (1) | Visuals (3)]
col_controls, col_viz = st.columns([1, 3])

# --- Column 1: The Filtering Engine ---
with col_controls:
    with st.container(border=True):
        st.markdown("**⚙️ Configuration**")
        
        # 1. Choose Dimension
        avail_dims = [c for c in ['Region', 'Category', 'Sub-Category', 'Product Name', 'State'] if c in df.columns]
        dimension = st.selectbox("Analyze By", avail_dims, index=0 if avail_dims else None)
        
        # 2. Choose Metric
        avail_metrics = [c for c in ['Sales', 'Profit', 'Quantity', 'Discount'] if c in df.columns]
        metric = st.selectbox("Metric", avail_metrics, index=0 if avail_metrics else None)
        
        st.divider()
        
        # 3. Conditional Filters (Only if "Product Name" is chosen)
        # This allows narrowing down products by specific region/category locally
        local_filtered_df = filtered_df.copy() # Start with globally filtered data
        
        if dimension == 'Product Name':
            st.markdown("**Product Filters**")
            if 'Region' in df.columns:
                f_region = st.multiselect("Filter Region", df['Region'].unique(), placeholder="All Regions")
                if f_region:
                    local_filtered_df = local_filtered_df[local_filtered_df['Region'].isin(f_region)]
            
            if 'Category' in df.columns:
                f_cat = st.multiselect("Filter Category", df['Category'].unique(), placeholder="All Categories")
                if f_cat:
                    local_filtered_df = local_filtered_df[local_filtered_df['Category'].isin(f_cat)]

# --- Column 2: The Visuals ---
with col_viz:
    if dimension and metric:
        # Get Ranked Data using the Engine
        ranks = get_ranked_performers(local_filtered_df, dimension, metric, top_n=10)
        
        # Create Tabs for Best vs Worst to save space, or side-by-side
        # User asked for "Best... Worst... comparison"
        
        v1, v2 = st.columns(2)
        
        with v1:
            st.markdown(f"**Top 10 {dimension}**")
            if not ranks['top'].empty:
                fig_top = px.bar(
                    ranks['top'], x=metric, y=dimension, orientation='h',
                    text_auto='.2s', color=metric, color_continuous_scale='Greens'
                )
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("No data found.")
                
        with v2:
            st.markdown(f"**Bottom 10 {dimension}**")
            if not ranks['bottom'].empty:
                fig_bot = px.bar(
                    ranks['bottom'], x=metric, y=dimension, orientation='h',
                    text_auto='.2s', color=metric, color_continuous_scale='Reds'
                )
                fig_bot.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=False)
                st.plotly_chart(fig_bot, use_container_width=True)
            else:
                st.info("No data found.")
    else:
        st.warning("Please select a valid Dimension and Metric to analyze.")