"""Daily total returns for the fund and SPY, a constant-maturity Treasury return from the par curve, and T-bill cash."""
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAW = "data/raw/"


def total_returns(symbols):
    px = pq.read_table(RAW + "stock_prices.parquet", columns=["symbol", "report_date", "close"],
                       filters=[("symbol", "in", symbols)]).to_pandas()
    px["close"] = px["close"].astype(float)
    px = px.pivot(index="report_date", columns="symbol", values="close")
    px.index = pd.to_datetime(px.index)
    dv = pq.read_table(RAW + "stock_dividend_events.parquet", filters=[("symbol", "in", symbols)]).to_pandas()
    dv["amount"] = dv["amount"].astype(float)
    dv["report_date"] = pd.to_datetime(dv["report_date"])
    dv = dv.pivot_table(index="report_date", columns="symbol", values="amount", aggfunc="sum").reindex(px.index).fillna(0.0)
    return ((px + dv) / px.shift(1) - 1).iloc[1:]


def par_bond_return(y, maturity, dt):
    """Daily return of a constant-maturity par bond: carry minus duration x change plus convexity (semi-annual)."""
    a = (1 + y / 2) ** (-2 * maturity)
    dur = (1 - a) / y
    conv = 2 / y ** 2 * (1 - a) - 2 * maturity / (y * (1 + y / 2) ** (2 * maturity + 1))
    dy = y.diff()
    return y.shift(1) * dt - dur.shift(1) * dy + 0.5 * conv.shift(1) * dy ** 2


def load(cfg):
    tr = total_returns([cfg["fund"], cfg["equity"]])
    y = pq.read_table(RAW + "daily_treasury_yield.parquet").to_pandas()
    y.index = pd.to_datetime(y.pop("report_date"))
    y = y.astype(float).reindex(tr.index).ffill()
    dt = tr.index.to_series().diff().dt.days / 365.25
    col = f"bc_{cfg['treasury_maturity']}year"
    df = pd.DataFrame({"fund": tr[cfg["fund"]], "equity": tr[cfg["equity"]],
                       "treasury": par_bond_return(y[col], cfg["treasury_maturity"], dt),
                       "cash": y["bc_3month"].shift(1) * dt}).dropna()
    return df.loc[cfg["start"]:cfg["end"]]


def monthly(df):
    return (1 + df).resample("ME").prod() - 1
