import pandas as pd
import numpy as np

def build_portfolio(scores: pd.DataFrame, regime: pd.Series, max_positions: int = 20):
    """
    100% sicuro: nessun boolean indexing ambiguo.
    """
    # Pre-allineamento indici
    regime_clean = regime.reindex(scores.index).fillna(0).astype(int)
    
    weights_df = pd.DataFrame(index=scores.index, columns=scores.columns, dtype=float)
    
    for i in range(len(scores)):
        date = scores.index[i]
        regime_val = int(regime_clean.iloc[i])  # SCALARE int
        
        if regime_val == 1:
            # Score per riga come dict per evitare Series ambigue
            row_scores = scores.iloc[i].to_dict()
            
            # Filtra solo valori validi
            valid_scores = {k: v for k, v in row_scores.items() if pd.notna(v)}
            
            if valid_scores:
                # Top N per valore assoluto
                top_items = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)[:max_positions]
                n_top = len(top_items)
                
                for ticker, score in top_items:
                    weights_df.loc[date, ticker] = 1.0 / n_top
    
    return weights_df.fillna(0)
