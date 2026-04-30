import numpy as np, pandas as pd

def _zscore(s):
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)

def compute_features(close: pd.DataFrame, volume: pd.DataFrame)->pd.DataFrame:
    ret=close.pct_change()
    features={}
    for t in close.columns:
        p=close[t]
        v=volume[t] if t in volume.columns else pd.Series(index=close.index, dtype=float)
        df=pd.DataFrame(index=close.index)
        df["ret_20"]=p.pct_change(20)
        df["ret_60"]=p.pct_change(60)
        df["ret_120"]=p.pct_change(120)
        df["sma_50_diff"]=p/p.rolling(50).mean()-1
        df["sma_200_diff"]=p/p.rolling(200).mean()-1
        df["vol_20"]=ret[t].rolling(20).std()*np.sqrt(252) if t in ret else np.nan
        df["vol_60"]=ret[t].rolling(60).std()*np.sqrt(252) if t in ret else np.nan
        df["dollar_vol"]=p*v.rolling(20).mean()
        features[t]=df
    return {k: v for k, v in features.items()}

def score_frame(df: pd.DataFrame)->pd.Series:
    s=0.28*_zscore(df["ret_20"]) + 0.28*_zscore(df["ret_60"]) + 0.14*_zscore(df["ret_120"])
    s += 0.15*_zscore(df["sma_50_diff"]) + 0.15*_zscore(df["sma_200_diff"])
    s += -0.10*_zscore(df["vol_20"])
    s += 0.10*_zscore(np.log1p(df["dollar_vol"]))
    return s
