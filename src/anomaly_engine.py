import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """
    Train Isolation Forest to find outliers and calculate Severity.
    
    Args:
        df: Input dataframe.
        contamination: Sensitivity (0.01 to 0.5). Higher = more anomalies.
    
    Returns:
        DataFrame containing only the anomalies with 'Severity', 'raw_score', and 'is_anomaly'.
    """
    # 1. Data Validity Checks
    if df.empty or len(df) < 50: 
        return pd.DataFrame() 

    # 2. Feature Selection
    # We focus on financial/operational metrics
    features = ['Sales', 'Profit', 'Discount', 'Quantity']
    available_features = [f for f in features if f in df.columns]
    
    # Need at least 2 features to find meaningful multi-dimensional outliers
    if len(available_features) < 2:
        return pd.DataFrame()

    # Fill NaNs with 0 to prevent model crash
    model_data = df[available_features].fillna(0)

    # 3. Fit Model
    # random_state ensures the same data always yields the same anomalies
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    preds = iso_forest.fit_predict(model_data)
    scores = iso_forest.decision_function(model_data)
    
    # 4. Process Results
    results = df.copy()
    results['is_anomaly'] = preds == -1 # -1 indicates anomaly
    results['raw_score'] = scores
    
    # 5. Calculate Severity (0 to 1 Scale)
    # The lower the raw_score, the more anomalous it is.
    # We normalize and invert so that 1.0 = Maximum Severity (Worst Outlier)
    min_score = results['raw_score'].min()
    max_score = results['raw_score'].max()
    
    if max_score != min_score:
        results['Severity'] = 1 - ((results['raw_score'] - min_score) / (max_score - min_score))
    else:
        results['Severity'] = 1.0 # Fallback if only one point/score exists
    
    # Return only the anomalies
    return results[results['is_anomaly']].copy()


def analyze_root_causes(anomalies: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
    """
    Appends a 'Main_Factor' column to explain WHY it is an anomaly.
    Uses Z-Score logic: Which column is furthest from the mean?
    """
    if anomalies.empty: return anomalies
    
    # Calculate Global Statistics
    numeric_cols = ['Sales', 'Profit', 'Discount', 'Quantity']
    valid_cols = [c for c in numeric_cols if c in full_df.columns]
    
    means = full_df[valid_cols].mean()
    stds = full_df[valid_cols].std()
    
    def get_primary_driver(row):
        max_z = 0
        driver = "Complex Pattern"
        
        for col in valid_cols:
            if stds[col] > 0:
                # Calculate absolute Z-score
                z_score = abs((row[col] - means[col]) / stds[col])
                
                # If this is the highest Z-score and significant (>2), mark it
                if z_score > max_z and z_score > 2.0:
                    max_z = z_score
                    driver = col
        return driver

    # Apply to every anomaly row
    anomalies['Main_Factor'] = anomalies.apply(get_primary_driver, axis=1)
    return anomalies


def get_anomaly_breakdown(anomalies: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates anomalies by Region and Category for heatmap visualization.
    """
    if anomalies.empty or 'Region' not in anomalies.columns or 'Category' not in anomalies.columns:
        return pd.DataFrame()
    
    # Count occurrences
    breakdown = anomalies.groupby(['Region', 'Category']).size().reset_index(name='Count')
    return breakdown


def get_top_anomalous_products(anomalies: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Finds the 'Frequent Offenders': Products that appear most often as anomalies.
    Calculates Total Loss and Average Severity per product.
    """
    if anomalies.empty or 'Product Name' not in anomalies.columns:
        return pd.DataFrame()
    
    # Define custom aggregation
    stats = anomalies.groupby('Product Name').agg(
        Anomaly_Count=('Product Name', 'count'),
        # Sum only negative profits (Real Losses)
        Total_Loss=('Profit', lambda x: x[x < 0].sum()), 
        Avg_Severity=('Severity', 'mean')
    ).reset_index()
    
    return stats.sort_values('Anomaly_Count', ascending=False).head(top_n)