# services/patch_portfolio_columns.py
import argparse, sqlite3

NEEDED = [
    ("classe", "TEXT"),
    ("categoria", "TEXT"),
    ("corretora", "TEXT"),
    ("liquidez", "TEXT"),
    ("objetivo_pct", "REAL DEFAULT 0"),
    ("moeda", "TEXT DEFAULT 'BRL'"),
]

def has_col(conn, table, col):
    info = conn.execute(f"PRAGMA table_info({table});").fetchall()
    names = [r[1] if isinstance(r, tuple) else r["name"] for r in info]
    return col in set(names)

def run(db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ativos'")
    if not cur.fetchone():
        # cria mínimo, se não existir
        cur.execute("CREATE TABLE ativos (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL)")
        print("Tabela 'ativos' criada (mínima).")
    added = []
    for col, typ in NEEDED:
        if not has_col(con, "ativos", col):
            cur.execute(f"ALTER TABLE ativos ADD COLUMN {col} {typ}")
            added.append(col)
    con.commit(); con.close()
    if added:
        print("Colunas adicionadas em 'ativos':", ", ".join(added))
    else:
        print("Nada a fazer. 'ativos' já está completo.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    run(args.db)
