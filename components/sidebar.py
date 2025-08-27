# components/sidebar.py
from __future__ import annotations

import re
from datetime import date
from dateutil.relativedelta import relativedelta

from dash import html, dcc, no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

from app import app
from services.globals import (
    dfReceitas, dfDespesas, dfInvestimentos,
    dfCatReceitas, dfCatDespesas, dfCatInvestimentos,
    catReceitas, catDespesas, catInvestimentos,
    append_receitas, append_despesas, append_investimentos,
    load_receitas, load_despesas, load_investimentos,
    load_cat_receitas, load_cat_despesas, load_cat_investimentos,
    refresh_globals,
)
from services.db import insert_trade

# ----------------- Helpers -----------------
def _parse_valor(valor):
    if valor in (None, ""):
        return None
    s = str(valor).strip()
    s = re.sub(r"[^\d,\.\-]", "", s)
    if s.count(",") == 1 and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "").replace(",", ".")
    try:
        return round(float(s), 2)
    except Exception:
        return None

def _toast(id_, text, color="success", is_open=False):
    return dbc.Toast(
        text,
        id=id_,
        header="Ok!" if color != "danger" else "Atenção",
        is_open=is_open,
        duration=2500,
        icon=color,
        dismissable=True,
        style={"position": "fixed", "top": 10, "right": 10, "zIndex": 2000},
    )

def _opts_from_df(df: pd.DataFrame):
    if df is None or df.empty or "Categoria" not in df.columns:
        return []
    vals = df["Categoria"].dropna().astype(str).tolist()
    return [{"label": v, "value": v} for v in vals]

def _pick_value(current, options):
    vals = [o["value"] for o in (options or [])]
    if current in vals:
        return current
    return (vals[0] if vals else None)

# ----------------- Layout -----------------
layout = html.Div(
    [
        dcc.Interval(id="bootSidebar", interval=200, n_intervals=0, max_intervals=1),

        # Stores globais — AGORA com "records"
        dcc.Store(id="storeReceitas", data=dfReceitas.to_dict("records")),
        dcc.Store(id="storeDespesas", data=dfDespesas.to_dict("records")),
        dcc.Store(id="storeInvestimentos", data=dfInvestimentos.to_dict("records")),
        dcc.Store(id="storeCatReceita", data=dfCatReceitas.to_dict("records")),
        dcc.Store(id="storeCatDespesas", data=dfCatDespesas.to_dict("records")),
        dcc.Store(id="storeCatInvestimentos", data=dfCatInvestimentos.to_dict("records")),

        # Toasts
        _toast("toast-receita", "Receita adicionada com sucesso!"),
        _toast("toast-despesa", "Despesa adicionada com sucesso!"),
        _toast("toast-aporte",  "Aporte adicionado com sucesso!"),
        _toast("toast-trade",   "Trade salvo!"),
        _toast("toast-erro-receita", "Revise os campos da Receita.", color="danger"),
        _toast("toast-erro-despesa", "Revise os campos da Despesa.", color="danger"),
        _toast("toast-erro-aporte",  "Revise os campos do Aporte.",  color="danger"),
        _toast("toast-erro-trade",   "Revise os campos do Trade.",   color="danger"),

        # Navegação rápida
        dbc.Card(
            dbc.CardBody([
                html.Small("Navegação rápida"),
                dbc.ButtonGroup([
                    dbc.Button("Dashboards", href="/dashboards", color="secondary", outline=True, size="sm"),
                    dbc.Button("Extratos",   href="/extratos",   color="secondary", outline=True, size="sm", className="ms-1"),
                    dbc.Button("Carteira",   href="/carteira",   color="secondary", outline=True, size="sm", className="ms-1"),
                    dbc.Button("Simulações", href="/simulacoes", color="secondary", outline=True, size="sm", className="ms-1"),
                ], className="mt-1")
            ]), className="mb-2"
        ),

        html.H4("Lançar transações"),
        html.Hr(),

        dcc.Tabs(
            id="tabsSidebar",
            value="tab_receitas",
            children=[
                # ========== RECEITAS ==========
                dcc.Tab(label="Receitas", value="tab_receitas", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([dbc.Label("Descrição"), dbc.Input(id="descricaoReceita", type="text")], md=6),
                            dbc.Col([dbc.Label("Valor (R$)"), dbc.Input(id="valorReceita", type="text")], md=6),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("Data"), dcc.DatePickerSingle(id="dataReceita", date=date.today(), display_format="DD/MM/YYYY", style={"width":"100%"})], md=4),
                            dbc.Col([dbc.Label("Extras"), dbc.Checklist(options=[{"label":"Recebido","value":1},{"label":"Recorrente","value":2}], value=[1], id="switchesInputReceita", switch=True)], md=4),
                            dbc.Col([dbc.Label("Categoria"),
                                     dbc.Select(id="selectReceita",
                                                options=[{"label":i,"value":i} for i in catReceitas],
                                                value=(catReceitas[0] if catReceitas else None))], md=4),
                        ], className="g-2", style={"marginTop":"6px"}),
                        dbc.Button("Salvar Receita", id="salvarReceita", color="success", className="mt-3 ms-auto"),
                    ], className="p-2")
                ]),

                # ========== DESPESAS ==========
                dcc.Tab(label="Despesas", value="tab_despesas", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([dbc.Label("Descrição"), dbc.Input(id="descricaoDespesa", type="text")], md=6),
                            dbc.Col([dbc.Label("Valor (R$)"), dbc.Input(id="valorDespesa", type="text")], md=6),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("Data"), dcc.DatePickerSingle(id="dataDespesa", date=date.today(), display_format="DD/MM/YYYY", style={"width":"100%"})], md=4),
                            dbc.Col([
                                dbc.Label("Tipo"),
                                dbc.Checklist(
                                    options=[{"label":"Pago","value":1},{"label":"Fixo","value":2},{"label":"Parcelado","value":3}],
                                    value=[], id="switchesInputDespesa", switch=True
                                ),
                                html.Div(
                                    [dbc.Label("Qtd. Parcelas", className="mt-2"), dbc.Input(id="qtdParcelas", type="number", min=1, step=1, value=1)],
                                    id="boxParcelas", style={"display":"none"}
                                ),
                            ], md=4),
                            dbc.Col([dbc.Label("Categoria"),
                                     dbc.Select(id="selectDespesa",
                                                options=[{"label":i,"value":i} for i in catDespesas],
                                                value=(catDespesas[0] if catDespesas else None))], md=4),
                        ], className="g-2", style={"marginTop":"6px"}),
                        dbc.Button("Salvar Despesa", id="salvarDespesa", color="danger", className="mt-3 ms-auto"),
                    ], className="p-2")
                ]),

                # ========== APORTES ==========
                dcc.Tab(label="Aportes", value="tab_aportes", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([dbc.Label("Descrição"), dbc.Input(id="descricaoInvestimento", type="text", placeholder="Ex.: Aporte corretora")], md=6),
                            dbc.Col([dbc.Label("Valor (R$)"), dbc.Input(id="valorInvestimento", type="text")], md=6),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("Data"), dcc.DatePickerSingle(id="dataInvestimento", date=date.today(), display_format="DD/MM/YYYY", style={"width":"100%"})], md=4),
                            dbc.Col([dbc.Label("Marcação"), dbc.Checklist(options=[{"label":"Recebido","value":1},{"label":"Fixo","value":2}], value=[], id="switchesInputInvestimento", switch=True)], md=4),
                            dbc.Col([dbc.Label("Categoria"),
                                     dbc.Select(id="selectInvestimento",
                                                options=[{"label":i,"value":i} for i in catInvestimentos],
                                                value=(catInvestimentos[0] if catInvestimentos else None))], md=4),
                        ], className="g-2", style={"marginTop":"6px"}),
                        dbc.Button("Salvar Aporte", id="salvarInvestimento", color="primary", className="mt-3 ms-auto"),
                    ], className="p-2")
                ]),

                # ========== TRADES ==========
                dcc.Tab(label="Trades (rápido)", value="tab_trades", children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([dbc.Label("Ticker"), dbc.Input(id="tr_ticker", placeholder="PETR4")], md=3),
                            dbc.Col([dbc.Label("Data"), dcc.DatePickerSingle(id="tr_data", display_format="DD/MM/YYYY", date=date.today())], md=3),
                            dbc.Col([dbc.Label("Tipo"), dcc.Dropdown(id="tr_tipo", options=[{"label":"Compra","value":"C"},{"label":"Venda","value":"V"}], placeholder="Selecione")], md=3),
                            dbc.Col([dbc.Label("Qtd"), dbc.Input(id="tr_qtd", type="number", min=0, step=1)], md=3),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("Preço"), dbc.Input(id="tr_preco", type="number", min=0, step=0.01)], md=4),
                            dbc.Col([dbc.Label("Taxas"), dbc.Input(id="tr_taxas", type="number", min=0, step=0.01, value=0)], md=4),
                            dbc.Col([dbc.Label("Descrição"), dbc.Input(id="tr_desc", placeholder="Observações")], md=4),
                        ], className="g-2 mt-1"),
                        dbc.Button("Salvar Trade", id="tr_salvar", color="secondary", className="mt-2"),
                    ], className="p-2")
                ]),
            ],
        ),

        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink([html.I(className="fa fa-line-chart me-2"), "Dashboard"],  href="/dashboards", active="exact"),
                dbc.NavLink([html.I(className="fa fa-table me-2"),      "Extratos"],   href="/extratos",   active="exact"),
                dbc.NavLink([html.I(className="fa fa-briefcase me-2"),  "Carteira"],   href="/carteira",   active="exact"),
                dbc.NavLink([html.I(className="fa fa-bar-chart me-2"),  "Simulações"], href="/simulacoes", active="exact"),
                dbc.NavLink([html.I(className="fa fa-bar-chart me-2"),  "Imposto de Renda"], href="/ir", active="exact"),
            ],
            vertical=True, pills=True, className="mb-3",
        ),
    ],
    id="sidebar-wrapper", className="p-2"
)

# ----------------- Callbacks -----------------
@app.callback(
    Output("storeCatReceita", "data", allow_duplicate=True),
    Output("storeCatDespesas", "data", allow_duplicate=True),
    Output("storeCatInvestimentos", "data", allow_duplicate=True),
    Output("selectReceita", "options", allow_duplicate=True),
    Output("selectReceita", "value", allow_duplicate=True),
    Output("selectDespesa", "options", allow_duplicate=True),
    Output("selectDespesa", "value", allow_duplicate=True),
    Output("selectInvestimento", "options", allow_duplicate=True),
    Output("selectInvestimento", "value", allow_duplicate=True),
    Input("bootSidebar", "n_intervals"),
    State("selectReceita", "value"),
    State("selectDespesa", "value"),
    State("selectInvestimento", "value"),
    prevent_initial_call="initial_duplicate",
)
def _boot_sync(_, v_r, v_d, v_i):
    dfr = load_cat_receitas()
    dfd = load_cat_despesas()
    dfi = load_cat_investimentos()
    opt_r, opt_d, opt_i = _opts_from_df(dfr), _opts_from_df(dfd), _opts_from_df(dfi)
    return (
        dfr.to_dict("records"), dfd.to_dict("records"), dfi.to_dict("records"),
        opt_r, _pick_value(v_r, opt_r),
        opt_d, _pick_value(v_d, opt_d),
        opt_i, _pick_value(v_i, opt_i),
    )

@app.callback(Output("boxParcelas", "style"), Input("switchesInputDespesa", "value"))
def _show_parcelas(switches):
    return {"display": "block"} if (switches and 3 in switches) else {"display": "none"}

# ----- SALVAR RECEITA -----
@app.callback(
    Output("storeReceitas", "data", allow_duplicate=True),
    Output("toast-receita", "is_open"),
    Output("toast-erro-receita", "is_open"),
    Input("salvarReceita", "n_clicks"),
    State("descricaoReceita", "value"),
    State("valorReceita", "value"),
    State("dataReceita", "date"),
    State("switchesInputReceita", "value"),
    State("selectReceita", "value"),
    prevent_initial_call=True,
)
def salvarReceita(n, descricao, valor, dt, switches, categoria):
    if not n:
        return no_update, False, False
    v = _parse_valor(valor)
    if v is None or not dt or not categoria:
        return no_update, False, True

    recebido = 1 if (switches and 1 in switches) else 0
    recorrente = 1 if (switches and 2 in switches) else 0
    categoria_val = categoria[0] if isinstance(categoria, list) else categoria

    df_new = pd.DataFrame([{
        "Valor": v,
        "Recebido": recebido,
        "Recorrente": recorrente,
        "Data": pd.to_datetime(dt).normalize(),
        "Categoria": categoria_val,
        "Descrição": descricao,
    }])

    try:
        append_receitas(df_new)
        refresh_globals()
        return load_receitas().to_dict("records"), True, False
    except Exception:
        return no_update, False, True

# ----- SALVAR DESPESA -----
@app.callback(
    Output("storeDespesas", "data", allow_duplicate=True),
    Output("toast-despesa", "is_open"),
    Output("toast-erro-despesa", "is_open"),
    Input("salvarDespesa", "n_clicks"),
    State("descricaoDespesa", "value"),
    State("valorDespesa", "value"),
    State("dataDespesa", "date"),
    State("switchesInputDespesa", "value"),
    State("selectDespesa", "value"),
    State("qtdParcelas", "value"),
    prevent_initial_call=True,
)
def salvarDespesa(n, descricao, valor, dt, switches, categoria, qtd_parc):
    if not n:
        return no_update, False, False

    v_total = _parse_valor(valor)
    if v_total is None or not dt or not categoria:
        return no_update, False, True

    data_ini = pd.to_datetime(dt).normalize()
    categoria_val = categoria[0] if isinstance(categoria, list) else categoria

    pago = 1 if (switches and 1 in switches) else 0
    fixo = 1 if (switches and 2 in switches) else 0
    parcelado = 1 if (switches and 3 in switches) else 0
    qtd = max(1, int(qtd_parc or 1))

    cols = ["Valor", "Pago", "Fixo", "Data", "Categoria", "Descrição", "Parcelado", "QtdParcelas", "ParcelaAtual"]

    if parcelado and qtd > 1:
        v_parc = round(v_total / qtd, 2)
        dados = []
        for i in range(1, qtd + 1):
            dados.append({
                "Valor": v_parc, "Pago": pago, "Fixo": fixo,
                "Data": (data_ini + relativedelta(months=i-1)),
                "Categoria": categoria_val, "Descrição": f"{descricao} ({i}/{qtd})",
                "Parcelado": 1, "QtdParcelas": qtd, "ParcelaAtual": i
            })
        df_new = pd.DataFrame(dados, columns=cols)
    else:
        df_new = pd.DataFrame([{
            "Valor": v_total, "Pago": pago, "Fixo": fixo,
            "Data": data_ini, "Categoria": categoria_val, "Descrição": descricao,
            "Parcelado": 0, "QtdParcelas": 1, "ParcelaAtual": 1
        }], columns=cols)

    try:
        append_despesas(df_new)
        refresh_globals()
        return load_despesas().to_dict("records"), True, False
    except Exception:
        return no_update, False, True

# ----- SALVAR APORTE (Investimento) -----
@app.callback(
    Output("storeInvestimentos", "data", allow_duplicate=True),
    Output("toast-aporte", "is_open"),
    Output("toast-erro-aporte", "is_open"),
    Input("salvarInvestimento", "n_clicks"),
    State("descricaoInvestimento", "value"),
    State("valorInvestimento", "value"),
    State("dataInvestimento", "date"),
    State("switchesInputInvestimento", "value"),
    State("selectInvestimento", "value"),
    prevent_initial_call=True,
)
def salvarInvestimento(n, descricao, valor, dt, switches, categoria):
    if not n:
        return no_update, False, False
    v = _parse_valor(valor)
    if v is None or not dt or not categoria:
        return no_update, False, True

    recebido = 1 if (switches and 1 in switches) else 0
    fixo = 1 if (switches and 2 in switches) else 0
    categoria_val = categoria[0] if isinstance(categoria, list) else categoria

    df_new = pd.DataFrame([{
        "Valor": v, "Tipo": None,
        "Data": pd.to_datetime(dt).normalize(),
        "Categoria": categoria_val, "Descrição": descricao,
        "Rentabilidade": None, "Vencimento": None, "Liquidez": None,
        "Recebido": recebido, "Fixo": fixo
    }])

    try:
        append_investimentos(df_new)
        refresh_globals()
        return load_investimentos().to_dict("records"), True, False
    except Exception:
        return no_update, False, True

# ----- TRADES (rápido) -----
@app.callback(
    Output("toast-trade", "is_open"),
    Output("toast-erro-trade", "is_open"),
    Input("tr_salvar", "n_clicks"),
    State("tr_ticker", "value"),
    State("tr_data", "date"),
    State("tr_tipo", "value"),
    State("tr_qtd", "value"),
    State("tr_preco", "value"),
    State("tr_taxas", "value"),
    State("tr_desc", "value"),
    prevent_initial_call=True,
)
def salvar_trade(n, ticker, data, tipo, qtd, preco, taxas, desc):
    if not n:
        return False, False
    try:
        insert_trade(ticker, data, tipo, qtd, preco, taxas or 0.0, desc)
        return True, False
    except Exception:
        return False, True
