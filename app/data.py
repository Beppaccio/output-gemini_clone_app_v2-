from __future__ import annotations
import pandas as pd, requests, yfinance as yf
from functools import lru_cache
from typing import Dict, List

EXCHANGE_URLS={
    "NASDAQ":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download",
    "NYSE":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download",
    "AMEX":"https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download",
}

@lru_cache(maxsize=1)
def load_universe()->pd.DataFrame:
    """Carica universo Nasdaq, NYSE, AMEX con parsing robusto."""
    frames = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for exch, url in EXCHANGE_URLS.items():
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            # Parsing robusto con gestione encoding e separatori
            content = r.text
            # Prova diversi encoding e separatori
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    content_decoded = content.encode().decode(enc)
                    for sep in [',', '\t', ';']:
                        df = pd.read_csv(pd.io.common.StringIO(content_decoded), sep=sep, 
                                       on_bad_lines='skip', low_memory=False)
                        
                        if not df.empty and len(df.columns) >= 2:
                            # Trova colonne Symbol e Name
                            sym_col = next((c for c in df.columns if 'symbol' in c.lower()), None)
                            name_col = next((c for c in df.columns if 'name' in c.lower()), None)
                            
                            if sym_col and name_col:
                                out = df[[sym_col, name_col]].copy()
                                out.columns = ["ticker", "name"]
                                out["exchange"] = exch
                                # Pulizia ticker
                                out["ticker"] = out["ticker"].astype(str).str.strip().str.upper()
                                out = out[out["ticker"].str.match(r"^[A-Z]{1,5}$") & 
                                        (~out["ticker"].str.contains(" ")) & 
                                        (~out["ticker"].str.contains("\\."))]
                                frames.append(out)
                                break
                    break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Errore exchange {exch}: {e}")
            continue
    
    if not frames:
        # Fallback con sample universe
        sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN', 'NFLX', 'AMD', 'CRM']
        uni = pd.DataFrame({
            'ticker': sample_tickers,
            'name': [f'Sample {t}' for t in sample_tickers],
            'exchange': 'NASDAQ'
        })
    else:
        uni = pd.concat(frames, ignore_index=True).drop_duplicates("ticker").reset_index(drop=True)
    
    return uni.head(500)  # Limite per performance

def download_ohlcv(tickers: List[str], period: str = "5y") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download OHLCV con gestione errori."""
    valid_tickers = []
    for t in tickers:
        try:
            yf.Ticker(t).history(period="5d")
            valid_tickers.append(t)
        except:
            continue
    
    if not valid_tickers:
        return pd.DataFrame(), pd.DataFrame()
    
    try:
        raw = yf.download(valid_tickers[:100], period=period, auto_adjust=True, 
                         group_by="ticker", threads=True, progress=False)
        closes, volumes = {}, {}
        for t in valid_tickers:
            if t in raw.columns.get_level_values(0):
                block = raw[t].dropna(how="all")
                if len(block) > 10 and "Close" in block.columns and "Volume" in block.columns:
                    closes[t] = block["Close"]
                    volumes[t] = block["Volume"]
        return pd.DataFrame(closes), pd.DataFrame(volumes)
    except:
        return pd.DataFrame(), pd.DataFrame()

def download_benchmark(symbol: str = "QQQ", period: str = "5y") -> pd.Series:
    try:
        df = yf.download(symbol, period=period, auto_adjust=True, progress=False)
        return df["Close"].dropna()
    except:
        return pd.Series(dtype=float)
