# components/simulacoes.py
from __future__ import annotations

from dash import html, dcc, Input, Output, State, callback, no_update
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app import app
from services.globals import fmt_brl
from services.projecoes import (
    # base & util
    ParametrosSimulacao,
    sim_compostos, sim_so_guardar, sim_monte_carlo,
    forecast_cashflow, recomendacao_reserva,
    # novos
    renda_fixa_cdi,
    dca_vs_lumpsum,
    price_schedule, sac_schedule, financiamento_kpis,
    necessidade_aporte, swr_meta, sim_serie_aporte,
)

# =========================================================
# Layout com abas (didático e simples)
# =========================================================
layout = html.Div([
    dcc.Tabs(id="tabs-simulacoes", value="tab-reserva", children=[
        # -------------------------------------------------
        # 1) RESERVA DE EMERGÊNCIA
        # -------------------------------------------------
        dcc.Tab(label="Reserva de Emergência", value="tab-reserva", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("O que é?"),
                    dbc.CardBody(html.P(
                        "A reserva de emergência é um dinheiro separado para imprevistos (saúde, carro, emprego). "
                        "Regra prática: guarde de 6 a 12 meses do seu gasto mensal em opções de baixíssimo risco e liquidez diária "
                        "(ex.: Tesouro Selic, CDB com liquidez diária).",
                        className="text-muted", style={"fontSize":"0.95rem"}
                    ))
                ]), md=12),
            ], className="g-2 mb-2"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Meta sugerida (pelas suas despesas)"),
                    dbc.CardBody([
                        html.Div(id="reserva-kpis"),
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([
                                dbc.InputGroupText("Meses desejados"),
                                dbc.Input(id="reserva-meses", type="number", min=1, max=24, step=1, value=None, placeholder="auto"),
                            ]), md=4),
                            dbc.Col(dbc.InputGroup([
                                dbc.InputGroupText("Quanto já tenho (R$)"),
                                dbc.Input(id="reserva-atual", type="number", min=0, step=50, value=0),
                            ]), md=4),
                            dbc.Col(dbc.Button("Calcular", id="reserva-run", color="primary"), md=2),
                        ], className="g-2 mt-1"),
                        html.Div(id="reserva-progresso", className="mt-3")
                    ])
                ]), md=12),
            ], className="g-2"),
        ]),

        # -------------------------------------------------
        # 2) RENDA FIXA – CDI
        # -------------------------------------------------
        dcc.Tab(label="Renda Fixa (CDB/LCI/LCA)", value="tab-rf", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Parâmetros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("% do CDI"), dbc.Input(id="rf-pct-cdi", type="number", value=105, step=1)]), md=3),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("CDI a.a. (%)"), dbc.Input(id="rf-cdi-aa", type="number", value=12.0, step=0.1)]), md=3),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Prazo (anos)"), dbc.Input(id="rf-anos", type="number", value=3, min=1)]), md=3),
                            dbc.Col(dbc.Checklist(id="rf-isento", options=[{"label":"Isento (LCI/LCA)","value":1}], value=[], switch=True), md=3),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Valor inicial"), dbc.Input(id="rf-v0", type="number", value=0, min=0, step=100)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Aporte mensal"), dbc.Input(id="rf-aporte", type="number", value=1000, min=0, step=50)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Inflação a.a. (%)"), dbc.Input(id="rf-inflacao", type="number", value=4.0, step=0.1)]), md=4),
                        ], className="g-2 mt-1"),
                        dbc.Button("Simular Renda Fixa", id="rf-run", color="primary", className="mt-2")
                    ])
                ]), md=12),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="rf-graf"))), md=12)
            ], className="g-2"),
        ]),

        # -------------------------------------------------
        # 3) AÇÕES – DCA × APORTE ÚNICO
        # -------------------------------------------------
        dcc.Tab(label="Ações (DCA × Aporte Único)", value="tab-dca", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Parâmetros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Valor inicial"), dbc.Input(id="dca-v0", type="number", value=0, min=0, step=100)]), md=3),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Aporte total"), dbc.Input(id="dca-aporte", type="number", value=12000, min=0, step=100)]), md=3),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Meses"), dbc.Input(id="dca-meses", type="number", value=12, min=1, step=1)]), md=2),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Taxa a.a. (%)"), dbc.Input(id="dca-taxa", type="number", value=12.0, step=0.1)]), md=2),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Inflação a.a. (%)"), dbc.Input(id="dca-inflacao", type="number", value=4.0, step=0.1)]), md=2),
                        ], className="g-2"),
                        dbc.Button("Comparar", id="dca-run", color="info", className="mt-2")
                    ])
                ]), md=12),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="dca-graf"))), md=12)
            ], className="g-2"),
        ]),

        # -------------------------------------------------
        # 4) FINANCIAMENTO – PRICE × SAC
        # -------------------------------------------------
        dcc.Tab(label="Financiamento Imobiliário", value="tab-fin", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Parâmetros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Valor (R$)"), dbc.Input(id="fin-valor", type="number", value=300000, step=1000)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Prazo (anos)"), dbc.Input(id="fin-anos", type="number", value=30, min=1)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Taxa a.a. (%)"), dbc.Input(id="fin-taxa", type="number", value=10.0, step=0.1)]), md=4),
                        ], className="g-2"),
                        dbc.Button("Calcular", id="fin-run", color="secondary", className="mt-2")
                    ])
                ]), md=12)
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="fin-graf"))), md=7),
                dbc.Col(dbc.Card(dbc.CardBody(html.Div(id="fin-kpis"))), md=5),
            ], className="g-2"),
        ]),

        # -------------------------------------------------
        # 5) OBJETIVO & APOSENTADORIA (SWR)
        # -------------------------------------------------
        dcc.Tab(label="Objetivo & Aposentadoria (SWR)", value="tab-goal", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Objetivo (aporte mensal necessário)"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Meta final (R$)"), dbc.Input(id="goal-meta", type="number", value=500000, min=0, step=1000)]), md=3),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Anos"), dbc.Input(id="goal-anos", type="number", value=10, min=1, max=60)]), md=2),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Taxa a.a. (%)"), dbc.Input(id="goal-taxa", type="number", value=10.0, step=0.1)]), md=2),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Valor inicial"), dbc.Input(id="goal-v0", type="number", value=0, min=0, step=100)]), md=3),
                            dbc.Col(dbc.Button("Calcular objetivo", id="goal-run", color="primary"), md=2),
                        ], className="g-2"),
                        html.Div(id="goal-kpis"),
                    ])
                ]), md=12),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="goal-graf"))), md=12),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("SWR – Retirada mensal sustentável"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Patrimônio (R$)"), dbc.Input(id="swr-patr", type="number", value=500000, min=0, step=1000)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("SWR a.a. (%)"), dbc.Input(id="swr-aa", type="number", value=4.0, step=0.1, min=0.5, max=10)]), md=3),
                            dbc.Col(dbc.Button("Calcular SWR", id="swr-run", color="success"), md=2),
                        ], className="g-2"),
                        html.Div(id="swr-kpi")
                    ])
                ]), md=12),
            ], className="g-2"),
        ]),

        # -------------------------------------------------
        # 6) CRESCIMENTO & MONTE CARLO + FORECAST
        # -------------------------------------------------
        dcc.Tab(label="Crescimento & Monte Carlo", value="tab-main", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Parâmetros"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Valor inicial"), dbc.Input(id="sim-v0", type="number", value=0, min=0, step=100)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Aporte mensal"), dbc.Input(id="sim-aporte", type="number", value=1000, min=0, step=50)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Anos"), dbc.Input(id="sim-anos", type="number", value=10, min=1, step=1)]), md=4),
                        ], className="g-2"),
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Taxa a.a. (%)"), dbc.Input(id="sim-taxa", type="number", value=12, step=0.1)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Inflação a.a. (%)"), dbc.Input(id="sim-inflacao", type="number", value=4, step=0.1)]), md=4),
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Vol. a.a. (%)"), dbc.Input(id="sim-vol", type="number", value=15, step=0.1)]), md=4),
                        ], className="g-2 mt-1"),
                        dbc.Row([
                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("Cenários"), dbc.Input(id="sim-npaths", type="number", value=500, min=100, max=5000, step=100)]), md=3),
                            dbc.Col(dbc.Button("Rodar", id="sim-run", color="primary", className="mt-1"), md=2),
                        ], className="g-2"),
                    ])
                ]), md=12),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="sim-g1"))), md=7),
                dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="sim-g2"))), md=5),
            ], className="g-2"),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(
                    dash_table.DataTable(
                        id="sim-table",
                        columns=[{"name": c, "id": c} for c in ["Data","SemJuros","Nominal","Real"]],
                        data=[], page_size=12, style_table={"overflowX":"auto"}
                    )
                )), md=12)
            ], className="g-2"),
            html.Hr(),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Previsão de Fluxo de Caixa (12 meses)"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id="fore-metodo",
                            options=[
                                {"label": "Tendência Linear (simples)", "value":"linear"},
                                {"label": "Média Exponencial (EMA 12)", "value":"ema"},
                                {"label": "Média 12m", "value":"media"},
                                {"label": "Mediana 12m", "value":"mediana"},
                            ],
                            value="linear", clearable=False, className="mb-2"
                        ),
                        dcc.Graph(id="fore-graph")
                    ])
                ]), md=12),
            ], className="g-2"),
        ]),
    ])
], className="p-2")

# =========================================================
# Callbacks
# =========================================================

# --------- Reserva de emergência ---------
@callback(
    Output("reserva-kpis", "children"),
    Input("reserva-run", "n_clicks"),
    prevent_initial_call=False
)
def _reserva_kpis(_):
    info = recomendacao_reserva()
    media = fmt_brl(info["despesa_media"])
    alvo = fmt_brl(info["alvo"])
    return dbc.Row([
        dbc.Col(dbc.Alert([html.B("Sua despesa média (12m): "), media], color="secondary"), md=5),
        dbc.Col(dbc.Alert([html.B(f"Meta sugerida ({int(info['meses'])} meses): "), alvo], color="info"), md=7),
    ], className="g-2")

@callback(
    Output("reserva-progresso", "children"),
    Input("reserva-atual", "value"),
    Input("reserva-meses", "value"),
)
def _reserva_progress(valor_atual, meses_desejados):
    info = recomendacao_reserva()
    meses = float(meses_desejados) if meses_desejados else float(info["meses"])
    alvo = float(info["despesa_media"]) * meses
    atual = float(valor_atual or 0.0)
    falta = max(0.0, alvo - atual)
    pct = 0.0 if alvo <= 0 else min(100.0, (atual / alvo) * 100.0)
    return html.Div([
        dbc.Progress(value=pct, striped=True, animated=True, label=f"{pct:0.1f}% da meta atingida", className="mb-2"),
        dbc.Row([
            dbc.Col(dbc.Badge(f"Meta: {fmt_brl(alvo)}", color="primary"), md="auto"),
            dbc.Col(dbc.Badge(f"Atual: {fmt_brl(atual)}", color="secondary"), md="auto"),
            dbc.Col(dbc.Badge(f"Falta: {fmt_brl(falta)}", color="warning"), md="auto"),
            dbc.Col(dbc.Badge(f"Meses na meta: {int(meses)}", color="info"), md="auto"),
        ], className="g-1"),
        html.Small("Dica: complete a reserva antes de assumir mais risco.", className="text-muted")
    ])

# --------- Renda Fixa (CDI) ---------
@callback(
    Output("rf-graf","figure"),
    Input("rf-run","n_clicks"),
    State("rf-pct-cdi","value"), State("rf-cdi-aa","value"),
    State("rf-anos","value"), State("rf-v0","value"), State("rf-aporte","value"),
    State("rf-inflacao","value"), State("rf-isento","value"),
    prevent_initial_call=True
)
def _rf_run(n, pct, cdi_aa, anos, v0, aporte, infl, isento):
    df = renda_fixa_cdi(
        valor_inicial=float(v0 or 0), aporte_mensal=float(aporte or 0),
        anos=int(anos or 1), cdi_aa=float((cdi_aa or 0)/100.0),
        pct_cdi=float((pct or 0)/100.0), inflacao_aa=float((infl or 0)/100.0),
        isento_ir=bool(isento and 1 in isento),
    )
    if df.empty:
        return go.Figure().update_layout(title="Sem dados")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Data"], y=df["Nominal"], name="Nominal", mode="lines"))
    fig.add_trace(go.Scatter(x=df["Data"], y=df["Real"], name="Real (descontado)", mode="lines", line=dict(dash="dot")))
    fig.update_layout(title="Renda Fixa – Evolução líquida", hovermode="x unified", yaxis_tickprefix="R$ ")
    return fig

# --------- DCA × Aporte Único ---------
@callback(
    Output("dca-graf","figure"),
    Input("dca-run","n_clicks"),
    State("dca-v0","value"), State("dca-aporte","value"),
    State("dca-meses","value"), State("dca-taxa","value"), State("dca-inflacao","value"),
    prevent_initial_call=True
)
def _dca_run(n, v0, aporte, meses, taxa, infl):
    df = dca_vs_lumpsum(
        valor_inicial=float(v0 or 0), aporte_total=float(aporte or 0),
        meses=int(meses or 1), taxa_anual=float((taxa or 0)/100.0),
        inflacao_anual=float((infl or 0)/100.0),
    )
    if df.empty:
        return go.Figure().update_layout(title="Sem dados")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Data"], y=df["LS_Nominal"], name="Aporte Único (Nominal)", mode="lines"))
    fig.add_trace(go.Scatter(x=df["Data"], y=df["DCA_Nominal"], name="DCA (Nominal)", mode="lines"))
    fig.add_trace(go.Scatter(x=df["Data"], y=df["LS_Real"], name="Aporte Único (Real)", mode="lines", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=df["Data"], y=df["DCA_Real"], name="DCA (Real)", mode="lines", line=dict(dash="dot")))
    fig.update_layout(title="DCA × Aporte Único", hovermode="x unified", yaxis_tickprefix="R$ ")
    return fig

# --------- Financiamento PRICE × SAC ---------
@callback(
    Output("fin-graf","figure"),
    Output("fin-kpis","children"),
    Input("fin-run","n_clicks"),
    State("fin-valor","value"), State("fin-anos","value"), State("fin-taxa","value"),
    prevent_initial_call=True
)
def _fin_run(n, valor, anos, taxa):
    valor = float(valor or 0); anos = int(anos or 1); taxa = float((taxa or 0)/100.0)
    df_p = price_schedule(valor, anos, taxa)
    df_s = sac_schedule(valor, anos, taxa)

    fig = go.Figure()
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p["Mes"], y=df_p["Parcela"], name="PRICE", mode="lines"))
    if not df_s.empty:
        fig.add_trace(go.Scatter(x=df_s["Mes"], y=df_s["Parcela"], name="SAC", mode="lines"))
    fig.update_layout(title="Evolução da Parcela – PRICE × SAC",
                      xaxis_title="Mês", yaxis_tickprefix="R$ ", hovermode="x unified")

    k_p = financiamento_kpis(df_p); k_s = financiamento_kpis(df_s)
    cards = dbc.Row([
        dbc.Col(dbc.Alert([html.B("PRICE – Juros totais: "), fmt_brl(k_p["total_juros"])], color="secondary"), md=6),
        dbc.Col(dbc.Alert([html.B("SAC – Juros totais: "), fmt_brl(k_s["total_juros"])], color="secondary"), md=6),
        dbc.Col(dbc.Alert([html.B("PRICE – Parcela média: "), fmt_brl(k_p["parcela_media"])], color="light"), md=6),
        dbc.Col(dbc.Alert([html.B("SAC – 1ª Parcela: "), fmt_brl(df_s["Parcela"].iloc[0] if not df_s.empty else 0.0)], color="light"), md=6),
    ], className="g-2")
    return fig, cards

# --------- Objetivo & SWR ---------
@callback(
    Output("goal-kpis", "children"),
    Output("goal-graf", "figure"),
    Input("goal-run", "n_clicks"),
    State("goal-meta", "value"),
    State("goal-anos", "value"),
    State("goal-taxa", "value"),
    State("goal-v0", "value"),
    prevent_initial_call=True
)
def _goal_calc(n, meta, anos, taxa, v0):
    meta = float(meta or 0); anos = int(anos or 1); taxa = float((taxa or 0)/100.0); v0 = float(v0 or 0)
    aporte_m = necessidade_aporte(meta_final=meta, anos=anos, taxa_aa=taxa, valor_inicial=v0)
    df = sim_serie_aporte(valor_inicial=v0, aporte_mensal=aporte_m, anos=anos, taxa_aa=taxa)

    final = float(df["Patrimonio"].iloc[-1]) if not df.empty else 0.0
    kpis = dbc.Row([
        dbc.Col(dbc.Alert([html.B("Aporte mensal sugerido: "), fmt_brl(aporte_m)], color="primary"), md=12),
        dbc.Col(dbc.Alert([html.B("Patrimônio final estimado: "), fmt_brl(final)], color="light"), md=12),
    ], className="g-2")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Data"], y=df["Patrimonio"], mode="lines", name="Patrimônio (nominal)"))
    fig.update_layout(title="Evolução com aporte sugerido", hovermode="x unified", yaxis_tickprefix="R$ ")
    return kpis, fig

@callback(
    Output("swr-kpi", "children"),
    Input("swr-run", "n_clicks"),
    State("swr-patr", "value"),
    State("swr-aa", "value"),
    prevent_initial_call=True
)
def _swr_calc(n, patr, swr_aa):
    patr = float(patr or 0); swr_aa = float((swr_aa or 0)/100.0)
    retirada_m = swr_meta(patrimonio=patr, swr_anual=swr_aa)
    return dbc.Alert([html.B("Retirada mensal sustentável: "), fmt_brl(retirada_m)], color="success")

# --------- Crescimento & Monte Carlo ---------
@callback(
    Output("sim-g1", "figure"),
    Output("sim-g2", "figure"),
    Output("sim-table", "data"),
    Input("sim-run", "n_clicks"),
    State("sim-v0", "value"),
    State("sim-aporte", "value"),
    State("sim-anos", "value"),
    State("sim-taxa", "value"),
    State("sim-inflacao", "value"),
    State("sim-vol", "value"),
    State("sim-npaths", "value"),
    prevent_initial_call=True
)
def _run_main(n, v0, aporte, anos, taxa, infl, vol, npaths):
    p = ParametrosSimulacao(
        valor_inicial=float(v0 or 0),
        aporte_mensal=float(aporte or 0),
        taxa_anual=float((taxa or 0) / 100.0),
        inflacao_anual=float((infl or 0) / 100.0),
        anos=int(anos or 1),
    )
    df_c = sim_compostos(p)
    df_s = sim_so_guardar(p)
    df_mc = sim_monte_carlo(p, vol_anual=float((vol or 0)/100.0), n_paths=int(npaths or 500))

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_s["Data"], y=df_s["Acumulado"], name="Só guardar", mode="lines"))
    fig1.add_trace(go.Scatter(x=df_c["Data"], y=df_c["Nominal"], name="Compostos (Nominal)", mode="lines"))
    fig1.add_trace(go.Scatter(x=df_c["Data"], y=df_c["Real"], name="Compostos (Real)", mode="lines", line=dict(dash="dot")))
    fig1.update_layout(yaxis_tickprefix="R$ ", hovermode="x unified", legend=dict(orientation="h"))

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_mc["Data"], y=df_mc["p95"], name="p95", mode="lines"))
    fig2.add_trace(go.Scatter(x=df_mc["Data"], y=df_mc["p50"], name="p50 (mediana)", mode="lines"))
    fig2.add_trace(go.Scatter(x=df_mc["Data"], y=df_mc["p5"], name="p5", mode="lines", fill="tonexty"))
    fig2.update_layout(yaxis_tickprefix="R$ ", hovermode="x unified")

    df_tab = pd.DataFrame({
        "Data": df_c["Data"].dt.strftime("%Y-%m"),
        "SemJuros": df_s["Acumulado"],
        "Nominal": df_c["Nominal"],
        "Real": df_c["Real"],
    })
    data = pd.concat([df_tab.head(6), df_tab.tail(6)]).to_dict("records")
    return fig1, fig2, data

# --------- Forecast de fluxo (12m) ---------
@callback(
    Output("fore-graph", "figure"),
    Input("fore-metodo", "value"),
)
def _fore_graph(metodo):
    df = forecast_cashflow(meses=12, metodo=metodo)
    if df.empty:
        return go.Figure().update_layout(title="Sem dados suficientes")
    fig = px.line(df, x="Data", y="Valor", color="Tipo", markers=True, title="Fluxo líquido: histórico vs previsão")
    fig.update_layout(yaxis_tickprefix="R$ ")
    return fig
