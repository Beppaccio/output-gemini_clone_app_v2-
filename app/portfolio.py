import pandas as pd
import numpy as np

def build_portfolio(scores: pd.DataFrame, regime: pd.Series, max_positions: int = 20):
    """
    Portafoglio bulletproof: gestisce TUTTI i casi edge.
    """
    # Regime sicuro: sempre 0 o 1, mai NaN
    regime_clean = regime.fillna(0).clip(0, 1).astype(int)
    
    weights_list = []
    
    for i, dt in enumerate(scores.index):
        row_weights = pd.Series(0.0, index=scores.columns)
        
        # Regime BULL solo
        if regime_clean.iloc[i] == 1:
            # Score validi per questa data
            scores_today = scores.iloc[i].dropna()
            
            if len(scores_today) > 0:
                # Top N ticker
                top_tickers = scores_today.nlargest(max_positions).index
                n_top = len(top_tickers)
                row_weights.loc[top_tickers] = 1.0 / n_top
        
        weights_list.append(row_weights)
    
    return pd.DataFrame(weights_list, index=scores.index)
