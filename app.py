import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from typing import Dict, List

st.set_page_config(page_title="Gemini Portfolio", layout="wide")

# Universo fisso per test immediato
SAMPLE_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']

def download_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
    """Download sicuro con fallback."""
    close_data = {}
    
    for ticker in tickers:
        try:
            data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not data.empty and len(data) > 30:
                close_data[ticker] = data['Close']
        except Exception as e:
            st.warning(f"Skip {ticker}: {e}")
            continue
    
    if not close_data:
        return pd.DataFrame()
    
    # COSTRUZIONE DF SICURA
    df_close = pd.DataFrame(close_data)
    df_close = df_close.dropna(how='all')
    
    return df_close

def momentum_scores(close_df: pd.DataFrame) -> pd.DataFrame:
    """Score momentum semplice."""
    if close_df.empty:
        return pd.DataFrame()
    
    scores = close_df.pct_change(20).fillna(0)
    return scores.rank(axis=1, ascending=False, method='first')

def build_weights(scores: pd.DataFrame, n_positions: int) -> pd.DataFrame:
    """Portfolio equal-weight top N."""
    if scores.empty:
        return pd.DataFrame()
    
    weights = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)
    
    for i in range(len(scores)):
        top_scores = scores.iloc[i].nlargest(n_positions)
        date = scores.index[i]
        if len(top_scores) > 0:
            weights.loc[date, top_scores.index] = 1.0 / len(top_scores)
    
    return weights

def backtest_returns(close_df: pd.DataFrame, weights_df: pd.DataFrame) -> pd.Series:
    """Backtest semplice."""
    rets = close_df.pct_change().fillna(0)
    port_rets = (weights_df.shift(1).fillna(0) * rets).sum(axis=1)
    return port_rets

# === UI ===
st.title("🚀 Gemini Momentum Portfolio")
st.markdown("*Reverse engineered da SystemTrader Gemini*")

# Sidebar
st.sidebar.title("⚙️ Selezione")
selected = st.sidebar.multiselect(
    "Titoli", 
    SAMPLE_TICKERS, 
    default=['AAPL', 'MSFT', 'GOOGL']
)
period = st.sidebar.selectbox("Dati", ["1y", "2y", "3y"])
n_pos = st.sidebar.slider("Posizioni", 2, 8, 4)

if st.sidebar.button("🔥 ANALIZZA", type="primary"):
    with st.spinner("Elaborazione..."):
        # Pipeline
        close_prices = download_prices(selected, period)
        
        if close_prices.empty:
            st.error("❌ Nessun dato valido")
            st.stop()
        
        st.success(f"✅ {len(close_prices.columns)} titoli, {len(close_prices)} giorni")
        
        scores = momentum_scores(close_prices)
        weights = build_weights(scores, n_pos)
        port_returns = backtest_returns(close_prices, weights)
        equity = (1 + port_returns).cumprod()
        
        # Risultati
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Titoli", len(close_prices.columns))
        col2.metric("Posizioni", n_pos)
        col3.metric("CAGR", f"{((equity.iloc[-1]**(252/len(equity)))**1-1):.1%}")
        col4.metric("Max DD", f"{(equity/equity.cummax()-1).min():.1%}")
        
        # Grafico
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=equity.values, name="Portfolio", line=dict(color="#00D4AA", width=3)))
        fig.update_layout(title="Equity Curve", xaxis_title="Data", yaxis_title="Valore")
        st.plotly_chart(fig, use_container_width=True)
        
        # Pesi finali
        st.subheader("🏆 Top holdings finali")
        final_weights = weights.iloc[-1].sort_values(ascending=False)
        st.bar_chart(final_weights.head(10))
        
        st.dataframe(weights.tail(5).round(3))

st.info("👈 Seleziona 3-6 titoli + clicca ANALIZZA")
