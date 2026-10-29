import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

NAVY, GOLD, GREY, RED, TEAL = "#1f3a5f", "#c9a227", "#8a8f98", "#b23a3a", "#2a7f7f"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlesize": 12.5, "figure.dpi": 150, "savefig.bbox": "tight"})


def growth(m, rep, path):
    i = rep.index
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for s, c, lab, lw in [(m["fund"].loc[i], RED, "High-yield ETF (JNK)", 2), (rep, NAVY, "Equity + Treasury replica", 2),
                          (m["treasury"].loc[i], GREY, "5-year Treasury", 1.2)]:
        ax.plot(i, (1 + s).cumprod(), color=c, lw=lw, label=lab)
    ax.set_ylabel("Growth of $1")
    ax.set_title(f"$1 in high yield vs a walk-forward equity + Treasury replica, {i[0]:%b %Y} to {i[-1]:%b %Y}")
    ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, loc="upper left"); fig.savefig(path); plt.close(fig)


def decomposition(reg, ud, path):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    vals = [reg["beta_equity"], reg["beta_treasury"]]
    b = ax.bar(["Equity beta (SPY)", "Treasury beta (5y)"], vals, color=[NAVY, GREY])
    for r, v in zip(b, vals): ax.text(r.get_x() + r.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center")
    ax.set_title(f"What the high-yield ETF is made of\n(monthly regression, R² {reg['r2']:.2f})")
    ax.text(0.5, -0.2, f"Left over (alpha): {reg['alpha_month']*1200:+.1f}% a year, t = {reg['alpha_t']:.1f}",
            transform=ax.transAxes, ha="center", color=RED)
    ax = axes[1]
    v2 = [ud["down"]["beta_equity"], ud["up"]["beta_equity"]]
    b = ax.bar(["Stocks falling", "Stocks rising"], v2, color=[RED, TEAL])
    for r, v in zip(b, v2): ax.text(r.get_x() + r.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center")
    ax.set_title("Equity beta\ndown months vs up months")
    fig.savefig(path); plt.close(fig)


def rolling_beta(B, path):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(B.index, B["b_equity"], color=NAVY, lw=2, label="Equity beta")
    ax.plot(B.index, B["b_treasury"], color=GREY, lw=1.5, label="Treasury beta")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_title("Rolling 36-month betas used by the replica (each estimated on past data only)")
    ax.legend(frameon=False); fig.savefig(path); plt.close(fig)


def crises(rows, path):
    names = [r[0] for r in rows]; x = np.arange(len(rows)); w = 0.26
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    for k, (lab, c) in enumerate([("High yield (JNK)", RED), ("S&P 500 (SPY)", NAVY), ("5-year Treasury", GREY)]):
        vals = [r[1 + k] * 100 for r in rows]
        bb = ax.bar(x + (k - 1) * w, vals, w, color=c, label=lab)
        for r, v in zip(bb, vals): ax.text(r.get_x() + r.get_width() / 2, v + (1 if v >= 0 else -3), f"{v:.0f}%", ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9); ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel("Total return over the episode (%)")
    ax.set_title("In every stress episode, high yield fell with stocks, not with Treasuries")
    ax.set_ylim(-42, 18); ax.legend(frameon=False, loc="upper right", ncol=3, fontsize=9); fig.savefig(path); plt.close(fig)


def hedged(hed, cash, path):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(hed.index, (1 + hed).cumprod(), color=RED, lw=2, label="High yield with its equity and Treasury beta hedged out")
    ax.plot(cash.index, (1 + cash).cumprod(), color=GREY, lw=1.5, label="3-month T-bills")
    ax.set_ylabel("Growth of $1"); ax.set_title("What is left after the hedge: less than cash")
    ax.legend(frameon=False, loc="upper left"); fig.savefig(path); plt.close(fig)
