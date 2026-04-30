import pandas as pd, numpy as np

def run_backtest(close: pd.DataFrame, weights: pd.DataFrame, slippage_bps=5.0, fee_bps=1.0):
    rets=close.pct_change().fillna(0)
    w=weights.reindex(close.index).fillna(0)
    port=(w.shift(1).fillna(0)*rets).sum(axis=1)
    turnover=w.diff().abs().sum(axis=1).fillna(0)
    costs=turnover*(slippage_bps+fee_bps)/10000.0
    net=port-costs
    equity=(1+net).cumprod()
    out=pd.DataFrame({"gross_return":port, "net_return":net, "turnover":turnover, "equity":equity}, index=close.index)
    return out
