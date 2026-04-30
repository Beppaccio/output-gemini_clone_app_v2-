import pandas as pd
import numpy as np

def market_regime(qqq: pd.Series) -> pd.Series:
    """Regime: 1=bull (QQQ>sma200 & sma50>sma200), 0=altro."""
    if len(qqq) < 200:
        return pd.Series(0, index=qqq.index)
    
    sma200 = qqq.rolling(200, min_periods=200).mean()
    sma50 = qqq.rolling(50, min_periods=50).mean()
    
    bull_condition = (qqq > sma200) & (sma50 > sma200)
    return bull_condition.astype(int)
