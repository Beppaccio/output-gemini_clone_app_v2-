from __future__ import annotations
import pandas as pd, requests, yfinance as yf
from functools import lru_cache

EXCHANGE_URLS={
    "NASDAQ":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download",
    "NYSE":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download",
    "AMEX":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download",
}

@lru_cache(maxsize=1)
def load_universe()->pd.DataFrame:
    frames=[]
    headers={"User-Agent":"Mozilla/5.0"}
    for exch,url in EXCHANGE_URLS.items():
        r=requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        df=pd.read_csv(pd.io.common.StringIO(r.text))
        sym=[c for c in df.columns if c.lower().startswith("symbol")][0]
        name=[c for c in df.columns if c.lower().startswith("name")][0]
        out=df[[sym,name]].copy()
        out.columns=["ticker","name"]
        out["exchange"]=exch
        frames.append(out)
    uni=pd.concat(frames, ignore_index=True).drop_duplicates("ticker")
    uni=uni[uni["ticker"].str.match(r"^[A-Z0-9\-]+$")].reset_index(drop=True)
    return uni

def download_ohlcv(tickers:list[str], period:str="5y"):
    raw=yf.download(tickers, period=period, auto_adjust=True, group_by="ticker", threads=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        closes={}; volumes={}
        for t in tickers:
            if t in raw.columns.get_level_values(0):
                block=raw[t].dropna(how="all")
                if not block.empty and "Close" in block and "Volume" in block:
                    closes[t]=block["Close"]
                    volumes[t]=block["Volume"]
        return pd.DataFrame(closes), pd.DataFrame(volumes)
    return raw[["Close"]].rename(columns={"Close":tickers[0]}), raw[["Volume"]].rename(columns={"Volume":tickers[0]})

def download_benchmark(symbol:str="QQQ", period:str="5y"):
    df=yf.download(symbol, period=period, auto_adjust=True, progress=False)
    return df["Close"].dropna()
