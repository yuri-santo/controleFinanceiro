# services/seed_ativos_carteira.py
import argparse, sqlite3

def run(db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ativos_carteira(
      ticker   TEXT,
      classe   TEXT,      -- ACAO | ETF | FII | BDR | CRIPTO | CDB
      moeda    TEXT,      -- BRL, USD...
      pct_cdi  REAL,      -- p/ CDB (ex.: 110.0)
      inicio   TEXT,      -- p/ CDB (YYYY-MM-DD)
      nominal  REAL       -- p/ CDB (valor base)
    );
    """)
    cur.execute("DELETE FROM ativos_carteira;")
    cur.executemany("""
    INSERT INTO ativos_carteira (ticker, classe, moeda, pct_cdi, inicio, nominal)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("PETR4", "ACAO",   "BRL", None,       None,      None),         # ação B3
        ("BTC",   "CRIPTO", "BRL", None,       None,      None),         # cripto
        ("CDB110","CDB",    "BRL", 110.0, "2024-01-10", 1000.0),         # cdb 110% CDI
    ])
    con.commit(); con.close()
    print("Carteira de teste criada em", db)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    run(args.db)
