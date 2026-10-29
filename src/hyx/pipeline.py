"""Run the study end to end: data -> regressions -> walk-forward replica -> metrics.json + figures."""
import json
from pathlib import Path

import pandas as pd
import yaml

from . import analysis as A
from . import data, figures as F

EPISODES = [("2008 crisis\n(Jan-Dec 2008)", "2008-01", "2008-12"), ("2011 euro crisis\n(Jul-Sep 2011)", "2011-07", "2011-09"),
            ("Energy bust\n(Jun 2015-Feb 2016)", "2015-06", "2016-02"), ("Q4 2018\n(Oct-Dec)", "2018-10", "2018-12"),
            ("Covid crash\n(Feb-Mar 2020)", "2020-02", "2020-03"), ("2022 rate shock\n(Jan-Dec 2022)", "2022-01", "2022-12")]


def main(cfg_path="configs/default.yaml"):
    cfg = yaml.safe_load(open(cfg_path))
    out = Path("reports"); (out / "figures").mkdir(parents=True, exist_ok=True)
    d = data.load(cfg)
    m = data.monthly(d)
    ex = m.drop(columns="cash").sub(m["cash"], axis=0)
    reg = A.regress(ex); ud = A.up_down(ex)
    B = A.walk_forward_betas(ex, cfg["window_months"])
    rep, hed = A.replica(m, ex, B, cfg["rebalance_cost_bp"])
    i = B.index; f = m["fund"].loc[i]
    mean_diff, t_diff = A.diff_test(f, rep)
    yearly = pd.DataFrame({"fund": (1 + f).groupby(i.year).prod() - 1, "replica": (1 + rep).groupby(i.year).prod() - 1,
                           "months": f.groupby(i.year).size()})
    yearly = yearly[yearly.months >= 6]
    sub = {f"{a}-{b}": {"fund": A.ann(f[a:b]), "replica": A.ann(rep[a:b]), "hedged": A.ann(hed[a:b])}
           for a, b in [("2011", "2015"), ("2016", "2020"), ("2021", "2026")]}
    stress = ex["equity"].loc[i] < cfg["stress_spy_month"]
    epi = [(n, (1 + m["fund"][a:b]).prod() - 1, (1 + m["equity"][a:b]).prod() - 1, (1 + m["treasury"][a:b]).prod() - 1) for n, a, b in EPISODES]
    res = {
        "sample": {"daily_start": str(d.index[0].date()), "daily_end": str(d.index[-1].date()), "months": len(m),
                   "replica_start": str(i[0].date()), "replica_months": len(i)},
        "full_sample_regression": reg, "up_down_beta": ud,
        "levels": {k: {"ann_return": A.ann(m[k]), "vol": A.vol(m[k]), "max_dd": A.mdd(m[k])} for k in ["fund", "equity", "treasury", "cash"]},
        "replica_window": {"fund": {"ann_return": A.ann(f), "vol": A.vol(f), "max_dd": A.mdd(f), "sharpe": (A.ann(f) - A.ann(m['cash'].loc[i])) / A.vol(f)},
                           "replica": {"ann_return": A.ann(rep), "vol": A.vol(rep), "max_dd": A.mdd(rep), "sharpe": (A.ann(rep) - A.ann(m['cash'].loc[i])) / A.vol(rep)},
                           "hedged_fund": {"ann_return": A.ann(hed), "vol": A.vol(hed)}, "cash": A.ann(m["cash"].loc[i]),
                           "gap_per_year": A.ann(f) - A.ann(rep), "mean_monthly_diff": mean_diff, "t_diff": t_diff,
                           "years_replica_ahead": int((yearly.replica > yearly.fund).sum()), "years": len(yearly),
                           "avg_beta_equity": B["b_equity"].mean(), "avg_beta_treasury": B["b_treasury"].mean(),
                           "correlation": float(f.corr(rep)), "tracking_error": A.vol(f - rep)},
        "sub_periods": sub,
        "stress_months": {"n": int(stress.sum()), "fund_avg": float(f[stress].mean()), "replica_avg": float(rep[stress].mean())},
        "episodes": {n.replace("\n", " "): {"fund": a, "equity": b, "treasury": c} for n, a, b, c in epi},
    }
    json.dump(res, open(out / "metrics.json", "w"), indent=2, default=float)
    yearly.to_csv(out / "yearly.csv"); B.to_csv(out / "betas.csv")
    F.growth(m, rep, out / "figures/growth.png"); F.decomposition(reg, ud, out / "figures/decomposition.png")
    F.rolling_beta(B, out / "figures/rolling_beta.png"); F.crises(epi, out / "figures/crises.png")
    F.hedged(hed, m["cash"].loc[i], out / "figures/hedged.png")
    print(json.dumps(res["replica_window"], indent=1, default=float)); print(json.dumps(res["full_sample_regression"], default=float))
    return res


if __name__ == "__main__":
    main()
