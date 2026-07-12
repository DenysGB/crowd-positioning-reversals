import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from analysis import crowd_z, by_oi_regime, Z_EXTREME

DATA, FIG = Path("data"), Path("figures")
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})


def fig_profile():
    panel = pd.read_parquet(DATA / "panel_BTCUSDT.parquet")
    z = crowd_z(panel["ls_account"])
    r = panel["ret"].values
    pre, post = 24, 72

    def avg_path(mask):
        idx = np.where(mask.values)[0]
        idx = idx[(idx > pre) & (idx < len(panel) - post)]
        paths = [np.concatenate([[0], np.cumsum(r[i-pre:i+post+1][1:])]) for i in idx]
        return np.arange(-pre, post+1), np.nanmean(paths, 0) * 100

    x, up = avg_path(z > Z_EXTREME)
    _, dn = avg_path(z < -Z_EXTREME)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axvline(0, color="0.6", lw=0.8, ls="--")
    ax.axhline(0, color="0.8", lw=0.6)
    ax.plot(x, up - up[pre], color="#b3402f", lw=1.6, label="after long extreme")
    ax.plot(x, dn - dn[pre], color="#2f5fb3", lw=1.6, label="after short extreme")
    ax.set_xlabel("hours from extreme")
    ax.set_ylabel("cumulative BTC return (%)")
    ax.set_title("BTC, 2020-2026: crowd long -> price fades, crowd short -> price rises")
    ax.legend(frameon=False)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_event_profile.png")


def fig_regime():
    btc = by_oi_regime(pd.read_parquet(DATA / "panel_BTCUSDT.parquet"))
    eth = by_oi_regime(pd.read_parquet(DATA / "panel_ETHUSDT.parquet"))
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axhline(0, color="0.3", lw=0.8)
    ax.bar(x - 0.2, btc["spread_pct"], 0.4, color="#1a2b3c", label="BTC")
    ax.bar(x + 0.2, eth["spread_pct"], 0.4, color="#2f5fb3", label="ETH")
    ax.set_xticks(x)
    ax.set_xticklabels(btc["oi_regime"])
    ax.set_ylabel("reversal spread (%, 72h)")
    ax.set_title("Reversal shows up when open interest is rising, not when it's flat")
    ax.legend(frameon=False)
    ax.grid(alpha=0.15, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_oi_regime.png")


if __name__ == "__main__":
    fig_profile()
    fig_regime()
    print("done")
