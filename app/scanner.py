import pandas as pd

def weekly_universe_update(latest_scores: pd.Series, old_universe: list[str], add_quantile=0.80, remove_quantile=0.20):
    s=latest_scores.dropna().sort_values(ascending=False)
    add=s[s>=s.quantile(add_quantile)].index.tolist()
    remove=s[s<=s.quantile(remove_quantile)].index.tolist()
    updated=[t for t in old_universe if t not in remove] + [t for t in add if t not in old_universe]
    return updated, add, remove
