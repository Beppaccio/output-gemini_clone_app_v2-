import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")
st.title("🔬 Research & Analisi Tecnica")

TICKERS = ['AAPL','MSFT','GOOGL','NVDA','TSLA','META','AMZN','AMD','CRM','NFLX',
           'PLTR','SNOW','CRWD','ZS','UBER','SHOP','MELI','SE','DDOG','NET']

st.sidebar.title("⚙️ Research Config")
ticker = st.sidebar.selectbox("Seleziona titolo", TICKERS, index=0)
period = st.sidebar.selectbox("Periodo", ["3mo","6mo","1y","2y","3y"], index=2)
show_sma50 = st.sidebar.checkbox("SMA 50", value=True)
show_sma200 = st.sidebar.checkbox("SMA 200", value=True)
show_bb = st.sidebar.checkbox("Boll. Bands", value=False)

@st.cache_data(ttl=3600)
def get_ohlcv(ticker, period):
    hist = yf.Ticker(ticker).history(period=period)
    if hist.empty:
        return pd.DataFrame()
    hist.index = hist.index.tz_localize(None)
    hist.index = hist.index.astype(str)
    return hist

data = get_ohlcv(ticker, period)

if data.empty:
    st.warning("Nessun dato disponibile")
    st.stop()

# Info titolo
@st.cache_data(ttl=7200)
def get_info(t):
    try:
        info = yf.Ticker(t).info
        return {
            "Nome": info.get("longName","N/A"),
            "Settore": info.get("sector","N/A"),
            "Industria": info.get("industry","N/A"),
            "Market Cap": f"${info.get('marketCap',0)/1e9:.1f}B",
            "P/E": info.get("trailingPE","N/A"),
            "52W High": info.get("fiftyTwoWeekHigh","N/A"),
            "52W Low": info.get("fiftyTwoWeekLow","N/A"),
        }
    except:
        return {}

info = get_info(ticker)
if info:
    cols = st.columns(len(info))
    for i, (k, v) in enumerate(info.items()):
        cols[i].metric(k, v)

st.markdown("---")

# Candlestick + indicatori
close = data["Close"]
close_vals = close.values.tolist()
dates = data.index.tolist()

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=dates,
    open=data["Open"].values.tolist(),
    high=data["High"].values.tolist(),
    low=data["Low"].values.tolist(),
    close=close_vals,
    name=ticker
))

# SMA 50
if show_sma50 and len(close) >= 50:
    sma50 = close.rolling(50).mean()
    fig.add_trace(go.Scatter(x=dates, y=sma50.values.tolist(),
                             name="SMA50", line=dict(color="orange", width=1.5)))

# SMA 200
if show_sma200 and len(close) >= 200:
    sma200 = close.rolling(200).mean()
    fig.add_trace(go.Scatter(x=dates, y=sma200.values.tolist(),
                             name="SMA200", line=dict(color="red", width=1.5)))

# Bollinger Bands
if show_bb:
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper = sma20 + 2 * std20
    lower = sma20 - 2 * std20
    fig.add_trace(go.Scatter(x=dates, y=upper.values.tolist(),
                             name="BB Upper", line=dict(color="gray", dash="dot")))
    fig.add_trace(go.Scatter(x=dates, y=lower.values.tolist(),
                             name="BB Lower", line=dict(color="gray", dash="dot"),
                             fill="tonexty", fillcolor="rgba(128,128,128,0.1)"))

fig.update_layout(
    title=f"{ticker} - Grafico Tecnico",
    paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
    font_color="#FAFAFA", xaxis_rangeslider_visible=False,
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Volume
fig_vol = go.Figure()
fig_vol.add_trace(go.Bar(x=dates, y=data["Volume"].values.tolist(),
                          marker_color="#00C2FF", name="Volume"))
fig_vol.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
                       font_color="#FAFAFA", height=200, title="Volume")
st.plotly_chart(fig_vol, use_container_width=True)

# Statistiche rendimenti
st.subheader("📊 Statistiche rendimenti")
rets = close.pct_change().dropna()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rendimento totale", f"{(close.iloc[-1]/close.iloc[0]-1)*100:.1f}%")
c2.metric("Vol. annua", f"{rets.std()*np.sqrt(252)*100:.1f}%")
c3.metric("Sharpe (rf=0)", f"{(rets.mean()/rets.std())*np.sqrt(252):.2f}")
max_dd = ((close/close.cummax())-1).min()
c4.metric("Max Drawdown", f"{max_dd*100:.1f}%")
c5.metric("Giorni dati", str(len(close)))
