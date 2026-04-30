import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("✅ Gemini Portfolio")

FIXED_TICKERS = ['AAPL','MSFT','GOOGL','NVDA','TSLA','META','AMZN','AMD','CRM','NFLX',
    'PLTR','SNOW','CRWD','ZS','UBER','SHOP','MELI','SE','DDOG','NET',
    'PANW','OKTA','TEAM','HUBS','BILL','GTLB','MDB','ESTC','CFLT','BRZE',
    'ORCL','ADBE','NOW','WDAY','VEEV','INTU','ANSS','CDNS','SNPS','TYL',
    'SMCI','ANET','FTNT','CIEN','LITE','COHR','WOLF','ONTO','AEHR','ACLS',
    'ENPH','FSLR','RUN','SEDG','ARRY','SPWR','NOVA','SHLS','STEM','BE','FTI']

@st.cache_data(ttl=3600)
def get_prices(tickers, period="1y"):
    frames = []
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period=period)
            if hist.empty or len(hist) < 30:
                continue
            series = hist["Close"].copy()
            series.name = str(t)
            series.index = series.index.tz_localize(None)
            frames.append(series)
        except:
            continue
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, axis=1)
    df.columns = [str(c) for c in df.columns]
    return df.dropna(how="all")

# Sidebar
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
        top = scores.iloc[i].nlargest(n_pos).index.tolist()
        for t in top:
            weights.at[prices.index[i], t] = 1.0 / n_pos

    port_rets = (weights.shift(1) * rets).sum(axis=1)
    equity = (1 + port_rets).cumprod()

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Titoli", len(prices.columns))
    cagr = (equity.iloc[-1] ** (252 / len(equity))) - 1
    col2.metric("CAGR est.", f"{cagr:.1%}")
    maxdd = (equity / equity.cummax() - 1).min()
    col3.metric("Max DD", f"{maxdd:.1%}")

    # Equity curve
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=list(range(len(equity))),
        y=equity.values.tolist(),
        name="Portfolio",
        line=dict(color="#00D4AA", width=2)
    ))
    fig1.update_layout(title="Equity Curve", paper_bgcolor="#0E1117",
                       plot_bgcolor="#0E1117", font_color="#FAFAFA")
    st.plotly_chart(fig1, use_container_width=True)

    # Bar chart pesi con Plotly - ZERO errori altair
    final_w = weights.iloc[-1].copy()
    final_w = final_w[final_w > 0].sort_values(ascending=False)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=final_w.index.tolist(),
        y=final_w.values.tolist(),
        marker_color="#00C2FF"
    ))
    fig2.update_layout(title="Pesi finali", paper_bgcolor="#0E1117",
                       plot_bgcolor="#0E1117", font_color="#FAFAFA")
    st.plotly_chart(fig2, use_container_width=True)

    # Tabella
    w_display = weights.tail(5).copy()
    w_display.index = w_display.index.astype(str)
    st.dataframe(w_display.round(3))
