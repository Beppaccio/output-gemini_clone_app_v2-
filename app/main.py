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
   if st.sidebar.button("Run full pipeline", type="primary"):
    with st.spinner("Downloading data..."):
        close, vol = download_ohlcv(selected[:100], period=period)  # Limite 100 per velocità
        
    if close.empty:
        st.error("Nessun dato scaricato. Prova con periodo più breve.")
        st.stop()
    
    st.success(f"Dati scaricati: {len(close.columns)} titoli")
    
    with st.spinner("Calcolando segnali..."):
        qqq = download_benchmark("QQQ", period=period).reindex(close.index).ffill()
        feats = compute_features(close, vol)
        score_ts = {}
        for t, df in feats.items():
            try:
                score_ts[t] = score_frame(df)
            except:
                continue
        scores = pd.DataFrame(score_ts).fillna(0)
    
    with st.spinner("Pipeline completa..."):
        regime = market_regime(qqq)
        weights = build_portfolio(scores, regime, max_positions=max_positions)
        results = run_backtest(close, weights, cfg.slippage_bps, cfg.fee_bps)
        latest_scores = scores.iloc[-1]
        updated, add_candidates, remove_candidates = weekly_universe_update(latest_scores, list(close.columns))
    
    render(results, weights, close.columns.tolist(), add_candidates, remove_candidates)
