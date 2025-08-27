# services/portfolio.py
from __future__ import annotations

import pandas as pd
from typing import Dict, Tuple

def _to_date(s):
    return pd.to_datetime(s, errors="coerce")

def compute_positions(trades: pd.DataFrame, prices: pd.DataFrame, ativos: pd.DataFrame, as_of=None) -> pd.DataFrame:
    """
    Calcula posições atuais por Ticker com PM (médio), VM e P/L não realizado.
    trades: [id, data, Ticker, ativo_id, tipo ('C'/'V'), quantidade, preco, taxas, descricao]
    prices: [id, data, ativo_id, Ticker, preco]
    ativos: [id, ticker, nome, classe, categoria, corretora, liquidez, objetivo_pct]
    """
    if trades is None: trades = pd.DataFrame()
    if prices is None: prices = pd.DataFrame()
    if ativos is None: ativos = pd.DataFrame()

    t = trades.copy()
    if t.empty:
        # base vazia com colunas esperadas
        t = pd.DataFrame(columns=["data","Ticker","tipo","quantidade","preco","taxas"])
    t["data"] = _to_date(t["data"])
    t["tipo"] = t["tipo"].astype(str).str.upper()
    t["quantidade"] = pd.to_numeric(t["quantidade"], errors="coerce").fillna(0.0)
    t["preco"] = pd.to_numeric(t["preco"], errors="coerce").fillna(0.0)
    t["taxas"] = pd.to_numeric(t.get("taxas", 0.0), errors="coerce").fillna(0.0)
    t = t.sort_values("data")

    p = prices.copy()
    if p.empty:
        p = pd.DataFrame(columns=["data","Ticker","preco"])
    p["data"] = _to_date(p["data"])
    if as_of is not None:
        as_of = _to_date(as_of)
        p = p[p["data"] <= as_of]

    # último preço por ticker
    if not p.empty:
        last_price = p.sort_values(["Ticker","data"]).groupby("Ticker", as_index=False).last()[["Ticker","preco"]]
    else:
        last_price = pd.DataFrame(columns=["Ticker","preco"])

    # cadastro de ativos
    a = ativos.copy()
    if not a.empty:
        a = a.rename(columns={
            "ticker":"Ticker", "nome":"Nome", "classe":"Classe", "categoria":"Categoria",
            "corretora":"Corretora", "liquidez":"Liquidez", "objetivo_pct":"Objetivo_pct"
        })[["Ticker","Nome","Classe","Categoria","Corretora","Liquidez","Objetivo_pct"]]
    else:
        a = pd.DataFrame(columns=["Ticker","Nome","Classe","Categoria","Corretora","Liquidez","Objetivo_pct"])

    # cálculo por ticker (PM médio e P/L realizado simples alocando taxas nas compras)
    rows = []
    realized_by_ticker: Dict[str, float] = {}
    for tick, tx in t.groupby("Ticker"):
        qty = 0.0
        cost = 0.0  # custo total de posição (para PM)
        realized = 0.0
        for _, r in tx.iterrows():
            tipo = str(r["tipo"]).upper()
            q = float(r["quantidade"]); pr = float(r["preco"]); taxas = float(r.get("taxas",0.0))
            if tipo == "C":
                # aloca taxas ao custo
                custo_compra = q*pr + taxas
                cost += custo_compra
                qty  += q
            elif tipo == "V":
                if qty <= 0:
                    # venda descoberta: considera custo zero para PM e todo valor como realized
                    realized += (q*pr - taxas)
                else:
                    pm_atual = cost / qty if qty else 0.0
                    receita = q * pr - taxas
                    custo_saida = q * pm_atual
                    realized += (receita - custo_saida)
                    qty -= q
                    cost -= min(cost, custo_saida)
        pm = cost / qty if qty else 0.0
        # preço de mercado: do prices; se não houver, usa último preço de trade
        if tick in last_price["Ticker"].values:
            price = float(last_price.loc[last_price["Ticker"] == tick, "preco"].iloc[0])
        else:
            last_tr = tx.iloc[-1] if len(tx) else None
            price = float(last_tr["preco"]) if last_tr is not None else 0.0
        vm = qty * price
        pl_nreal = (price - pm) * qty
        realized_by_ticker[tick] = realized
        rows.append([tick, qty, pm, cost, price, vm, pl_nreal, realized])

    pos = pd.DataFrame(rows, columns=["Ticker","Quantidade","PM","CustoTotal","Preço","VM","PL_NReal","PL_Realizado"])
    if pos.empty:
        pos = pd.DataFrame(columns=["Ticker","Quantidade","PM","CustoTotal","Preço","VM","PL_NReal","PL_Realizado"])

    # agrega cadastro
    df = a.merge(pos, on="Ticker", how="outer")
    for c in ["Quantidade","PM","CustoTotal","Preço","VM","PL_NReal","PL_Realizado","Objetivo_pct"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    # pesos e rebalanceamento (com base em Objetivo_pct)
    total_vm = float(df["VM"].sum()) if "VM" in df.columns else 0.0
    if total_vm > 0:
        df["Peso"] = df["VM"] / total_vm
    else:
        df["Peso"] = 0.0
    if "Objetivo_pct" in df.columns:
        df["Objetivo_pct"] = df["Objetivo_pct"].fillna(0.0)
        df["Dif_Peso"] = df["Peso"] - (df["Objetivo_pct"] / 100.0)
        df["Rebalancear"] = (df["Dif_Peso"] * total_vm) * -1.0  # positivo = comprar
    else:
        df["Dif_Peso"] = 0.0
        df["Rebalancear"] = 0.0

    # ordena por VM desc
    df = df.sort_values("VM", ascending=False).reset_index(drop=True)
    return df

def allocation_by(positions: pd.DataFrame, col: str) -> pd.DataFrame:
    """Resumo de alocação (VM) por coluna (Classe/Categoria/Corretora etc.)."""
    if positions.empty or "VM" not in positions.columns or col not in positions.columns:
        return pd.DataFrame(columns=[col, "VM"])
    g = positions.groupby(col, as_index=False)["VM"].sum().sort_values("VM", ascending=False)
    return g

def rebalance_suggestion(positions: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """
    Retorna (df_movimentos, total_movimentar).
    df_movimentos: por Ticker, valor a Comprar/Vender para atingir objetivo_pct.
    """
    if positions.empty or "Rebalancear" not in positions.columns:
        return pd.DataFrame(columns=["Ticker","Rebalancear"]), 0.0
    df = positions.loc[:, ["Ticker","Rebalancear"]].copy()
    total = float(df["Rebalancear"].abs().sum()) / 2.0  # metade compra, metade venda (aprox.)
    return df.sort_values("Rebalancear"), total
