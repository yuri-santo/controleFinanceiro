# services/fifo.py
from __future__ import annotations
import pandas as pd
from collections import deque
from typing import Tuple

def fifo_realized_per_month(trades: pd.DataFrame, class_map: dict[str,str] | None = None) -> pd.DataFrame:
    """
    trades: colunas [data, Ticker, tipo ('C'/'V'), quantidade, preco, taxas]
    class_map: dict Ticker->Classe (para separar FIIs de Ações)
    Retorna: por mês/ticker: vendas_brutas, custo_fifo, pl_realizado, classe
    """
    if trades.empty:
        return pd.DataFrame(columns=["AnoMes","Ticker","Classe","Vendas","Custo","PL_Realizado"])

    t = trades.copy()
    t["data"] = pd.to_datetime(t["data"])
    t = t.sort_values("data")

    rows = []
    for tick, tx in t.groupby("Ticker"):
        lots = deque()  # cada lote: [qtd_restante, preco_unitario]
        for _, r in tx.iterrows():
            q = float(r["quantidade"]); p = float(r["preco"]); taxas = float(r.get("taxas",0.0))
            if str(r["tipo"]).upper() == "C":
                lots.append([q, (q*p + taxas)/q])  # custo médio desse lote com taxas embutidas
            else:
                vendas = q * p - taxas
                custo = 0.0
                qv = q
                while qv > 1e-12 and lots:
                    ql, pl = lots[0]
                    take = min(qv, ql)
                    custo += take * pl
                    ql -= take; qv -= take
                    if ql <= 1e-12:
                        lots.popleft()
                    else:
                        lots[0][0] = ql
                pl = vendas - custo
                anomes = r["data"].strftime("%Y-%m")
                rows.append([anomes, tick, vendas, custo, pl])
    df = pd.DataFrame(rows, columns=["AnoMes","Ticker","Vendas","Custo","PL_Realizado"])
    if class_map:
        df["Classe"] = df["Ticker"].map(class_map).fillna("Ação")
    else:
        df["Classe"] = "Ação"
    return df

def fiscal_summary_br(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regras (simplificadas):
      - Ações: isenção se Vendas mês <= 20k; caso contrário, 15% sobre lucro líquido do mês.
      - FIIs: 20% sobre lucro líquido, sem isenção.
    """
    if df.empty:
        return pd.DataFrame(columns=["AnoMes","Classe","Vendas","Lucro","Imposto"])

    out = []
    for (mes, classe), g in df.groupby(["AnoMes","Classe"]):
        vendas = float(g["Vendas"].sum())
        lucro  = float(g["PL_Realizado"].sum())
        imposto = 0.0
        if classe.upper() in ("FII","FIIS"):
            imposto = max(lucro, 0.0) * 0.20
        else:  # Ações
            if vendas > 20000.0:
                imposto = max(lucro, 0.0) * 0.15
        out.append([mes, classe, vendas, lucro, imposto])
    return pd.DataFrame(out, columns=["AnoMes","Classe","Vendas","Lucro","Imposto"]).sort_values(["AnoMes","Classe"])
