# services/performance.py
from __future__ import annotations
import math
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from services.db import load_trades, load_precos, load_proventos, load_ativos, load_benchmarks, save_portfolio_daily

def _to_date(x): return pd.to_datetime(x, errors="coerce")

def build_positions_daily(as_of: Optional[str] = None) -> pd.DataFrame:
    """
    Constrói série diária de:
      - vm_total: soma(qtd_dia * preço_dia) em BRL
      - aportes: compras líquidas (qtd*preco + taxas) do dia
      - retiradas: vendas líquidas (receita) do dia
      - proventos: proventos do dia
    Usa o último preço disponível (forward-fill) por ticker.
    """
    ativos = load_ativos()
    trades = load_trades()
    precos = load_precos()
    prov = load_proventos()

    if trades.empty and precos.empty:
        return pd.DataFrame(columns=["data","vm_total","aportes","retiradas","proventos"])

    # calendário
    min_d = min([d for d in [
        trades["data"].min() if not trades.empty else None,
        precos["data"].min() if not precos.empty else None
    ] if pd.notna(d)])
    end_d = _to_date(as_of) if as_of else max(trades["data"].max() if not trades.empty else pd.Timestamp.today(),
                                              precos["data"].max() if not precos.empty else pd.Timestamp.today())
    days = pd.date_range(min_d, end_d, freq="D")

    # Quantidades por ticker no tempo (cumsum)
    if not trades.empty:
        qmov = trades.copy()
        qmov["q"] = np.where(qmov["tipo"].str.upper()=="C", qmov["quantidade"].astype(float), -qmov["quantidade"].astype(float))
        q_daily = (qmov.groupby(["Ticker","data"])["q"].sum().unstack(fill_value=0)
                        .reindex(columns=days, fill_value=0))
        qpos = q_daily.cumsum(axis=1)
    else:
        qpos = pd.DataFrame(index=[], columns=days)

    # Preços por dia (forward fill)
    if not precos.empty:
        p = (precos.pivot_table(index="Ticker", columns="data", values="preco", aggfunc="last")
                    .reindex(columns=days).sort_index(axis=1))
        p = p.ffill(axis=1)  # carrega último preço conhecido
    else:
        p = pd.DataFrame(index=qpos.index, columns=days, data=0.0)

    # VM por dia
    # alinhar índices
    all_ticks = sorted(set(qpos.index).union(set(p.index)))
    qpos = qpos.reindex(all_ticks).fillna(0.0)
    p = p.reindex(all_ticks).fillna(method="ffill", axis=1).fillna(0.0)

    vm = (qpos * p).sum(axis=0)  # soma por dia

    # Fluxos: aportes/retiradas (caixa)
    aportes = pd.Series(0.0, index=days)
    retiradas = pd.Series(0.0, index=days)
    if not trades.empty:
        buys = trades[trades["tipo"].str.upper()=="C"].copy()
        sells = trades[trades["tipo"].str.upper()=="V"].copy()
        if not buys.empty:
            aportes = buys.groupby("data").apply(lambda d: float((d["quantidade"]*d["preco"]).sum() + d["taxas"].sum())).reindex(days).fillna(0.0)
        if not sells.empty:
            retiradas = sells.groupby("data").apply(lambda d: float((d["quantidade"]*d["preco"]).sum() - d["taxas"].sum())).reindex(days).fillna(0.0)

    # Proventos
    proventos = pd.Series(0.0, index=days)
    if not prov.empty:
        proventos = prov.groupby("data")["valor_total"].sum().reindex(days).fillna(0.0)

    out = pd.DataFrame({
        "data": days,
        "vm_total": vm.values.astype(float),
        "aportes": aportes.values.astype(float),
        "retiradas": retiradas.values.astype(float),
        "proventos": proventos.values.astype(float),
    })
    return out

def twr_from_series(vm_df: pd.DataFrame) -> float:
    """
    Calcula TWR no período inteiro:
      1) converte em retornos diários ignorando fluxos (retirada/aporte),
      2) encadeia subperíodos entre fluxos.
    Simplificação: retorno bruto = (VM_t - VM_{t-1} - fluxos) / VM_{t-1}
    """
    d = vm_df.sort_values("data").reset_index(drop=True).copy()
    if len(d) < 2: return 0.0
    d["fluxo"] = d["aportes"] - d["retiradas"] + d["proventos"]  # proventos como fluxo
    ret = []
    for i in range(1, len(d)):
        vm0 = d.loc[i-1, "vm_total"]
        vm1 = d.loc[i, "vm_total"]
        fx = d.loc[i, "fluxo"]
        if vm0 <= 0: continue
        r = (vm1 - vm0 - fx) / vm0
        ret.append(1.0 + r)
    acc = np.prod(ret) if ret else 1.0
    return float(acc - 1.0)

def _xnpv(rate: float, cashflows: list[tuple[pd.Timestamp, float]]) -> float:
    t0 = cashflows[0][0]
    return sum(cf / ((1 + rate) ** ((t - t0).days / 365.0)) for t, cf in cashflows)

def xirr(cashflows: list[tuple[pd.Timestamp, float]], guess: float = 0.1) -> float:
    """cashflows: aportes negativos, retiradas positivas + VM final como positivo"""
    if not cashflows: return 0.0
    rate = guess
    for _ in range(100):
        f = _xnpv(rate, cashflows)
        # derivada numérica
        f1 = (_xnpv(rate + 1e-6, cashflows) - f) / 1e-6
        if abs(f1) < 1e-12: break
        new_rate = rate - f / f1
        if abs(new_rate - rate) < 1e-8: return float(new_rate)
        rate = new_rate
    return float(rate)

def volatility_annual(returns_daily: np.ndarray, trading_days: int = 252) -> float:
    return float(np.std(returns_daily, ddof=1) * math.sqrt(trading_days)) if len(returns_daily) > 1 else 0.0

def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0: return 0.0
    cummax = np.maximum.accumulate(values)
    dd = (values - cummax) / cummax
    return float(dd.min())  # negativo

def sharpe_ratio(returns_daily: np.ndarray, rf_daily: float = 0.0, trading_days: int = 252) -> float:
    exceso = returns_daily - rf_daily
    mu = exceso.mean() if len(exceso) else 0.0
    vol = returns_daily.std(ddof=1) if len(returns_daily) > 1 else 0.0
    if vol == 0: return 0.0
    return float((mu * trading_days) / (vol * math.sqrt(trading_days)))

def compute_metrics(as_of: Optional[str] = None, bench_serie: Optional[str] = None):
    vm = build_positions_daily(as_of=as_of)
    if vm.empty:
        return {"twr":0.0,"irr":0.0,"vol":0.0,"dd":0.0,"sharpe":0.0}, vm, pd.DataFrame()

    # salvar/atualizar materialização
    save_portfolio_daily(vm)

    # retornos diários ignorando fluxos
    d = vm.copy()
    d["fluxo"] = d["aportes"] - d["retiradas"] + d["proventos"]
    ret = []
    for i in range(1, len(d)):
        vm0, vm1, fx = d.loc[i-1,"vm_total"], d.loc[i,"vm_total"], d.loc[i,"fluxo"]
        r = 0.0 if vm0 <= 0 else (vm1 - vm0 - fx) / vm0
        ret.append(r)
    ret = np.array(ret, dtype=float)

    # TWR
    twr = twr_from_series(vm)

    # IRR (fluxos + VM final)
    cfs = []
    for _, r in d.iterrows():
        # aportes (negativos), retiradas e proventos (positivos)
        val = -float(r["aportes"]) + float(r["retiradas"]) + float(r["proventos"])
        if abs(val) > 1e-12:
            cfs.append((pd.to_datetime(r["data"]), val))
    # add valor final como positivo (resgate hipotético)
    if not d.empty:
        cfs.append((pd.to_datetime(d["data"].iloc[-1]), float(d["vm_total"].iloc[-1])))
    irr = xirr(cfs) if cfs else 0.0

    vol = volatility_annual(ret)
    dd = max_drawdown(d["vm_total"].values)
    # benchmark (opcional)
    bench = pd.DataFrame()
    if bench_serie:
        bench = load_benchmarks(bench_serie)
        bench["data"] = pd.to_datetime(bench["data"])
        bench = bench[bench["data"].between(vm["data"].min(), vm["data"].max())].copy()

    sharpe = sharpe_ratio(ret, rf_daily=0.0)

    return {"twr":twr,"irr":irr,"vol":vol,"dd":dd,"sharpe":sharpe}, vm, bench
