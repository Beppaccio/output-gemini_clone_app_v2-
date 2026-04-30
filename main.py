from __future__ import annotations
import streamlit as st
from app.config import Config
from app.data import load_universe, download_ohlcv, download_benchmark
from app.signals import compute_features, score_frame
from app.regime import market_regime
from app.portfolio import build_portfolio
from app.backtest import run_backtest
from app.scanner import weekly_universe_update
from app.ui import render

def render_app():
    st.set_page_config(page_title="Gemini-like Portfolio", layout="wide")
    cfg=Config()
    universe=load_universe()
    selected=st.sidebar.multiselect("Universe", universe["ticker"].tolist(), default=universe["ticker"].head(200).tolist())
    period=st.sidebar.selectbox("History", ["2y","3y","5y"], index=2)
    max_positions=st.sidebar.slider("Max positions", 5, 40, cfg.max_positions)
    if st.sidebar.button("Run full pipeline"):
        close, vol = download_ohlcv(selected, period=period)
        qqq = download_benchmark("QQQ", period=period).reindex(close.index).ffill()
        feats = compute_features(close, vol)
        score_ts = {}
        for t, df in feats.items():
            score_ts[t]=score_frame(df)
        scores = __import__("pandas").DataFrame(score_ts)
        regime = market_regime(qqq)
        weights = build_portfolio(scores, regime, max_positions=max_positions)
        results = run_backtest(close, weights, cfg.slippage_bps, cfg.fee_bps)
        latest = scores.iloc[-1]
        updated, add, remove = weekly_universe_update(latest, selected)
        render(results, weights, selected, add, remove)
