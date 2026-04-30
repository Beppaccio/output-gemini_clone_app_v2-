from pathlib import Path
import pandas as pd
BASE=Path("data")
BASE.mkdir(exist_ok=True)

def save_df(df: pd.DataFrame, name: str):
    path=BASE/f"{name}.parquet"
    df.to_parquet(path)
    return path

def load_df(name: str):
    path=BASE/f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else None
