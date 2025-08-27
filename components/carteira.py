# components/carteira.py
from __future__ import annotations

import math
import pandas as pd
from datetime import date
from typing import Any, Dict, List, Optional

import dash
from dash import html, dcc, no_update, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from app import app
from services import db as _db
from services.performance import compute_metrics
from services.portfolio import compute_positions, allocation_by, rebalance_suggestion

# ========================= Helpers =========================

def _coerce_date_str(s: Any) -> Optional[str]:
    """
    Converte diferentes formatos de data para 'YYYY-MM-DD'.
    - Evita warnings do pandas (dayfirst etc.) usando format explícita quando possível.
    - Retorna None para valores inválidos.
    """
    if s in (None, "", pd.NaT):
        return None
    try:
        # tenta ISO direto
        dt = pd.to_datetime(s, format="%Y-%m-%d", errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    # fallback genérico (sem dayfirst)
    dt = pd.to_datetime(s, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime("%Y-%m-%d")


def _fmt_brl(x: float) -> str:
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _kpi_card(title: str, value: str, help_text: Optional[str] = None, color: str = "light"):
    return dbc.Card(
        dbc.CardBody([
            html.Small(title, className="text-muted"),
            html.H5(value, className="mb-0"),
            html.Small(help_text or "", className="text-muted")
        ]),
        className="shadow-sm", color=color, outline=True
    )


def _table_style():
    return dict(
        style_table={"overflowX": "auto"},
        style_cell={"padding": "6px", "fontSize": 13},
        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
        page_size=12
    )


# ========================= Layout =========================

def layout():
    return html.Div(
        [
            # KPIs sobre a carteira (TWR/IRR/VM/DD etc.)
            dbc.Row([
                dbc.Col(_kpi_card("Valor de Mercado", _fmt_brl(0), "Total atualizado"), md=3),
                dbc.Col(_kpi_card("TWR (acum.)", "0,00%", "Retorno time-weighted"), md=3),
                dbc.Col(_kpi_card("IRR (a.a.)", "0,00%", "Retorno com fluxos"), md=3),
                dbc.Col(_kpi_card("Drawdown Máx.", "0,00%", "Pior queda no período"), md=3),
            ], className="g-2", id="kpis-carteira"),

            html.H4("Carteira"),
            html.Hr(),

            dcc.Tabs(id="tabsCarteira", value="tab-ativos", children=[
                dcc.Tab(label="Ativos", value="tab-ativos", children=_tab_ativos()),
                dcc.Tab(label="Trades", value="tab-trades", children=_tab_trades()),
                dcc.Tab(label="Preços", value="tab-precos", children=_tab_precos()),
                dcc.Tab(label="Proventos", value="tab-proventos", children=_tab_proventos()),
            ]),
            dcc.Interval(id="bootCarteira", interval=250, n_intervals=0, max_intervals=1),
        ],
        className="p-2"
    )


# ========================= Abas =========================

def _tab_ativos():
    ativos = _db.load_ativos()
    cols = [
        dict(name="id", id="id", type="numeric", editable=False),
        dict(name="ticker", id="ticker", type="text"),
        dict(name="nome", id="nome", type="text"),
        dict(name="classe", id="classe", type="text"),
        dict(name="categoria", id="categoria", type="text"),
        dict(name="corretora", id="corretora", type="text"),
        dict(name="liquidez", id="liquidez", type="text"),
        dict(name="objetivo_pct", id="objetivo_pct", type="numeric"),
        dict(name="moeda", id="moeda", type="text"),
    ]
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.H6("Novo ativo"),
            dbc.Row([
                dbc.Col(dbc.Input(id="a_ticker", placeholder="Ticker (ex.: PETR4)"), md=3),
                dbc.Col(dbc.Input(id="a_nome", placeholder="Nome"), md=3),
                dbc.Col(dcc.Dropdown(id="a_classe", options=[{"label":i,"value":i} for i in ["Ação","FII","ETF","BDR","RF","Cripto","Fundo","Outros"]], placeholder="Classe"), md=2),
                dbc.Col(dbc.Input(id="a_categoria", placeholder="Categoria"), md=2),
                dbc.Col(dcc.Dropdown(id="a_moeda", options=[{"label":m,"value":m} for m in ["BRL","USD","EUR","BTC"]], placeholder="Moeda"), md=2),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Input(id="a_corretora", placeholder="Corretora"), md=3),
                dbc.Col(dbc.Input(id="a_liquidez", placeholder="Liquidez"), md=3),
                dbc.Col(dbc.Input(id="a_objpct", placeholder="Objetivo %", type="number", min=0, step=0.1), md=2),
                dbc.Col(dbc.Button("Adicionar", id="a_add", color="primary"), md=2),
                dbc.Col(dbc.Button("Excluir selecionados", id="a_del_sel", color="danger", outline=True), md=2),
            ], className="g-2 mt-1"),
        ]), className="mb-2"),

        dash_table.DataTable(
            id="tblAtivos",
            columns=cols,
            data=ativos.to_dict("records"),
            editable=True,
            row_selectable="multi",
            **_table_style()
        ),
    ])


def _tab_trades():
    trades = _db.load_trades()
    ativos = _db.load_ativos()
    cols = [
        dict(name="id", id="id", type="numeric", editable=False),
        dict(name="data", id="data", type="text"),
        dict(name="Ticker", id="Ticker", type="text"),
        dict(name="tipo", id="tipo", type="text"),
        dict(name="quantidade", id="quantidade", type="numeric"),
        dict(name="preco", id="preco", type="numeric"),
        dict(name="taxas", id="taxas", type="numeric"),
        dict(name="descricao", id="descricao", type="text"),
        dict(name="ativo_id", id="ativo_id", type="numeric", editable=False),
    ]
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.H6("Novo trade"),
            dbc.Row([
                dbc.Col(dcc.Input(id="t_data", type="text", placeholder="Data (YYYY-MM-DD)", value=date.today().strftime("%Y-%m-%d")), md=3),
                dbc.Col(dbc.Input(id="t_ticker", placeholder="Ticker"), md=2),
                dbc.Col(dcc.Dropdown(id="t_tipo", options=[{"label":"Compra","value":"C"},{"label":"Venda","value":"V"}], placeholder="Tipo"), md=2),
                dbc.Col(dbc.Input(id="t_qtd", type="number", placeholder="Qtd"), md=2),
                dbc.Col(dbc.Input(id="t_preco", type="number", placeholder="Preço"), md=2),
                dbc.Col(dbc.Input(id="t_taxas", type="number", placeholder="Taxas", value=0), md=1),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Input(id="t_desc", placeholder="Descrição"), md=9),
                dbc.Col(dbc.Button("Adicionar", id="t_add", color="primary"), md=2),
                dbc.Col(dbc.Button("Excluir selecionados", id="t_del_sel", color="danger", outline=True), md=1),
            ], className="g-2 mt-1"),
        ]), className="mb-2"),

        dash_table.DataTable(
            id="tblTrades",
            columns=cols,
            data=trades.to_dict("records"),
            editable=True,
            row_selectable="multi",
            **_table_style()
        ),
    ])


def _tab_precos():
    precos = _db.load_precos()
    cols = [
        dict(name="id", id="id", type="numeric", editable=False),
        dict(name="data", id="data", type="text"),
        dict(name="Ticker", id="Ticker", type="text"),
        dict(name="preco", id="preco", type="numeric"),
        dict(name="ativo_id", id="ativo_id", type="numeric", editable=False),
    ]
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.H6("Novo preço"),
            dbc.Row([
                dbc.Col(dcc.Input(id="p_data", type="text", placeholder="Data (YYYY-MM-DD)", value=date.today().strftime("%Y-%m-%d")), md=3),
                dbc.Col(dbc.Input(id="p_ticker", placeholder="Ticker"), md=3),
                dbc.Col(dbc.Input(id="p_preco", type="number", placeholder="Preço"), md=3),
                dbc.Col(dbc.Button("Adicionar", id="p_add", color="primary"), md=2),
                dbc.Col(dbc.Button("Excluir selecionados", id="p_del_sel", color="danger", outline=True), md=1),
            ], className="g-2"),
        ]), className="mb-2"),

        dash_table.DataTable(
            id="tblPrecos",
            columns=cols,
            data=precos.to_dict("records"),
            editable=True,
            row_selectable="multi",
            **_table_style()
        ),
    ])


def _tab_proventos():
    prov = _db.load_proventos()
    cols = [
        dict(name="id", id="id", type="numeric", editable=False),
        dict(name="data", id="data", type="text"),
        dict(name="Ticker", id="Ticker", type="text"),
        dict(name="tipo", id="tipo", type="text"),
        dict(name="valor_total", id="valor_total", type="numeric"),
        dict(name="qtd_base", id="qtd_base", type="numeric"),
        dict(name="observacao", id="observacao", type="text"),
        dict(name="ativo_id", id="ativo_id", type="numeric", editable=False),
    ]
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.H6("Novo provento"),
            dbc.Row([
                dbc.Col(dcc.Input(id="pv_data", type="text", placeholder="Data (YYYY-MM-DD)", value=date.today().strftime("%Y-%m-%d")), md=3),
                dbc.Col(dbc.Input(id="pv_ticker", placeholder="Ticker"), md=2),
                dbc.Col(dcc.Dropdown(id="pv_tipo", options=[{"label":l,"value":v} for v,l in [("DIV","Dividendo"),("JCP","JCP"),("ALUGUEL","Aluguel"),("OUTRO","Outro")]], placeholder="Tipo"), md=2),
                dbc.Col(dbc.Input(id="pv_valor", type="number", placeholder="Valor total"), md=3),
                dbc.Col(dbc.Input(id="pv_qtd", type="number", placeholder="Qtd. base (opcional)"), md=2),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Input(id="pv_obs", placeholder="Observação"), md=10),
                dbc.Col(dbc.Button("Adicionar", id="pv_add", color="primary"), md=1),
                dbc.Col(dbc.Button("Excluir selecionados", id="pv_del_sel", color="danger", outline=True), md=1),
            ], className="g-2 mt-1"),
        ]), className="mb-2"),

        dash_table.DataTable(
            id="tblProventos",
            columns=cols,
            data=prov.to_dict("records"),
            editable=True,
            row_selectable="multi",
            **_table_style()
        ),
    ])


# ========================= Callbacks =========================

@app.callback(
    Output("kpis-carteira", "children"),
    Input("bootCarteira", "n_intervals"),
    prevent_initial_call=False,
)
def _load_kpis(_):
    try:
        metrics, vm_df, _bench = compute_metrics()
        vm_total = vm_df["vm_total"].iloc[-1] if not vm_df.empty else 0.0
        twr = metrics.get("twr", 0.0)
        irr = metrics.get("irr", 0.0)
        dd  = metrics.get("dd", 0.0)
        cards = [
            dbc.Col(_kpi_card("Valor de Mercado", _fmt_brl(vm_total), "Total atualizado"), md=3),
            dbc.Col(_kpi_card("TWR (acum.)", f"{twr*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X","."), "Retorno time-weighted"), md=3),
            dbc.Col(_kpi_card("IRR (a.a.)", f"{irr*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X","."), "Retorno com fluxos"), md=3),
            dbc.Col(_kpi_card("Drawdown Máx.", f"{abs(dd)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X","."), "Pior queda no período"), md=3),
        ]
        return cards
    except Exception:
        # Em caso de erro, mantém cartões neutros
        return dash.no_update


# ---------- ATIVOS: adicionar / excluir selecionados / editar (upsert) ----------

@app.callback(
    Output("tblAtivos", "data"),
    Input("a_add", "n_clicks"),
    State("a_ticker", "value"),
    State("a_nome", "value"),
    State("a_classe", "value"),
    State("a_categoria", "value"),
    State("a_corretora", "value"),
    State("a_liquidez", "value"),
    State("a_objpct", "value"),
    State("a_moeda", "value"),
    prevent_initial_call=True
)
def add_ativo(n, ticker, nome, classe, categoria, corretora, liquidez, objpct, moeda):
    if not n:
        return no_update
    try:
        _db.upsert_ativo({
            "ticker": (ticker or "").upper(),
            "nome": nome,
            "classe": classe,
            "categoria": categoria,
            "corretora": corretora,
            "liquidez": liquidez,
            "objetivo_pct": float(objpct or 0),
            "moeda": moeda or "BRL",
        })
        return _db.load_ativos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblAtivos", "data", allow_duplicate=True),
    Input("a_del_sel", "n_clicks"),
    State("tblAtivos", "selected_rows"),
    State("tblAtivos", "data"),
    prevent_initial_call=True
)
def del_ativos(_, selected_rows, data):
    if not selected_rows:
        return no_update
    ids = []
    for i in selected_rows:
        row = data[i]
        if "id" in row and row["id"] is not None:
            ids.append(int(row["id"]))
    try:
        _db.delete_ativos(ids)
        return _db.load_ativos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblAtivos", "data", allow_duplicate=True),
    Input("tblAtivos", "data_timestamp"),
    State("tblAtivos", "data"),
    prevent_initial_call=True
)
def edit_ativos(_, rows):
    # upsert linha a linha pelo ticker (chave natural)
    try:
        for r in rows or []:
            if not r.get("ticker"):
                continue
            _db.upsert_ativo({
                "ticker": (r.get("ticker") or "").upper(),
                "nome": r.get("nome"),
                "classe": r.get("classe"),
                "categoria": r.get("categoria"),
                "corretora": r.get("corretora"),
                "liquidez": r.get("liquidez"),
                "objetivo_pct": float(r.get("objetivo_pct") or 0),
                "moeda": r.get("moeda") or "BRL",
            })
        return _db.load_ativos().to_dict("records")
    except Exception:
        return no_update


# ---------- TRADES: adicionar / excluir selecionados / editar ----------

@app.callback(
    Output("tblTrades", "data"),
    Input("t_add", "n_clicks"),
    State("t_data", "value"),
    State("t_ticker", "value"),
    State("t_tipo", "value"),
    State("t_qtd", "value"),
    State("t_preco", "value"),
    State("t_taxas", "value"),
    State("t_desc", "value"),
    prevent_initial_call=True
)
def add_trade(n, d, ticker, tipo, qtd, preco, taxas, desc):
    if not n:
        return no_update
    d = _coerce_date_str(d)
    if not d or not ticker or not tipo or not qtd or not preco:
        return no_update
    try:
        _db.insert_trade(
            data=d, ticker=(ticker or "").upper(), tipo=tipo,
            quantidade=float(qtd), preco=float(preco), taxas=float(taxas or 0), descricao=desc
        )
        return _db.load_trades().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblTrades", "data", allow_duplicate=True),
    Input("t_del_sel", "n_clicks"),
    State("tblTrades", "selected_rows"),
    State("tblTrades", "data"),
    prevent_initial_call=True
)
def del_trades(_, selected_rows, data):
    if not selected_rows:
        return no_update
    ids = []
    for i in selected_rows:
        row = data[i]
        if "id" in row and row["id"] is not None:
            ids.append(int(row["id"]))
    try:
        _db.delete_trades(ids)
        return _db.load_trades().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblTrades", "data", allow_duplicate=True),
    Input("tblTrades", "data_timestamp"),
    State("tblTrades", "data"),
    prevent_initial_call=True
)
def edit_trades(_, rows):
    try:
        for r in rows or []:
            rid = r.get("id")
            if not rid:
                continue
            payload: Dict[str, Any] = {}
            if r.get("data"): payload["data"] = _coerce_date_str(r.get("data"))
            for k in ("Ticker","tipo","quantidade","preco","taxas","descricao"):
                if r.get(k) is not None:
                    payload[k if k != "Ticker" else "Ticker"] = r.get(k)
            _db.update_trade(int(rid), payload)
        return _db.load_trades().to_dict("records")
    except Exception:
        return no_update


# ---------- PREÇOS: adicionar / excluir selecionados / editar ----------

@app.callback(
    Output("tblPrecos", "data"),
    Input("p_add", "n_clicks"),
    State("p_data", "value"),
    State("p_ticker", "value"),
    State("p_preco", "value"),
    prevent_initial_call=True
)
def add_preco(n, d, ticker, preco):
    if not n:
        return no_update
    d = _coerce_date_str(d)
    if not d or not ticker or preco in (None, ""):
        return no_update
    try:
        _db.upsert_preco((ticker or "").upper(), d, float(preco))
        return _db.load_precos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblPrecos", "data", allow_duplicate=True),
    Input("p_del_sel", "n_clicks"),
    State("tblPrecos", "selected_rows"),
    State("tblPrecos", "data"),
    prevent_initial_call=True
)
def del_precos(_, selected_rows, data):
    # Preços não têm delete em lote direto -> use SQL auxiliar por id
    if not selected_rows:
        return no_update
    ids = []
    for i in selected_rows:
        row = data[i]
        if row.get("id") is not None:
            ids.append(int(row["id"]))
    if not ids:
        return no_update
    try:
        with _db.connect() as con:
            con.executemany("DELETE FROM precos WHERE id=?", [(i,) for i in ids])
        return _db.load_precos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblPrecos", "data", allow_duplicate=True),
    Input("tblPrecos", "data_timestamp"),
    State("tblPrecos", "data"),
    prevent_initial_call=True
)
def edit_precos(_, rows):
    try:
        for r in rows or []:
            rid = r.get("id")
            if not rid:
                continue
            # edição de preço: fazemos upsert pela (ticker,data)
            d = _coerce_date_str(r.get("data"))
            ticker = (r.get("Ticker") or "").upper()
            pr = r.get("preco")
            if d and ticker and pr not in (None, ""):
                _db.upsert_preco(ticker, d, float(pr))
        return _db.load_precos().to_dict("records")
    except Exception:
        return no_update


# ---------- PROVENTOS: adicionar / excluir selecionados / editar ----------

@app.callback(
    Output("tblProventos", "data"),
    Input("pv_add", "n_clicks"),
    State("pv_data", "value"),
    State("pv_ticker", "value"),
    State("pv_tipo", "value"),
    State("pv_valor", "value"),
    State("pv_qtd", "value"),
    State("pv_obs", "value"),
    prevent_initial_call=True
)
def add_provento(n, d, ticker, tipo, valor, qtd, obs):
    if not n:
        return no_update
    d = _coerce_date_str(d)
    if not d or not ticker or not tipo or valor in (None, ""):
        return no_update
    try:
        _db.upsert_provento(
            (ticker or "").upper(), d, tipo, float(valor),
            qtd_base=(float(qtd) if qtd not in (None, "") else None),
            observacao=obs
        )
        return _db.load_proventos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblProventos", "data", allow_duplicate=True),
    Input("pv_del_sel", "n_clicks"),
    State("tblProventos", "selected_rows"),
    State("tblProventos", "data"),
    prevent_initial_call=True
)
def del_proventos(_, selected_rows, data):
    if not selected_rows:
        return no_update
    ids = []
    for i in selected_rows:
        row = data[i]
        if row.get("id") is not None:
            ids.append(int(row["id"]))
    try:
        _db.delete_proventos(ids)
        return _db.load_proventos().to_dict("records")
    except Exception:
        return no_update


@app.callback(
    Output("tblProventos", "data", allow_duplicate=True),
    Input("tblProventos", "data_timestamp"),
    State("tblProventos", "data"),
    prevent_initial_call=True
)
def edit_proventos(_, rows):
    try:
        for r in rows or []:
            rid = r.get("id")
            if not rid:
                continue
            payload = dict(
                ticker=(r.get("Ticker") or "").upper(),
                data=_coerce_date_str(r.get("data")),
                tipo=r.get("tipo"),
                valor_total=(float(r.get("valor_total")) if r.get("valor_total") not in (None, "") else None),
                qtd_base=(float(r.get("qtd_base")) if r.get("qtd_base") not in (None, "") else None),
                observacao=r.get("observacao"),
            )
            _db.upsert_provento(
                payload["ticker"], payload["data"], payload["tipo"], payload["valor_total"],
                qtd_base=payload["qtd_base"], observacao=payload["observacao"], row_id=int(rid)
            )
        return _db.load_proventos().to_dict("records")
    except Exception:
        return no_update


# ======= Exposição =======

# Importado por myindex.py -> use "layout" como callable
page_layout = layout()
