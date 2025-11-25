import pandas as pd

# Define rules for specific METRICS
METRIC_RULES = {
    "Total Revenue": ["Sales"],
    "Total Profit": ["Profit"],
    "Profit Margin %": ["Sales", "Profit"],
    "Total Loss": ["Profit"],  # New Capability
    "YoY Growth %": ["Order Date", "Sales"],
    "Geospatial Map": ["State", "Sales"],
    "Top Selling Category": ["Category", "Sales"],
    "Cost of Inaction": ["Profit", "Sales"]
}

def check_kpi_feasibility(available_columns: list) -> dict:
    valid_metrics = []
    blocked_metrics = []
    
    for metric, requirements in METRIC_RULES.items():
        missing = [req for req in requirements if req not in available_columns]
        if not missing:
            valid_metrics.append(metric)
        else:
            blocked_metrics.append({"metric": metric, "missing_columns": missing})
            
    return {"valid": valid_metrics, "blocked": blocked_metrics}

def calculate_kpis(df: pd.DataFrame) -> dict:
    """Returns a dictionary of scalar KPIs including Loss."""
    if df.empty:
        return {
            "total_sales": 0, "total_profit": 0, "profit_margin": 0, 
            "total_loss": 0, "yoy_growth": 0, "order_count": 0
        }

    total_sales = df['Sales'].sum() if 'Sales' in df.columns else 0
    total_profit = df['Profit'].sum() if 'Profit' in df.columns else 0
    
    # NEW: Calculate explicit loss (sum of negative profits)
    total_loss = 0
    if 'Profit' in df.columns:
        # Sum of negative values only (absolute value for display)
        total_loss = abs(df[df['Profit'] < 0]['Profit'].sum())
    
    profit_margin = 0
    if total_sales > 0 and 'Profit' in df.columns:
        profit_margin = (total_profit / total_sales * 100)
    
    yoy_growth = 0
    if 'Order Date' in df.columns and 'Sales' in df.columns:
        current_year = df['Order Date'].dt.year.max()
        prev_year = current_year - 1
        sales_curr = df[df['Order Date'].dt.year == current_year]['Sales'].sum()
        sales_prev = df[df['Order Date'].dt.year == prev_year]['Sales'].sum()
        if sales_prev > 0:
            yoy_growth = ((sales_curr - sales_prev) / sales_prev * 100)

    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "profit_margin": profit_margin,
        "total_loss": total_loss,
        "yoy_growth": yoy_growth,
        "order_count": len(df)
    }

def get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates sales by month."""
    if 'Order Date' not in df.columns or 'Sales' not in df.columns:
        return pd.DataFrame()
        
    df = df.copy()
    df['Month_Year'] = df['Order Date'].dt.to_period('M').astype(str)
    cols = ['Sales']
    if 'Profit' in df.columns: cols.append('Profit')
    
    trend = df.groupby('Month_Year')[cols].sum().reset_index()
    return trend

def get_ranked_performers(df: pd.DataFrame, group_col: str, metric_col: str, top_n: int = 5) -> dict:
    """
    Generic ranking engine.
    Returns Top N and Bottom N dataframes for the given dimension and metric.
    """
    if group_col not in df.columns or metric_col not in df.columns:
        return {"top": pd.DataFrame(), "bottom": pd.DataFrame()}

    grouped = df.groupby(group_col)[metric_col].sum().reset_index()
    
    top = grouped.sort_values(metric_col, ascending=False).head(top_n)
    bottom = grouped.sort_values(metric_col, ascending=True).head(top_n)
    
    return {"top": top, "bottom": bottom}