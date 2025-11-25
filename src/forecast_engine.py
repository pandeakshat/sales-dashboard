import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.linear_model import LinearRegression

def calculate_elasticity(df: pd.DataFrame) -> float:
    """
    Calculates Price Elasticity: How sensitive is Sales to Discount?
    Returns a coefficient (e.g., 1.5 = 10% discount increase -> 15% sales lift).
    """
    # Safety: Need data and variance in discount to calculate regression
    if df.empty or len(df) < 10 or df['Discount'].nunique() < 2:
        return 0.0
        
    # Prepare X (Discount) and y (Sales)
    X = df['Discount'].values.reshape(-1, 1)
    y = df['Sales'].values
    
    # Simple Linear Regression
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate Impact
    slope = model.coef_[0]
    avg_sales = df['Sales'].mean()
    
    if avg_sales == 0: return 0.0
    
    # Elasticity = (Slope / Average Sales)
    # This approximates the % lift for a unit change in discount
    elasticity = slope / avg_sales
    return elasticity

def prepare_data(df: pd.DataFrame, target_col: str = 'Sales') -> pd.DataFrame:
    """Aggregates data for Prophet."""
    if 'Order Date' not in df.columns or target_col not in df.columns:
        return pd.DataFrame()
    
    # Aggregate by daily sum
    daily = df.groupby('Order Date')[target_col].sum().reset_index()
    daily.columns = ['ds', 'y']
    return daily

def train_model(df: pd.DataFrame, target_col: str = 'Sales'):
    """Trains Prophet on the filtered dataset."""
    data = prepare_data(df, target_col)
    
    # Prophet needs at least ~2 rows, but for quality we want 30+
    if len(data) < 30: 
        return None
    
    # Initialize Prophet with seasonality
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    model.fit(data)
    return model

def generate_forecast(model, periods: int, elasticity: float, discount_change: float) -> pd.DataFrame:
    """
    Generates forecast and applies Causal "What-If" logic.
    discount_change: 0.05 means +5% discount.
    """
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    
    # Causal Logic:
    # Impact Factor = 1 + (Elasticity * Discount_Change)
    # Example: Elasticity 2.0, Discount +5% (0.05) -> Impact = 1 + (2.0 * 0.05) = 1.10 (+10% Sales)
    impact_factor = 1 + (elasticity * discount_change)
    
    # Apply only to FUTURE predictions
    last_hist_date = model.history['ds'].max()
    future_mask = forecast['ds'] > last_hist_date
    
    forecast['yhat_scenario'] = forecast['yhat']
    forecast.loc[future_mask, 'yhat_scenario'] = forecast.loc[future_mask, 'yhat'] * impact_factor
    
    return forecast