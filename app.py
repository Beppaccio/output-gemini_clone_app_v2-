import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("✅ Gemini Portfolio")

FIXED_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN']

@st.cache_data(ttl=3600)
def get_prices(tickers, period="1y"):
    frames = []
    valid_tickers = []
    for t in tickers:
        try:
            # Usa Ticker().history() - restituisce SEMPRE DataFrame pulito
            hist = yf.Ticker(t).history(period=period)
            if hist.empty or len(hist) < 30:
                continue
            # Prendi solo Close come Series con nome ticker
            series = hist["Close"].copy()
            series.name = t
            series.index = series.index.tz_localize(None)
            frames.append(series)
            valid_tickers.append(t)
        except Exception as e:
            continue

    if not frames:
        return pd.DataFrame()

    # Unisci con concat lungo axis=1 - SICURO al 100%
    df = pd.concat(frames, axis=1)
    df = df.dropna(how="all")
    return df

# --- UI ---
st.sidebar.title("⚙️ Config")
selected = st.sidebar.multiselect("Titoli", FIXED_TICKERS, default=['AAPL','MSFT','GOOGL','NVDA'])
period = st.sidebar.selectbox("Periodo", ["6mo","1y","2y","3y"], index=1)
n_pos = st.sidebar.slider("Posizioni", 2, 6, 3)

prices = get_prices(tuple(selected), period)

if prices.empty:
    st.error("❌ Nessun dato")
    st.stop()

st.sidebar.success(f"✅ {len(prices.columns)} titoli")

if st.sidebar.button("🚀 ANALIZZA", type="primary"):
    rets = prices.pct_change().fillna(0)
    scores = prices.pct_change(20).fillna(0).rank(axis=1, ascending=False)
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)

    for i in range(20, len(prices)):
        top = scores.iloc[i].nlargest(n_pos).index
        for t in top:
            col_idx = prices.columns.get_loc(t)
            weights.iloc[i, col_idx] = 1.0 / n_pos

    port_rets = (weights.shift(1) * rets).sum(axis=1)
    equity = (1 + port_rets).cumprod()

    col1, col2, col3 = st.columns(3)
    col1.metric("Titoli", len(prices.columns))
    cagr = (equity.iloc[-1] ** (252 / len(equity))) - 1
    col2.metric("CAGR est.", f"{cagr:.1%}")
    maxdd = (equity / equity.cummax() - 1).min()
    col3.metric("Max DD", f"{maxdd:.1%}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=equity.values, name="Portfolio", line=dict(color="#00D4AA", width=2)))
    fig.update_layout(
        title="Equity Curve",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font_color="#FAFAFA"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pesi finali")
    st.bar_chart(weights.iloc[-1].sort_values(ascending=False))

    st.subheader("Ultime posizioni")
    st.dataframe(weights.tail(5).round(3))
