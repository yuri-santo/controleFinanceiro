# components/extratos.py
from __future__ import annotations

from dash import html, dcc, dash_table, no_update, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import re

from app import app
from services.globals import (
    dfReceitas, dfDespesas, dfInvestimentos,
    dfCatDespesas, dfCatReceitas, dfCatInvestimentos,
    fmt_brl, filter_period_and_categories, series_by_period,
    load_receitas, load_despesas, load_investimentos,
    update_receita_row, update_despesa_row, update_invest_row,
    append_receitas, append_despesas, append_investimentos,
)

# tenta importar operações de exclusão em massa
try:
    from services.globals import delete_receitas, delete_despesas, delete_investimentos
except Exception:
    delete_receitas = delete_despesas = delete_investimentos = None


# ========================== Helpers ==========================
EDITABLE_REC  = {"Valor","Recebido","Recorrente","Data","Categoria","Descrição"}
EDITABLE_DESP = {"Valor","Pago","Fixo","Data","Categoria","Descrição"}
EDITABLE_INV  = {"Valor","Data","Categoria","Descrição"}

PALETTE = px.colors.qualitative.Set3 + px.colors.qualitative.Safe + px.colors.qualitative.Pastel

def _cat_color_map(cats_iter):
    cats = [str(c) for c in list(dict.fromkeys(cats_iter))]
    m = {}
    for c in cats:
        m[c] = PALETTE[hash(c) % len(PALETTE)]
    return m

def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty: return df
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.normalize()
    if "Valor" in df.columns:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
    for c in ("Categoria","Descrição"):
        if c in df.columns: df[c] = df[c].astype(str)
    return df

def _fmt_fig_currency(fig, title=None):
    if title: fig.update_layout(title=title)
    fig.update_layout(yaxis_tickformat="R$,.2f")
    fig.update_traces(hovertemplate="%{x}<br>Valor: R$ %{y:.2f}<extra></extra>")
    return fig

def _datatable(df: pd.DataFrame, table_id: str, editable_cols: set[str]):
    cols = [{"name": c, "id": c, "editable": c in editable_cols} for c in df.columns]
    hidden = [c for c in df.columns if c in ("id","Valor_num")]
    style_cond = [{"if": {"column_id": "Valor"}, "textAlign": "right"}]
    if "Anomalia" in df.columns:
        style_cond.append({"if": {"filter_query": "{Anomalia} = '⚠️'"}, "backgroundColor": "#fff3cd"})
    return dash_table.DataTable(
        id=table_id,
        columns=cols,
        data=df.to_dict("records"),
        page_size=15,
        sort_action="native",
        filter_action="native",
        editable=True,
        row_selectable="multi",
        selected_rows=[],
        hidden_columns=hidden,
        style_table={"overflowX": "auto", "overflowY": "auto", "maxHeight": "60vh"},
        style_cell={"fontFamily": "Montserrat, Arial", "fontSize": "14px", "padding": "8px"},
        style_header={"fontWeight": "600", "position":"sticky", "top":0, "zIndex":1, "backgroundColor":"#fff"},
        style_data_conditional=style_cond,
    )

def _update_slider(df: pd.DataFrame):
    if df.empty or "Valor" not in df:
        return 0, 0, [0, 0], "R$ 0,00 – R$ 0,00"
    vmin = float(df["Valor"].min()); vmax = float(df["Valor"].max())
    return vmin, vmax, [vmin, vmax], f"{fmt_brl(vmin)} – {fmt_brl(vmax)}"

def _apply_extra_filters(df: pd.DataFrame, so_status=False, campo_status=None,
                         desc_contains=None, valor_min=None, valor_max=None) -> pd.DataFrame:
    if df.empty: return df
    f = df.copy()
    if so_status and campo_status and campo_status in f.columns: f = f[f[campo_status] == 1]
    if desc_contains:
        s = str(desc_contains).strip().lower()
        if s and "Descrição" in f.columns: f = f[f["Descrição"].str.lower().str.contains(s, na=False)]
    if valor_min is not None: f = f[f["Valor"] >= float(valor_min)]
    if valor_max is not None: f = f[f["Valor"] <= float(valor_max)]
    return f

def _prev_window(start, end):
    if not start or not end: return None, None
    s = pd.to_datetime(start).normalize(); e = pd.to_datetime(end).normalize()
    delta = (e - s).days + 1
    prev_end = s - pd.offsets.Day(1); prev_start = prev_end - pd.offsets.Day(delta - 1)
    return prev_start, prev_end

def kpi_delta_card(title: str, atual: float, anterior: float, good_when: str = "up"):
    delta = (atual - anterior); perc = (delta / anterior * 100.0) if anterior else None
    trend = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
    good = (delta > 0) if good_when == "up" else (delta < 0)
    cor = "success" if good else ("danger" if delta != 0 else "secondary")
    txt_perc = f" ({perc:.1f}%)" if perc is not None else ""
    return dbc.Card(dbc.CardBody([html.Small(title), html.H4(fmt_brl(atual), className="mt-1 mb-0"),
                                  html.Div(f"{trend} {fmt_brl(delta)}{txt_perc}", className=f"text-{cor}")]),
                    className="shadow-sm")

def apply_pareto(df_cat_sum: pd.DataFrame, on: str = "Valor", pct: float = 0.8):
    if df_cat_sum.empty: return df_cat_sum
    d = df_cat_sum.sort_values(on, ascending=False).copy()
    d["acum"] = d[on].cumsum() / d[on].sum()
    return d[d["acum"] <= pct]

def _parse_bool(v):
    if isinstance(v, (int, float)): return 1 if int(v) != 0 else 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1","true","sim","yes"): return 1
        if s in ("0","false","nao","não","no"): return 0
    if isinstance(v, bool): return 1 if v else 0
    return 0

# ----- normalização de payload (corrige warning de datas ISO do DataTable) -----
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

def _normalize_payload_for_update(row: dict, editable_cols: set[str]) -> dict:
    import math
    payload = {}
    for k, v in row.items():
        if k not in editable_cols:
            continue
        if k == "Valor":
            if isinstance(v, str):
                s = v.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                try: v = float(s)
                except Exception: continue
            if isinstance(v, (int, float)) and not math.isnan(v):
                payload[k] = float(v)
        elif k == "Data":
            try:
                if isinstance(v, str) and _ISO_RE.match(v):
                    d = pd.to_datetime(v, format="%Y-%m-%dT%H:%M:%S", errors="coerce")
                else:
                    d = pd.to_datetime(v, dayfirst=True, errors="coerce")
                if pd.isna(d): continue
                payload[k] = d.strftime("%Y-%m-%d")
            except Exception:
                continue
        elif k in ("Recebido","Recorrente","Pago","Fixo"):
            payload[k] = _parse_bool(v)
        elif isinstance(v, str):
            payload[k] = v.strip()
        else:
            payload[k] = v
    return payload

def _anomalias(df: pd.DataFrame) -> pd.Series:
    """Retorna série booleana: True se valor é anômalo (>2 desvios dentro da categoria)."""
    if df.empty or "Categoria" not in df.columns or "Valor" not in df.columns:
        return pd.Series([False]*len(df), index=df.index)
    z = (df["Valor"] - df.groupby("Categoria")["Valor"].transform("mean")) / df.groupby("Categoria")["Valor"].transform("std")
    return (z.abs() >= 2).fillna(False)


# ========================== Layout ==========================
layout = html.Div(
    [
        # boot & stores locais
        dcc.Interval(id="bootExtrato", n_intervals=0, max_intervals=1, interval=300),

        dcc.Store(id="storeReceitasExtrato", data=dfReceitas.to_dict()),
        dcc.Store(id="storeDespesasExtrato", data=dfDespesas.to_dict()),
        dcc.Store(id="storeInvestExtrato", data=dfInvestimentos.to_dict()),
        dcc.Store(id="storeExtratoProfiles", storage_type="local"),
        dcc.Store(id="storeMetasDesp", storage_type="local"),

        # toasts
        dbc.Toast("Receita atualizada!", id="toastEditRecOK",   is_open=False, duration=1500, icon="success",
                  style={"position":"fixed","top":10,"right":10,"zIndex":2000}),
        dbc.Toast("Erro ao atualizar Receita.", id="toastEditRecERR", is_open=False, duration=2500, icon="danger",
                  style={"position":"fixed","top":10,"right":10,"zIndex":2000}),
        dbc.Toast("Despesa atualizada!", id="toastEditDespOK",  is_open=False, duration=1500, icon="success",
                  style={"position":"fixed","top":50,"right":10,"zIndex":2000}),
        dbc.Toast("Erro ao atualizar Despesa.", id="toastEditDespERR", is_open=False, duration=2500, icon="danger",
                  style={"position":"fixed","top":50,"right":10,"zIndex":2000}),
        dbc.Toast("Investimento atualizado!", id="toastEditInvOK", is_open=False, duration=1500, icon="success",
                  style={"position":"fixed","top":90,"right":10,"zIndex":2000}),
        dbc.Toast("Erro ao atualizar Investimento.", id="toastEditInvERR", is_open=False, duration=2500, icon="danger",
                  style={"position":"fixed","top":90,"right":10,"zIndex":2000}),
        dbc.Toast("Linhas duplicadas!", id="toastDupOK", is_open=False, duration=1500, icon="info",
                  style={"position":"fixed","top":130,"right":10,"zIndex":2000}),
        dbc.Toast("Perfil salvo!", id="toastProfileOK", is_open=False, duration=1500, icon="primary",
                  style={"position":"fixed","top":170,"right":10,"zIndex":2000}),
        dbc.Toast("Registros excluídos!", id="toastDelOK", is_open=False, duration=1500, icon="warning",
                  style={"position":"fixed","top":210,"right":10,"zIndex":2000}),
        dbc.Toast("Falha ao excluir.", id="toastDelERR", is_open=False, duration=2500, icon="danger",
                  style={"position":"fixed","top":210,"right":10,"zIndex":2000}),

        # Filtros superiores
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4("Período"),
                        dcc.DatePickerRange(id="dprGlobal", display_format="DD/MM/YYYY", minimum_nights=0),
                        html.Div(
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("Mês atual", id="chipMesAtual", outline=True, color="secondary", size="sm"),
                                    dbc.Button("Últimos 3M", id="chipUlt3",  outline=True, color="secondary", size="sm"),
                                    dbc.Button("Ano atual",  id="chipAno",   outline=True, color="secondary", size="sm"),
                                    dbc.Button("12 meses",   id="chip12m",   outline=True, color="secondary", size="sm"),
                                    dbc.Button("Limpar",     id="chipLimpar",outline=True, color="secondary", size="sm"),
                                ]
                            ),
                            className="mt-2",
                        ),
                        dbc.RadioItems(
                            id="riAgruparPorGlobal",
                            options=[{"label":"Mensal","value":"M"},{"label":"Semanal","value":"W"},{"label":"Diário","value":"D"}],
                            value="M", inline=True, className="mt-2",
                        ),
                    ],
                    md=5,
                ),
                dbc.Col(
                    [
                        html.H4("Perfis de filtro"),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Dropdown(id="ddPerfil", placeholder="Selecione um perfil"), md=5),
                                dbc.Col(dbc.Input(id="inputPerfil", placeholder="Nome do perfil"), md=4),
                                dbc.Col(dbc.Button("Salvar perfil", id="btnSavePerfil", color="primary"), md=3),
                            ], className="g-2"
                        ),
                        dbc.ButtonGroup(
                            [
                                dbc.Button("Aplicar", id="btnApplyPerfil", size="sm", color="secondary", className="mt-1"),
                                dbc.Button("Excluir", id="btnDelPerfil",   size="sm", color="danger",    className="mt-1 ms-2"),
                            ]
                        ),
                    ],
                    md=7,
                ),
            ],
            className="mb-3",
        ),

        # ===== ABAS =====
        dcc.Tabs(
            id="tabsExtrato",
            value="tab-rec",
            children=[
                # ---------------- Receitas ----------------
                dcc.Tab(label="Receitas", value="tab-rec", children=[
                    html.Hr(), html.H3("Receitas"),
                    dbc.Row(id="kpis-receitas", className="mb-2"),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafTop10Rec"), md=6),
                            dbc.Col(dcc.Graph(id="grafTopDescRec"), md=6),
                        ]), type="default"
                    ),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafDOWRec"), md=4),
                            dbc.Col(dcc.Graph(id="grafSerieRec"), md=8),
                        ], className="mt-2"), type="default"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("Filtros"),
                                    dcc.Dropdown(
                                        id="ddCatRecExtrato",
                                        options=[{"label": c, "value": c} for c in dfCatReceitas["Categoria"].tolist()],
                                        multi=True, placeholder="Categorias"
                                    ),
                                    dbc.Checklist(id="chkParetoRec", options=[{"label":"Pareto 80/20","value":1}],
                                                  value=[], switch=True, className="mt-2"),
                                    dbc.Input(id="txtBuscaRec", placeholder="buscar descrição...", type="text", className="mt-2"),
                                    dbc.Checklist(id="chkRecebRec", options=[{"label":"Somente recebidas","value":1}],
                                                  value=[], switch=True, className="mt-2"),
                                    html.Small(id="rsValoresRecLabel", className="mt-2 d-block"),
                                    dcc.RangeSlider(id="rsValoresRec", step=1),
                                    html.Hr(),
                                    html.H6("Ações em massa"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Marcar RECEBIDA", id="btnRecMark", color="success", size="sm"),
                                            dbc.Button("Desmarcar", id="btnRecUnmark", color="secondary", size="sm"),
                                            dbc.Button("Duplicar selecionadas", id="btnRecDup", color="info", size="sm"),
                                            dbc.Button("Excluir selecionadas", id="btnRecDel", color="danger", size="sm"),
                                        ], className="mt-1", size="sm"
                                    ),
                                ], md=3
                            ),
                            dbc.Col(
                                dcc.Loading(
                                    _datatable(pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Recebido","Recorrente","Anomalia"]),
                                               "gridReceitas", EDITABLE_REC), type="default"
                                ), md=9
                            ),
                        ],
                        className="mt-2",
                    ),
                ]),

                # ---------------- Despesas ----------------
                dcc.Tab(label="Despesas", value="tab-desp", children=[
                    html.Hr(), html.H3("Despesas"),
                    dbc.Row(id="kpis-despesas", className="mb-2"),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafTop10Desp"), md=6),
                            dbc.Col(dcc.Graph(id="grafTopDescDesp"), md=6),
                        ]), type="default"
                    ),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafDOWDesp"), md=4),
                            dbc.Col(dcc.Graph(id="grafSerieDesp"), md=8),
                        ], className="mt-2"), type="default"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("Filtros"),
                                    dcc.Dropdown(
                                        id="ddCatDespExtrato",
                                        options=[{"label": c, "value": c} for c in dfCatDespesas["Categoria"].tolist()],
                                        multi=True, placeholder="Categorias"
                                    ),
                                    dbc.Checklist(id="chkParetoDesp", options=[{"label":"Pareto 80/20","value":1}],
                                                  value=[], switch=True, className="mt-2"),
                                    dbc.Input(id="txtBuscaDesp", placeholder="buscar descrição...", type="text", className="mt-2"),
                                    dbc.Checklist(id="chkPagoDesp", options=[{"label":"Somente pagas","value":1}],
                                                  value=[], switch=True, className="mt-2"),
                                    html.Small(id="rsValoresDespLabel", className="mt-2 d-block"),
                                    dcc.RangeSlider(id="rsValoresDesp", step=1),
                                    html.Hr(),
                                    html.H6("Metas (mês) • Despesas"),
                                    dcc.Dropdown(id="ddMetaCatDesp", placeholder="Categoria"),
                                    dbc.Input(id="inputMetaDesp", type="number", placeholder="Meta R$"),
                                    dbc.Button("Salvar Meta", id="btnSaveMetaDesp", size="sm", className="mt-2"),
                                    html.Div(id="divMetasDesp", className="mt-2"),
                                    html.Hr(),
                                    html.H6("Ações em massa"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Marcar PAGA", id="btnDespMark", color="success", size="sm"),
                                            dbc.Button("Desmarcar", id="btnDespUnmark", color="secondary", size="sm"),
                                            dbc.Button("Duplicar selecionadas", id="btnDespDup", color="info", size="sm"),
                                            dbc.Button("Excluir selecionadas", id="btnDespDel", color="danger", size="sm"),
                                        ], className="mt-1", size="sm"
                                    ),
                                ], md=3
                            ),
                            dbc.Col(
                                dcc.Loading(
                                    _datatable(pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Pago","Fixo",
                                                                     "Parcelado","QtdParcelas","ParcelaAtual","Anomalia"]),
                                               "gridDespesas", EDITABLE_DESP), type="default"
                                ), md=9
                            ),
                        ],
                        className="mt-2",
                    ),
                ]),

                # ---------------- Investimentos ----------------
                dcc.Tab(label="Investimentos", value="tab-inv", children=[
                    html.Hr(), html.H3("Investimentos"),
                    dbc.Row(id="kpis-invest", className="mb-2"),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafTop10Inv"), md=6),
                            dbc.Col(dcc.Graph(id="grafTopDescInv"), md=6),
                        ]), type="default"
                    ),
                    dcc.Loading(
                        dbc.Row([
                            dbc.Col(dcc.Graph(id="grafDOWInv"), md=4),
                            dbc.Col(dcc.Graph(id="grafSerieInv"), md=8),
                        ], className="mt-2"), type="default"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("Filtros"),
                                    dcc.Dropdown(
                                        id="ddCatInvExtrato",
                                        options=[{"label": c, "value": c} for c in dfCatInvestimentos["Categoria"].tolist()],
                                        multi=True, placeholder="Categorias"
                                    ),
                                    dbc.Checklist(id="chkParetoInv", options=[{"label":"Pareto 80/20","value":1}],
                                                  value=[], switch=True, className="mt-2"),
                                    dbc.Input(id="txtBuscaInv", placeholder="buscar descrição...", type="text", className="mt-2"),
                                    html.Small(id="rsValoresInvLabel", className="mt-2 d-block"),
                                    dcc.RangeSlider(id="rsValoresInv", step=1),
                                    html.Hr(),
                                    html.H6("Ações em massa"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button("Duplicar selecionados", id="btnInvDup", color="info", size="sm"),
                                            dbc.Button("Excluir selecionados", id="btnInvDel", color="danger", size="sm"),
                                        ], className="mt-1", size="sm"
                                    ),
                                    html.Hr(),
                                    dbc.Button("CSV", id="btnCsvInv", className="mt-1", color="secondary", size="sm"),
                                    dbc.Button("Excel", id="btnXlsxInv", className="mt-1 ms-2", color="secondary", size="sm"),
                                    dcc.Download(id="downCsvInv"), dcc.Download(id="downXlsxInv"),
                                ], md=3
                            ),
                            dbc.Col(
                                dcc.Loading(
                                    _datatable(pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Anomalia"]),
                                               "gridInvestimentos", EDITABLE_INV), type="default"
                                ), md=9
                            ),
                        ],
                        className="mt-2",
                    ),
                ]),
            ],
        ),
    ]
)


# ====================== BOOT & SINCRONIZAÇÃO ======================
@app.callback(
    Output("dprGlobal", "start_date", allow_duplicate=True),
    Output("dprGlobal", "end_date", allow_duplicate=True),
    Input("bootExtrato", "n_intervals"),
    prevent_initial_call="initial_duplicate",
)
def _extrato_periodo_mes_corrente(_):
    hoje = pd.Timestamp.today().normalize()
    inicio = hoje.replace(day=1)
    fim = (inicio + pd.offsets.MonthEnd(1))
    return inicio, fim

# Chips período
@app.callback(
    Output("dprGlobal", "start_date", allow_duplicate=True),
    Output("dprGlobal", "end_date", allow_duplicate=True),
    Input("chipMesAtual", "n_clicks"), Input("chipUlt3", "n_clicks"),
    Input("chipAno", "n_clicks"), Input("chip12m", "n_clicks"), Input("chipLimpar", "n_clicks"),
    prevent_initial_call=True,
)
def quick_period(n_m, n_3, n_ano, n_12, n_clear):
    trig = (callback_context.triggered[0]["prop_id"].split(".")[0]
            if callback_context.triggered else None)
    today = pd.Timestamp.today().normalize()
    if trig == "chipMesAtual":
        ini = today.replace(day=1); fim = (ini + pd.offsets.MonthEnd(1)); return ini, fim
    if trig == "chipUlt3":
        fim = (today + pd.offsets.MonthEnd(0)); ini = (today.replace(day=1) - pd.offsets.MonthBegin(2)); return ini, fim
    if trig == "chipAno":
        ini = pd.Timestamp(today.year,1,1); fim = pd.Timestamp(today.year,12,31); return ini, fim
    if trig == "chip12m":
        fim = (today + pd.offsets.MonthEnd(0)); ini = (today + pd.offsets.MonthBegin(-11)).replace(day=1); return ini, fim
    if trig == "chipLimpar": return None, None
    return no_update, no_update

# Sincroniza Stores locais com os globais (se existirem no app)
@app.callback(Output("storeReceitasExtrato","data", allow_duplicate=True),
              Input("storeReceitas","data"), prevent_initial_call=True)
def _sync_r(d): return d
@app.callback(Output("storeDespesasExtrato","data", allow_duplicate=True),
              Input("storeDespesas","data"), prevent_initial_call=True)
def _sync_d(d): return d
@app.callback(Output("storeInvestExtrato","data", allow_duplicate=True),
              Input("storeInvestimentos","data"), prevent_initial_call=True)
def _sync_i(d): return d


# ========================= SLIDERS =========================
@app.callback(Output("rsValoresRec","min"), Output("rsValoresRec","max"),
              Output("rsValoresRec","value"), Output("rsValoresRecLabel","children"),
              Input("storeReceitasExtrato","data"))
def _sl_r(d): return _update_slider(_coerce(pd.DataFrame(d)))

@app.callback(Output("rsValoresDesp","min"), Output("rsValoresDesp","max"),
              Output("rsValoresDesp","value"), Output("rsValoresDespLabel","children"),
              Input("storeDespesasExtrato","data"))
def _sl_d(d): return _update_slider(_coerce(pd.DataFrame(d)))

@app.callback(Output("rsValoresInv","min"), Output("rsValoresInv","max"),
              Output("rsValoresInv","value"), Output("rsValoresInvLabel","children"),
              Input("storeInvestExtrato","data"))
def _sl_i(d): return _update_slider(_coerce(pd.DataFrame(d)))


# ========================= RECEITAS =========================
@app.callback(
    Output("kpis-receitas","children"),
    Output("grafTop10Rec","figure"), Output("grafTopDescRec","figure"),
    Output("grafDOWRec","figure"), Output("grafSerieRec","figure"),
    Output("gridReceitas","data"), Output("gridReceitas","columns"),
    Output("ddCatRecExtrato","options"),
    Input("storeReceitasExtrato","data"),
    Input("ddCatRecExtrato","value"), Input("dprGlobal","start_date"), Input("dprGlobal","end_date"),
    Input("riAgruparPorGlobal","value"), Input("chkParetoRec","value"),
    Input("chkRecebRec","value"), Input("txtBuscaRec","value"), Input("rsValoresRec","value"),
)
def analise_receitas(dataR, categorias, start, end, agrupar, chkPareto, chkRec, busca, faixa):
    df = _coerce(pd.DataFrame(dataR))
    if df.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Recebido","Recorrente","Anomalia"])
        opts = []
        return [dbc.Col(dbc.Alert("Sem dados no filtro.", color="light"), md=12)], vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_REC} for c in tab.columns], opts

    # opções atualizadas
    opts = [{"label": c, "value": c} for c in sorted(df["Categoria"].dropna().astype(str).unique().tolist())]

    df_f = filter_period_and_categories(df, start, end, categorias or [])
    df_f = _apply_extra_filters(df_f, so_status=1 in (chkRec or []), campo_status="Recebido",
                                desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])

    # KPIs com delta
    prev_s, prev_e = _prev_window(start, end)
    df_prev = filter_period_and_categories(df, prev_s, prev_e, categorias or [])
    df_prev = _apply_extra_filters(df_prev, so_status=1 in (chkRec or []), campo_status="Recebido",
                                   desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])
    total_atual = float(df_f["Valor"].sum()) if not df_f.empty else 0.0
    total_prev  = float(df_prev["Valor"].sum()) if not df_prev.empty else 0.0
    kpis = [dbc.Col(kpi_delta_card("Receitas (período)", total_atual, total_prev, good_when="up"), md=3)]

    if df_f.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados no filtro")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Recebido","Recorrente","Anomalia"])
        return kpis, vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_REC} for c in tab.columns], opts

    # Cores por categoria
    color_map = _cat_color_map(df_f["Categoria"].unique())

    # Top categorias (Pareto opcional)
    top_cat = df_f.groupby("Categoria", as_index=False)["Valor"].sum()
    top_cat = apply_pareto(top_cat, "Valor", 0.8) if 1 in (chkPareto or []) else top_cat.sort_values("Valor", ascending=False).head(10)
    fig_top = _fmt_fig_currency(px.bar(top_cat, x="Categoria", y="Valor", color="Categoria", color_discrete_map=color_map), "Top por Categoria")

    # Top descrições
    topdesc = (df_f.groupby("Descrição", as_index=False)["Valor"].sum()
               .sort_values("Valor", ascending=False).head(10))
    fig_desc = _fmt_fig_currency(px.bar(topdesc, x="Descrição", y="Valor"), "Top por Descrição")

    # DOW e Série
    dow = df_f.copy()
    try: dow["Dia"] = dow["Data"].dt.day_name(locale="pt_BR").str[:3]
    except Exception: dow["Dia"] = dow["Data"].dt.day_name().str[:3]
    fig_dow = _fmt_fig_currency(px.bar(dow.groupby("Dia", as_index=False)["Valor"].sum(), x="Dia", y="Valor"), "Por dia da semana")
    serie = series_by_period(df_f, agrupar)
    fig_serie = _fmt_fig_currency(px.line(serie, x="Periodo", y="Valor", markers=True), "Entradas por período")

    # Tabela + anomalias
    df_tab = df_f.loc[:, [c for c in ["id","Data","Categoria","Descrição","Valor","Recebido","Recorrente"] if c in df_f.columns]]\
                 .sort_values("Data", ascending=False).copy()
    anom = _anomalias(df_tab.rename(columns={"Descrição":"Descricao"}).rename(columns={"Descricao":"Descrição"}))
    df_tab["Anomalia"] = ["⚠️" if x else "" for x in anom.tolist()]

    cols = [{"name":c,"id":c,"editable":c in EDITABLE_REC} for c in df_tab.columns]
    return kpis, fig_top, fig_desc, fig_dow, fig_serie, df_tab.to_dict("records"), cols, opts

# Edição inline (Receitas)
@app.callback(
    Output("toastEditRecOK","is_open"), Output("toastEditRecERR","is_open"),
    Output("storeReceitasExtrato","data", allow_duplicate=True),
    Input("gridReceitas","data_timestamp"),
    State("gridReceitas","data"), State("gridReceitas","data_previous"),
    prevent_initial_call=True,
)
def save_edit_rec(ts, data, data_prev):
    if data_prev is None: return False, False, no_update
    try:
        prev_map = {r.get("id"): r for r in data_prev if r and "id" in r}
        for curr in data:
            rid = curr.get("id")
            if rid is None or rid not in prev_map: continue
            prev = prev_map[rid]
            if any(curr.get(k) != prev.get(k) for k in EDITABLE_REC):
                payload = _normalize_payload_for_update(curr, EDITABLE_REC)
                if payload:
                    update_receita_row(int(rid), payload)
        return True, False, load_receitas().to_dict()
    except Exception:
        return False, True, no_update

# Bulk actions Receitas (inclui EXCLUIR)
@app.callback(
    Output("storeReceitasExtrato","data", allow_duplicate=True),
    Output("toastDupOK","is_open", allow_duplicate=True),
    Output("toastDelOK","is_open", allow_duplicate=True),
    Output("toastDelERR","is_open", allow_duplicate=True),
    Input("btnRecMark","n_clicks"), Input("btnRecUnmark","n_clicks"), Input("btnRecDup","n_clicks"), Input("btnRecDel","n_clicks"),
    State("gridReceitas","selected_rows"), State("gridReceitas","data"),
    prevent_initial_call=True,
)
def bulk_rec(mark, unmark, dup, delete, sel_rows, data):
    trig = (callback_context.triggered[0]["prop_id"].split(".")[0]
            if callback_context.triggered else None)
    rows = [data[i] for i in (sel_rows or []) if 0 <= i < len(data)]
    if not rows: return no_update, False, False, False

    if trig in ("btnRecMark", "btnRecUnmark"):
        val = 1 if trig == "btnRecMark" else 0
        for r in rows:
            rid = r.get("id")
            if rid is not None:
                update_receita_row(int(rid), {"Recebido": val})
        return load_receitas().to_dict(), False, False, False

    if trig == "btnRecDup":
        import pandas as pd
        cols = ["Valor","Recebido","Recorrente","Data","Categoria","Descrição"]
        df_new = pd.DataFrame([{k: r.get(k) for k in cols if k in r} for r in rows])
        if not df_new.empty:
            append_receitas(df_new)
        return load_receitas().to_dict(), True, False, False

    if trig == "btnRecDel":
        ids = [int(r.get("id")) for r in rows if r.get("id") is not None]
        if not ids: return no_update, False, False, True
        try:
            if delete_receitas is None:
                raise RuntimeError("delete_receitas() não disponível em services.globals")
            delete_receitas(ids)
            return load_receitas().to_dict(), False, True, False
        except Exception:
            return no_update, False, False, True

    return no_update, False, False, False


# ========================= DESPESAS =========================
@app.callback(
    Output("kpis-despesas","children"),
    Output("grafTop10Desp","figure"), Output("grafTopDescDesp","figure"),
    Output("grafDOWDesp","figure"), Output("grafSerieDesp","figure"),
    Output("gridDespesas","data"), Output("gridDespesas","columns"),
    Output("ddCatDespExtrato","options"), Output("ddMetaCatDesp","options"), Output("divMetasDesp","children"),
    Input("storeDespesasExtrato","data"),
    Input("ddCatDespExtrato","value"), Input("dprGlobal","start_date"), Input("dprGlobal","end_date"),
    Input("riAgruparPorGlobal","value"), Input("chkParetoDesp","value"),
    Input("chkPagoDesp","value"), Input("txtBuscaDesp","value"), Input("rsValoresDesp","value"),
    State("storeMetasDesp","data"),
)
def analise_despesas(dataD, categorias, start, end, agrupar, chkPareto, chkPago, busca, faixa, metas_store):
    df = _coerce(pd.DataFrame(dataD))
    opts = [{"label": c, "value": c} for c in sorted(df["Categoria"].dropna().astype(str).unique().tolist())] if not df.empty else []
    metas_opts = opts

    if df.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Pago","Fixo","Parcelado","QtdParcelas","ParcelaAtual","Anomalia"])
        return [dbc.Col(dbc.Alert("Sem dados no filtro.", color="light"), md=12)], vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_DESP} for c in tab.columns], opts, metas_opts, []

    df_f = filter_period_and_categories(df, start, end, categorias or [])
    df_f = _apply_extra_filters(df_f, so_status=1 in (chkPago or []), campo_status="Pago",
                                desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])

    # KPIs com delta
    prev_s, prev_e = _prev_window(start, end)
    df_prev = filter_period_and_categories(df, prev_s, prev_e, categorias or [])
    df_prev = _apply_extra_filters(df_prev, so_status=1 in (chkPago or []), campo_status="Pago",
                                   desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])
    total_atual = float(df_f["Valor"].sum()) if not df_f.empty else 0.0
    total_prev  = float(df_prev["Valor"].sum()) if not df_prev.empty else 0.0
    kpis = [dbc.Col(kpi_delta_card("Despesas (período)", total_atual, total_prev, good_when="down"), md=3)]

    if df_f.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados no filtro")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Pago","Fixo","Parcelado","QtdParcelas","ParcelaAtual","Anomalia"])
        return kpis, vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_DESP} for c in tab.columns], opts, metas_opts, []

    # Cores e gráficos
    color_map = _cat_color_map(df_f["Categoria"].unique())
    top_cat = df_f.groupby("Categoria", as_index=False)["Valor"].sum()
    top_cat = apply_pareto(top_cat, "Valor", 0.8) if 1 in (chkPareto or []) else top_cat.sort_values("Valor", ascending=False).head(10)
    fig_top = _fmt_fig_currency(px.bar(top_cat, x="Categoria", y="Valor", color="Categoria", color_discrete_map=color_map), "Top por Categoria")

    topdesc = (df_f.groupby("Descrição", as_index=False)["Valor"].sum()
               .sort_values("Valor", ascending=False).head(10))
    fig_desc = _fmt_fig_currency(px.bar(topdesc, x="Descrição", y="Valor"), "Top por Descrição")

    dow = df_f.copy()
    try: dow["Dia"] = dow["Data"].dt.day_name(locale="pt_BR").str[:3]
    except Exception: dow["Dia"] = dow["Data"].dt.day_name().str[:3]
    fig_dow = _fmt_fig_currency(px.bar(dow.groupby("Dia", as_index=False)["Valor"].sum(), x="Dia", y="Valor"), "Por dia da semana")

    serie = series_by_period(df_f, agrupar)
    fig_serie = _fmt_fig_currency(px.line(serie, x="Periodo", y="Valor", markers=True), "Saídas por período")

    # Tabela + anomalias
    df_tab = df_f.loc[:, [c for c in ["id","Data","Categoria","Descrição","Valor","Pago","Fixo","Parcelado","QtdParcelas","ParcelaAtual"] if c in df_f.columns]]\
                 .sort_values("Data", ascending=False).copy()
    anom = _anomalias(df_tab)
    df_tab["Anomalia"] = ["⚠️" if x else "" for x in anom.tolist()]

    cols = [{"name":c,"id":c,"editable":c in EDITABLE_DESP} for c in df_tab.columns]

    # Metas e progresso por categoria neste período
    metas = metas_store or {}
    barras = []
    if metas and not df_f.empty:
        atual = df_f.groupby("Categoria")["Valor"].sum().to_dict()
        for cat, meta in metas.items():
            meta_val = float(meta or 0)
            if meta_val <= 0: continue
            atual_val = float(atual.get(cat, 0.0))
            perc = min(int(round(atual_val / meta_val * 100)) if meta_val else 0, 999)
            cor = "danger" if perc >= 100 else ("warning" if perc >= 80 else "success")
            barras.append(
                html.Div([
                    html.Small(f"{cat}: {fmt_brl(atual_val)} / {fmt_brl(meta_val)}"),
                    dbc.Progress(value=min(perc,100), color=cor, className="mb-1", striped=True, animated=False),
                ])
            )

    return kpis, fig_top, fig_desc, fig_dow, fig_serie, df_tab.to_dict("records"), cols, opts, metas_opts, barras

# Edição inline (Despesas)
@app.callback(
    Output("toastEditDespOK","is_open"), Output("toastEditDespERR","is_open"),
    Output("storeDespesasExtrato","data", allow_duplicate=True),
    Input("gridDespesas","data_timestamp"),
    State("gridDespesas","data"), State("gridDespesas","data_previous"),
    prevent_initial_call=True,
)
def save_edit_desp(ts, data, data_prev):
    if data_prev is None: return False, False, no_update
    try:
        prev_map = {r.get("id"): r for r in data_prev if r and "id" in r}
        for curr in data:
            rid = curr.get("id")
            if rid is None or rid not in prev_map: continue
            prev = prev_map[rid]
            if any(curr.get(k) != prev.get(k) for k in EDITABLE_DESP):
                payload = _normalize_payload_for_update(curr, EDITABLE_DESP)
                if payload:
                    update_despesa_row(int(rid), payload)
        return True, False, load_despesas().to_dict()
    except Exception:
        return False, True, no_update

# Bulk actions Despesas (inclui EXCLUIR)
@app.callback(
    Output("storeDespesasExtrato","data", allow_duplicate=True),
    Output("toastDupOK","is_open", allow_duplicate=True),
    Output("toastDelOK","is_open", allow_duplicate=True),
    Output("toastDelERR","is_open", allow_duplicate=True),
    Input("btnDespMark","n_clicks"), Input("btnDespUnmark","n_clicks"), Input("btnDespDup","n_clicks"), Input("btnDespDel","n_clicks"),
    State("gridDespesas","selected_rows"), State("gridDespesas","data"),
    prevent_initial_call=True,
)
def bulk_desp(mark, unmark, dup, delete, sel_rows, data):
    trig = (callback_context.triggered[0]["prop_id"].split(".")[0]
            if callback_context.triggered else None)
    rows = [data[i] for i in (sel_rows or []) if 0 <= i < len(data)]
    if not rows: return no_update, False, False, False

    if trig in ("btnDespMark", "btnDespUnmark"):
        val = 1 if trig == "btnDespMark" else 0
        for r in rows:
            rid = r.get("id")
            if rid is not None:
                update_despesa_row(int(rid), {"Pago": val})
        return load_despesas().to_dict(), False, False, False

    if trig == "btnDespDup":
        import pandas as pd
        cols = ["Valor","Pago","Fixo","Data","Categoria","Descrição","Parcelado","QtdParcelas","ParcelaAtual"]
        df_new = pd.DataFrame([{k: r.get(k) for k in cols if k in r} for r in rows])
        if not df_new.empty:
            append_despesas(df_new)
        return load_despesas().to_dict(), True, False, False

    if trig == "btnDespDel":
        ids = [int(r.get("id")) for r in rows if r.get("id") is not None]
        if not ids: return no_update, False, False, True
        try:
            if delete_despesas is None:
                raise RuntimeError("delete_despesas() não disponível em services.globals")
            delete_despesas(ids)
            return load_despesas().to_dict(), False, True, False
        except Exception:
            return no_update, False, False, True

    return no_update, False, False, False

# Metas: salvar
@app.callback(
    Output("storeMetasDesp","data", allow_duplicate=True),
    Input("btnSaveMetaDesp","n_clicks"),
    State("ddMetaCatDesp","value"), State("inputMetaDesp","value"),
    State("storeMetasDesp","data"),
    prevent_initial_call=True,
)
def save_meta_desp(n, cat, meta, store):
    if not n or not cat or meta is None: return no_update
    s = dict(store or {})
    s[str(cat)] = float(meta)
    return s


# ========================= INVESTIMENTOS =========================
@app.callback(
    Output("kpis-invest","children"),
    Output("grafTop10Inv","figure"), Output("grafTopDescInv","figure"),
    Output("grafDOWInv","figure"), Output("grafSerieInv","figure"),
    Output("gridInvestimentos","data"), Output("gridInvestimentos","columns"),
    Output("ddCatInvExtrato","options"),
    Input("storeInvestExtrato","data"),
    Input("ddCatInvExtrato","value"), Input("dprGlobal","start_date"), Input("dprGlobal","end_date"),
    Input("riAgruparPorGlobal","value"), Input("chkParetoInv","value"),
    Input("txtBuscaInv","value"), Input("rsValoresInv","value"),
)
def analise_invest(dataI, categorias, start, end, agrupar, chkPareto, busca, faixa):
    df = _coerce(pd.DataFrame(dataI))
    opts = [{"label": c, "value": c} for c in sorted(df["Categoria"].dropna().astype(str).unique().tolist())] if not df.empty else []

    if df.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Anomalia"])
        return [dbc.Col(dbc.Alert("Sem dados no filtro.", color="light"), md=12)], vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_INV} for c in tab.columns], opts

    df_f = filter_period_and_categories(df, start, end, categorias or [])
    df_f = _apply_extra_filters(df_f, so_status=False, campo_status=None,
                                desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])

    # KPIs
    prev_s, prev_e = _prev_window(start, end)
    df_prev = filter_period_and_categories(df, prev_s, prev_e, categorias or [])
    df_prev = _apply_extra_filters(df_prev, so_status=False, campo_status=None,
                                   desc_contains=busca, valor_min=(faixa or [None,None])[0], valor_max=(faixa or [None,None])[1])
    total_atual = float(df_f["Valor"].sum()) if not df_f.empty else 0.0
    total_prev  = float(df_prev["Valor"].sum()) if not df_prev.empty else 0.0
    kpis = [dbc.Col(kpi_delta_card("Investimentos (aportes)", total_atual, total_prev, good_when="up"), md=3)]

    if df_f.empty:
        vazio = _fmt_fig_currency(px.bar(), "Sem dados no filtro")
        tab = pd.DataFrame(columns=["id","Data","Categoria","Descrição","Valor","Anomalia"])
        return kpis, vazio, vazio, vazio, vazio, tab.to_dict("records"), [{"name":c,"id":c,"editable":c in EDITABLE_INV} for c in tab.columns], opts

    color_map = _cat_color_map(df_f["Categoria"].unique())
    top_cat = df_f.groupby("Categoria", as_index=False)["Valor"].sum()
    top_cat = apply_pareto(top_cat, "Valor", 0.8) if 1 in (chkPareto or []) else top_cat.sort_values("Valor", ascending=False).head(10)
    fig_top = _fmt_fig_currency(px.bar(top_cat, x="Categoria", y="Valor", color="Categoria", color_discrete_map=color_map), "Top por Categoria")

    topdesc = (df_f.groupby("Descrição", as_index=False)["Valor"].sum()
               .sort_values("Valor", ascending=False).head(10))
    fig_desc = _fmt_fig_currency(px.bar(topdesc, x="Descrição", y="Valor"), "Top por Descrição")

    dow = df_f.copy()
    try: dow["Dia"] = dow["Data"].dt.day_name(locale="pt_BR").str[:3]
    except Exception: dow["Dia"] = dow["Data"].dt.day_name().str[:3]
    fig_dow = _fmt_fig_currency(px.bar(dow.groupby("Dia", as_index=False)["Valor"].sum(), x="Dia", y="Valor"), "Por dia da semana")

    serie = series_by_period(df_f, agrupar)
    fig_serie = _fmt_fig_currency(px.line(serie, x="Periodo", y="Valor", markers=True), "Aportes por período")

    df_tab = df_f.loc[:, [c for c in ["id","Data","Categoria","Descrição","Valor"] if c in df_f.columns]]\
                 .sort_values("Data", ascending=False).copy()
    anom = _anomalias(df_tab)
    df_tab["Anomalia"] = ["⚠️" if x else "" for x in anom.tolist()]
    cols = [{"name":c,"id":c,"editable":c in EDITABLE_INV} for c in df_tab.columns]

    return kpis, fig_top, fig_desc, fig_dow, fig_serie, df_tab.to_dict("records"), cols, opts

# Edição inline (Investimentos)
@app.callback(
    Output("toastEditInvOK","is_open"), Output("toastEditInvERR","is_open"),
    Output("storeInvestExtrato","data", allow_duplicate=True),
    Input("gridInvestimentos","data_timestamp"),
    State("gridInvestimentos","data"), State("gridInvestimentos","data_previous"),
    prevent_initial_call=True,
)
def save_edit_inv(ts, data, data_prev):
    if data_prev is None: return False, False, no_update
    try:
        prev_map = {r.get("id"): r for r in data_prev if r and "id" in r}
        for curr in data:
            rid = curr.get("id")
            if rid is None or rid not in prev_map: continue
            prev = prev_map[rid]
            if any(curr.get(k) != prev.get(k) for k in EDITABLE_INV):
                payload = _normalize_payload_for_update(curr, EDITABLE_INV)
                if payload:
                    update_invest_row(int(rid), payload)
        return True, False, load_investimentos().to_dict()
    except Exception:
        return False, True, no_update

# Bulk actions Investimentos (duplicar + EXCLUIR)
@app.callback(
    Output("storeInvestExtrato","data", allow_duplicate=True),
    Output("toastDupOK","is_open", allow_duplicate=True),
    Output("toastDelOK","is_open", allow_duplicate=True),
    Output("toastDelERR","is_open", allow_duplicate=True),
    Input("btnInvDup","n_clicks"), Input("btnInvDel","n_clicks"),
    State("gridInvestimentos","selected_rows"), State("gridInvestimentos","data"),
    prevent_initial_call=True,
)
def bulk_inv_ops(n_dup, n_del, sel_rows, data):
    trig = (callback_context.triggered[0]["prop_id"].split(".")[0]
            if callback_context.triggered else None)
    rows = [data[i] for i in (sel_rows or []) if 0 <= i < len(data)]
    if not rows: return no_update, False, False, False

    if trig == "btnInvDup":
        import pandas as pd
        cols = ["Valor","Data","Categoria","Descrição"]
        df_new = pd.DataFrame([{k: r.get(k) for k in cols if k in r} for r in rows])
        if not df_new.empty:
            append_investimentos(df_new)
        return load_investimentos().to_dict(), True, False, False

    if trig == "btnInvDel":
        ids = [int(r.get("id")) for r in rows if r.get("id") is not None]
        if not ids: return no_update, False, False, True
        try:
            if delete_investimentos is None:
                raise RuntimeError("delete_investimentos() não disponível em services.globals")
            delete_investimentos(ids)
            return load_investimentos().to_dict(), False, True, False
        except Exception:
            return no_update, False, False, True

    return no_update, False, False, False


# ========================= Downloads Investimentos =========================
@app.callback(Output("downCsvInv","data"), Input("btnCsvInv","n_clicks"),
              State("gridInvestimentos","data"), prevent_initial_call=True)
def down_csv_inv(n, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_csv, filename="investimentos_filtrados.csv", index=False, encoding="utf-8")

@app.callback(Output("downXlsxInv","data"), Input("btnXlsxInv","n_clicks"),
              State("gridInvestimentos","data"), prevent_initial_call=True)
def down_xlsx_inv(n, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_excel, filename="investimentos_filtrados.xlsx", index=False, sheet_name="Investimentos")
