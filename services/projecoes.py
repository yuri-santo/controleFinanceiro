# services/projecoes.py
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

from services.globals import (
    dfReceitas, dfDespesas, dfInvestimentos,
)

# ----------------------------
# Utilidades
# ----------------------------
def taxa_mensal_aa(t_aa: float) -> float:
    """Equivalência anual->mensal:  (1+a)^(1/12)-1 ."""
    return (1.0 + float(t_aa))**(1.0/12.0) - 1.0

def monthly_series(df: pd.DataFrame) -> pd.Series:
    """Agrupa por mês (fim do mês) e soma Valor; espera colunas 'Data' e 'Valor'."""
    if df.empty:
        return pd.Series(dtype="float64")
    s = (
        df.copy()
          .assign(Data=pd.to_datetime(df["Data"], errors="coerce"))
          .set_index("Data")["Valor"]
          .astype(float)
          .groupby(pd.Grouper(freq="ME"))  # "ME" = MonthEnd
          .sum(min_count=1)
    )
    s.index = s.index.normalize()
    s = s.fillna(0.0).astype("float64")
    return s

def cash_flows() -> Dict[str, pd.Series]:
    """Séries mensais: receitas, despesas (positivas), investimentos (positivos), líquido."""
    r = monthly_series(dfReceitas) if isinstance(dfReceitas, pd.DataFrame) else pd.Series(dtype="float64")
    d = monthly_series(dfDespesas) if isinstance(dfDespesas, pd.DataFrame) else pd.Series(dtype="float64")
    i = monthly_series(dfInvestimentos) if isinstance(dfInvestimentos, pd.DataFrame) else pd.Series(dtype="float64")
    d = d * -1.0  # despesas negativas para montar fluxo líquido
    idx = r.index.union(d.index).union(i.index)
    r = r.reindex(idx, fill_value=0.0)
    d = d.reindex(idx, fill_value=0.0)
    i = i.reindex(idx, fill_value=0.0)
    liquido = r + d + i
    return {"receitas": r, "despesas": -d, "invest": i, "liquido": liquido}

# ----------------------------
# Parâmetros e simulações
# ----------------------------
@dataclass
class ParametrosSimulacao:
    valor_inicial: float = 0.0
    aporte_mensal: float = 0.0
    taxa_anual: float = 0.12
    inflacao_anual: float = 0.04
    anos: int = 10

    @property
    def meses(self) -> int:
        return int(self.anos * 12)

    @property
    def taxa_m(self) -> float:
        return taxa_mensal_aa(self.taxa_anual)

    @property
    def inflacao_m(self) -> float:
        return taxa_mensal_aa(self.inflacao_anual)

def sim_compostos(p: ParametrosSimulacao) -> pd.DataFrame:
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=p.meses, freq="ME")
    v = float(p.valor_inicial)
    deflator = 1.0
    nom, real = [], []
    for _ in range(p.meses):
        v = v * (1 + p.taxa_m) + float(p.aporte_mensal)
        deflator *= (1 + p.inflacao_m)
        nom.append(v)
        real.append(v / deflator)
    return pd.DataFrame({"Data": datas, "Nominal": nom, "Real": real})

def sim_so_guardar(p: ParametrosSimulacao) -> pd.DataFrame:
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=p.meses, freq="ME")
    v = float(p.valor_inicial)
    serie = []
    for _ in range(p.meses):
        v += float(p.aporte_mensal)
        serie.append(v)
    return pd.DataFrame({"Data": datas, "Acumulado": serie})

def sim_monte_carlo(p: ParametrosSimulacao, vol_anual: float = 0.15, n_paths: int = 500) -> pd.DataFrame:
    """Retornos ~ Normal(mu_m, sigma_m). mu_m = taxa_m; sigma_m = vol_anual->mensal. Série do patrimônio."""
    mu = p.taxa_m
    sigma = taxa_mensal_aa(vol_anual + 1e-12)  # aprox. simples para mensalizar o desvio
    n = p.meses
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=n, freq="ME")

    trajetorias = np.zeros((n, n_paths), dtype=float)
    for k in range(n_paths):
        v = float(p.valor_inicial)
        for t in range(n):
            rnd = np.random.normal(mu, sigma)
            v = max(0.0, v * (1 + rnd)) + float(p.aporte_mensal)
            trajetorias[t, k] = v

    df = pd.DataFrame({
        "Data": datas,
        "p5":  np.percentile(trajetorias, 5,  axis=1),
        "p50": np.percentile(trajetorias, 50, axis=1),
        "p95": np.percentile(trajetorias, 95, axis=1),
    })
    return df

# ----------------------------
# Forecast de fluxo
# ----------------------------
def forecast_cashflow(meses: int = 12, metodo: str = "media") -> pd.DataFrame:
    s = cash_flows()["liquido"]
    if s.empty:
        return pd.DataFrame(columns=["Data","Valor","Tipo"])
    hist = s.copy()
    last = hist.index.max() if not hist.empty else pd.Timestamp.today().normalize()
    future_idx = pd.date_range((last + pd.offsets.MonthEnd(1)).normalize(), periods=meses, freq="ME")
    if metodo == "mediana":
        v = float(hist.tail(12).median()) if len(hist) else 0.0
    else:
        v = float(hist.tail(12).mean()) if len(hist) else 0.0
    prev = pd.Series(v, index=future_idx)
    out = pd.concat([
        pd.DataFrame({"Data": hist.index, "Valor": hist.values, "Tipo": "Histórico"}),
        pd.DataFrame({"Data": prev.index, "Valor": prev.values, "Tipo": "Previsão"}),
    ], ignore_index=True)
    out["Data"] = pd.to_datetime(out["Data"])
    return out.sort_values("Data")

# ----------------------------
# Reserva de emergência
# ----------------------------
def monthly_expenses_stats(janelas_meses: int = 12) -> Tuple[float, float, int]:
    if dfDespesas.empty:
        return 0.0, 0.0, 0
    s = monthly_series(dfDespesas)
    if s.empty:
        return 0.0, 0.0, 0
    s = s.iloc[-janelas_meses:]
    return float(s.mean()), float(s.std(ddof=1) if len(s) > 1 else 0.0), int(len(s))

def recomendacao_reserva(meses_base: int = 6) -> Dict[str, float]:
    media, desvio, n = monthly_expenses_stats(12)
    if n == 0:
        return {"meses": float(meses_base), "despesa_media": 0.0, "alvo": 0.0}
    cv = (desvio / media) if media > 0 else 0.0
    meses = float(meses_base)
    if cv > 0.55:
        meses = 12.0
    elif cv > 0.35:
        meses = 9.0
    alvo = media * meses
    return {"meses": meses, "despesa_media": media, "alvo": alvo}

# ----------------------------
# Renda Fixa CDI (CDB/LCI/LCA)
# ----------------------------
def renda_fixa_cdi(valor_inicial: float, aporte_mensal: float, anos: int,
                   cdi_aa: float, pct_cdi: float, inflacao_aa: float = 0.0,
                   isento_ir: bool = False, meses_corridos: Optional[int] = None) -> pd.DataFrame:
    """
    cdi_aa: ex 0.12 (12% a.a.); pct_cdi: ex 1.05 (105% do CDI).
    IR regressivo (CDB) aproximado sobre rendimento mensal; LCI/LCA isentos.
    """
    n = meses_corridos if meses_corridos is not None else int(anos * 12)
    r_m_cdi = taxa_mensal_aa(cdi_aa)
    r_m = r_m_cdi * float(pct_cdi)
    pi_m = taxa_mensal_aa(float(inflacao_aa))
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=n, freq="ME")

    v_bruto = float(valor_inicial)
    deflator = 1.0
    nominal_series, real_series, imposto_series = [], [], []

    prev_v = v_bruto
    for m in range(1, n+1):
        v_bruto = v_bruto * (1 + r_m) + aporte_mensal
        rendimento_mes = max(0.0, v_bruto - prev_v - aporte_mensal)
        prev_v = v_bruto

        if isento_ir:
            imposto = 0.0
        else:
            if m <= 6: aliq = 0.225
            elif m <= 12: aliq = 0.20
            elif m <= 24: aliq = 0.175
            else: aliq = 0.15
            imposto = rendimento_mes * aliq

        v_liq = v_bruto - imposto
        nominal_series.append(v_liq)

        deflator *= (1 + pi_m)
        real_series.append(v_liq / deflator)
        imposto_series.append(imposto)

    return pd.DataFrame({"Data": datas, "Nominal": nominal_series, "Real": real_series, "ImpostoMes": imposto_series})

# ----------------------------
# DCA × Aporte Único
# ----------------------------
def dca_vs_lumpsum(valor_inicial: float, aporte_total: float, meses: int,
                   taxa_anual: float, inflacao_anual: float = 0.0) -> pd.DataFrame:
    r_m = taxa_mensal_aa(taxa_anual)
    pi_m = taxa_mensal_aa(inflacao_anual)
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=int(meses), freq="ME")

    # Lump Sum
    v_ls = valor_inicial + aporte_total
    defl = 1.0
    ls_nom, ls_real = [], []
    for _ in range(int(meses)):
        v_ls *= (1 + r_m); defl *= (1 + pi_m)
        ls_nom.append(v_ls); ls_real.append(v_ls / defl)

    # DCA
    aporte_m = (aporte_total / meses) if meses > 0 else 0.0
    v_dca = valor_inicial
    defl2 = 1.0
    dca_nom, dca_real = [], []
    for _ in range(int(meses)):
        v_dca = v_dca * (1 + r_m) + aporte_m
        defl2 *= (1 + pi_m)
        dca_nom.append(v_dca); dca_real.append(v_dca / defl2)

    return pd.DataFrame({"Data": datas,
                         "LS_Nominal": ls_nom, "LS_Real": ls_real,
                         "DCA_Nominal": dca_nom, "DCA_Real": dca_real})

# ----------------------------
# Financiamento (PRICE e SAC)
# ----------------------------
def price_schedule(valor: float, anos: int, taxa_aa: float) -> pd.DataFrame:
    n = int(anos * 12)
    i = taxa_mensal_aa(taxa_aa)
    if i <= 0 or n <= 0:
        return pd.DataFrame(columns=["Mes","Parcela","Juros","Amortizacao","Saldo"])
    pmt = valor * (i * (1 + i)**n) / ((1 + i)**n - 1)
    saldo = float(valor)
    rows = []
    for m in range(1, n+1):
        juros = saldo * i
        amort = pmt - juros
        saldo = max(saldo - amort, 0.0)
        rows.append([m, pmt, juros, amort, saldo])
    return pd.DataFrame(rows, columns=["Mes","Parcela","Juros","Amortizacao","Saldo"])

def sac_schedule(valor: float, anos: int, taxa_aa: float) -> pd.DataFrame:
    n = int(anos * 12)
    i = taxa_mensal_aa(taxa_aa)
    if i <= 0 or n <= 0:
        return pd.DataFrame(columns=["Mes","Parcela","Juros","Amortizacao","Saldo"])
    amort = valor / n
    saldo = float(valor)
    rows = []
    for m in range(1, n+1):
        juros = saldo * i
        parcela = amort + juros
        saldo = max(saldo - amort, 0.0)
        rows.append([m, parcela, juros, amort, saldo])
    return pd.DataFrame(rows, columns=["Mes","Parcela","Juros","Amortizacao","Saldo"])

def financiamento_kpis(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return {"total_juros": 0.0, "parcela_media": 0.0, "maior_parcela": 0.0}
    total_juros = float(df["Juros"].sum())
    parcela_media = float(df["Parcela"].mean())
    maior_parcela = float(df["Parcela"].max())
    return {"total_juros": total_juros, "parcela_media": parcela_media, "maior_parcela": maior_parcela}

# ----------------------------
# Objetivo / Aposentadoria
# ----------------------------
def necessidade_aporte(meta_final: float, anos: int, taxa_aa: float, valor_inicial: float = 0.0) -> float:
    n = int(anos * 12)
    r = taxa_mensal_aa(taxa_aa)
    fv_inicial = valor_inicial * (1 + r)**n
    alvo_series = meta_final - fv_inicial
    if n <= 0:
        return 0.0
    if r == 0:
        return alvo_series / n
    return alvo_series * r / ((1 + r)**n - 1)

def swr_meta(patrimonio: float, swr_anual: float = 0.04) -> float:
    return float(patrimonio) * (float(swr_anual) / 12.0)

def sim_serie_aporte(valor_inicial: float, aporte_mensal: float, anos: int, taxa_aa: float) -> pd.DataFrame:
    n = int(anos * 12)
    r = taxa_mensal_aa(taxa_aa)
    datas = pd.date_range(pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0), periods=n, freq="ME")
    v = float(valor_inicial)
    serie = []
    for _ in range(n):
        v = v * (1 + r) + float(aporte_mensal)
        serie.append(v)
    return pd.DataFrame({"Data": datas, "Patrimonio": serie})
