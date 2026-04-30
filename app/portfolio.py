import pandas as pd, numpy as np

def build_portfolio(scores: pd.DataFrame, regime: pd.Series, max_positions:int=20):
    weights=[]
    for dt in scores.index:
        w=pd.Series(0.0, index=scores.columns)
        if regime.loc[dt] == 1:
            top=scores.loc[dt].dropna().sort_values(ascending=False).head(max_positions).index
            if len(top): w.loc[top]=1/len(top)
        weights.append(w)
    return pd.DataFrame(weights, index=scores.index)
