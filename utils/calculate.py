import pandas as pd
import numpy as np

def get_basic_kpis(df):
    return {
        "total_sales": df["Sales"].sum(),
        "total_profit": df["Profit"].sum(),
        "avg_discount": df["Discount"].mean(),
        "total_orders": df["Order ID"].nunique(),
    }

def sales_trend(df):
    trend = (
        df.groupby(df["Order Date"].dt.to_period("M"))
        .sum(numeric_only=True)
        .reset_index()
    )
    trend["Order Date"] = trend["Order Date"].astype(str)
    return trend

def best_selling_month(df):
    df["Month"] = df["Order Date"].dt.month_name()
    month_sales = df.groupby("Month")["Sales"].sum().sort_values(ascending=False)
    best_month = month_sales.idxmax()
    return best_month, month_sales

def discount_to_sales_ratio(df):
    ratio = df.groupby("Category")[["Discount", "Sales"]].mean()
    ratio["Sales-to-Discount"] = ratio["Sales"] / ratio["Discount"].replace(0, np.nan)
    return ratio

def category_performance_by_month(df):
    df["Month"] = df["Order Date"].dt.month_name()
    return df.groupby(["Category", "Month"])[["Sales", "Profit"]].sum().reset_index()


def get_profit_margin(df):
    """Compute overall profit margin (%)"""
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0
    return round(margin, 2)


def profit_margin_by_category(df):
    """Compute profit margin (%) per category"""
    category_margin = (
        df.groupby("Category")[["Sales", "Profit"]]
        .sum()
        .assign(Profit_Margin=lambda x: (x["Profit"] / x["Sales"]) * 100)
        .reset_index()
    )
    return category_margin


def regional_summary(df):
    """Aggregate sales and profit by region"""
    region_df = (
        df.groupby("Region")[["Sales", "Profit"]]
        .sum()
        .sort_values("Sales", ascending=False)
        .reset_index()
    )
    return region_df


def best_region(df):
    """Return the region with highest total sales"""
    region_sales = df.groupby("Region")["Sales"].sum()
    return region_sales.idxmax()


def statewise_sales(df):
    """Summarize sales and profit by state for choropleth map"""
    state_df = (
        df.groupby("State")[["Sales", "Profit"]]
        .sum()
        .reset_index()
    )

    # Mapping of full state names to abbreviations (USA)
    us_state_abbrev = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL',
        'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
        'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
        'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT',
        'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND',
        'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
        'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
        'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI',
        'Wyoming': 'WY'
    }

    state_df["State Code"] = state_df["State"].map(us_state_abbrev)
    state_df = state_df.dropna(subset=["State Code"])  # remove unrecognized states
    return state_df

def top_products(df, n=10):
    """Top n products by total sales"""
    top_df = (
        df.groupby("Product Name")[["Sales", "Profit"]]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(n)
        .reset_index()
    )
    return top_df


def bottom_products(df, n=10):
    """Bottom n products by total profit (lowest first)"""
    bottom_df = (
        df.groupby("Product Name")[["Sales", "Profit"]]
        .sum()
        .sort_values("Profit", ascending=True)
        .head(n)
        .reset_index()
    )
    return bottom_df

def segment_summary(df):
    """Aggregate sales, profit, and discount by customer segment."""
    seg_df = (
        df.groupby("Segment")[["Sales", "Profit", "Discount"]]
        .mean(numeric_only=True)
        .reset_index()
    )
    seg_df["Total_Sales"] = df.groupby("Segment")["Sales"].sum().values
    seg_df["Profit_Margin(%)"] = (
        df.groupby("Segment")["Profit"].sum().values
        / df.groupby("Segment")["Sales"].sum().values
    ) * 100
    return seg_df


def best_segment(df):
    """Return segment with highest total sales."""
    seg_sales = df.groupby("Segment")["Sales"].sum()
    return seg_sales.idxmax()


def correlation_matrix(df):
    """Compute correlation matrix for key numeric features."""
    numeric_cols = ["Sales", "Profit", "Discount", "Quantity"]
    available_cols = [col for col in numeric_cols if col in df.columns]
    corr = df[available_cols].corr(numeric_only=True)
    return corr.round(2)

def detect_outliers(df, z_thresh=2.5):
    """
    Detect products with abnormal discount or profit behavior.
    Uses Z-score to identify outliers.
    """
    outlier_cols = ["Sales", "Profit", "Discount"]
    numeric_df = df[outlier_cols].copy()

    # Compute z-scores
    z_scores = (numeric_df - numeric_df.mean()) / numeric_df.std()
    outliers = df[(abs(z_scores["Profit"]) > z_thresh) | (abs(z_scores["Discount"]) > z_thresh)]

    # Summarize by product
    summary = (
        outliers.groupby("Product Name")[["Sales", "Profit", "Discount"]]
        .mean()
        .sort_values("Profit", ascending=True)
        .reset_index()
    )
    return summary


def loss_drivers(df):
    """Find products consistently yielding negative profit."""
    loss_df = (
        df.groupby("Product Name")[["Sales", "Profit", "Discount"]]
        .mean()
        .query("Profit < 0")
        .sort_values("Profit")
        .reset_index()
    )
    return loss_df
