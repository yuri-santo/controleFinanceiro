# services/sync_quotes.py
# Requer: requests, pandas (opcional), yfinance (opcional; se não houver, usa Stooq)
import argparse, datetime as dt, sqlite3, json, math
from typing import List, Dict, Tuple, Optional
import requests

# ---------- Helpers gerais ----------
TODAY = dt.date.today()

def brl(value: float) -> float:
    return float(f"{value:.6f}")

def get_usdbrl() -> float:
    # BCB SGS série 1 = USD/BRL (venda) – sem chave
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    # BCB retorna "valor" com vírgula decimal
    return float(str(data[0]["valor"]).replace(",", "."))  # ex.: 5.1234
# :contentReference[oaicite:4]{index=4}

def get_cdi_series(start: dt.date, end: dt.date) -> List[Tuple[dt.date, float]]:
    # BCB SGS série 12 = CDI (ao dia, %) – sem chave
    url = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?"
        f"formato=json&dataInicial={start.strftime('%d/%m/%Y')}&dataFinal={end.strftime('%d/%m/%Y')}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    js = r.json()
    out = []
    for row in js:
        d = dt.datetime.strptime(row["data"], "%d/%m/%Y").date()
        val = float(str(row["valor"]).replace(",", "."))  # % a.d.
        out.append((d, val))
    return out
# :contentReference[oaicite:5]{index=5}

def accrue_cdb(nominal: float, pct_cdi: float, start: dt.date, end: dt.date) -> float:
    """Aproximação: capitalização diária por CDI do período * pct_cdi."""
    if end <= start:
        return nominal
    series = get_cdi_series(start, end)
    value = float(nominal)
    for d, cdi_day_pct in series:
        # CDI diário vem em % a.d.; aplicar percentual do contrato (ex.: 110% do CDI -> 1.10)
        daily_rate = (cdi_day_pct / 100.0) * (pct_cdi / 100.0)
        value *= (1.0 + daily_rate)
    return value

# ---------- Provedores de preço ----------
def price_crypto_symbol(symbol: str) -> Optional[float]:
    """Tenta Coinbase spot (USD), fallback Binance (USDT), converte p/ BRL pelo USD/BRL (BCB)."""
    sym = symbol.upper()
    usd_brl = get_usdbrl()
    # 1) Coinbase spot (sem auth)
    # GET https://api.coinbase.com/v2/prices/BTC-USD/spot
    url = f"https://api.coinbase.com/v2/prices/{sym}-USD/spot"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            amount = float(r.json()["data"]["amount"])
            return brl(amount * usd_brl)
    except Exception:
        pass
    # 2) Binance public (sem auth): GET /api/v3/ticker/price?symbol=BTCUSDT
    try:
        r = requests.get("https://www.binance.com/api/v3/ticker/price", params={"symbol": f"{sym}USDT"}, timeout=10)
        if r.status_code == 200:
            px_usdt = float(r.json()["price"])
            return brl(px_usdt * usd_brl)  # USDT ~ USD
    except Exception:
        pass
    return None
# :contentReference[oaicite:6]{index=6}

def price_equities_yf(symbols: List[str]) -> Dict[str, float]:
    """Usa yfinance se disponível; retorna BRL quando símbolo já é .SA; caso contrário, retorna na moeda nativa."""
    out: Dict[str, float] = {}
    try:
        import yfinance as yf  # sem conta
        # yfinance aceita batch:
        tick = yf.Tickers(" ".join(symbols))
        for s in symbols:
            try:
                t = tick.tickers[s]
                # fast_info é rápido; fallback para history
                val = None
                if hasattr(t, "fast_info") and t.fast_info is not None:
                    v = t.fast_info.get("last_price")
                    if v:
                        val = float(v)
                if val is None:
                    h = t.history(period="1d")
                    if not h.empty:
                        val = float(h["Close"].iloc[-1])
                if val is not None:
                    out[s] = brl(val)
            except Exception:
                continue
    except Exception:
        # yfinance não instalado ou falhou -> tentar Stooq simples (diário em CSV)
        for s in symbols:
            sym = s.lower()
            # Heurística simples: B3 geralmente usa ".sa" no Stooq. Ajuste conforme sua carteira.
            if not sym.endswith(".sa"):
                sym_sa = f"{sym}.sa"
            else:
                sym_sa = sym
            url = f"https://stooq.com/q/d/l/?s={sym_sa}&i=d"  # CSV diário
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200 and "Close" in r.text:
                    last = r.text.strip().splitlines()[-1].split(",")[-1]
                    out[s] = brl(float(last))
            except Exception:
                continue
    return out
# :contentReference[oaicite:7]{index=7}

# ---------- Integração com sua base ----------
def ensure_schema(conn: sqlite3.Connection):
    # Tabela de cotações (ajuste o nome/colunas para o seu padrão)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS cotacoes (
        ticker TEXT NOT NULL,
        data   TEXT NOT NULL,
        preco_brl REAL NOT NULL,
        fonte TEXT,
        PRIMARY KEY (ticker, data)
    )
    """)
    conn.commit()

def upsert_quote(conn: sqlite3.Connection, ticker: str, price_brl: float, fonte: str):
    conn.execute("""
        INSERT INTO cotacoes (ticker, data, preco_brl, fonte)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ticker, data) DO UPDATE SET
            preco_brl=excluded.preco_brl,
            fonte=excluded.fonte
    """, (ticker.upper(), TODAY.isoformat(), float(price_brl), fonte))
    conn.commit()

def load_portfolio_from_db(conn: sqlite3.Connection) -> List[Dict]:
    """
    Adapte este SELECT para a SUA estrutura.
    Retorne uma lista com: [{'ticker': 'PETR4', 'classe': 'ACAO', 'moeda': 'BRL', 'pct_cdi': None, 'inicio': None}, ...]
    Exemplos de mapeamento:
      - Suas ações/ETFs/FIIs/BDRs -> classe em {'ACAO','ETF','FII','BDR'}
      - Suas criptos -> 'CRIPTO'
      - Seus CDBs -> 'CDB' + campos adicionais (pct_cdi, inicio)
    """
    rows = []
    # EXEMPLO 1: se você tem uma tabela 'ativos_carteira'
    try:
        cur = conn.execute("""SELECT ticker, classe, COALESCE(moeda,'BRL'), COALESCE(pct_cdi,0), inicio FROM ativos_carteira""")
        for t, classe, moeda, pct, inicio in cur.fetchall():
            rows.append({
                "ticker": t.strip(),
                "classe": classe.strip().upper(),
                "moeda": (moeda or "BRL").upper(),
                "pct_cdi": float(pct) if pct else None,
                "inicio": dt.date.fromisoformat(inicio) if inicio else None,
            })
        if rows:
            return rows
    except Exception:
        pass

    # EXEMPLO 2: se você preferir listar manualmente por enquanto
    # return [
    #   {"ticker":"PETR4","classe":"ACAO","moeda":"BRL"},
    #   {"ticker":"BTC","classe":"CRIPTO","moeda":"BRL"},
    #   {"ticker":"MEU_CDB","classe":"CDB","moeda":"BRL","pct_cdi":110.0,"inicio": dt.date(2024,1,10),"nominal":1000.0},
    # ]

    return rows

def normalize_b3_symbols(rows: List[Dict]) -> List[str]:
    out = []
    for r in rows:
        t = r["ticker"].upper()
        if r["classe"] in {"ACAO","ETF","FII","BDR"}:
            # Heurística Yahoo Finance: B3 usa sufixo .SA
            if not t.endswith(".SA"):
                t = f"{t}.SA"
        out.append(t)
    return out

def sync(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn)
        portfolio = load_portfolio_from_db(conn)
        if not portfolio:
            print("Nenhum ativo encontrado. Ajuste load_portfolio_from_db().")
            return

        # 1) Equities em lote
        eq_symbols = normalize_b3_symbols([r for r in portfolio if r["classe"] in {"ACAO","ETF","FII","BDR"}])
        eq_prices = price_equities_yf(eq_symbols) if eq_symbols else {}

        # 2) Cripto individual
        crypto_rows = [r for r in portfolio if r["classe"] == "CRIPTO"]
        crypto_prices = {}
        for r in crypto_rows:
            px = price_crypto_symbol(r["ticker"])
            if px is not None:
                crypto_prices[r["ticker"].upper()] = px

        # 3) CDB (accrual CDI)
        rf_rows = [r for r in portfolio if r["classe"] == "CDB"]
        rf_prices = {}
        for r in rf_rows:
            pct = float(r.get("pct_cdi") or 0.0)
            inicio = r.get("inicio")
            nominal = float(r.get("nominal") or 0.0)  # opcional, inclua na sua tabela
            if pct > 0 and inicio:
                val = accrue_cdb(nominal or 1000.0, pct, inicio, TODAY)
                rf_prices[r["ticker"].upper()] = brl(val)

        # Persistir (apenas ativos que retornaram preço)
        for sym, price in eq_prices.items():
            upsert_quote(conn, sym.replace(".SA",""), price, "yfinance/stooq")
        for sym, price in crypto_prices.items():
            upsert_quote(conn, sym, price, "coinbase/binance + BCB USD/BRL")
        for sym, price in rf_prices.items():
            upsert_quote(conn, sym, price, "BCB CDI accrual")

        # Resumo
        print(json.dumps({
            "equities": eq_prices,
            "crypto": crypto_prices,
            "cdb": rf_prices
        }, ensure_ascii=False, indent=2))
        print("✔ Cotações atualizadas.")
    finally:
        conn.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Caminho do SQLite (ex.: data/finance.db)")
    args = ap.parse_args()
    sync(args.db)
