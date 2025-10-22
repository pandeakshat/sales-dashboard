import pandas as pd
import numpy as np
from utils.calculate import (
    best_selling_month,
    discount_to_sales_ratio,
    profit_margin_by_category,
    best_region,
    best_segment,
    detect_outliers,
    loss_drivers,
)

def generate_recommendations(df, month_sales, discount_ratio):
    recs = []

    # 1️⃣ Seasonal Sales Insight
    lowest_month = month_sales.idxmin()
    highest_month = month_sales.idxmax()
    recs.append(
        f"📅 Sales peak in **{highest_month}** and dip in **{lowest_month}** — plan marketing campaigns to balance seasonal demand."
    )

    # 2️⃣ Category-Level Optimization
    margin_df = profit_margin_by_category(df)
    top_margin = margin_df.loc[margin_df["Profit_Margin"].idxmax()]
    low_margin = margin_df.loc[margin_df["Profit_Margin"].idxmin()]
    recs.append(
        f"💰 `{top_margin['Category']}` has the highest profit margin at **{top_margin['Profit_Margin']:.1f}%**, "
        f"while `{low_margin['Category']}` underperforms with only **{low_margin['Profit_Margin']:.1f}%** — consider optimizing pricing or logistics."
    )

    # 3️⃣ Discount Efficiency
    high_discount = discount_ratio["Discount"].idxmax()
    low_discount = discount_ratio["Discount"].idxmin()
    recs.append(
        f"💡 `{high_discount}` relies heavily on discounts, while `{low_discount}` performs well with minimal discounting — "
        f"experiment with strategic discounting to improve margins."
    )

    # 4️⃣ Regional Strengths
    region = best_region(df)
    recs.append(
        f"🌍 `{region}` region continues to drive the highest total sales — ensure consistent inventory flow and marketing alignment there."
    )

    # 5️⃣ Customer Segment Efficiency
    try:
        segment = best_segment(df)
        recs.append(
            f"👥 `{segment}` segment shows the strongest buying pattern — target retention programs or loyalty perks."
        )
    except Exception:
        pass

    # 6️⃣ Outlier Warnings
    total_products = df["Product Name"].nunique()

    outlier_df = detect_outliers(df)
    if not outlier_df.empty:
        recs.append(
            f"🚨 {len(outlier_df)} out of **{total_products}** products "
            f"show unusual profit or discount behavior — review pricing and promotional impact."
        )

    # 7️⃣ Persistent Loss Drivers
    losses = loss_drivers(df)
    if not losses.empty:
        recs.append(
            f"📉 {len(losses)} out of **{total_products}** products "
            f"consistently generate negative profit — review supplier costs or remove them from promotion."
        )

    return recs
