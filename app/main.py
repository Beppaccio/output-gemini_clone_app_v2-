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
    cfg = Config()
    
    # Sidebar
    st.sidebar.title("⚙️ Configurazione")
    universe = load_universe()
    selected = st.sidebar.multiselect(
        "Titoli (max 100)", 
        universe["ticker"].tolist()[:300], 
        default=universe["ticker"].head(20).tolist()
    )
    period = st.sidebar.selectbox("Periodo dati", ["1y", "2y", "3y", "5y"])
    max_positions = st.sidebar.slider("Max posizioni", 5, 40, 20)
    
    if st.sidebar.button("🚀 Run full pipeline", type="primary"):
        with st.spinner("📥 Downloading data..."):
            close, vol = download_ohlcv(selected[:100], period=period)
        
        if close.empty or len(close.columns) == 0:
            st.error("❌ Nessun dato valido scaricato")
            st.stop()
        
        st.success(f"✅ Dati: {len(close.columns)} titoli, {len(close)} giorni")
        
        with st.spinner("🧮 Calcolando segnali..."):
            qqq = download_benchmark("QQQ", period=period).reindex(close.index).ffill()
            feats = compute_features(close, vol)
            score_ts = {}
            for t, df in feats.items():
                try:
                    score_ts[t] = score_frame(df)
                except:
                    continue
            scores = pd.DataFrame(score_ts).fillna(method='ffill').fillna(0)
        
        with st.spinner("⚙️ Pipeline completa..."):
            regime = market_regime(qqq)
            weights = build_portfolio(scores, regime, max_positions=max_positions)
            results = run_backtest(close, weights)
            latest_scores = scores.iloc[-1]
            updated, add_candidates, remove_candidates = weekly_universe_update(latest_scores, list(close.columns))
        
        render(results, weights, close.columns.tolist(), add_candidates, remove_candidates)
