#!/usr/bin/env python3
# Simple one-shot upgrader for an existing finance.db.
# - Creates unified 'categorias' table
# - Converts cat_* to compatibility VIEWS with triggers (INSERT/DELETE)
# - Ensures base tables exist (receitas, despesas, investimentos)
# - Adds missing optional columns in investimentos (Tipo, Rentabilidade, Vencimento, Liquidez)
# - Creates useful indexes
# - All changes happen in a single transaction when possible
# Usage:
#   python upgrade_finance_db.py --db path/to/finance.db

import argparse
import shutil
import sqlite3
from pathlib import Path

def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def object_type(conn: sqlite3.Connection, name: str):
    cur = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (name,))
    row = cur.fetchone()
    if not row:
        return None
    # sqlite3.Row supports key or index
    return row["type"] if "type" in row.keys() else row[0]

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return object_type(conn, name) == "table"

def view_exists(conn: sqlite3.Connection, name: str) -> bool:
    return object_type(conn, name) == "view"

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    try:
        cur = conn.execute(f"PRAGMA table_info({table});")
        return any(r["name"] == column for r in cur.fetchall())
    except sqlite3.Error:
        return False

def ensure_base_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS receitas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      Valor REAL NOT NULL DEFAULT 0,
      Recebido INTEGER NOT NULL DEFAULT 0,
      Recorrente INTEGER NOT NULL DEFAULT 0,
      Data TEXT NOT NULL,
      Categoria TEXT NOT NULL,
      "Descrição" TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS despesas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      Valor REAL NOT NULL DEFAULT 0,
      Pago INTEGER NOT NULL DEFAULT 0,
      Fixo INTEGER NOT NULL DEFAULT 0,
      Data TEXT NOT NULL,
      Categoria TEXT NOT NULL,
      "Descrição" TEXT NOT NULL,
      Parcelado INTEGER NOT NULL DEFAULT 0,
      QtdParcelas INTEGER NOT NULL DEFAULT 1,
      ParcelaAtual INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS investimentos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      Valor REAL NOT NULL DEFAULT 0,
      Recebido INTEGER NOT NULL DEFAULT 0,
      Fixo INTEGER NOT NULL DEFAULT 0,
      Data TEXT NOT NULL,
      Categoria TEXT NOT NULL,
      "Descrição" TEXT NOT NULL
    );
    """)
    # Add optional columns if missing
    for col, typ in [
        ("Tipo", "TEXT"),
        ("Rentabilidade", "REAL"),
        ("Vencimento", "TEXT"),
        ("Liquidez", "TEXT"),
    ]:
        if not column_exists(conn, "investimentos", col):
            conn.execute(f"ALTER TABLE investimentos ADD COLUMN {col} {typ};")

def ensure_unified_categories(conn: sqlite3.Connection) -> None:
    # 1) create unified table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
          id   INTEGER PRIMARY KEY AUTOINCREMENT,
          tipo TEXT NOT NULL CHECK (tipo IN ('receita','despesa','investimento')),
          nome TEXT NOT NULL,
          UNIQUE (tipo, nome)
        );
    """)
    # 2) migrate data from cat_* if they exist (table or view)
    def copy_from(source: str, tipo: str) -> None:
        if view_exists(conn, source) or table_exists(conn, source):
            conn.execute(
                "INSERT OR IGNORE INTO categorias (tipo, nome) "
                f"SELECT ?, Categoria FROM {source}",
                (tipo,)
            )
    copy_from("cat_receitas", "receita")
    copy_from("cat_despesas", "despesa")
    copy_from("cat_investimentos", "investimento")
    
    # 3) if cat_* are tables, rename to backups to free names for views
    for name in ("cat_receitas", "cat_despesas", "cat_investimentos"):
        if table_exists(conn, name):
            conn.execute(f"ALTER TABLE {name} RENAME TO _{name}_backup;")
    # If some views already exist, drop and recreate cleanly
    conn.execute("DROP VIEW IF EXISTS cat_receitas;")
    conn.execute("DROP VIEW IF EXISTS cat_despesas;")
    conn.execute("DROP VIEW IF EXISTS cat_investimentos;")
    
    # 4) create compatibility views
    conn.executescript("""
    CREATE VIEW cat_receitas AS
      SELECT nome AS Categoria FROM categorias WHERE tipo='receita';
    CREATE VIEW cat_despesas AS
      SELECT nome AS Categoria FROM categorias WHERE tipo='despesa';
    CREATE VIEW cat_investimentos AS
      SELECT nome AS Categoria FROM categorias WHERE tipo='investimento';
    """)
    # 5) create INSTEAD OF triggers so INSERT/DELETE on views work
    conn.executescript("""
    CREATE TRIGGER IF NOT EXISTS trg_cat_receitas_insert
    INSTEAD OF INSERT ON cat_receitas
    BEGIN
      INSERT OR IGNORE INTO categorias (tipo, nome) VALUES ('receita', NEW.Categoria);
    END;
    CREATE TRIGGER IF NOT EXISTS trg_cat_receitas_delete
    INSTEAD OF DELETE ON cat_receitas
    BEGIN
      DELETE FROM categorias WHERE tipo='receita' AND nome=OLD.Categoria;
    END;
    CREATE TRIGGER IF NOT EXISTS trg_cat_despesas_insert
    INSTEAD OF INSERT ON cat_despesas
    BEGIN
      INSERT OR IGNORE INTO categorias (tipo, nome) VALUES ('despesa', NEW.Categoria);
    END;
    CREATE TRIGGER IF NOT EXISTS trg_cat_despesas_delete
    INSTEAD OF DELETE ON cat_despesas
    BEGIN
      DELETE FROM categorias WHERE tipo='despesa' AND nome=OLD.Categoria;
    END;
    CREATE TRIGGER IF NOT EXISTS trg_cat_invest_insert
    INSTEAD OF INSERT ON cat_investimentos
    BEGIN
      INSERT OR IGNORE INTO categorias (tipo, nome) VALUES ('investimento', NEW.Categoria);
    END;
    CREATE TRIGGER IF NOT EXISTS trg_cat_invest_delete
    INSTEAD OF DELETE ON cat_investimentos
    BEGIN
      DELETE FROM categorias WHERE tipo='investimento' AND nome=OLD.Categoria;
    END;
    """)

def ensure_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE INDEX IF NOT EXISTS idx_receitas_data ON receitas(Data);
    CREATE INDEX IF NOT EXISTS idx_receitas_cat  ON receitas(Categoria);
    CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(Data);
    CREATE INDEX IF NOT EXISTS idx_despesas_cat  ON despesas(Categoria);
    CREATE INDEX IF NOT EXISTS idx_invest_data   ON investimentos(Data);
    CREATE INDEX IF NOT EXISTS idx_invest_cat    ON investimentos(Categoria);
    CREATE INDEX IF NOT EXISTS idx_cat_tipo_nome ON categorias(tipo, nome);
    """)

def main() -> None:
    ap = argparse.ArgumentParser(description="Upgrade an existing finance.db to unified schema (SQLite).")
    ap.add_argument("--db", required=True, help="Path to finance.db")
    ap.add_argument("--no-backup", action="store_true", help="Do not create a .bak copy of the DB before changes")
    args = ap.parse_args()
    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")
    if not args.no_backup:
        backup = db_path.with_suffix(db_path.suffix + ".bak")
        shutil.copy2(db_path, backup)
        print(f"Backup created: {backup}")
    with connect(db_path) as conn:
        try:
            conn.execute("BEGIN;")
            ensure_base_tables(conn)
            ensure_unified_categories(conn)
            ensure_indexes(conn)
            conn.commit()
            print("Upgrade complete ✅")
        except Exception:
            conn.rollback()
            print("Error during upgrade, rolled back.")
            raise
    print("All done.")

if __name__ == "__main__":
    main()
