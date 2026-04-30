import streamlit as st

# Importa TUTTO qui per evitare problemi di scope
from app.config import Config
from app.data import load_universe, download_ohlcv, download_benchmark
from app.signals import compute_features, score_frame
from app.regime import market_regime
from app.portfolio import build_portfolio
from app.backtest import run_backtest
from app.scanner import weekly_universe_update
import pandas as pd
import plotly.graph_objects as go

def render_app():
    st.set_page_config(page_title="Gemini-like Portfolio", layout="wide")
    
    # Header
    st.title("🚀 Gemini-like Momentum Portfolio")
    st.markdown("**Reverse engineering della strategia SystemTrader Gemini**")
    
    # Sidebar
    st.sidebar.title("⚙️ Configurazione")
    cfg = Config()
    
    universe = load_universe()
    if universe.empty:
        st.sidebar.error("Universo vuoto")
        st.stop()
    
    ticker_list = universe["ticker"].tolist()
    selected = st.sidebar.multiselect(
        "Titoli", 
        ticker_list[:300], 
        default=ticker_list[:20]
    )
    
    period = st.sidebar.selectbox("Periodo", ["1y", "2y", "3y"], index=1)
    max_pos = st.sidebar.slider("Max posizioni", 5, 40, 15)
    
    # Pipeline button
    if st.sidebar.button("🚀 Analizza portafoglio", type="primary", use_container_width=True):
        run_pipeline(selected[:80], period, max_pos, cfg)
    
    # Info
    st.sidebar.markdown("---")
    st.sidebar.info(f"Universo: {len(universe)} titoli")

def run_pipeline(selected, period, max_pos, cfg):
    with st.spinner("📊 Pipeline completa in corso..."):
        # Download dati
        close, vol = download_ohlcv(selected, period)
        if close.empty:
            st.error("❌ Dati vuoti")
            return
        
        # Segnali
        qqq = download_benchmark("QQQ", period).reindex(close.index).ffill()
        feats = compute_features(close, vol)
        scores = pd.DataFrame({t: score_frame(df) for t, df in feats.items()}).fillna(0)
        
        # Regime e portafoglio
        regime = market_regime(qqq)
        weights = build_portfolio(scores, regime, max_pos)
        results = run_backtest(close, weights)
        
        # Scanner
        latest = scores.iloc[-1]
        updated, adds, removes = weekly_universe_update(latest, list(close.columns))
        
        # Render
        show_results(results, weights.tail(), close.columns.tolist(), adds, removes)

def show_results(results, weights, universe, adds, removes):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Titoli", len(universe))
    col2.metric("Aggiunti", len(adds))
    col3.metric("Rimosse", len(removes))
    col4.metric("Posizioni", int((weights.iloc[-1] > 0).sum()))
    
    # Grafico equity
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=results["equity"], name="Portafoglio", line=dict(color="#00D4AA")))
    fig.add_trace(go.Scatter(y=(1 + results["net_return"]).cumprod(), name="Benchmark netto"))
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Performance recenti")
    st.dataframe(results[["net_return", "turnover"]].tail(20))
    
    st.subheader("Pesi attuali")
    st.dataframe(weights.iloc[-1].sort_values(ascending=False).head(20))

if __name__ == "__main__":
    render_app()
