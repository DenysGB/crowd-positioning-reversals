# Build the hourly panel from raw Binance futures dumps.
# price (klines 1h) + open interest & long/short ratios (metrics 5m) + funding (8h).
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("data")


def read_ts(path, col):
    df = pd.read_csv(path)
    df[col] = pd.to_datetime(df[col], format="ISO8601", utc=True)
    df = df.set_index(col).sort_index()
    return df[~df.index.duplicated()]


def make_panel(sym):
    px = read_ts(DATA / f"klines_{sym}_1h.csv", "date")
    # metrics come every 5 min, take the last reading in each hour
    m = read_ts(DATA / f"metrics_{sym}.csv", "create_time").resample("1h").last()
    fund = read_ts(DATA / f"funding_{sym}.csv", "date")["fundingRate"]
    fund = fund.resample("1h").ffill()   # funding settles every 8h, carry it forward

    out = pd.DataFrame(index=px.index)
    out["close"] = px["close"]
    out["ret"] = np.log(px["close"]).diff()
    out["oi"] = m["sum_open_interest"]
    out["ls_account"] = m["count_long_short_ratio"]           # retail accounts long/short
    out["ls_top"] = m["sum_toptrader_long_short_ratio"]       # top traders long/short
    out["funding"] = fund
    return out.dropna()


if __name__ == "__main__":
    for sym in ("BTCUSDT", "ETHUSDT"):
        p = make_panel(sym)
        p.to_parquet(DATA / f"panel_{sym}.parquet")
        p.to_csv(DATA / f"panel_{sym}.csv")
        print(sym, len(p), p.index.min().date(), "->", p.index.max().date())
