import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Ticker fissi per test
FIXED_TICKERS = ['AAPL', 'MSFT', 'GOOGL']

st.title("✅ Gemini Portfolio - VERSIONE TEST")

# Download SEQUENZIALE sicuro
@st.cache_data
def get_prices():
    all_data = {}
    for ticker in FIXED_TICKERS:
        try:
            data = yf.download(ticker, period="1y", progress=False)
            if not data.empty:
                all_data[ticker] = data['Close']
        except:
            continue
    return pd.DataFrame(all_data).dropna()

prices = get_prices()

if prices.empty:
    st.error("No data")
    st.stop()

st.success(f"✅ Dati: {len(prices.columns)} titoli")

# Momentum semplice
rets = prices.pct_change(20).fillna(0)
scores = rets.rank(axis=1, ascending=False)

# Portfolio
n_pos = 3
weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
for i in range(20, len(prices)):
    top = scores.iloc[i].nlargest(n_pos).index
    weights.iloc[i, top] = 1.0 / n_pos

# Backtest
port_rets = (weights.shift(1) * prices.pct_change()).sum(axis=1)
equity = (1 + port_rets.dropna()).cumprod()

# Plot
fig = go.Figure()
fig.add_trace(go.Scatter(y=equity, name="Portfolio", line=dict(color="green")))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Pesi finali")
st.bar_chart(weights.iloc[-1])

st.dataframe(weights.tail())
