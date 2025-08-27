# services/upgrade_portfolio_db.py
from __future__ import annotations
import argparse, shutil
from pathlib import Path
import sqlite3
from textwrap import dedent

DDL = dedent("""
PRAGMA foreign_keys=ON;

-- ================= Legado: índices de desempenho =================
CREATE INDEX IF NOT EXISTS idx_receitas_data ON receitas(Data);
CREATE INDEX IF NOT EXISTS idx_receitas_cat  ON receitas(Categoria);
CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(Data);
CREATE INDEX IF NOT EXISTS idx_despesas_cat  ON despesas(Categoria);
CREATE INDEX IF NOT EXISTS idx_invest_data   ON investimentos(Data);
CREATE INDEX IF NOT EXISTS idx_invest_cat    ON investimentos(Categoria);

-- ================= Ativos / Carteira =================
CREATE TABLE IF NOT EXISTS ativos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  nome TEXT,
  classe TEXT,         -- Ação, FII, RF, ETF, BDR, Cripto...
  categoria TEXT,      -- Setor/tema
  corretora TEXT,
  liquidez TEXT,
  objetivo_pct REAL DEFAULT 0,
  moeda TEXT DEFAULT 'BRL'   -- multi-moeda
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ativos_ticker ON ativos(ticker);

CREATE TABLE IF NOT EXISTS trades(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  ativo_id INTEGER NOT NULL,
  tipo TEXT CHECK(tipo IN ('C','V')) NOT NULL,  -- Compra/Venda
  quantidade REAL NOT NULL,
  preco REAL NOT NULL,
  taxas REAL DEFAULT 0,
  descricao TEXT,
  FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_trades_ativo ON trades(ativo_id);
CREATE INDEX IF NOT EXISTS idx_trades_data  ON trades(data);

CREATE TABLE IF NOT EXISTS precos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  ativo_id INTEGER NOT NULL,
  preco REAL NOT NULL,
  FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_preco_ativo_data ON precos(ativo_id, data);

-- ================= Proventos =================
CREATE TABLE IF NOT EXISTS proventos(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  ativo_id INTEGER NOT NULL,
  tipo TEXT CHECK(tipo IN ('DIV','JCP','ALUGUEL','OUTRO')) NOT NULL,
  valor_total REAL NOT NULL,
  qtd_base REAL,
  observacao TEXT,
  FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_prov_ativo_data ON proventos(ativo_id, data);

-- ================= Ações Corporativas =================
CREATE TABLE IF NOT EXISTS corporate_actions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  ativo_id INTEGER NOT NULL,
  tipo TEXT CHECK(tipo IN ('SPLIT','INPLIT','BONUS','SUBSCRICAO','GRUPAMENTO')) NOT NULL,
  fator REAL NOT NULL,
  preco_subscricao REAL,
  observacao TEXT,
  FOREIGN KEY (ativo_id) REFERENCES ativos(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_corp_ativo_data ON corporate_actions(ativo_id, data);

-- ================= FX & Benchmarks =================
CREATE TABLE IF NOT EXISTS fx_rates(
  data TEXT NOT NULL,
  moeda TEXT NOT NULL,
  brl REAL NOT NULL,   -- 1 unidade da moeda = brl
  PRIMARY KEY (data, moeda)
);

CREATE TABLE IF NOT EXISTS benchmarks(
  serie TEXT NOT NULL,  -- 'CDI', 'IBOV', 'IFIX'...
  data TEXT NOT NULL,
  valor REAL NOT NULL,  -- índice acumulado (base 100) ou retorno diário (%)
  PRIMARY KEY (serie, data)
);

-- ================= Série materializada de valor de carteira =================
CREATE TABLE IF NOT EXISTS portfolio_daily(
  data TEXT PRIMARY KEY,
  vm_total REAL NOT NULL,
  aportes REAL NOT NULL DEFAULT 0,
  retiradas REAL NOT NULL DEFAULT 0,
  proventos REAL NOT NULL DEFAULT 0
);

-- ================= Auditoria =================
CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tabela TEXT NOT NULL,
  registro_id INTEGER,
  acao TEXT NOT NULL,       -- INSERT/UPDATE/DELETE
  ts TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- triggers simples de auditoria
CREATE TRIGGER IF NOT EXISTS trg_audit_trades_ai AFTER INSERT ON trades
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('trades', NEW.id, 'INSERT'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_trades_au AFTER UPDATE ON trades
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('trades', NEW.id, 'UPDATE'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_trades_ad AFTER DELETE ON trades
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('trades', OLD.id, 'DELETE'); END;

CREATE TRIGGER IF NOT EXISTS trg_audit_precos_ai AFTER INSERT ON precos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('precos', NEW.id, 'INSERT'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_precos_au AFTER UPDATE ON precos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('precos', NEW.id, 'UPDATE'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_precos_ad AFTER DELETE ON precos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('precos', OLD.id, 'DELETE'); END;

CREATE TRIGGER IF NOT EXISTS trg_audit_proventos_ai AFTER INSERT ON proventos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('proventos', NEW.id, 'INSERT'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_proventos_au AFTER UPDATE ON proventos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('proventos', NEW.id, 'UPDATE'); END;
CREATE TRIGGER IF NOT EXISTS trg_audit_proventos_ad AFTER DELETE ON proventos
BEGIN INSERT INTO audit_log(tabela,registro_id,acao) VALUES('proventos', OLD.id, 'DELETE'); END;

-- ================= Trigger anti short-sell (venda > posição)
-- (simples; não cobre concorrência/mesmo timestamp)
CREATE TRIGGER IF NOT EXISTS trg_no_short_sell BEFORE INSERT ON trades
WHEN NEW.tipo = 'V'
BEGIN
  SELECT CASE
    WHEN (
      (SELECT IFNULL(SUM(CASE WHEN tipo='C' THEN quantidade ELSE -quantidade END),0)
         FROM trades
        WHERE ativo_id = NEW.ativo_id
          AND date(data) <= date(NEW.data)
      ) - NEW.quantidade
    ) < -0.0001
    THEN RAISE(ABORT, 'Venda supera quantidade disponível.')
  END;
END;

CREATE TRIGGER IF NOT EXISTS trg_no_short_sell_upd BEFORE UPDATE ON trades
WHEN NEW.tipo = 'V'
BEGIN
  SELECT CASE
    WHEN (
      (SELECT IFNULL(SUM(CASE WHEN tipo='C' THEN quantidade ELSE -quantidade END),0)
         FROM trades
        WHERE ativo_id = NEW.ativo_id
          AND date(data) <= date(NEW.data)
          AND id <> NEW.id
      ) - NEW.quantidade
    ) < -0.0001
    THEN RAISE(ABORT, 'Venda supera quantidade disponível.')
  END;
END;
""")

def run(db_path: Path, make_backup: bool = True):
    if not db_path.exists():
        raise SystemExit(f"DB não encontrado: {db_path}")
    if make_backup:
        bak = db_path.with_suffix(db_path.suffix + ".bak2")
        shutil.copy2(db_path, bak)
        print(f"Backup criado: {bak}")
    con = sqlite3.connect(db_path)
    try:
        con.executescript(DDL)
        con.commit()
        print("Schema atualizado ✅")
    finally:
        con.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="caminho do arquivo .db")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()
    run(Path(args.db), make_backup=not args.no_backup)
