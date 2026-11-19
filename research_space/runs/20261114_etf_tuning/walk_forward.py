"""Walk-forward Optuna tuning of the plan 27 book (2026-11-14, D-162). User: "看看参数，然后optuna，贝恩斯优化怎么放进来？" -> "1".

Objective on a training window = mean yearly Sharpe (excess over cash) − 0.5 × std, minus a penalty when the max
drawdown is worse than −12%. Search space: vol window 20..250, A股 trend windows, A股 vol target, bond switch, 港股 ratio,
gold and commodity risk budgets, risk-weight rebalance; split 60/40 fixed (the user's choice).
Walk-forward: train 2014..Y−1, test year Y, Y = 2018..2026 (TPE 200 trials per fold). Two picks per fold:
  best      -- the top trial
  consensus -- median / mode of the top 20 trials (plateau pick)
OOS years stitched and compared with the fixed base. Also a full-sample TPE run (500 trials) with the deflated Sharpe
(Bailey & López de Prado 2014) of its best trial. The book itself is causal, so one full-history run per trial is
scored on any window.
"""
from __future__ import annotations
import importlib.util, json, logging
from pathlib import Path
import numpy as np, optuna, pandas as pd
from scipy.stats import kurtosis, norm, skew

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ps", HERE.parent / "20261114_etf_universe/param_sensitivity.py")
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
OUT = Path("/Volumes/Treasury/quant_cn_lake/meta/runs/research/20261114_etf_tuning"); OUT.mkdir(parents=True, exist_ok=True)
optuna.logging.set_verbosity(logging.WARNING); pd.set_option("display.width", 240)
TRENDS = [(21,), (63,), (252,), (5, 10, 21), (10, 21, 42, 252), (21, 63, 252), (42, 126, 252)]
SWITCHES = [None, (21,), (63,), (21, 63, 252), (63, 126, 252)]
VOLT = [0.10, 0.15, 0.20, 0.30, 0.0]  # 0 = no vol sizing
FOLDS = list(range(2018, 2027)); TRIALS = 200; TOP = 20; DD_CAP = -0.12


def to_params(t: optuna.Trial) -> dict:
    return {"vol_window": t.suggest_int("vol_window", 20, 250, log=True), "trend": TRENDS[t.suggest_int("trend", 0, len(TRENDS) - 1)],
            "vol_target": VOLT[t.suggest_int("vol_target", 0, len(VOLT) - 1)], "switch": SWITCHES[t.suggest_int("switch", 0, len(SWITCHES) - 1)],
            "hk": t.suggest_float("hk", 0.0, 2.0), "risk_share": 0.6, "rebalance": t.suggest_categorical("rebalance", ["W", "M", "Q"]),
            "budget": (1.0, t.suggest_float("b_gold", 0.5, 1.5), t.suggest_float("b_comm", 0.5, 1.5))}


def from_raw(r: dict) -> dict:
    return {"vol_window": int(r["vol_window"]), "trend": TRENDS[int(r["trend"])], "vol_target": VOLT[int(r["vol_target"])],
            "switch": SWITCHES[int(r["switch"])], "hk": float(r["hk"]), "risk_share": 0.6, "rebalance": r["rebalance"],
            "budget": (1.0, float(r["b_gold"]), float(r["b_comm"]))}


def objective(ex: pd.Series) -> float:
    yr = ex.groupby(ex.index.year).agg(lambda z: z.mean() / z.std() * 252 ** 0.5)
    cum = (1 + ex).cumprod(); dd = (cum / cum.cummax() - 1).min()
    return float(yr.mean() - 0.5 * yr.std() - (max(0.0, DD_CAP - dd) * 10))


def sharpe(ex: pd.Series) -> float:
    return float(ex.mean() / ex.std() * 252 ** 0.5)


def tune(R, cash, end: int, n: int, seed: int) -> optuna.Study:
    def f(t: optuna.Trial) -> float:
        x = ps.book(R, cash, to_params(t)); ex = (x - cash.loc[x.index]).loc[: str(end)]
        t.set_user_attr("sr", sharpe(ex)); return objective(ex)
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed, multivariate=True))
    st.enqueue_trial({"vol_window": 60, "trend": 4, "vol_target": 2, "switch": 3, "hk": 1.0, "rebalance": "M", "b_gold": 1.0, "b_comm": 1.0})
    st.optimize(f, n_trials=n); return st


def consensus(st: optuna.Study) -> dict:
    top = sorted([t for t in st.trials if t.value is not None], key=lambda t: -t.value)[:TOP]
    P = pd.DataFrame([t.params for t in top])
    raw = {k: (P[k].mode().iloc[0] if k in ("trend", "vol_target", "switch", "rebalance") else P[k].median()) for k in P}
    return from_raw(raw)


def deflated(ex: pd.Series, trial_sr: np.ndarray) -> float:
    """Probability the best Sharpe beats the max expected from N trials of noise (daily units)."""
    n, sr = len(trial_sr), ex.mean() / ex.std(); v = np.var(trial_sr / 252 ** 0.5, ddof=1); g = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e)))
    s, k = skew(ex), kurtosis(ex, fisher=False)
    return float(norm.cdf((sr - sr0) * np.sqrt(len(ex) - 1) / np.sqrt(1 - s * sr + (k - 1) / 4 * sr ** 2)))


def show(p: dict) -> str:
    return (f"vw{p['vol_window']} tr{p['trend']} vt{p['vol_target']} sw{p['switch']} hk{p['hk']:.2f} {p['rebalance']} "
            f"金{p['budget'][1]:.2f} 商{p['budget'][2]:.2f}")


def main() -> None:
    R, cash = ps.load(); ex_of = lambda p: (lambda x: x - cash.loc[x.index])(ps.book(R, cash, p))
    base = ex_of(ps.BASE); oos = {"base": [], "best": [], "consensus": []}; rows = []
    for y in FOLDS:
        st = tune(R, cash, y - 1, TRIALS, seed=y)
        picks = {"best": from_raw(st.best_trial.params), "consensus": consensus(st)}
        rec = {"test": y, "train_score_base": st.trials[0].value, "train_score_best": st.best_value}
        oos["base"].append(base.loc[str(y)])
        for name, p in picks.items():
            z = ex_of(p).loc[str(y)]; oos[name].append(z); rec[f"{name}_sr"] = sharpe(z); rec[f"{name}_p"] = show(p)
        rec["base_sr"] = sharpe(base.loc[str(y)]); rows.append(rec)
        print(f"{y}: base {rec['base_sr']:+.2f} best {rec['best_sr']:+.2f} cons {rec['consensus_sr']:+.2f} | best: {rec['best_p']} | cons: {rec['consensus_p']}")
    F = pd.DataFrame(rows); F.to_csv(OUT / "folds.csv", index=False)
    S = {k: pd.concat(v) for k, v in oos.items()}
    summ = pd.DataFrame({k: {"夏普": sharpe(z), "年化超额": z.mean() * 252, "最大回撤": ((1 + z).cumprod() / (1 + z).cumprod().cummax() - 1).min(),
                             "赢base年数": int((F[f"{k}_sr"] > F["base_sr"]).sum()) if k != "base" else None} for k, z in S.items()}).T
    print(f"\n== 样本外 {FOLDS[0]}..{FOLDS[-1]} 拼接 (超额 over cash)"); print(summ.round(3))
    full = tune(R, cash, 2026, 500, seed=7); bp = from_raw(full.best_trial.params); bx = ex_of(bp)
    srs = np.array([t.user_attrs["sr"] for t in full.trials if "sr" in t.user_attrs])
    info = {"full_best": show(bp), "full_best_sr": sharpe(bx), "base_sr": sharpe(base), "trials": len(srs),
            "trial_sr_median": float(np.median(srs)), "trial_sr_p90": float(np.quantile(srs, 0.9)),
            "dsr_best": deflated(bx, srs), "dsr_base_1trial_equiv": deflated(base, srs),
            "full_consensus": show(consensus(full)), "full_consensus_sr": sharpe(ex_of(consensus(full)))}
    imp = optuna.importance.get_param_importances(full); info["importance"] = {k: round(v, 3) for k, v in imp.items()}
    print("\n== 全样本 TPE 500 次 (in-sample)"); print(json.dumps(info, ensure_ascii=False, indent=1))
    (OUT / "full_sample.json").write_text(json.dumps(info, ensure_ascii=False, indent=1)); summ.to_csv(OUT / "oos_summary.csv")


if __name__ == "__main__":
    main()
