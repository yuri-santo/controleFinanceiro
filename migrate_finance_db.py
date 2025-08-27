import sqlite3
import pandas as pd
from services import db

def normalize_dates_table(con, table, col="Data"):
    try:
        df = pd.read_sql_query(f'SELECT id, {col} FROM "{table}"', con)
        if df.empty or col not in df.columns:
            return
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
        for _, r in df.iterrows():
            if pd.notna(r[col]):
                con.execute(f'UPDATE "{table}" SET {col}=? WHERE id=?', (r[col], int(r["id"])))
    except Exception:
        pass

def main():
    # garante tabelas/colunas e cria índices
    db.ensure_core_schema()
    with db.connect() as con:
        # normalizações simples nas tabelas que têm Data+id
        for t in ("receitas","despesas","investimentos","proventos","trades"):
            # "proventos" e "trades" podem não ter id autoincrement em todos os casos; ignore se falhar
            try:
                normalize_dates_table(con, t, "Data")
            except Exception:
                continue
        # índices já são criados dentro de ensure_core_schema()

    print("✔ Migração/normalização concluída.")

if __name__ == "__main__":
    main()
