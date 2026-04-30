import pandas as pd

def market_regime(qqq: pd.Series)->pd.Series:
    sma200=qqq.rolling(200).mean()
    sma50=qqq.rolling(50).mean()
    return ((qqq > sma200) & (sma50 > sma200)).astype(int)
