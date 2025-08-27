# services/sync_precos_direct.py
from __future__ import annotations
import argparse, os, datetime as dt, sqlite3, requests
from typing import List, Dict, Optional

TODAY = dt.date.today()

# ======== Helpers gerais ========
def brl(v: float) -> float:
    return float(f"{float(v):.6f}")

def get_usdbrl() -> float:
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
    r = requests.get(url, timeout=15); r.raise_for_status()
    return float(str(r.json()[0]["valor"]).replace(",", "."))

def get_cdi_series(start: dt.date, end: dt.date):
    url = ( "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?"
            f"formato=json&dataInicial={start.strftime('%d/%m/%Y')}&dataFinal={end.strftime('%d/%m/%Y')}" )
    r = requests.get(url, timeout=30); r.raise_for_status()
    out = []
    for row in r.json():
        d = dt.datetime.strptime(row["data"], "%d/%m/%Y").date()
        val = float(str(row["valor"]).replace(",", "."))  # % a.d.
        out.append((d, val))
    return out

def accrue_cdb(nominal: float, pct_cdi: float, start: dt.date, end: dt.date) -> float:
    if end <= start: return nominal
    value = float(nominal)
    for _, cdi_day in get_cdi_series(start, end):
        value *= (1.0 + (cdi_day/100.0) * (pct_cdi/100.0))
    return value

# ======== Provedores ========
def price_crypto_brl(symbol: str) -> Optional[float]:
    sym = symbol.upper(); usdbrl = get_usdbrl()
    # Coinbase spot
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot", timeout=10)
        if r.status_code == 200:
            px_usd = float(r.json()["data"]["amount"])
            return brl(px_usd * usdbrl)
    except Exception:
        pass
    # Binance fallback
    try:
        r = requests.get("https://www.binance.com/api/v3/ticker/price",
                         params={"symbol": f"{sym}USDT"}, timeout=10)
        if r.status_code == 200:
            px_usdt = float(r.json()["price"])
            return brl(px_usdt * usdbrl)
    except Exception:
        pass
    return None

def price_equities_brl(symbols: List[str]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    try:
        import yfinance as yf
        yfs = [s if s.endswith(".SA") else f"{s}.SA" for s in symbols]
        tk = yf.Tickers(" ".join(yfs))
        for s2 in yfs:
            try:
                t = tk.tickers[s2]
                val = getattr(getattr(t, "fast_info", None), "last_price", None)
                if val is None:
                    h = t.history(period="1d")
                    if not h.empty: val = float(h["Close"].iloc[-1])
                if val is not None:
                    base = s2[:-3] if s2.endswith(".SA") else s2
                    out[base.upper()] = brl(val)
            except Exception:
                continue
        return out
    except Exception:
        # Stooq fallback
        for s in symbols:
            s2 = s.lower() if s.lower().endswith(".sa") else f"{s.lower()}.sa"
            try:
                r = requests.get(f"https://stooq.com/q/d/l/?s={s2}&i=d", timeout=10)
                if r.status_code == 200 and "Close" in r.text:
                    last = r.text.strip().splitlines()[-1].split(",")[-1]
                    out[s.upper()] = brl(float(last))
            except Exception:
                continue
        return out

# ======== Utilidades de schema ========
def has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    info = conn.execute(f"PRAGMA table_info({table});").fetchall()
    names = [r[1] if isinstance(r, tuple) else r["name"] for r in info]
    return col in set(names)

# ======== Leitura da carteira (posição > 0) – sem depender de 'classe/moeda' existirem ========
def load_portfolio_from_db_for_positions(conn: sqlite3.Connection):
    rows = []
    has_classe = has_column(conn, "ativos", "classe")
    has_moeda  = has_column(conn, "ativos", "moeda")

    sql = "SELECT UPPER(a.ticker) as ticker"
    sql += (", UPPER(COALESCE(a.classe,'ACAO')) as classe" if has_classe else ", 'ACAO' as classe")
    sql += (", UPPER(COALESCE(a.moeda,'BRL'))  as moeda"  if has_moeda  else ", 'BRL' as moeda")
    sql += """
      FROM ativos a
      JOIN trades t ON t.ativo_id = a.id
     GROUP BY a.id
    HAVING SUM(CASE WHEN t.tipo='C' THEN t.quantidade ELSE -t.quantidade END) > 0
    """

    for t, cl, md in conn.execute(sql).fetchall():
        rows.append({"ticker": t, "classe": cl, "moeda": md})

    # CDBs opcionais a partir de ativos_carteira
    try:
        cur = conn.execute("""SELECT UPPER(ticker), COALESCE(pct_cdi,0), inicio, COALESCE(nominal,0)
                                FROM ativos_carteira WHERE UPPER(classe)='CDB'""")
        for t, pct, inicio, nominal in cur.fetchall():
            rows.append({"ticker": t, "classe": "CDB", "moeda":"BRL",
                         "pct_cdi": float(pct or 0.0),
                         "inicio": dt.date.fromisoformat(inicio) if inicio else None,
                         "nominal": float(nominal or 0.0)})
    except Exception:
        pass
    return rows

# ======== Upserts mínimos, compatíveis com schema antigo ========
def ensure_ativo_min(conn: sqlite3.Connection, ticker: str) -> int:
    t = ticker.upper().strip()
    r = conn.execute("SELECT id FROM ativos WHERE UPPER(ticker)=?", (t,)).fetchone()
    if r: return int(r[0])
    # Inserção mínima (só 'ticker'); outras colunas ficam NULL/DEFAULT
    conn.execute("INSERT INTO ativos (ticker) VALUES (?)", (t,))
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

def upsert_preco_min(conn: sqlite3.Connection, ativo_id: int, data_iso: str, preco: float):
    # tenta ON CONFLICT; se não houver índice único, cai pro modo manual
    try:
        conn.execute("""
            INSERT INTO precos (data, ativo_id, preco) VALUES (?, ?, ?)
            ON CONFLICT(ativo_id, data) DO UPDATE SET preco=excluded.preco
        """, (data_iso, int(ativo_id), float(preco)))
    except sqlite3.OperationalError:
        old = conn.execute("SELECT id FROM precos WHERE ativo_id=? AND data=?", (int(ativo_id), data_iso)).fetchone()
        if old:
            conn.execute("UPDATE precos SET preco=? WHERE id=?", (float(preco), int(old[0])))
        else:
            conn.execute("INSERT INTO precos (data, ativo_id, preco) VALUES (?, ?, ?)", (data_iso, int(ativo_id), float(preco)))

# ======== Execução principal ========
def run(db_path: str):
    import yfinance  # garante erro cedo se faltar (ou remova esta linha para usar fallback Stooq)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        carteira = load_portfolio_from_db_for_positions(conn)

        ok, fail = [], []

        # Equities B3
        eq = [r["ticker"] for r in carteira if r["classe"] in {"ACAO","ETF","FII","BDR"}]
        if eq:
            prices = price_equities_brl(list(set(eq)))
            for t, px in prices.items():
                try:
                    aid = ensure_ativo_min(conn, t)
                    upsert_preco_min(conn, aid, TODAY.isoformat(), px)
                    ok.append((t, px, "EQ"))
                except Exception as e:
                    fail.append((t, str(e)))
            conn.commit()

        # Cripto
        cr = [r["ticker"] for r in carteira if r["classe"]=="CRIPTO"]
        for t in set(cr):
            try:
                px = price_crypto_brl(t)
                if px is None: 
                    fail.append((t, "sem preço")); continue
                aid = ensure_ativo_min(conn, t)
                upsert_preco_min(conn, aid, TODAY.isoformat(), px)
                ok.append((t, px, "CR"))
            except Exception as e:
                fail.append((t, str(e)))
        conn.commit()

        # CDB
        cdb_rows = [r for r in carteira if r["classe"]=="CDB" and r.get("pct_cdi") and r.get("inicio")]
        for r in cdb_rows:
            try:
                val = accrue_cdb(r.get("nominal") or 1000.0, float(r["pct_cdi"]), r["inicio"], TODAY)
                aid = ensure_ativo_min(conn, r["ticker"])
                upsert_preco_min(conn, aid, TODAY.isoformat(), val)
                ok.append((r["ticker"], val, "CDB"))
            except Exception as e:
                fail.append((r["ticker"], str(e)))
        conn.commit()

    print("Atualizados (ticker, preço, tipo):")
    for t, px, tp in ok:
        print(f"  - {t}: {px} ({tp})")
    if fail:
        print("\nFalhas:")
        for t, msg in fail:
            print(f"  - {t}: {msg}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    run(args.db)
