import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🔍 Scanner Settimanale Universo")

FULL_UNIVERSE = [
    'AAPL','MSFT','GOOGL','NVDA','TSLA','META','AMZN','AMD','CRM','NFLX',
    'PLTR','SNOW','CRWD','ZS','UBER','SHOP','MELI','SE','DDOG','NET',
    'PANW','OKTA','TEAM','HUBS','BILL','GTLB','MDB','ESTC','CFLT','BRZE',
    'ORCL','ADBE','NOW','WDAY','VEEV','INTU','ANSS','CDNS','SNPS','TYL',
    'SMCI','ANET','FTNT','CIEN','LITE','COHR','WOLF','ONTO','AEHR','ACLS',
    'ENPH','FSLR','RUN','SEDG','ARRY','SPWR','NOVA','SHLS','STEM','BE'
]

st.sidebar.title("⚙️ Scanner Config")
period = st.sidebar.selectbox("Periodo dati", ["3mo","6mo","1y"], index=1)
top_n = st.sidebar.slider("Top N titoli", 5, 30, 15)
min_mom_20 = st.sidebar.slider("Min momentum 20gg (%)", -20, 50, 5)
min_mom_60 = st.sidebar.slider("Min momentum 60gg (%)", -30, 80, 10)
run_scan = st.sidebar.button("▶️ LANCIA SCANNER", type="primary")

if not run_scan:
    st.info("👈 Configura i parametri e clicca **LANCIA SCANNER**")
    st.markdown("""
    ### Come funziona lo scanner
    1. **Scarica** prezzi degli ultimi 6 mesi per tutti i ticker dell'universo
    2. **Calcola** momentum 20gg, 60gg, posizione su SMA50/SMA200
    3. **Rank** complessivo e filtro sui criteri selezionati
    4. **Output**: tabella titoli da aggiungere/rimuovere dall'universo attivo
    """)
    st.stop()

@st.cache_data(ttl=3600, show_spinner=True)
def scan_universe(tickers, period):
    rows = []
    progress = st.progress(0, text="Scansione in corso...")
    for i, t in enumerate(tickers):
        try:
            hist = yf.Ticker(t).history(period=period)
            if hist.empty or len(hist) < 60:
                continue
            hist.index = hist.index.tz_localize(None)
            close = hist["Close"]
            volume = hist["Volume"]
            rets = close.pct_change()

            mom_20 = (close.iloc[-1] / close.iloc[-21] - 1) * 100 if len(close) >= 21 else np.nan
            mom_60 = (close.iloc[-1] / close.iloc[-61] - 1) * 100 if len(close) >= 61 else np.nan
            sma50 = close.rolling(50).mean().iloc[-1]
            sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else np.nan
            above_sma50 = close.iloc[-1] > sma50
            above_sma200 = (close.iloc[-1] > sma200) if not np.isnan(sma200) else False
            vol_20 = rets.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
            avg_dollar_vol = (close * volume).rolling(20).mean().iloc[-1] / 1e6

            rows.append({
                "Ticker": t,
                "Prezzo": round(close.iloc[-1], 2),
                "Mom 20gg %": round(mom_20, 1),
                "Mom 60gg %": round(mom_60, 1),
                "Vol annua %": round(vol_20, 1),
                "Vol $ media (M)": round(avg_dollar_vol, 1),
                ">SMA50": "✅" if above_sma50 else "❌",
                ">SMA200": "✅" if above_sma200 else "❌",
            })
        except:
            continue
        progress.progress((i+1)/len(tickers), text=f"Scansione: {t}")
    progress.empty()
    return pd.DataFrame(rows)

df = scan_universe(tuple(FULL_UNIVERSE), period)

if df.empty:
    st.error("Nessun dato disponibile")
    st.stop()

# Filtro criteri
filtered = df[
    (df["Mom 20gg %"] >= min_mom_20) &
    (df["Mom 60gg %"] >= min_mom_60) &
    (df[">SMA50"] == "✅")
].sort_values("Mom 60gg %", ascending=False)

# Score composto
df["Score"] = (
    df["Mom 20gg %"].rank(pct=True) * 0.35 +
    df["Mom 60gg %"].rank(pct=True) * 0.35 +
    df["Vol $ media (M)"].rank(pct=True) * 0.15 +
    (1 - df["Vol annua %"].rank(pct=True)) * 0.15
)
df["Score"] = (df["Score"] * 100).round(1)

top_picks = df.nlargest(top_n, "Score")
bottom_picks = df.nsmallest(top_n // 2, "Score")

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ticker scansionati", len(df))
c2.metric("Titoli filtrati", len(filtered))
c3.metric("Top picks", len(top_picks))
c4.metric("Da rimuovere", len(bottom_picks))

st.markdown("---")

# Top picks
st.subheader(f"🟢 TOP {top_n} - Da aggiungere/mantenere")
st.dataframe(top_picks.set_index("Ticker").round(2), use_container_width=True)

# Bar chart score
fig = go.Figure()
fig.add_trace(go.Bar(
    x=top_picks["Ticker"].tolist(),
    y=top_picks["Score"].tolist(),
    marker_color="#00D4AA", name="Score"
))
fig.update_layout(title="Score composito Top picks",
                  paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
                  font_color="#FAFAFA")
st.plotly_chart(fig, use_container_width=True)

# Bottom picks
st.subheader("🔴 DA RIMUOVERE - Score basso")
st.dataframe(bottom_picks.set_index("Ticker").round(2), use_container_width=True)

# Scatter momentum
st.subheader("📈 Mappa momentum 20gg vs 60gg")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=df["Mom 20gg %"].tolist(),
    y=df["Mom 60gg %"].tolist(),
    mode="markers+text",
    text=df["Ticker"].tolist(),
    textposition="top center",
    marker=dict(
        size=df["Score"].fillna(0).tolist(),
        color=df["Score"].tolist(),
        colorscale="Viridis",
        showscale=True
    )
))
fig2.update_layout(
    title="Momentum 20gg vs 60gg (size=score)",
    xaxis_title="Momentum 20gg %",
    yaxis_title="Momentum 60gg %",
    paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
    font_color="#FAFAFA"
)
st.plotly_chart(fig2, use_container_width=True)

# Export
st.subheader("💾 Export")
csv = top_picks.to_csv(index=False)
st.download_button("⬇️ Download Top Picks CSV", csv, "top_picks.csv", "text/csv")
