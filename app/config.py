from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    period: str = "5y"
    min_price: float = 5.0
    min_avg_dollar_volume: float = 10_000_000
    max_positions: int = 20
    rebalance_frequency_days: int = 5
    score_lookbacks: tuple = (20, 60, 120)
    qqq_sma_days: int = 200
    slippage_bps: float = 5.0
    fee_bps: float = 1.0
