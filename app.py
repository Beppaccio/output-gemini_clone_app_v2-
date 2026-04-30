import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
from functools import lru_cache

st.set_page_config(page_title="Gemini Portfolio", layout="wide")

@lru_cache()
def get_sample_universe():
    return pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 
                   'AMD', 'CRM', 'UBER', 'LYFT', 'PLTR', 'SNOW', 'CRWD', 'ZS'],
        'name': ['Apple', 'Microsoft', 'Google', 'Amazon', 'Nvidia', 'Tesla', 'Meta', 
                'Netflix', 'AMD', 'Salesforce', 'Uber', 'Lyft', 'Palantir', 'Snowflake', 'CrowdStrike', 'Zscaler'],
        'exchange': ['NASDAQ']*16
    })

def download_data(tickers, period="2y"):
    close_data = {}
    for ticker in tickers[:20]:  # Limite sicuro
        try:
            data = yf.download(ticker, period=period, progress=False)['Close']
            if len(data) > 50:
                close_data[ticker] = data
        except:
            continue
    return pd.DataFrame(close_data)

def simple_momentum_scores(close_df):
    scores = pd.DataFrame(index=close_df.index, columns=close_df.columns)
    for col in close_df.columns:
        prices = close_df[col]
        scores[col] = prices.pct_change(20).fillna(0)
    return scores.rank(axis=1, ascending=False)

st.title("🚀 Gemini Momentum Portfolio")
st.markdown("**Test versione semplificata**")

# Sidebar
selected = st.sidebar.multiselect("Titoli", get_sample_universe()['ticker'].tolist(), default=['AAPL','MSFT','GOOGL'])
period = st.sidebar.selectbox("Periodo", ["1y", "2y"])
n_pos = st.sidebar.slider("Posizioni", 3, 10, 5)

if st.sidebar.button("Analizza", type="primary"):
    close = download_data(selected, period)
    if close.empty:
        st.error("No data")
    else:
        scores = simple_momentum_scores(close)
        weights = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        rets = close.pct_change()
        
        for i in range(20, len(close)):
            top_scores = scores.iloc[i].nlargest(n_pos)
            date = close.index[i]
            weights.loc[date, top_scores.index] = 1.0 / n_pos
        
        port_rets = (weights.shift(1) * rets).sum(axis=1)
        equity = (1 + port_rets).cumprod()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=equity, name="Portfolio"))
        st.plotly_chart(fig)
        
        st.dataframe(weights.tail())
        st.success("✅ Funziona!")
