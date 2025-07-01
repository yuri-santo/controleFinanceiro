from dash import html, dcc
from dash.dependencies import Input, Output, State
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
from app import app
from services.globals import *

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": "50px",
    "margin": "auto",
}

# =========  Layout  =========== #
layout = dbc.Col(
    [
        dcc.Store(id="storeReceitas", data=dfReceitas.to_dict()),
        dcc.Store(id="storeDespesas", data=dfDespesas.to_dict()),
        dcc.Store(id="storeInvestimentos", data=dfInvestimentos.to_dict()),
        dcc.Store(id="storeCatReceita", data=dfCatReceitas.to_dict()),
        dcc.Store(id="storeCatDespesas", data=dfCatDespesas.to_dict()),
        dcc.Store(id="storeCatInvestimentos", data=dfCatInvestimentos.to_dict()),
        dbc.Row(
            [
                dbc.Col(
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                [
                                    html.Legend(
                                        "Saldo Patrimonial", className="text-center"
                                    ),
                                    html.H5(
                                        "R$ 1.000.000,00",
                                        id="patrimonioDashboard",
                                        style={},
                                    ),
                                ],
                                style={"padding": "10px", "margin": "10px"},
                            ),
                            dbc.Card(
                                html.Div(className="fa fa-university", style=card_icon),
                                color="warning",
                                style={
                                    "maxWidth": 75,
                                    "height": 100,
                                    "margin-left": "-10px",
                                    "margin-top": "10px",
                                },
                            ),
                        ]
                    ),
                ),
                dbc.Col(
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                [
                                    html.Legend(
                                        "Saldo Investido", className="text-center"
                                    ),
                                    html.H5(
                                        "R$ 1.500.000,00",
                                        id="investidoDashboard",
                                        style={},
                                    ),
                                ],
                                style={"padding": "10px", "margin": "10px"},
                            ),
                            dbc.Card(
                                html.Div(className="fa fa-money", style=card_icon),
                                color="success",
                                style={
                                    "maxWidth": 75,
                                    "height": 100,
                                    "margin-left": "-10px",
                                    "margin-top": "10px",
                                },
                            ),
                        ]
                    ),
                ),
                dbc.Col(
                    dbc.CardGroup(
                        [
                            dbc.Card(
                                [
                                    html.Legend("Despesas", className="text-center"),
                                    html.H5(
                                        "R$ 500.000,00",
                                        id="despesaDashboard",
                                        style={},
                                    ),
                                ],
                                style={"padding": "10px", "margin": "10px"},
                            ),
                            dbc.Card(
                                html.Div(className="fa fa-meh-o", style=card_icon),
                                color="danger",
                                style={
                                    "maxWidth": 75,
                                    "height": 100,
                                    "margin-left": "-10px",
                                    "margin-top": "10px",
                                },
                            ),
                        ]
                    ),
                ),
            ]
        ),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    html.Legend("Filtrar lancamentos", className="card-title"),
                    html.Label("Categorias das receitas"),
                    html.Div(
                        dcc.Dropdown(
                            id="dropdownReceita",
                            clearable=False,
                            style={"width": "100%"},
                            persistence=True,
                            persistence_type="session",
                            multi=True,)
                        ),
                    html.Label("Categorias das despesas"),
                    html.Div(
                        dcc.Dropdown(
                            id="dropdownDespesa",
                            clearable=False,
                            style={"width": "100%"},
                            persistence=True,
                            persistence_type="session",
                            multi=True,)
                        ),
                    html.Label("Categorias dos investimentos"),
                    html.Div(
                        dcc.Dropdown(
                            id="dropdownInvestimento",
                            clearable=False,
                            style={"width": "100%"},
                            persistence=True,
                            persistence_type="session",
                            multi=True,)
                        ),
                    html.Label("Período de análise", style={"margin-top": "10px"}),
                    dcc.DatePickerRange(
                        id="datePickerRange",
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today(),
                        display_format="DD/MM/YYYY",
                        style={'z-index':'100'}),
                ], style={'height': "100%", 'padding': '25px'})
            ], width=4),

            dbc.Col(
                dbc.Card(dcc.Graph(id='graph1'), style={'height': '100%', 'padding': '10px'}), width=8
            )
        ], style={'margin':'10px'}),

        dbc.Row([
            dbc.Col(dbc.Card(dcc.Graph(id='graph2'), style={'padding': '10px'}), width=6),
            dbc.Col(dbc.Card(dcc.Graph(id='graph3'), style={'padding': '10px'}), width=3),
            dbc.Col(dbc.Card(dcc.Graph(id='graph4'), style={'padding': '10px'}), width=3),
        ])
    ]
)


# =========  Callbacks  =========== #
@app.callback(
    [
        Output('dropdownReceita', 'options'),
        Output('dropdownReceita', 'value'),
        Output('patrimonioDashboard', 'children')
    ],
    [
        Input('storeReceitas', 'data'),
        Input('storeDespesas', 'data'),
        Input('storeInvestimentos', 'data'),
    ]
)
def popularDropdownReceita(receitas, despesas, investimentos):
    dfReceitas = pd.DataFrame(receitas)
    dfDespesas = pd.DataFrame(despesas)
    dfInvestimentos = pd.DataFrame(investimentos)

    valReceitas = dfReceitas["Categoria"].unique().tolist() if not dfReceitas.empty else []
    totalReceitas = dfReceitas["Valor"].sum() if "Valor" in dfReceitas.columns else 0
    totalDespesas = dfDespesas["Valor"].sum() if "Valor" in dfDespesas.columns else 0
    totalInvestimentos = dfInvestimentos["Valor"].sum() if "Valor" in dfInvestimentos.columns else 0

    saldoPatrimonial = totalReceitas - totalDespesas - totalInvestimentos

    return (
        [{'label': x, 'value': x} for x in valReceitas],
        valReceitas,
        f"R$ {saldoPatrimonial:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


@app.callback(
    [
        Output('dropdownDespesa', 'options'),
        Output('dropdownDespesa', 'value'),
        Output('dropdownInvestimento', 'options'),
        Output('dropdownInvestimento', 'value'),

        Output('despesaDashboard', 'children'),
        Output('investidoDashboard', 'children'),
    ],
    [
        Input('storeDespesas', 'data'),
        Input('storeInvestimentos', 'data'),
    ]
)
def atualizarDespesasInvestimentos(dataDespesas, dataInvestimentos):
    dfDespesas = pd.DataFrame(dataDespesas)
    valDespesas = dfDespesas["Categoria"].unique().tolist() if not dfDespesas.empty else []
    totalDespesas = dfDespesas["Valor"].sum() if "Valor" in dfDespesas.columns else 0

    dfInvestimentos = pd.DataFrame(dataInvestimentos)
    valInvestimentos = dfInvestimentos["Categoria"].unique().tolist() if not dfInvestimentos.empty else []
    totalInvestimentos = dfInvestimentos["Valor"].sum() if "Valor" in dfInvestimentos.columns else 0

    return (
        
        [{'label': x, 'value': x} for x in valDespesas], valDespesas,
        [{'label': x, 'value': x} for x in valInvestimentos], valInvestimentos,

        
        f"R$ {totalDespesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"R$ {totalInvestimentos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )





# ========= Funções auxiliares ========= #
def gerar_divididas(df):
    novas_linhas = []
    for _, row in df.iterrows():
        if row.get("Dividida", False) and pd.notnull(row.get("QtdParcelas")):
            valor_parcela = row["Valor"] / int(row["QtdParcelas"])
            for i in range(int(row["QtdParcelas"])):
                nova_data = (pd.to_datetime(row["Data"]) + pd.DateOffset(months=i)).normalize()
                novas_linhas.append({**row, "Data": nova_data, "Valor": valor_parcela})
        else:
            novas_linhas.append(row)
    return pd.DataFrame(novas_linhas)

def gerar_recorrentes(df):
    novas_linhas = []
    for _, row in df.iterrows():
        if row.get("Recorrente", False):
            base_data = pd.to_datetime(row["Data"])
            for i in range(12 - base_data.month + 1):
                nova_data = (base_data + pd.DateOffset(months=i)).normalize()
                novas_linhas.append({**row, "Data": nova_data})
        else:
            novas_linhas.append(row)
    return pd.DataFrame(novas_linhas)

# ========= Callback de Gráficos ========= #
@app.callback(
    [
        Output('graph1', 'figure'),  
        Output('graph2', 'figure'),  
        Output('graph3', 'figure'),  
        Output('graph4', 'figure')   
    ],
    [
        Input('storeReceitas', 'data'),
        Input('storeDespesas', 'data'),
        Input('storeInvestimentos', 'data'),
        Input('dropdownReceita', 'value'),
        Input('dropdownDespesa', 'value'),
        Input('dropdownInvestimento', 'value'),
        Input('datePickerRange', 'start_date'),
        Input('datePickerRange', 'end_date')
    ]
)
def atualizarGraficos(receitas, despesas, investimentos, catRec, catDesp, catInv, start, end):
    # Conversão de datas do filtro
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    # Carrega DataFrames
    dfReceitas = pd.DataFrame(receitas)
    dfDespesas = pd.DataFrame(despesas)
    dfInvestimentos = pd.DataFrame(investimentos)

    # Converte colunas para datetime e valores numéricos
    for df in [dfReceitas, dfDespesas, dfInvestimentos]:
        if not df.empty:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    # Filtro de período e categorias
    dfRec = dfReceitas.copy()
    if not dfRec.empty:
        dfRec = dfRec[
            (dfRec["Data"] >= start) &
            (dfRec["Data"] <= end) &
            (dfRec["Categoria"].isin(catRec))
        ]

    dfDesp = dfDespesas.copy()
    if not dfDesp.empty:
        dfDesp = dfDesp[
            (dfDesp["Data"] >= start) &
            (dfDesp["Data"] <= end) &
            (dfDesp["Categoria"].isin(catDesp))
        ]

    dfInv = dfInvestimentos.copy()
    if not dfInv.empty:
        dfInv = dfInv[
            (dfInv["Data"] >= start) &
            (dfInv["Data"] <= end) &
            (dfInv["Categoria"].isin(catInv))
        ]

    # Agrupamento por mês
    dfRecGroup = (
        dfRec.assign(AnoMes=dfRec["Data"].dt.to_period("M").dt.to_timestamp())
        .groupby("AnoMes")["Valor"].sum()
        .reset_index(name="Receitas")
    ) if not dfRec.empty else pd.DataFrame(columns=["AnoMes", "Receitas"])

    dfDespGroup = (
        dfDesp.assign(AnoMes=dfDesp["Data"].dt.to_period("M").dt.to_timestamp())
        .groupby("AnoMes")["Valor"].sum()
        .reset_index(name="Despesas")
    ) if not dfDesp.empty else pd.DataFrame(columns=["AnoMes", "Despesas"])

    dfInvGroup = (
        dfInv.assign(AnoMes=dfInv["Data"].dt.to_period("M").dt.to_timestamp())
        .groupby("AnoMes")["Valor"].sum()
        .reset_index(name="Investimentos")
    ) if not dfInv.empty else pd.DataFrame(columns=["AnoMes", "Investimentos"])

    # Merge dos dados
    dfMerged = pd.merge(dfRecGroup, dfDespGroup, on="AnoMes", how="outer")
    dfMerged = pd.merge(dfMerged, dfInvGroup, on="AnoMes", how="outer")
    dfMerged = dfMerged.fillna(0).infer_objects(copy=False).sort_values("AnoMes")

    # Cálculo dos acumulados
    dfMerged["SaldoMes"] = dfMerged["Receitas"] - dfMerged["Despesas"] + dfMerged["Investimentos"]
    dfMerged["SaldoAcumulado"] = dfMerged["SaldoMes"].cumsum()
    dfMerged["DespesasAcumuladas"] = dfMerged["Despesas"].cumsum()
    dfMerged["InvestimentosAcumulados"] = dfMerged["Investimentos"].cumsum()

    # Gráfico de linha (Evolução Financeira)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dfMerged["AnoMes"], y=dfMerged["SaldoAcumulado"], mode="lines+markers", name="Saldo Acumulado"))
    fig1.add_trace(go.Scatter(x=dfMerged["AnoMes"], y=dfMerged["DespesasAcumuladas"], mode="lines+markers", name="Despesas Acumuladas"))
    fig1.add_trace(go.Scatter(x=dfMerged["AnoMes"], y=dfMerged["InvestimentosAcumulados"], mode="lines+markers", name="Investimentos Acumulados"))
    fig1.update_layout(title="Evolução Financeira Mensal", xaxis_title="Mês", yaxis_title="Valor (R$)")

    # Gráficos de pizza
    fig2 = px.pie(dfDesp, values="Valor", names="Categoria", title="Distribuição das Despesas") if not dfDesp.empty else px.pie(title="Sem dados de Despesas")
    fig3 = px.pie(dfInv, values="Valor", names="Categoria", title="Distribuição dos Investimentos") if not dfInv.empty else px.pie(title="Sem dados de Investimentos")

    # Gráfico de barras
    fig4 = px.bar(
        x=["Receitas", "Despesas", "Investimentos"],
        y=[dfRec["Valor"].sum(), dfDesp["Valor"].sum(), dfInv["Valor"].sum()],
        color=["Receitas", "Despesas", "Investimentos"],
        title="Comparativo Geral",
        labels={"x": "Tipo", "y": "Total"}
    )

    return fig1, fig2, fig3, fig4
