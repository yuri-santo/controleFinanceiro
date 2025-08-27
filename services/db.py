# services/db.py
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Union

import pandas as pd

# ============================================================
# Caminho do banco
# ============================================================
_DB_ENV = os.environ.get("FINANCE_DB", "").strip()
DB_PATH = Path(_DB_ENV) if _DB_ENV else Path("finance.db").absolute()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# Conexão e utilitários
# ============================================================
@contextmanager
def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("PRAGMA foreign_keys=ON;")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def _read_df(con: sqlite3.Connection, query: str, params: Union[Sequence, Dict, None] = None) -> pd.DataFrame:
    df = pd.read_sql_query(query, con, params=params or {})
    # normalizações comuns
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    if "data" in df.columns and "Data" not in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

def _table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = con.execute(f'PRAGMA table_info("{table}")').fetchall()
        return {str(r[1]) for r in rows}  # r[1] = name
    except Exception:
        return set()

def _has_column(con: sqlite3.Connection, table: str, col: str) -> bool:
    cols = _table_columns(con, table)
    return any(c.lower() == col.lower() for c in cols)

# === (coloque no topo, você já tem imports e connect/_read_df/_has_column) ===

# ------------ utilidades de DataFrame <-> SQLite ------------
def load_table(table: str) -> pd.DataFrame:
    with connect() as con:
        try:
            df = _read_df(con, f'SELECT * FROM "{table}"')
        except Exception:
            return pd.DataFrame()
    return df

def replace_table(table: str, df: pd.DataFrame) -> None:
    if df is None:
        return
    with connect() as con:
        df.to_sql(table, con, if_exists="replace", index=False)

def append_rows(table: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    with connect() as con:
        df.to_sql(table, con, if_exists="append", index=False)

def update_row(table: str, row_id: int, payload: dict) -> None:
    if not payload:
        return
    cols = ", ".join([f'"{k}" = :{k}' for k in payload.keys()])
    params = dict(payload)
    params["id"] = int(row_id)
    with connect() as con:
        con.execute(f'UPDATE "{table}" SET {cols} WHERE id = :id', params)

def insert_row(table: str, payload: dict) -> int:
    keys = ", ".join([f'"{k}"' for k in payload.keys()])
    binds = ", ".join([f':{k}' for k in payload.keys()])
    with connect() as con:
        cur = con.execute(f'INSERT INTO "{table}" ({keys}) VALUES ({binds})', payload)
        return int(cur.lastrowid)

def delete_rows(table: str, ids: list[int]) -> None:
    if not ids:
        return
    qmarks = ", ".join(["?"] * len(ids))
    with connect() as con:
        con.execute(f'DELETE FROM "{table}" WHERE id IN ({qmarks})', ids)

# ------------ categorias ------------
def load_cat_receitas() -> pd.DataFrame:      return load_table("cat_receitas")
def load_cat_despesas() -> pd.DataFrame:      return load_table("cat_despesas")
def load_cat_investimentos() -> pd.DataFrame: return load_table("cat_investimentos")

def save_cat_receitas(df: pd.DataFrame) -> None:      replace_table("cat_receitas", df)
def save_cat_despesas(df: pd.DataFrame) -> None:      replace_table("cat_despesas", df)
def save_cat_investimentos(df: pd.DataFrame) -> None: replace_table("cat_investimentos", df)

# ------------ fluxo de caixa: CRUD padronizado ------------
_BASE_COLS = ["Valor","Data","Categoria","Descrição"]

def _coerce_fluxo(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if d.empty:
        return d
    if "Data" in d.columns:
        d["Data"] = pd.to_datetime(d["Data"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "Valor" in d.columns:
        d["Valor"] = pd.to_numeric(d["Valor"], errors="coerce").fillna(0.0)
    for c in ("Categoria","Descrição"):
        if c in d.columns:
            d[c] = d[c].astype(str)
    return d

# Receitas
def load_receitas() -> pd.DataFrame:
    df = load_table("receitas")
    return df if not df.empty else pd.DataFrame(columns=["id"] + _BASE_COLS + ["Recebido","Recorrente"])

def save_receitas(df: pd.DataFrame) -> None:
    replace_table("receitas", _coerce_fluxo(df))

def append_receitas(df: pd.DataFrame) -> None:
    append_rows("receitas", _coerce_fluxo(df))

def update_receita_row(row_id: int, payload: dict) -> None:
    update_row("receitas", row_id, _coerce_fluxo(pd.DataFrame([payload])).iloc[0].to_dict())

def delete_receitas(ids: list[int]) -> None:
    delete_rows("receitas", ids)

# Despesas
def load_despesas() -> pd.DataFrame:
    df = load_table("despesas")
    return df if not df.empty else pd.DataFrame(columns=["id"] + _BASE_COLS + ["Pago","Fixo","Parcelado","QtdParcelas","ParcelaAtual"])

def save_despesas(df: pd.DataFrame) -> None:
    replace_table("despesas", _coerce_fluxo(df))

def append_despesas(df: pd.DataFrame) -> None:
    append_rows("despesas", _coerce_fluxo(df))

def update_despesa_row(row_id: int, payload: dict) -> None:
    update_row("despesas", row_id, _coerce_fluxo(pd.DataFrame([payload])).iloc[0].to_dict())

def delete_despesas(ids: list[int]) -> None:
    delete_rows("despesas", ids)

# Investimentos (fluxo, não “trades”)
def load_investimentos() -> pd.DataFrame:
    df = load_table("investimentos")
    return df if not df.empty else pd.DataFrame(columns=["id"] + _BASE_COLS + ["Tipo","Rentabilidade","Vencimento","Liquidez","Recebido","Fixo"])

def save_investimentos(df: pd.DataFrame) -> None:
    replace_table("investimentos", _coerce_fluxo(df))

def append_investimentos(df: pd.DataFrame) -> None:
    append_rows("investimentos", _coerce_fluxo(df))

def update_invest_row(row_id: int, payload: dict) -> None:
    update_row("investimentos", row_id, _coerce_fluxo(pd.DataFrame([payload])).iloc[0].to_dict())

def delete_investimentos(ids: list[int]) -> None:
    delete_rows("investimentos", ids)

# ------------ ÍNDICES para performance ------------
def _create_indexes(con: sqlite3.Connection) -> None:
    stmts = [
        # fluxo de caixa
        'CREATE INDEX IF NOT EXISTS idx_receitas_data ON receitas(Data);',
        'CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(Data);',
        'CREATE INDEX IF NOT EXISTS idx_invest_data ON investimentos(Data);',
        # mercado
        'CREATE INDEX IF NOT EXISTS idx_precos_ticker_data ON precos(Ticker, Data);',
        'CREATE INDEX IF NOT EXISTS idx_proventos_ticker_data ON proventos(Ticker, Data);',
        'CREATE INDEX IF NOT EXISTS idx_trades_ticker_data ON trades(Ticker, Data);',
    ]
    for s in stmts:
        con.execute(s)

def _ensure_schema() -> None:
    # compat: alguns trechos chamam _ensure_schema()
    ensure_core_schema()

def ensure_core_schema() -> None:
    # (mantenha seu corpo atual) ...
    # ao final:
    with connect() as con:
        _create_indexes(con)


# ============================================================
# DDL — fluxo de caixa, categorias, trades, mercado
# (sem CREATE INDEX aqui — índices são criados condicionalmente)
# ============================================================
DDL_CORE_TABLES = """
CREATE TABLE IF NOT EXISTS receitas(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Valor REAL NOT NULL,
  Recebido INTEGER DEFAULT 0,
  Recorrente INTEGER DEFAULT 0,
  Data TEXT NOT NULL,
  Categoria TEXT,
  "Descrição" TEXT
);

CREATE TABLE IF NOT EXISTS despesas(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Valor REAL NOT NULL,
  Pago INTEGER DEFAULT 0,
  Fixo INTEGER DEFAULT 0,
  Data TEXT NOT NULL,
  Categoria TEXT,
  "Descrição" TEXT,
  Parcelado INTEGER DEFAULT 0,
  QtdParcelas INTEGER DEFAULT 1,
  ParcelaAtual INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS investimentos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Valor REAL NOT NULL,
  Tipo TEXT,
  Data TEXT NOT NULL,
  Categoria TEXT,
  "Descrição" TEXT,
  Rentabilidade REAL,
  Vencimento TEXT,
  Liquidez TEXT,
  Recebido INTEGER DEFAULT 0,
  Fixo INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cat_receitas( Categoria TEXT PRIMARY KEY );
CREATE TABLE IF NOT EXISTS cat_despesas( Categoria TEXT PRIMARY KEY );
CREATE TABLE IF NOT EXISTS cat_investimentos( Categoria TEXT PRIMARY KEY );
"""

DDL_TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Data TEXT,
  Ticker TEXT,
  Tipo TEXT,             -- 'C' ou 'V'
  Qtd REAL,
  Preco REAL,
  Taxas REAL DEFAULT 0,
  Descricao TEXT
);
"""

DDL_MARKET_TABLES = """
CREATE TABLE IF NOT EXISTS precos(
  Data TEXT NOT NULL,
  Ticker TEXT NOT NULL,
  Close REAL NOT NULL,
  PRIMARY KEY (Data, Ticker)
);

CREATE TABLE IF NOT EXISTS proventos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Data TEXT NOT NULL,
  Ticker TEXT NOT NULL,
  Tipo TEXT,
  Valor REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS ativos(
  Ticker TEXT PRIMARY KEY,
  Nome TEXT,
  Setor TEXT,
  Classe TEXT
);

CREATE TABLE IF NOT EXISTS benchmarks(
  Data TEXT NOT NULL,
  Symbol TEXT NOT NULL,
  Close REAL NOT NULL,
  PRIMARY KEY (Data, Symbol)
);

CREATE TABLE IF NOT EXISTS portfolio_daily(
  Data TEXT NOT NULL,
  Ticker TEXT,
  Valor REAL,
  Qtde REAL,
  PM REAL,
  PnL REAL,
  Aporte REAL,
  PRIMARY KEY (Data, Ticker)
);
"""

# ============================================================
# Ensure schema (compatível com bancos antigos)
#   - cria tabelas se faltarem
#   - adiciona colunas que não existirem
#   - cria índices somente se as colunas existirem
# ============================================================
def ensure_core_schema() -> None:
    with connect() as con:
        # Tabelas
        con.executescript(DDL_CORE_TABLES)
        con.executescript(DDL_TRADES_TABLE)
        con.executescript(DDL_MARKET_TABLES)

        # Migrações leves — TRADES
        trades_cols = {
            "Data": "TEXT", "Ticker": "TEXT", "Tipo": "TEXT",
            "Qtd": "REAL", "Preco": "REAL", "Taxas": "REAL", "Descricao": "TEXT",
        }
        existing = _table_columns(con, "trades")
        for col, typ in trades_cols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE trades ADD COLUMN "{col}" {typ}')

        # Migrações leves — PRECOS
        precos_cols = {"Data": "TEXT", "Ticker": "TEXT", "Close": "REAL"}
        existing = _table_columns(con, "precos")
        for col, typ in precos_cols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE precos ADD COLUMN "{col}" {typ}')

        # Migrações leves — PROVENTOS
        proventos_cols = {"Data": "TEXT", "Ticker": "TEXT", "Tipo": "TEXT", "Valor": "REAL"}
        existing = _table_columns(con, "proventos")
        for col, typ in proventos_cols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE proventos ADD COLUMN "{col}" {typ}')

        # Migrações leves — ATIVOS
        ativos_cols = {"Ticker": "TEXT", "Nome": "TEXT", "Setor": "TEXT", "Classe": "TEXT"}
        existing = _table_columns(con, "ativos")
        for col, typ in ativos_cols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE ativos ADD COLUMN "{col}" {typ}')

        # Migrações leves — BENCHMARKS
        bmk_cols = {"Data": "TEXT", "Symbol": "TEXT", "Close": "REAL"}
        existing = _table_columns(con, "benchmarks")
        for col, typ in bmk_cols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE benchmarks ADD COLUMN "{col}" {typ}')

        # Migrações leves — PORTFOLIO_DAILY
        pcols = {"Data": "TEXT", "Ticker": "TEXT", "Valor": "REAL", "Qtde": "REAL", "PM": "REAL", "PnL": "REAL", "Aporte": "REAL"}
        existing = _table_columns(con, "portfolio_daily")
        for col, typ in pcols.items():
            if not any(c.lower() == col.lower() for c in existing):
                con.execute(f'ALTER TABLE portfolio_daily ADD COLUMN "{col}" {typ}')

        # Índices condicionais (só se coluna existe)
        # receitas/despesas/investimentos
        if _has_column(con, "receitas", "Data"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_receitas_data ON receitas(Data)")
        if _has_column(con, "receitas", "Categoria"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_receitas_cat ON receitas(Categoria)")
        if _has_column(con, "despesas", "Data"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(Data)")
        if _has_column(con, "despesas", "Categoria"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_despesas_cat ON despesas(Categoria)")
        if _has_column(con, "investimentos", "Data"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_inv_data ON investimentos(Data)")
        if _has_column(con, "investimentos", "Categoria"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_inv_cat ON investimentos(Categoria)")

        # trades
        if _has_column(con, "trades", "Data"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_trades_data ON trades(Data)")
        if _has_column(con, "trades", "Ticker"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(Ticker)")

        # mercado
        if _has_column(con, "precos", "Ticker"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_preco_ticker ON precos(Ticker)")
        if _has_column(con, "proventos", "Ticker"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_prov_ticker ON proventos(Ticker)")
        if _has_column(con, "benchmarks", "Symbol"):
            con.execute("CREATE INDEX IF NOT EXISTS idx_bmk_symbol ON benchmarks(Symbol)")

# Wrapper compatível com services/globals.py
def _ensure_schema() -> None:
    ensure_core_schema()

# ============================================================
# LOAD/REPLACE/APPEND genéricos
# ============================================================
def load_table(name: str) -> pd.DataFrame:
    _ensure_schema()
    with connect() as con:
        try:
            df = _read_df(con, f'SELECT * FROM "{name}"')
        except Exception:
            df = pd.DataFrame()
    if not df.empty:
        if "Data" in df.columns:
            df = df.sort_values(["Data"] + (["id"] if "id" in df.columns else [])).reset_index(drop=True)
        elif "id" in df.columns:
            df = df.sort_values("id").reset_index(drop=True)
    return df

def replace_table(name: str, df: pd.DataFrame) -> None:
    _ensure_schema()
    with connect() as con:
        con.execute(f'DELETE FROM "{name}"')
        if df is None or df.empty:
            return
        d = df.copy()
        if "Data" in d.columns:
            d["Data"] = pd.to_datetime(d["Data"], errors="coerce").dt.strftime("%Y-%m-%d")
        d.to_sql(name, con, if_exists="append", index=False)

def append_rows(name: str, df: pd.DataFrame) -> None:
    _ensure_schema()
    if df is None:
        return
    if isinstance(df, pd.DataFrame) and df.empty:
        return
    d = df.copy()
    if "Data" in d.columns:
        d["Data"] = pd.to_datetime(d["Data"], errors="coerce").dt.strftime("%Y-%m-%d")
    with connect() as con:
        d.to_sql(name, con, if_exists="append", index=False)

# ============================================================
# UPDATE/DELETE utilitários
# ============================================================
def update_row(table: str, row_id: int, payload: Dict[str, Any]) -> None:
    if not payload:
        return
    p = dict(payload)
    if "Data" in p and p["Data"] is not None:
        p["Data"] = pd.to_datetime(p["Data"], errors="coerce").strftime("%Y-%m-%d")
    sets = ", ".join([f'"{k}"=:{k}' for k in p.keys()])
    args = {**p, "id": int(row_id)}
    with connect() as con:
        con.execute(f'UPDATE "{table}" SET {sets} WHERE id=:id', args)

def delete_rows(table: str, ids: Iterable[int]) -> None:
    ids = [int(i) for i in (ids or [])]
    if not ids:
        return
    with connect() as con:
        con.executemany(f'DELETE FROM "{table}" WHERE id=?', [(i,) for i in ids])

# ============================================================
# Fluxo de Caixa — aliases
# ============================================================
def load_receitas() -> pd.DataFrame:          return load_table("receitas")
def load_despesas() -> pd.DataFrame:          return load_table("despesas")
def load_investimentos() -> pd.DataFrame:     return load_table("investimentos")

def replace_receitas(df: pd.DataFrame) -> None:      replace_table("receitas", df)
def replace_despesas(df: pd.DataFrame) -> None:      replace_table("despesas", df)
def replace_investimentos(df: pd.DataFrame) -> None: replace_table("investimentos", df)

def save_receitas(df: pd.DataFrame) -> None:          replace_receitas(df)
def save_despesas(df: pd.DataFrame) -> None:          replace_despesas(df)
def save_investimentos(df: pd.DataFrame) -> None:     replace_investimentos(df)

def append_receitas(df: pd.DataFrame) -> None:      append_rows("receitas", df)
def append_despesas(df: pd.DataFrame) -> None:      append_rows("despesas", df)
def append_investimentos(df: pd.DataFrame) -> None: append_rows("investimentos", df)

# ============================================================
# Trades
# ============================================================
def load_trades() -> pd.DataFrame:
    df = load_table("trades")
    if df.empty:
        return pd.DataFrame(columns=["data","Ticker","tipo","quantidade","preco","taxas","descricao"])
    # renomeia para o padrão usado em performance/portfolio
    d = df.rename(columns={
        "Data": "data", "Tipo": "tipo", "Qtd": "quantidade",
        "Preco": "preco", "Taxas": "taxas", "Descricao": "descricao",
    })
    # normaliza tipos
    d["data"] = pd.to_datetime(d["data"], errors="coerce")
    for c in ["quantidade", "preco", "taxas"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["tipo"] = d["tipo"].astype(str)
    return d

def insert_trade(dt: str, ticker: str, tipo: str, qtd: float, preco: float, taxas: float, desc: str | None) -> None:
    ensure_core_schema()
    payload = {
        "Data": pd.to_datetime(dt, errors="coerce").strftime("%Y-%m-%d"),
        "Ticker": str(ticker).strip().upper(),
        "Tipo": str(tipo).strip().upper(),
        "Qtd": float(qtd),
        "Preco": float(preco),
        "Taxas": float(taxas or 0),
        "Descricao": desc,
    }
    with connect() as con:
        cols = ", ".join(payload.keys())
        binds = ", ".join([f":{k}" for k in payload.keys()])
        con.execute(f"INSERT INTO trades ({cols}) VALUES ({binds})", payload)

# ============================================================
# Dados de Mercado (preços/proventos/ativos/benchmarks)
#  -> funções retornam nomes que o performance.py espera
# ============================================================
def load_precos(ticker: str | None = None, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    _ensure_schema()
    q = "SELECT Data, Ticker, Close FROM precos WHERE 1=1"
    params: Dict[str, Any] = {}
    if ticker:
        q += " AND Ticker = :t"; params["t"] = ticker
    if start:
        q += " AND Data >= :s"; params["s"] = pd.to_datetime(start, errors="coerce").strftime("%Y-%m-%d")
    if end:
        q += " AND Data <= :e"; params["e"] = pd.to_datetime(end, errors="coerce").strftime("%Y-%m-%d")
    with connect() as con:
        df = _read_df(con, q, params)
    if df.empty:
        return pd.DataFrame(columns=["Ticker","data","preco"])
    d = df.rename(columns={"Data":"data","Close":"preco"}).copy()
    d["data"] = pd.to_datetime(d["data"], errors="coerce")
    d["preco"] = pd.to_numeric(d["preco"], errors="coerce")
    return d.sort_values(["Ticker","data"]).reset_index(drop=True)

def save_precos(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    d = df.rename(columns={"data":"Data","preco":"Close"}).copy()
    if "Data" in d.columns:
        d["Data"] = pd.to_datetime(d["Data"], errors="coerce").dt.strftime("%Y-%m-%d")
    replace_table("precos", d)

def append_precos(df: pd.DataFrame) -> None:
    d = df.rename(columns={"data":"Data","preco":"Close"}).copy()
    append_rows("precos", d)

def load_proventos(ticker: str | None = None) -> pd.DataFrame:
    _ensure_schema()
    q = "SELECT id, Data, Ticker, Tipo, Valor FROM proventos"
    params = None
    if ticker:
        q += " WHERE Ticker = ?"; params = (ticker,)
    with connect() as con:
        df = _read_df(con, q, params)
    if df.empty:
        return pd.DataFrame(columns=["id","data","Ticker","tipo","valor","valor_total"])
    d = df.rename(columns={"Data":"data","Tipo":"tipo","Valor":"valor"}).copy()
    d["data"] = pd.to_datetime(d["data"], errors="coerce")
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce")
    d["valor_total"] = d["valor"]  # compat com performance.py (groupby usa 'valor_total')
    return d.sort_values(["Ticker","data","id"]).reset_index(drop=True)

def save_proventos(df: pd.DataFrame) -> None:
    d = df.rename(columns={"data":"Data","tipo":"Tipo","valor":"Valor"}).copy()
    replace_table("proventos", d)

def append_proventos(df: pd.DataFrame) -> None:
    d = df.rename(columns={"data":"Data","tipo":"Tipo","valor":"Valor"}).copy()
    append_rows("proventos", d)

def load_ativos() -> pd.DataFrame:
    df = load_table("ativos")
    if df.empty:
        return pd.DataFrame(columns=["Ticker","Nome","Setor","Classe"])
    return df[["Ticker","Nome","Setor","Classe"]]

def save_ativos(df: pd.DataFrame) -> None:
    replace_table("ativos", df)

def append_ativos(df: pd.DataFrame) -> None:
    append_rows("ativos", df)

def load_benchmarks(symbol: str | None = None) -> pd.DataFrame:
    _ensure_schema()
    q = "SELECT Data, Symbol, Close FROM benchmarks"
    params = None
    if symbol:
        q += " WHERE Symbol = ?"; params = (symbol,)
    with connect() as con:
        df = _read_df(con, q, params)
    if df.empty:
        return pd.DataFrame(columns=["data","Symbol","Close"])
    d = df.rename(columns={"Data":"data"}).copy()
    d["data"] = pd.to_datetime(d["data"], errors="coerce")
    return d.sort_values(["Symbol","data"]).reset_index(drop=True)

def save_benchmarks(df: pd.DataFrame) -> None:
    d = df.rename(columns={"data":"Data"}).copy()
    replace_table("benchmarks", d)

def append_benchmarks(df: pd.DataFrame) -> None:
    d = df.rename(columns={"data":"Data"}).copy()
    append_rows("benchmarks", d)

# ============================================================
# Série diária do portfólio
# ============================================================
def load_portfolio_daily(ticker: str | None = None) -> pd.DataFrame:
    _ensure_schema()
    q = "SELECT * FROM portfolio_daily"
    params = None
    if ticker:
        q += " WHERE Ticker = ?"; params = (ticker,)
    with connect() as con:
        df = _read_df(con, q, params)
    if df.empty:
        return pd.DataFrame(columns=["Data","Ticker","Valor","Qtde","PM","PnL","Aporte"])
    return df.sort_values([c for c in ["Data","Ticker"] if c in df.columns]).reset_index(drop=True)

def save_portfolio_daily(df: pd.DataFrame) -> None:
    replace_table("portfolio_daily", df)

def append_portfolio_daily(df: pd.DataFrame) -> None:
    append_rows("portfolio_daily", df)
# ============================================================
# Categorias (compatível com services.globals e sidebar)
# ============================================================
def load_cat_receitas() -> pd.DataFrame:
    return load_table("cat_receitas")

def load_cat_despesas() -> pd.DataFrame:
    return load_table("cat_despesas")

def load_cat_investimentos() -> pd.DataFrame:
    return load_table("cat_investimentos")

def save_cat_receitas(df: pd.DataFrame) -> None:
    replace_table("cat_receitas", df)

def save_cat_despesas(df: pd.DataFrame) -> None:
    replace_table("cat_despesas", df)

def save_cat_investimentos(df: pd.DataFrame) -> None:
    replace_table("cat_investimentos", df)

# (opcionais, se você quiser dar append em vez de replace)
def append_cat_receitas(df: pd.DataFrame) -> None:
    append_rows("cat_receitas", df)

def append_cat_despesas(df: pd.DataFrame) -> None:
    append_rows("cat_despesas", df)

def append_cat_investimentos(df: pd.DataFrame) -> None:
    append_rows("cat_investimentos", df)
