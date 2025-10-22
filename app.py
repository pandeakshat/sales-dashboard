# ================================================================
# 📊 Sales Dashboard for E-commerce Analytics
# Author: Akshat Pande
# ================================================================

import streamlit as st
import plotly.express as px
from utils.load import load_data
from utils.recommend import generate_recommendations

from utils.calculate import *
# ================================================================
# 🎨 THEME CONFIGURATION
# ================================================================
THEMES = {
    "Classic (Yellow-Green)": {
        "primary": "#eab308",  # yellow-500
        "secondary": "#16a34a",  # green-600
        "background": "#fefce8",  # light warm yellow
        "text": "#1e293b",  # slate-800
        "accent": "#84cc16"  # lime-500
    },
    "Dark Mode": {
        "primary": "#facc15",
        "secondary": "#22c55e",
        "background": "#111827",
        "text": "#f1f5f9",
        "accent": "#10b981"
    }
}

# --- Sidebar Theme Selector ---
selected_theme = st.sidebar.selectbox("Choose Theme", list(THEMES.keys()))
colors = THEMES[selected_theme]

# Inject CSS dynamically based on chosen theme
st.markdown(
    f"""
    <style>
    body {{
        background-color: {colors['background']};
        color: {colors['text']};
    }}
    .stApp {{
        background-color: {colors['background']};
        color: {colors['text']};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {colors['primary']};
    }}
    .stMetricLabel, .stMetricValue {{
        color: {colors['secondary']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================================================================
# 🌐 PAGE SETUP
# ================================================================
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="💹",
    layout="wide"
)

# --- Header ---
st.title("Sales Dashboard for E-commerce Analytics")

with st.expander("Project Overview & Outcome"):
    st.markdown(f"""
    ### Overview
    An interactive Streamlit dashboard that visualizes **sales**, **profit**, and **customer data** 
    from an e-commerce store. Built to showcase **business insights** and support **data-driven decisions**.

    ### Outcome
    Helps identify top-performing categories, peak sales months, and key profitability drivers.

    ---
    **Theme:** {selected_theme}  
    """)

# ================================================================
# 🧩 DATA LOADING SECTION
# ================================================================
df = load_data()

if df is not None:
    st.success("Data successfully loaded and validated!")

    # ============================================================
    # 📈 KPI SECTION
    # ============================================================
    kpis = get_basic_kpis(df)
    profit_margin = get_profit_margin(df)  # ➕ compute margin
    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Sales", f"${kpis['total_sales']:,.0f}")
    col2.metric("Total Profit", f"${kpis['total_profit']:,.0f}")
    col3.metric("Profit Margin", f"{profit_margin:.2f}%")        # ➕ new KPI
    col4.metric("Avg Discount", f"{kpis['avg_discount']:.2%}")
    col5.metric("Total Orders", kpis['total_orders'])

    # ============================================================
    #  DASHBOARD TABS
    # ============================================================
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📅 Overview",
        "📦 Category Insights",
        "🗺️ Regional Analysis",
        "📈 Product Performance",
        "👥 Segment Analysis",
        "📊 Correlation Matrix",
        "🚨 Outlier Detection",     
        "💡 Recommendations"
    ])



    # ----------------------------------------------------------------
    # TAB 1: Overview
    # ----------------------------------------------------------------
    with tab1:
        st.markdown("### Sales Overview")

        # Sales trend over time
        trend = sales_trend(df)
        fig1 = px.line(
            trend,
            x="Order Date",
            y="Sales",
            title="Sales Over Time",
            markers=True,
            labels={"Order Date": "Month", "Sales": "Total Sales"},
            color_discrete_sequence=[colors['secondary']]
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Best month
        best_month, month_sales = best_selling_month(df)
        st.info(f"**Best Selling Month (All Years):** {best_month}")

        # Monthly breakdown
        st.markdown("#### Average Sales by Month")
        fig2 = px.bar(
            month_sales,
            x=month_sales.index,
            y=month_sales.values,
            title="Total Sales by Month",
            labels={"x": "Month", "y": "Sales"},
            color_discrete_sequence=[colors['primary']]
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ----------------------------------------------------------------
    # TAB 2: Category Insights
    # ----------------------------------------------------------------
    with tab2:
        st.markdown("### Category Performance")

        # Category-wise monthly trend
        category_month = category_performance_by_month(df)
        fig3 = px.line(
            category_month,
            x="Month",
            y="Sales",
            color="Category",
            markers=True,
            title="Category-wise Sales by Month",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Discount to sales ratio
        st.markdown("### Discount vs Sales Ratio")
        discount_ratio = discount_to_sales_ratio(df)
        st.dataframe(discount_ratio.style.format("{:.2f}"))

        fig4 = px.bar(
            discount_ratio,
            x=discount_ratio.index,
            y="Sales-to-Discount",
            title="Sales-to-Discount Ratio by Category",
            labels={"x": "Category", "y": "Sales-to-Discount Ratio"},
            color_discrete_sequence=[colors['accent']]
        )
        st.plotly_chart(fig4, use_container_width=True)
        # --- Profit Margin by Category ---
        st.markdown("### Profit Margin by Category")
        margin_df = profit_margin_by_category(df)

        fig5 = px.bar(
            margin_df,
            x="Category",
            y="Profit_Margin",
            title="Profit Margin (%) by Category",
            labels={"Profit_Margin": "Profit Margin (%)"},
            color_discrete_sequence=[colors['secondary']]
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ----------------------------------------------------------------
    # TAB 3: Regional Analysis
    # ----------------------------------------------------------------
    with tab3:
        st.markdown("### 🗺️ Regional Analysis")

        # --- KPI: Best Region ---
        top_region = best_region(df)
        st.success(f"🏆 **Top Performing Region:** {top_region}")

        # --- Sales vs Profit by Region ---
        region_df = regional_summary(df)
        fig6 = px.bar(
            region_df,
            x="Region",
            y=["Sales", "Profit"],
            barmode="group",
            title="Sales vs Profit by Region",
            labels={"value": "Amount ($)", "Region": "Region", "variable": "Metric"},
            color_discrete_sequence=[colors['primary'], colors['secondary']]
        )
        st.plotly_chart(fig6, use_container_width=True)

        # --- Choropleth Map: Sales by State ---
        st.markdown("### 🌍 Sales Distribution by State (USA)")
        state_df = statewise_sales(df)

        if not state_df.empty:
            fig7 = px.choropleth(
                state_df,
                locations="State Code",       # use abbreviations now
                locationmode="USA-states",
                color="Sales",
                scope="usa",
                color_continuous_scale="YlGn",
                title="Total Sales by State"
            )
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.warning("⚠️ State-level data unavailable or not recognized.")

        # --- Regional Profit Margin ---
        st.markdown("### 💰 Regional Profit Margin (%)")
        region_df["Profit Margin (%)"] = (region_df["Profit"] / region_df["Sales"]) * 100
        fig8 = px.bar(
            region_df,
            x="Region",
            y="Profit Margin (%)",
            title="Profit Margin by Region",
            color_discrete_sequence=[colors['secondary']]
        )
        st.plotly_chart(fig8, use_container_width=True)

    # ----------------------------------------------------------------
    # TAB 4: Product Performance
    # ----------------------------------------------------------------
    with tab4:
        st.markdown("### 📈 Product Performance Analysis")

        # --- Top 10 Products by Sales ---
        st.markdown("#### 🏆 Top 10 Products by Sales")
        top_df = top_products(df)
        fig9 = px.bar(
            top_df,
            x="Sales",
            y="Product Name",
            orientation="h",
            title="Top 10 Products by Sales",
            color_discrete_sequence=[colors['primary']]
        )
        st.plotly_chart(fig9, use_container_width=True)
        st.dataframe(top_df.style.format({"Sales": "{:,.0f}", "Profit": "{:,.0f}"}))

        st.markdown("---")

        # --- Bottom 10 Products by Profit ---
        st.markdown("#### ⚠️ Bottom 10 Products by Profit")
        bottom_df = bottom_products(df)
        fig10 = px.bar(
            bottom_df,
            x="Profit",
            y="Product Name",
            orientation="h",
            title="Bottom 10 Products by Profit",
            color_discrete_sequence=[colors['secondary']]
        )
        st.plotly_chart(fig10, use_container_width=True)
        st.dataframe(bottom_df.style.format({"Sales": "{:,.0f}", "Profit": "{:,.0f}"}))

    # ----------------------------------------------------------------
    # TAB 5: Segment Analysis
    # ----------------------------------------------------------------
    with tab5:
        st.markdown("### 👥 Segment Analysis")

        seg_df = segment_summary(df)
        top_seg = best_segment(df)
        st.success(f"🏆 **Top Performing Segment:** {top_seg}")

        # --- Sales & Profit by Segment ---
        st.markdown("#### 💰 Sales & Profit by Segment")
        fig11 = px.bar(
            seg_df,
            x="Segment",
            y=["Total_Sales", "Profit"],
            barmode="group",
            title="Sales vs Profit by Segment",
            labels={"value": "Amount ($)", "Segment": "Segment", "variable": "Metric"},
            color_discrete_sequence=[colors["primary"], colors["secondary"]],
        )
        st.plotly_chart(fig11, use_container_width=True)

        # --- Profit Margin by Segment ---
        st.markdown("#### 📈 Profit Margin by Segment (%)")
        fig12 = px.bar(
            seg_df,
            x="Segment",
            y="Profit_Margin(%)",
            title="Profit Margin (%) by Segment",
            color_discrete_sequence=[colors["secondary"]],
        )
        st.plotly_chart(fig12, use_container_width=True)

        # --- Average Discount by Segment ---
        st.markdown("#### 💸 Average Discount by Segment")
        fig13 = px.bar(
            seg_df,
            x="Segment",
            y="Discount",
            title="Average Discount by Segment",
            color_discrete_sequence=[colors["accent"]],
        )
        st.plotly_chart(fig13, use_container_width=True)

        # --- Data Table ---
        st.dataframe(
            seg_df.style.format(
                {
                    "Total_Sales": "{:,.0f}",
                    "Profit": "{:,.0f}",
                    "Discount": "{:.2%}",
                    "Profit_Margin(%)": "{:.2f}",
                }
            )
        )


    # ----------------------------------------------------------------
    # TAB 6: Correlation Matrix
    # ----------------------------------------------------------------
    with tab6:
        st.markdown("### 📊 Correlation Analysis")

        corr_df = correlation_matrix(df)
        st.dataframe(corr_df.style.background_gradient(cmap="YlGn", axis=None))

        # --- Plotly Heatmap ---
        import plotly.figure_factory as ff

        z = corr_df.values
        x = corr_df.columns.tolist()
        y = corr_df.columns.tolist()

        fig14 = ff.create_annotated_heatmap(
            z=z,
            x=x,
            y=y,
            colorscale="YlGn",
            showscale=True,
            zmin=-1,
            zmax=1
        )
        fig14.update_layout(
            title="Correlation Matrix (Sales, Profit, Discount, Quantity)",
            title_x=0.5,
            font=dict(size=12, color=colors["text"]),
            plot_bgcolor=colors["background"],
            paper_bgcolor=colors["background"]
        )
        st.plotly_chart(fig14, use_container_width=True)

        # --- Insight hint ---
        st.info("🧠 **Tip:** A negative correlation between Profit and Discount suggests that higher discounts reduce profit margins.")



    # ----------------------------------------------------------------
    # TAB 7: Outlier Detection
    # ----------------------------------------------------------------
    with tab7:
        st.markdown("### 🚨 Outlier & Loss Analysis")

        st.markdown("#### ⚠️ Products with Abnormal Profit or Discount Patterns")
        outlier_df = detect_outliers(df)

        if not outlier_df.empty:
            st.dataframe(
                outlier_df.style.format({"Sales": "{:,.0f}", "Profit": "{:,.0f}", "Discount": "{:.2%}"})
                .background_gradient(cmap="YlOrBr", subset=["Discount"])
            )

            import plotly.express as px
            fig15 = px.scatter(
                outlier_df,
                x="Discount",
                y="Profit",
                color="Sales",
                hover_name="Product Name",
                title="Outlier Products: Profit vs Discount",
                color_continuous_scale="YlGn",
            )
            st.plotly_chart(fig15, use_container_width=True)
        else:
            st.success("✅ No significant outliers detected in the dataset.")

        st.markdown("---")
        st.markdown("#### 💸 Persistent Loss-Making Products")
        loss_df = loss_drivers(df)
        if not loss_df.empty:
            st.dataframe(loss_df.style.format({"Sales": "{:,.0f}", "Profit": "{:,.0f}", "Discount": "{:.2%}"}))
            fig16 = px.bar(
                loss_df.head(10),
                x="Profit",
                y="Product Name",
                orientation="h",
                title="Top 10 Products with Negative Profit",
                color_discrete_sequence=[colors["secondary"]],
            )
            st.plotly_chart(fig16, use_container_width=True)
        else:
            st.info("🎉 No consistently loss-making products found!")

    # ----------------------------------------------------------------
    # TAB 8: Recommendations
    # ----------------------------------------------------------------
    with tab8:
        st.markdown("### 💡 Data-Driven Recommendations")

        recs = generate_recommendations(df, month_sales, discount_ratio)
        for r in recs:
            st.markdown(f"- {r}")

        st.markdown("---")
        st.caption("📈 These recommendations are generated using pattern analysis on sales, discounts, and seasonal performance.")

else:
    st.warning("⚠️ Please load a dataset to start analysis.")


# ============================================================
# 🎯 Floating CTA Button (Bottom-Right)
# ============================================================
cta_url = "mailto:contact@pandeakshat.com"  # 🔗 update to your actual link
cta_label = "For Advanced Analytics - Contact"

st.markdown(
    f"""
    <style>
    .fixed-button {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: {colors['primary']};
        color: white;
        padding: 12px 22px;
        border-radius: 30px;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
        text-align: center;
        transition: all 0.3s ease;
        z-index: 9999;
    }}
    .fixed-button:hover {{
        background-color: {colors['secondary']};
        transform: scale(1.05);
        cursor: pointer;
    }}
    </style>

    <a href="{cta_url}" target="_blank" class="fixed-button">{cta_label}</a>
    """,
    unsafe_allow_html=True
)
