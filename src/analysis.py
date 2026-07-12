# Do prices reverse after the retail crowd piles onto one side, and when?
# This is an effect study, not a strategy. Positioning = long/short account ratio.
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

DATA = Path("data")
LOOKBACKS = (168, 336, 720)   # 1w, 2w, 1m in hours
Z_EXTREME = 1.5


def crowd_z(x, lookbacks=LOOKBACKS):
    # average the z-score over a few lookbacks so it doesn't break when the
    # market speeds up or slows down (a single fixed window did break, badly)
    parts = [(x - x.rolling(w).mean()) / x.rolling(w).std() for w in lookbacks]
    return sum(parts) / len(parts)


def bh_reject(pvals, alpha=0.05):
    # Benjamini-Hochberg, returns bool array of which p-values survive
    p = np.asarray(pvals, float)
    o = np.argsort(p)
    line = alpha * np.arange(1, len(p) + 1) / len(p)
    below = p[o] <= line
    last = np.where(below)[0].max() if below.any() else -1
    keep = np.zeros(len(p), bool)
    if last >= 0:
        keep[o[:last + 1]] = True
    return keep


def spread(ret, z, h, mask=None):
    # forward return over h hours, after long extreme vs after short extreme
    fwd = ret.shift(-1).rolling(h).sum().shift(-(h - 1))
    hi, lo = z > Z_EXTREME, z < -Z_EXTREME
    if mask is not None:
        hi, lo = hi & mask, lo & mask
    a, b = fwd[lo].dropna(), fwd[hi].dropna()   # after short, after long
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return a.mean() - b.mean(), t, p, len(a) + len(b)


def by_horizon(panel):
    z = crowd_z(panel["ls_account"])
    out = []
    for h in (12, 24, 72, 168):
        s, t, p, n = spread(panel["ret"], z, h)
        out.append([h, round(s * 100, 3), round(t, 2), round(p, 5), n])
    df = pd.DataFrame(out, columns=["h", "spread_pct", "t", "p", "n"])
    df["fdr"] = bh_reject(df["p"])
    return df


def by_oi_regime(panel, h=72):
    # split by how fast open interest is growing (30d), in three buckets
    z = crowd_z(panel["ls_account"])
    g = panel["oi"].pct_change(720).rank(pct=True)
    out = []
    for name, lo, hi in [("flat", 0, 1/3), ("rising", 1/3, 2/3), ("surging", 2/3, 1.01)]:
        s, t, _, n = spread(panel["ret"], z, h, (g >= lo) & (g < hi))
        out.append([name, round(s * 100, 3), round(t, 2), n])
    return pd.DataFrame(out, columns=["oi_regime", "spread_pct", "t", "n"])


def liq_after_extreme(panel, sym, h=24):
    # after a long extreme, how much bigger are long liquidations vs normal?
    liq = pd.read_csv(DATA / f"liq_{sym}.csv", usecols=["event_time", "side", "quantity", "price"])
    liq["ts"] = pd.to_datetime(liq["event_time"], unit="ms", utc=True)
    # SELL-side force orders = longs getting liquidated
    longs = np.where(liq["side"] == "SELL", liq["quantity"] * liq["price"], 0.0)
    hourly = pd.Series(longs, index=liq["ts"]).resample("1h").sum()

    df = panel.join(hourly.rename("long_liq"), how="inner")
    z = crowd_z(df["ls_account"])
    fwd = df["long_liq"].shift(-1).rolling(h).sum().shift(-(h - 1))
    hot = z > Z_EXTREME
    return fwd[hot].mean(), fwd[~hot].mean()


if __name__ == "__main__":
    for sym in ("BTCUSDT", "ETHUSDT"):
        panel = pd.read_parquet(DATA / f"panel_{sym}.parquet")
        print("\n" + sym, f"({len(panel)} hours)")

        h = by_horizon(panel)
        print(h.to_string(index=False))
        h.to_csv(DATA / f"results_{sym[:3].lower()}.csv", index=False)

        print(by_oi_regime(panel).to_string(index=False))

        after, base = liq_after_extreme(panel, sym)
        print(f"long liq after extreme: {after/1e6:.1f}M vs {base/1e6:.1f}M (x{after/base:.2f})")
