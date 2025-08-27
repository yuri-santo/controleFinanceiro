# components/dashboards.py
from __future__ import annotations

from dash import html, dcc
from dash.dependencies import Input, Output
from datetime import date
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from app import app
from services.globals import (
    dfReceitas, dfDespesas, dfInvestimentos,
    dfCatReceitas, dfCatDespesas, dfCatInvestimentos,
    fmt_brl, filter_period_and_categories
)

# ================== Layout ==================
card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": "42px",
    "margin": "auto",
}

kpi_value_style = {"fontWeight": "600", "fontSize": "20px", "marginTop": "2px"}
kpi_card_style = {"padding": "10px", "margin": "10px", "height": "100%"}

layout = dbc.Col(
    [
        # Linha de KPIs (6 cartões)
        dbc.Row(
            [
                # Saldo Patrimonial
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Saldo Patrimonial"),
                                html.Div(id="kpi-saldo", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-university", style=card_icon),
                                 color="warning", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
                # Total Receitas
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Receitas"),
                                html.Div(id="kpi-receitas", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-arrow-up", style=card_icon),
                                 color="success", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
                # Total Despesas
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Despesas"),
                                html.Div(id="kpi-despesas", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-arrow-down", style=card_icon),
                                 color="danger", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
                # Media Guardada
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Média Guardada"),
                                html.Div(id="kpi-sr", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-pie-chart", style=card_icon),
                                 color="primary", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
                # Média gasta (média 3M)
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Média gasta (média 3M)"),
                                html.Div(id="kpi-burn", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-fire", style=card_icon),
                                 color="secondary", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
                # Tempo de sobrevivência
                dbc.Col(
                    dbc.CardGroup([
                        dbc.Card(
                            [
                                html.Small("Tempo de sobrevivência (meses)"),
                                html.Div(id="kpi-runway", style=kpi_value_style),
                            ], style=kpi_card_style
                        ),
                        dbc.Card(html.Div(className="fa fa-clock-o", style=card_icon),
                                 color="info", style={"maxWidth": 72, "height": 96,
                                 "marginLeft": "-10px", "marginTop": "10px"}),
                    ])
                ),
            ], className="g-0"
        ),

        # Filtros e gráfico principal
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Legend("Filtrar lançamentos", className="card-title"),
                                html.Label("Categorias das receitas"),
                                dcc.Dropdown(
                                    id="dropdownReceita",
                                    clearable=False,
                                    style={"width": "100%"},
                                    persistence=True,
                                    persistence_type="session",
                                    multi=True,
                                ),
                                html.Label("Categorias das despesas", className="mt-3"),
                                dcc.Dropdown(
                                    id="dropdownDespesa",
                                    clearable=False,
                                    style={"width": "100%"},
                                    persistence=True,
                                    persistence_type="session",
                                    multi=True,
                                ),
                                html.Label("Categorias dos investimentos", className="mt-3"),
                                dcc.Dropdown(
                                    id="dropdownInvestimento",
                                    clearable=False,
                                    style={"width": "100%"},
                                    persistence=True,
                                    persistence_type="session",
                                    multi=True,
                                ),
                                html.Label("Período de análise", style={"marginTop": "10px"}),
                                dcc.DatePickerRange(
                                    id="datePickerRange",
                                    start_date=date.today(),
                                    end_date=date.today(),
                                    display_format="DD/MM/YYYY",
                                    style={"zIndex": "100"},
                                ),
                            ]
                        ),
                        style={"height": "100%", "padding": "10px"},
                    ),
                    width=4,
                ),
                dbc.Col(
                    dbc.Card(dcc.Graph(id="graph-cashflow"), style={"height": "100%", "padding": "10px"}),
                    width=8,
                ),
            ],
            style={"margin": "10px"},
        ),

        # Linhas de gráficos secundários
        dbc.Row(
            [
                dbc.Col(dbc.Card(dcc.Graph(id="graph-treemap"), style={"padding": "10px"}), width=5),
                dbc.Col(dbc.Card(dcc.Graph(id="graph-heatmap"), style={"padding": "10px"}), width=4),
                dbc.Col(dbc.Card(dcc.Graph(id="graph-savings"), style={"padding": "10px"}), width=3),
            ], className="g-2", style={"margin": "2px 10px"}
        ),

        dbc.Row(
            [
                dbc.Col(dbc.Card(dcc.Graph(id="graph-comparativo"), style={"padding": "10px"}), width=4),
                dbc.Col(dbc.Card(dcc.Graph(id="graph-top10"), style={"padding": "10px"}), width=8),
            ], className="g-2", style={"margin": "2px 10px"}
        ),

        # Insights automáticos
        dbc.Card(
            dbc.CardBody([
                html.H5("Insights do período"),
                html.Ul(id="insights")
            ]), className="m-3"
        ),
    ],
    className="p-3",
)

# ================== Helpers ==================
def _to_df(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data)
    if df.empty:
        return df
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.normalize()
    if "Valor" in df.columns:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0).astype("float64")
    if "Categoria" in df.columns:
        df["Categoria"] = df["Categoria"].astype(str)
    return df

def _group_month(df: pd.DataFrame, colname: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["AnoMes", colname])
    g = (
        df.assign(AnoMes=df["Data"].dt.to_period("M").dt.to_timestamp())
          .groupby("AnoMes", as_index=False)["Valor"].sum()
          .rename(columns={"Valor": colname})
    )
    return g

def _ema(series: pd.Series, alpha: float = 0.35) -> pd.Series:
    if series.empty:
        return series
    return series.ewm(alpha=alpha, adjust=False).mean()

# ================== Callbacks ==================

# 0) Popular categorias
@app.callback(
    [Output("dropdownReceita", "options"), Output("dropdownReceita", "value")],
    [Input("storeReceitas", "data")],
)
def popularDropdownReceita(receitas):
    dfR = _to_df(receitas)
    valores = dfR["Categoria"].dropna().astype(str).unique().tolist() if not dfR.empty else []
    return ([{"label": x, "value": x} for x in valores], valores)

@app.callback(
    [
        Output("dropdownDespesa", "options"),
        Output("dropdownDespesa", "value"),
        Output("dropdownInvestimento", "options"),
        Output("dropdownInvestimento", "value"),
    ],
    [Input("storeDespesas", "data"), Input("storeInvestimentos", "data")],
)
def popularDropdownsDespesasInvest(dataDespesas, dataInvestimentos):
    dfD = _to_df(dataDespesas)
    dfI = _to_df(dataInvestimentos)
    valsD = dfD["Categoria"].dropna().astype(str).unique().tolist() if not dfD.empty else []
    valsI = dfI["Categoria"].dropna().astype(str).unique().tolist() if not dfI.empty else []
    return (
        [{"label": x, "value": x} for x in valsD], valsD,
        [{"label": x, "value": x} for x in valsI], valsI
    )

# 0.2) Ajusta período automático
@app.callback(
    [Output("datePickerRange", "start_date"), Output("datePickerRange", "end_date")],
    [Input("storeReceitas", "data"), Input("storeDespesas", "data"), Input("storeInvestimentos", "data")],
)
def inicializa_periodo(dataR, dataD, dataI):
    dfs = [_to_df(x) for x in (dataR, dataD, dataI)]
    datas = []
    for df in dfs:
        if not df.empty and "Data" in df.columns and df["Data"].notna().any():
            datas += [df["Data"].min(), df["Data"].max()]
    if not datas:
        today = pd.Timestamp.today().normalize()
        return today, today
    return min(datas), max(datas)

# 0.3) KPIs (inclui savings rate, burn e runway)
@app.callback(
    [
        Output("kpi-saldo", "children"),
        Output("kpi-receitas", "children"),
        Output("kpi-despesas", "children"),
        Output("kpi-sr", "children"),
        Output("kpi-burn", "children"),
        Output("kpi-runway", "children"),
    ],
    [
        Input("storeReceitas", "data"),
        Input("storeDespesas", "data"),
        Input("storeInvestimentos", "data"),
        Input("dropdownReceita", "value"),
        Input("dropdownDespesa", "value"),
        Input("dropdownInvestimento", "value"),
        Input("datePickerRange", "start_date"),
        Input("datePickerRange", "end_date"),
    ],
)
def atualizar_kpis(dataR, dataD, dataI, catRec, catDesp, catInv, start, end):
    dfR, dfD, dfI = _to_df(dataR), _to_df(dataD), _to_df(dataI)
    dfR_f = filter_period_and_categories(dfR, start, end, catRec or [])
    dfD_f = filter_period_and_categories(dfD, start, end, catDesp or [])
    dfI_f = filter_period_and_categories(dfI, start, end, catInv or [])

    totalR = float(dfR_f["Valor"].sum()) if "Valor" in dfR_f else 0.0
    totalD = float(dfD_f["Valor"].sum()) if "Valor" in dfD_f else 0.0
    totalI = float(dfI_f["Valor"].sum()) if "Valor" in dfI_f else 0.0

    saldo = totalR - totalD - totalI

    # Savings rate = (R - D - I) / R (quando R>0)
    sr = (saldo / totalR) if totalR > 0 else 0.0
    sr_txt = f"{sr*100:.1f}%"

    # Burn rate (média 3 meses de despesas)
    gD = _group_month(dfD_f, "Despesas")
    burn = float(_ema(gD["Despesas"], 0.5).tail(3).mean()) if not gD.empty else 0.0

    # Runway (meses) = saldo atual / burn
    runway = (saldo / burn) if burn > 0 else 0.0
    runway_txt = f"{runway:.1f}"

    return (
        fmt_brl(saldo),
        fmt_brl(totalR),
        fmt_brl(totalD),
        sr_txt,
        fmt_brl(burn),
        runway_txt,
    )

# 1) Gráficos + insights
@app.callback(
    [
        Output("graph-cashflow", "figure"),
        Output("graph-treemap", "figure"),
        Output("graph-heatmap", "figure"),
        Output("graph-savings", "figure"),
        Output("graph-comparativo", "figure"),
        Output("graph-top10", "figure"),
        Output("insights", "children"),
    ],
    [
        Input("storeReceitas", "data"),
        Input("storeDespesas", "data"),
        Input("storeInvestimentos", "data"),
        Input("dropdownReceita", "value"),
        Input("dropdownDespesa", "value"),
        Input("dropdownInvestimento", "value"),
        Input("datePickerRange", "start_date"),
        Input("datePickerRange", "end_date"),
    ],
)
def atualizar_graficos(receitas, despesas, investimentos, catRec, catDesp, catInv, start, end):
    dfR = _to_df(receitas)
    dfD = _to_df(despesas)
    dfI = _to_df(investimentos)

    dfRec = filter_period_and_categories(dfR, start, end, catRec or [])
    dfDesp = filter_period_and_categories(dfD, start, end, catDesp or [])
    dfInv = filter_period_and_categories(dfI, start, end, catInv or [])

    # Séries mensais
    gR = _group_month(dfRec, "Receitas")
    gD = _group_month(dfDesp, "Despesas")
    gI = _group_month(dfInv, "Investimentos")
    dfM = (
        pd.merge(pd.merge(gR, gD, on="AnoMes", how="outer"), gI, on="AnoMes", how="outer")
          .sort_values("AnoMes")
    )

    # >>> Corrige FutureWarning: downcasting em fillna
    # Converte explicitamente para numérico e dá fillna apenas nas colunas numéricas
    for col in ["Receitas", "Despesas", "Investimentos"]:
        dfM[col] = pd.to_numeric(dfM[col], errors="coerce")
    dfM[["Receitas", "Despesas", "Investimentos"]] = dfM[["Receitas", "Despesas", "Investimentos"]].fillna(0.0)
    dfM[["Receitas", "Despesas", "Investimentos"]] = dfM[["Receitas", "Despesas", "Investimentos"]].astype("float64")

    dfM["SaldoMes"] = dfM["Receitas"] - dfM["Despesas"] - dfM["Investimentos"]
    dfM["SaldoAcumulado"] = dfM["SaldoMes"].cumsum()
    dfM["SaldoEMA3"] = _ema(dfM["SaldoMes"], 0.5)

    # Graph Cashflow (barras empilhadas e linhas)
    fig1 = go.Figure()
    fig1.add_bar(x=dfM["AnoMes"], y=dfM["Receitas"], name="Receitas")
    fig1.add_bar(x=dfM["AnoMes"], y=-dfM["Despesas"], name="Despesas")
    fig1.add_bar(x=dfM["AnoMes"], y=-dfM["Investimentos"], name="Investimentos")
    fig1.add_scatter(x=dfM["AnoMes"], y=dfM["SaldoMes"], name="Saldo do mês", mode="lines+markers")
    fig1.add_scatter(x=dfM["AnoMes"], y=dfM["SaldoAcumulado"], name="Saldo acumulado", mode="lines")
    fig1.add_scatter(x=dfM["AnoMes"], y=dfM["SaldoEMA3"], name="Média móvel (3m)", mode="lines", line=dict(dash="dot"))
    fig1.update_layout(barmode="relative", hovermode="x unified", yaxis_tickprefix="R$ ",
                       title="Fluxo Mensal (R, D, I) + Saldo e Tendência")

    # Treemap de despesas
    if dfDesp.empty:
        fig2 = go.Figure(); fig2.update_layout(title="Treemap de Despesas por Categoria (sem dados)")
    else:
        tre = dfDesp.groupby("Categoria", as_index=False)["Valor"].sum().sort_values("Valor", ascending=False)
        fig2 = px.treemap(tre, path=["Categoria"], values="Valor", title="Despesas por Categoria (Treemap)")

    # Heatmap (mês × dia da semana) de despesas
    if dfDesp.empty:
        fig3 = px.imshow(np.array([[0]]), text_auto=True, title="Heatmap de Despesas (mês × dia)")
    else:
        tmp = dfDesp.copy()
        tmp["Mes"] = tmp["Data"].dt.to_period("M").dt.to_timestamp()
        tmp["DiaSem"] = tmp["Data"].dt.day_name(locale="pt_BR").str[:3]
        mat = tmp.pivot_table(index="DiaSem", columns="Mes", values="Valor", aggfunc="sum").fillna(0.0)
        # ordena dias (seg..dom)
        ordem = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        mapa = {"Seg": "Mon", "Ter": "Tue", "Qua": "Wed", "Qui": "Thu", "Sex": "Fri", "Sáb": "Sat", "Dom": "Sun"}
        mat["ordem"] = [ordem.index(mapa.get(x, "Mon")) if mapa.get(x) in ordem else 0 for x in mat.index]
        mat = mat.sort_values("ordem").drop(columns=["ordem"])
        fig3 = px.imshow(mat.values, aspect="auto",
                         x=[c.strftime("%Y-%m") for c in mat.columns], y=list(mat.index),
                         labels=dict(x="Mês", y="Dia da Semana", color="Despesas"),
                         title="Heatmap de Despesas (mês × dia)")
        fig3.update_layout(yaxis_title=None)

    # Rosquinha Savings Rate
    totalR = float(dfRec["Valor"].sum()) if not dfRec.empty else 0.0
    totalD = float(dfDesp["Valor"].sum()) if not dfDesp.empty else 0.0
    totalI = float(dfInv["Valor"].sum()) if not dfInv.empty else 0.0
    saldo = totalR - totalD - totalI
    savings = max(saldo, 0.0)
    spending = max(totalR - savings, 0.0)
    fig4 = px.pie(values=[savings, spending], names=["Poupança (saldo)", "Gastos"],
                  hole=0.6, title="Taxa de Poupança no Período")
    fig4.update_traces(textposition="inside", textinfo="percent+label")

    # Comparativo geral
    fig5 = px.bar(
        x=["Receitas", "Despesas", "Investimentos"],
        y=[totalR, totalD, totalI],
        title="Comparativo Geral (período selecionado)",
        labels={"x": "Tipo", "y": "Total"},
    )

    # Top 10 Despesas (barra horizontal) — placeholder seguro se vazio
    if dfDesp.empty:
        fig6 = go.Figure(); fig6.update_layout(title="Sem dados de Despesas")
    else:
        top = (dfDesp.groupby("Categoria", as_index=False)["Valor"].sum()
               .sort_values("Valor", ascending=False).head(10))
        fig6 = px.bar(top, x="Valor", y="Categoria", orientation="h", title="Top 10 Categorias de Despesas")

    # Insights automáticos
    insights = []
    if totalR > 0:
        sr = (saldo / totalR) * 100
        insights.append(html.Li(f"Savings Rate no período: {sr:.1f}%."))

    if not dfDesp.empty:
        top_all = (dfDesp.groupby("Categoria", as_index=False)["Valor"].sum()
                   .sort_values("Valor", ascending=False))
        if not top_all.empty:
            cat_top = top_all.iloc[0]["Categoria"]
            v_top = top_all.iloc[0]["Valor"]
            p_top = (v_top / totalD) * 100 if totalD else 0
            insights.append(html.Li(f"Categoria que mais pesa nas despesas: {cat_top} ({p_top:.1f}% do total)."))

    if not dfM.empty and (dfM["SaldoMes"] > 0).sum() + (dfM["SaldoMes"] < 0).sum() > 0:
        meses_pos = int((dfM["SaldoMes"] > 0).sum())
        meses_tot = int(len(dfM))
        insights.append(html.Li(f"Meses com saldo positivo: {meses_pos}/{meses_tot}."))

    if not dfM.empty:
        tendencia = dfM["SaldoEMA3"].iloc[-1] if not dfM["SaldoEMA3"].isna().all() else 0.0
        if tendencia > 0:
            insights.append(html.Li("Tendência recente do saldo mensal é de ALTA (média móvel 3m positiva)."))
        elif tendencia < 0:
            insights.append(html.Li("Tendência recente do saldo mensal é de BAIXA (média móvel 3m negativa)."))

    if savings == 0 and totalR > 0:
        insights.append(html.Li("Sem poupança líquida no período — reveja despesas/investimentos ou aumente receitas."))

    return fig1, fig2, fig3, fig4, fig5, fig6, insights
