import numpy as np
import pandas as pd

from hyx import analysis as A, data


def _ex(n=60, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2010-01-31", periods=n, freq="ME")
    e, t = rng.normal(0.01, 0.04, n), rng.normal(0.002, 0.01, n)
    f = 0.5 * e + 0.3 * t + rng.normal(0, 0.005, n)
    return pd.DataFrame({"fund": f, "equity": e, "treasury": t}, index=idx)


def test_walk_forward_uses_only_past_months():
    ex = _ex(); B1 = A.walk_forward_betas(ex, 36)
    ex2 = ex.copy(); ex2.iloc[-1] = ex2.iloc[-1] * 50          # change the last month only
    B2 = A.walk_forward_betas(ex2, 36)
    pd.testing.assert_frame_equal(B1, B2)                        # betas for every month, including the last, are unchanged


def test_regression_recovers_known_betas():
    r = A.regress(_ex(240, 1))
    assert abs(r["beta_equity"] - 0.5) < 0.03 and abs(r["beta_treasury"] - 0.3) < 0.08


def test_par_bond_return_signs():
    idx = pd.date_range("2020-01-01", periods=3)
    dt = pd.Series([np.nan, 1 / 365.25, 1 / 365.25], index=idx)
    flat = data.par_bond_return(pd.Series([0.04, 0.04, 0.04], index=idx), 5, dt)
    assert abs(flat.iloc[2] - 0.04 / 365.25) < 1e-12           # unchanged yield: carry only
    up = data.par_bond_return(pd.Series([0.04, 0.04, 0.05], index=idx), 5, dt)
    assert -0.05 < up.iloc[2] < -0.04                            # +100 bp on a 5y par bond: about -4.4%


def test_zero_beta_replica_is_cash():
    ex = _ex(); m = ex.add(0.001); m["cash"] = 0.001
    B = pd.DataFrame({"b_equity": 0.0, "b_treasury": 0.0}, index=ex.index[36:])
    rep, _ = A.replica(m, ex, B, 0)
    assert np.allclose(rep, 0.001)
