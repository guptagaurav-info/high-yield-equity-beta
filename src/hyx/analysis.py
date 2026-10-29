"""Factor regressions, a walk-forward equity + Treasury replica, and the hedged residual."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

ann = lambda r: (1 + r).prod() ** (12 / len(r)) - 1
vol = lambda r: r.std() * np.sqrt(12)
mdd = lambda r: ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min()


def regress(ex, y="fund", x=("equity", "treasury"), lags=6):
    r = sm.OLS(ex[y], sm.add_constant(ex[list(x)])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return {"alpha_month": r.params["const"], "alpha_t": r.tvalues["const"], **{f"beta_{k}": r.params[k] for k in x},
            **{f"t_{k}": r.tvalues[k] for k in x}, "r2": r.rsquared, "n": int(r.nobs)}


def up_down(ex):
    dn = ex["equity"] < 0
    out = {}
    for name, msk in [("down", dn), ("up", ~dn)]:
        r = sm.OLS(ex["fund"][msk], sm.add_constant(ex[["equity", "treasury"]][msk])).fit()
        out[name] = {"beta_equity": r.params["equity"], "beta_treasury": r.params["treasury"], "months": int(msk.sum())}
    return out


def walk_forward_betas(ex, window):
    """Betas for month i use only months i-window .. i-1."""
    rows = []
    for i in range(window, len(ex)):
        w = ex.iloc[i - window:i]
        p = sm.OLS(w["fund"], sm.add_constant(w[["equity", "treasury"]])).fit().params
        rows.append((ex.index[i], p["equity"], p["treasury"]))
    return pd.DataFrame(rows, columns=["date", "b_equity", "b_treasury"]).set_index("date")


def replica(m, ex, B, cost_bp):
    i = B.index
    gross = m["cash"].loc[i] + B["b_equity"] * ex["equity"].loc[i] + B["b_treasury"] * ex["treasury"].loc[i]
    turnover = B.diff().abs().sum(axis=1).fillna(B.iloc[0].abs().sum())
    net = gross - turnover * cost_bp / 1e4
    hedged = m["fund"].loc[i] - B["b_equity"] * ex["equity"].loc[i] - B["b_treasury"] * ex["treasury"].loc[i]
    return net, hedged


def diff_test(a, b, lags=6):
    d = a - b
    r = sm.OLS(d, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(r.params.iloc[0]), float(r.tvalues.iloc[0])
