import pandas as pd, numpy as np
import warnings
warnings.filterwarnings("ignore")

def build_portfolio(scores: pd.DataFrame, regime: pd.Series, max_positions: int = 20):
    """
    Costruisce portafoglio con filtro regime.
    Gestisce NaN nel regime con fallback neutrale.
    """
    weights = []
    
    # Regime sicuro: 1=bull, 0=bear/neutro, NaN→neutro
    regime_safe = regime.fillna(0).astype(int).reindex(scores.index, fill_value=0)
    
    for dt in scores.index:
        w = pd.Series(0.0, index=scores.columns)
        
        # Solo in regime bull (1)
        if regime_safe.loc[dt] == 1:
            # Top N per score, escludendo NaN
            valid_scores = scores.loc[dt].dropna()
            if len(valid_scores) > 0:
                top = valid_scores.nlargest(max_positions).index
                w.loc[top] = 1.0 / len(top)
        
        weights.append(w)
    
    return pd.DataFrame(weights, index=scores.index)
