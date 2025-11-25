import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ==============================================================================
# 1. EXECUTIVE SUMMARY: Performance Gaps
# ==============================================================================
def analyze_performance_gaps(df: pd.DataFrame) -> list:
    """
    Identifies the Best and Worst performers across Regions and Categories.
    """
    recs = []
    
    if df.empty: return recs

    # 1. Region Analysis
    if 'Region' in df.columns and 'Profit' in df.columns:
        reg_perf = df.groupby('Region')[['Sales', 'Profit']].sum().reset_index()
        best_reg = reg_perf.loc[reg_perf['Profit'].idxmax()]
        worst_reg = reg_perf.loc[reg_perf['Profit'].idxmin()]
        
        recs.append({
            "section": "Executive Summary",
            "type": "Success",
            "text": f"🏆 **Region Star**: The **{best_reg['Region']}** region is your profit engine, contributing **${best_reg['Profit']:,.0f}**."
        })
        
        recs.append({
            "section": "Executive Summary",
            "type": "Warning",
            "text": f"📉 **Regional Lag**: The **{worst_reg['Region']}** region is underperforming with the lowest profit (${worst_reg['Profit']:,.0f}). Focus turnaround efforts here."
        })

    # 2. Category Analysis (Specific to the Worst Region)
    # "Look at the worst performer and specifically in category this..."
    if 'Region' in df.columns and 'Category' in df.columns:
        worst_reg_name = worst_reg['Region']
        worst_reg_data = df[df['Region'] == worst_reg_name]
        
        cat_perf = worst_reg_data.groupby('Category')['Profit'].sum().reset_index()
        worst_cat = cat_perf.loc[cat_perf['Profit'].idxmin()]
        
        recs.append({
            "section": "Executive Summary",
            "type": "Action",
            "text": f"🎯 **Targeted Action**: Inside the {worst_reg_name} region, the **{worst_cat['Category']}** category is the main drag on performance (Profit: ${worst_cat['Profit']:,.0f}). Review cost structure immediately."
        })

    return recs


# ==============================================================================
# 2. ANOMALY: Loss Breakdown & Driver Analysis
# ==============================================================================
def analyze_anomaly_impact(anomalies: pd.DataFrame) -> list:
    """
    Breakdown of which Category/Region is losing the most money 
    and what the primary anomaly driver is.
    """
    recs = []
    if anomalies.empty: return recs

    # Filter for actual losses (Negative Profit)
    loss_df = anomalies[anomalies['Profit'] < 0].copy()
    
    if loss_df.empty:
        recs.append({
            "section": "Anomaly Analysis",
            "type": "Info",
            "text": "✅ Good News: Detected anomalies are not currently causing financial losses (no negative profit records found)."
        })
        return recs

    # 1. "Breakdown of which category is losing the most in which region"
    # Group by Region + Category -> Sum Profit
    impact = loss_df.groupby(['Region', 'Category'])['Profit'].sum().reset_index()
    worst_case = impact.loc[impact['Profit'].idxmin()] # Min because profit is negative
    
    recs.append({
        "section": "Anomaly Analysis",
        "type": "Critical",
        "text": f"🛑 **Highest Loss Zone**: **{worst_case['Category']}** in the **{worst_case['Region']}** region accounts for the largest anomaly-driven loss (**${abs(worst_case['Profit']):,.0f}**)."
    })

    # 2. "Focus on count and discount... or profit"
    # We analyze the 'Main_Factor' column we generated in anomaly_engine
    if 'Main_Factor' in anomalies.columns:
        # Count frequency of drivers
        driver_counts = anomalies['Main_Factor'].value_counts()
        top_driver = driver_counts.idxmax()
        count = driver_counts.max()
        pct = (count / len(anomalies)) * 100
        
        recs.append({
            "section": "Anomaly Analysis",
            "type": "Insight",
            "text": f"🔍 **Root Cause Pattern**: **{top_driver}** is the dominant anomaly driver, triggering **{pct:.0f}%** of all alerts. Adjust operational thresholds for {top_driver}."
        })

    return recs


# ==============================================================================
# 3. FORECAST: Optimization Strategy (Elasticity-Based)
# ==============================================================================
def calculate_local_elasticity(df):
    """Helper to calculate elasticity for a slice of data."""
    if len(df) < 10 or df['Discount'].nunique() < 2:
        return 0.0
    X = df['Discount'].values.reshape(-1, 1)
    y = df['Sales'].values
    model = LinearRegression().fit(X, y)
    avg_sales = df['Sales'].mean()
    if avg_sales == 0: return 0.0
    return model.coef_[0] / avg_sales

def generate_profit_strategy(df: pd.DataFrame) -> list:
    """
    Iterates through Regions to find the best Discount Strategy to maximize profit.
    Logic:
    - If Elasticity < 1.0 (Inelastic): Cutting discount saves margin without hurting sales much -> DO IT.
    - If Elasticity > 2.0 (Highly Elastic): Increasing discount drives massive volume -> CONSIDER IT.
    """
    recs = []
    if df.empty: return recs
    
    # We only look at top 3 regions by volume to keep advice relevant
    top_regions = df.groupby('Region')['Sales'].sum().sort_values(ascending=False).head(3).index
    
    for region in top_regions:
        reg_df = df[df['Region'] == region]
        elasticity = calculate_local_elasticity(reg_df)
        
        # Strategy Logic
        if elasticity < 0.8:
            # Inelastic: Customers don't care about price. Stop giving money away.
            recs.append({
                "section": "Strategic Forecast",
                "type": "Profit Opportunity",
                "text": f"💰 **Profit Maximizer ({region})**: Demand is inelastic (Score: {elasticity:.2f}). **Strategy**: Reduce discounts by 5-10%. You will retain most sales while significantly boosting pure profit."
            })
        elif elasticity > 2.5:
            # Elastic: Customers love deals.
            recs.append({
                "section": "Strategic Forecast",
                "type": "Volume Opportunity",
                "text": f"📈 **Volume Play ({region})**: Demand is highly sensitive (Score: {elasticity:.2f}). **Strategy**: A strategic 5% discount increase could drive >12% volume growth."
            })
        else:
            # Neutral: Don't change much.
             recs.append({
                "section": "Strategic Forecast",
                "type": "Info",
                "text": f"⚖️ **Steady State ({region})**: Pricing is balanced (Score: {elasticity:.2f}). Maintain current discount levels."
            })
            
    return recs