import pandas as pd

def calculate_cost_of_inaction(anomalies_df: pd.DataFrame) -> dict:
    """
    Calculates potential loss if anomalies (negative profit) continue.
    Assumption: These anomalies repeat for the next 30 days.
    """
    # Filter for anomalies where profit is negative (actual losses)
    loss_makers = anomalies_df[anomalies_df['Profit'] < 0]
    
    avg_daily_loss = abs(loss_makers['Profit'].mean()) if not loss_makers.empty else 0
    projected_loss_30d = avg_daily_loss * 30
    
    return {
        "anomaly_count": len(anomalies_df),
        "loss_making_anomalies": len(loss_makers),
        "avg_daily_loss": avg_daily_loss,
        "projected_cost_30d": projected_loss_30d
    }

def generate_executive_summary(kpis: dict, cost_metrics: dict) -> str:
    """Generates a text summary string."""
    text = f"""
    ### 📝 Executive Summary
    
    **Performance**: Total sales are **${kpis['total_sales']:,.0f}** with a profit margin of **{kpis['profit_margin']:.1f}%**.
    
    **Risk Alert**: We detected **{cost_metrics['anomaly_count']}** transaction anomalies. 
    Specific attention is needed on **{cost_metrics['loss_making_anomalies']}** loss-making events.
    
    **Cost of Inaction**: If these efficiency gaps persist, the projected loss over the next month is **${cost_metrics['projected_cost_30d']:,.0f}**.
    """
    return text