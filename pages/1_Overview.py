import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")
st.title("📊 Overview Mercato")

TICKERS = ['AAPL','MSFT','GOOGL','NVDA','TSLA','META','AMZN','AMD','CRM','NFLX']

@st.cache_data(ttl=3600)
def get_prices_overview(tickers, period):
    frames = []
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period=period)
            if hist.empty or len(hist) < 10:
                continue
            s = hist["Close"].copy()
            s.name = str(t)
            s.index = s.index.tz_localize(None)
            frames.append(s)
        except:
            continue
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, axis=1)
    df.columns = [str(c) for c in df.columns]
    return df.dropna(how="all")

# Sidebar
st.sidebar.title("⚙️ Overview Config")
period = st.sidebar.selectbox("Periodo", ["1mo","3mo","6mo","1y","2y"], index=3)
benchmark = st.sidebar.selectbox("Benchmark", ["QQQ","SPY","IWM"], index=0)
selected = st.sidebar.multiselect("Titoli", TICKERS, default=TICKERS[:6])

prices = get_prices_overview(tuple(selected), period)

if prices.empty:
    st.warning("Caricamento dati in corso...")
    st.stop()

# Benchmark
@st.cache_data(ttl=3600)
def get_bench(symbol, period):
    hist = yf.Ticker(symbol).history(period=period)
    if hist.empty:
        return pd.Series(dtype=float)
    s = hist["Close"].copy()
    s.index = s.index.tz_localize(None)
    return s

bench = get_bench(benchmark, period)

# Metrics top row
st.subheader("📈 Performance da inizio periodo")
cols = st.columns(len(prices.columns))
for i, col in enumerate(prices.columns):
    perf = (prices[col].iloc[-1] / prices[col].dropna().iloc[0] - 1) * 100
    cols[i].metric(col, f"{prices[col].iloc[-1]:.2f}", f"{perf:.1f}%")

st.markdown("---")

# Grafico normalizzato
st.subheader("📉 Performance normalizzata (Base 100)")
fig = go.Figure()
for col in prices.columns:
    norm = prices[col] / prices[col].dropna().iloc[0] * 100
    fig.add_trace(go.Scatter(
        x=norm.index.astype(str).tolist(),
        y=norm.values.tolist(),
        name=col, mode="lines"
    ))
if not bench.empty:
    bench_norm = bench / bench.dropna().iloc[0] * 100
    bench_aligned = bench_norm.reindex(prices.index, method="ffill")
    fig.add_trace(go.Scatter(
        x=bench_aligned.index.astype(str).tolist(),
        y=bench_aligned.values.tolist(),
        name=benchmark, mode="lines",
        line=dict(color="white", dash="dash", width=2)
    ))
fig.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
                  font_color="#FAFAFA", legend=dict(bgcolor="#161B22"))
st.plotly_chart(fig, use_container_width=True)

# Heatmap rendimenti
st.subheader("🌡️ Heatmap rendimenti mensili (portafoglio)")
rets_monthly = prices.resample("ME").last().pct_change().dropna() * 100
fig2 = go.Figure(data=go.Heatmap(
    z=rets_monthly.values.tolist(),
    x=rets_monthly.columns.tolist(),
    y=rets_monthly.index.astype(str).tolist(),
    colorscale="RdYlGn", zmid=0
))
fig2.update_layout(paper_bgcolor="#0E1117", font_color="#FAFAFA",
                   title="Rendimenti mensili %")
st.plotly_chart(fig2, use_container_width=True)

# Tabella dati
st.subheader("📋 Prezzi recenti")
display = prices.tail(10).copy()
display.index = display.index.astype(str)
st.dataframe(display.round(2))
