"""Black-Litterman inputs for the user's ETF book and a reference solve (2026-11-14).

Universe: high-liquidity, low-premium ETFs only (user cannot trade futures; no 白银 LOF / high-premium QDII).
Covariance: weekly returns (Friday) over the last 156 weeks, annualised x52, shrunk 20% toward the diagonal.
Reference portfolio (prior): 股25 / 债35 / 黄金商品20 / 港股20, split inside each group as in REF.
Prior returns: Π = δ Σ w_ref (excess over cash 511880). Views: P, Q with confidence c in (0, 1]:
ω = (1 − c) / c · p τΣ p'. Posterior μ = [(τΣ)^-1 + P'Ω^-1 P]^-1 [(τΣ)^-1 Π + P'Ω^-1 Q].
Weights: max μ'w − δ/2 w'Σw, w ≥ 0, Σw ≤ 1 (rest in cash), projected gradient.
Writes bl_inputs.json (for the BL page) and prints the reference solve for two example views.
"""
from __future__ import annotations
import json
from pathlib import Path
import duckdb, numpy as np, pandas as pd

LAKE = Path("/Volumes/Treasury/quant_cn_lake")
OUT = LAKE / "meta/runs/research/20261114_black_litterman"; OUT.mkdir(parents=True, exist_ok=True)
ASSETS = [("510300.SH", "沪深300", "A股", 0.12), ("512100.SH", "中证1000", "A股", 0.07), ("159915.SZ", "创业板", "A股", 0.06),
          ("511010.SH", "5年国债", "债券", 0.15), ("511260.SH", "10年国债", "债券", 0.15), ("511090.SH", "30年国债", "债券", 0.05),
          ("518880.SH", "黄金", "黄金商品", 0.12), ("159980.SZ", "有色期货", "黄金商品", 0.04), ("159981.SZ", "能化期货", "黄金商品", 0.04),
          ("159920.SZ", "恒生", "港股", 0.10), ("513130.SH", "恒生科技", "港股", 0.10)]
CASH, WEEKS, SHRINK, TAU, DELTA = "511880.SH", 156, 0.2, 0.05, 3.0


def solve(mu: np.ndarray, S: np.ndarray, delta: float, iters: int = 5000) -> np.ndarray:
    w = np.full(len(mu), 1 / len(mu)) * 0.5
    step = 1 / (delta * np.linalg.eigvalsh(S).max())
    for _ in range(iters):
        w = w + step * (mu - delta * S @ w)
        w = np.clip(w, 0, None)
        if w.sum() > 1:  # project onto the simplex
            u = np.sort(w)[::-1]; css = np.cumsum(u) - 1
            k = np.nonzero(u - css / np.arange(1, len(u) + 1) > 0)[0][-1]
            w = np.clip(w - css[k] / (k + 1), 0, None)
    return w


def posterior(Pi: np.ndarray, S: np.ndarray, P: np.ndarray, Q: np.ndarray, conf: np.ndarray) -> np.ndarray:
    tS = TAU * S
    omega = np.diag([(1 - c) / c * p @ tS @ p for p, c in zip(P, conf)])
    A = np.linalg.inv(tS) + P.T @ np.linalg.inv(omega) @ P
    return np.linalg.solve(A, np.linalg.inv(tS) @ Pi + P.T @ np.linalg.inv(omega) @ Q)


def main() -> None:
    c = duckdb.connect()
    codes = [a[0] for a in ASSETS] + [CASH]
    D = c.execute(f"""select ts_code, trade_date, close/pre_close-1 ret from read_parquet('{LAKE}/curated/fund_daily/**/*.parquet', union_by_name=true)
                      where ts_code in ({','.join(repr(x) for x in codes)}) and pre_close > 0""").df()
    D["trade_date"] = pd.to_datetime(D.trade_date)
    R = D.pivot_table(index="trade_date", columns="ts_code", values="ret").sort_index().clip(-0.2, 0.2)
    W = ((1 + R.fillna(0)).resample("W-FRI").prod() - 1).iloc[-WEEKS:]
    X = W[[a[0] for a in ASSETS]].sub(W[CASH], axis=0)
    S0 = X.cov().to_numpy() * 52
    S = (1 - SHRINK) * S0 + SHRINK * np.diag(np.diag(S0))
    w_ref = np.array([a[3] for a in ASSETS])
    Pi = DELTA * S @ w_ref
    hist = (X.mean() * 52).to_numpy()
    cash_y = float((1 + W[CASH]).prod() ** (52 / len(W)) - 1)
    print(f"weeks {W.index[0].date()}..{W.index[-1].date()}, cash yield {cash_y:.2%}, ref vol {np.sqrt(w_ref @ S @ w_ref):.2%}")
    T = pd.DataFrame({"name": [a[1] for a in ASSETS], "vol": np.sqrt(np.diag(S)), "prior": Pi, "hist_3y": hist, "w_ref": w_ref})
    w0 = solve(Pi, S, DELTA)
    T["w_prior_solve"] = w0
    # example views: 1) A股 (沪深300) absolute 8% excess, 50%; 2) 黄金 beats 10年国债 by 5%, 30%
    n = len(ASSETS); P = np.zeros((2, n)); P[0, 0] = 1; P[1, 6] = 1; P[1, 4] = -1
    mu = posterior(Pi, S, P, np.array([0.08, 0.05]), np.array([0.5, 0.3]))
    T["mu_example"] = mu; T["w_example"] = solve(mu, S, DELTA)
    pd.set_option("display.width", 200)
    f = T.copy()
    for col in ("vol", "prior", "hist_3y", "w_ref", "w_prior_solve", "mu_example", "w_example"):
        f[col] = f[col].map(lambda v: f"{v*100:.1f}%")
    print(f.to_string(index=False))
    print("cash in example:", f"{1 - T.w_example.sum():.1%}")
    corr = (S / np.sqrt(np.outer(np.diag(S), np.diag(S))))
    json.dump({"asof": str(W.index[-1].date()), "start": str(W.index[0].date()), "cash_yield": cash_y,
               "tau": TAU, "delta": DELTA,
               "assets": [{"code": a[0], "name": a[1], "group": a[2], "w_ref": a[3]} for a in ASSETS],
               "cov": S.round(8).tolist(), "corr": corr.round(3).tolist(), "hist": hist.round(5).tolist(),
               "check": {"mu": mu.round(6).tolist(), "w": T.w_example.round(6).tolist()}},
              open(OUT / "bl_inputs.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
