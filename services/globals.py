# services/globals.py
from __future__ import annotations

import pandas as pd
from . import db as _db

# Garante schema (compat via wrapper)
_db.ensure_core_schema()

# ================= DFs globais =================
dfReceitas: pd.DataFrame = pd.DataFrame()
dfDespesas: pd.DataFrame = pd.DataFrame()
dfInvestimentos: pd.DataFrame = pd.DataFrame()

DEFAULT_CAT_RECEITAS = ["Salário", "Extra", "Outros"]
DEFAULT_CAT_DESPESAS = ["Moradia", "Transporte", "Alimentação", "Lazer", "Outros"]
DEFAULT_CAT_INVEST   = ["Renda Fixa", "Ações", "Fundos", "Cripto", "Outros"]

def _load_or_seed_cat(table: str, defaults: list[str]) -> pd.DataFrame:
    df = _db.load_table(table)
    if df.empty or "Categoria" not in df.columns:
        df = pd.DataFrame({"Categoria": defaults})
        _db.replace_table(table, df)
    return df

def load_cat_receitas() -> pd.DataFrame:      return _db.load_cat_receitas()
def load_cat_despesas() -> pd.DataFrame:      return _db.load_cat_despesas()
def load_cat_investimentos() -> pd.DataFrame: return _db.load_cat_investimentos()

def save_cat_receitas(df: pd.DataFrame) -> None:      _db.save_cat_receitas(df)
def save_cat_despesas(df: pd.DataFrame) -> None:      _db.save_cat_despesas(df)
def save_cat_investimentos(df: pd.DataFrame) -> None: _db.save_cat_investimentos(df)

def fmt_brl(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def refresh_globals():
    global dfReceitas, dfDespesas, dfInvestimentos
    dfReceitas = _db.load_receitas()
    dfDespesas = _db.load_despesas()
    dfInvestimentos = _db.load_investimentos()

def _boot():
    global dfCatReceitas, dfCatDespesas, dfCatInvestimentos
    dfCatReceitas = _load_or_seed_cat("cat_receitas", DEFAULT_CAT_RECEITAS)
    dfCatDespesas = _load_or_seed_cat("cat_despesas", DEFAULT_CAT_DESPESAS)
    dfCatInvestimentos = _load_or_seed_cat("cat_investimentos", DEFAULT_CAT_INVEST)

    global catReceitas, catDespesas, catInvestimentos
    catReceitas = dfCatReceitas["Categoria"].astype(str).tolist()
    catDespesas = dfCatDespesas["Categoria"].astype(str).tolist()
    catInvestimentos = dfCatInvestimentos["Categoria"].astype(str).tolist()

    refresh_globals()

_boot()

# Aliases usados pelos components
def load_receitas() -> pd.DataFrame:      return _db.load_receitas()
def load_despesas() -> pd.DataFrame:      return _db.load_despesas()
def load_investimentos() -> pd.DataFrame: return _db.load_investimentos()

# Salva substituindo toda a tabela (mantém IDs pois é TRUNCATE lógico)
def save_receitas(df: pd.DataFrame) -> None:      _db.save_receitas(df)
def save_despesas(df: pd.DataFrame) -> None:      _db.save_despesas(df)
def save_investimentos(df: pd.DataFrame) -> None: _db.save_investimentos(df)

# APPEND linha a linha (usado na Sidebar)
def append_receitas(df: pd.DataFrame) -> None:      _db.append_receitas(df)
def append_despesas(df: pd.DataFrame) -> None:      _db.append_despesas(df)
def append_investimentos(df: pd.DataFrame) -> None: _db.append_investimentos(df)

# UPDATE/DELETE (para DataTables e Extratos)
def update_receita_row(row_id: int, payload: dict) -> None: _db.update_receita_row(row_id, payload)
def update_despesa_row(row_id: int, payload: dict) -> None: _db.update_despesa_row(row_id, payload)
def update_invest_row(row_id: int, payload: dict) -> None:  _db.update_invest_row(row_id, payload)

def delete_receitas(ids: list[int]) -> None:      _db.delete_receitas(ids)
def delete_despesas(ids: list[int]) -> None:      _db.delete_despesas(ids)
def delete_investimentos(ids: list[int]) -> None: _db.delete_investimentos(ids)

def series_by_period(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Periodo", "Valor"])
    s = df.copy()
    s["Periodo"] = pd.to_datetime(s["Data"], errors="coerce").dt.to_period(freq).dt.to_timestamp()
    return s.groupby("Periodo", as_index=False)["Valor"].sum()

def filter_period_and_categories(df, start, end, categorias):
    if df.empty:
        return df
    f = df.copy()
    if start:
        f = f[pd.to_datetime(f["Data"], errors="coerce") >= pd.to_datetime(start).normalize()]
    if end:
        f = f[pd.to_datetime(f["Data"], errors="coerce") <= pd.to_datetime(end).normalize()]
    if categorias:
        f = f[f["Categoria"].astype(str).isin([str(c) for c in categorias])]
    return f
