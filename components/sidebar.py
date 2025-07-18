import os
import dash
from dateutil.relativedelta import relativedelta
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from app import app
from dash import callback_context
import locale

from services.globals import *
from datetime import datetime, date
import plotly.express as px
import numpy as np
import pandas as pd

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')





# ========= Layout ========= #
content = html.Div(id="page-content")
layout = dbc.Col([
                dcc.Store(id="storeReceitas", data=dfReceitas.to_dict()),
                dcc.Store(id="storeDespesas", data=dfDespesas.to_dict()),
                dcc.Store(id="storeInvestimentos", data=dfInvestimentos.to_dict()),
                dcc.Store(id="storeCatReceita", data=dfCatReceitas.to_dict()),
                dcc.Store(id="storeCatDespesas", data=dfCatDespesas.to_dict()),
                dcc.Store(id="storeCatInvestimentos", data=dfCatInvestimentos.to_dict()),

                html.H1("Gerenciador Patrimônial", className="text-primary"),
                html.P("Feito por Yuri Santos", className="text-secondary"),
                html.Hr(),
    
    # Seção PERFIL --------------------
                dbc.Button(id='botaoAvatar',
                        children=[html.Img(src='/assets/img_hom.png', id='avatar', className='perfilAvatar')
                ], style={'background-color': 'transparent', 'border': 'none'}),
    
    # Seção adicionar ----------------
                dbc.Row(
                    [
                    dbc.Col([
                        dbc.Button(color='success', id='novaReceita', className="w-100",
                                   children=['+ Receita'])
                    ], width=4, style={'padding': '5px'}),
                    dbc.Col([
                        dbc.Button(color='warning', id='novaInvestimento', className="w-100 text-nowrap",
                                   children=['Investimento'])
                    ], width=4, style={'padding': '5px'}),
                    dbc.Col([
                        dbc.Button(color='danger', id='novaDespesa', className="w-100",
                                   children=['- Despesa'])
                    ], width=4, style={'padding': '5px'})   
                ],    className="mb-4"),
    
        # Modal para adicionar receita
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Adicionar Receita')),
                        dbc.ModalBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label('Descrição: '),
                                    dbc.Input(id='descricaoReceita', type='text', placeholder='dividendo da bolsa, empresa ...')
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Valor: "),
                                    dbc.Input(placeholder="$100,00", id="valorReceita", value="")
                                ], width=6)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Data: "),
                                    dcc.DatePickerSingle(id='dataReceita',
                                        date=datetime.today(),
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'}
                                    ),
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Extras: "),
                                    dbc.Checklist(
                                        options=[{"label": "Foi recebida", "value": 1},
                                                 {"label": "Receita Recorrente", "value": 2}],
                                        value=[1],
                                        id='switchesInputReceita',
                                        switch=True
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectReceita', options=[{'label': i, 'value': i} for i in catReceitas], value=catReceitas[0])
                                ], width=4)
                            ], style={'margin-top': '10px'}),

                            dbc.Row([
                                dbc.Accordion([
                                    dbc.AccordionItem(children=[
                                        dbc.Row([
                                            dbc.Col([
                                                html.Legend("Adicionar categoria", style={'color': 'black'}),
                                                dbc.Input(id='inputReceita', type='text', placeholder='Nova categoria', value=""),
                                                html.Br(),
                                                dbc.Button("Adicionar", className="btn btn-success", id='addCategoriaReceita', style={'margin-top': '10px'}),
                                                html.Br(),
                                                html.Div(id='outputCategoriaReceita', style={})
                                            ], width=6),
                                        
                                            dbc.Col([
                                                html.Legend("Excluir categoria", style={'color': 'black'}),
                                                dbc.Checklist(id='checklistReceita', options=[{'label': i, 'value': i} for i in catReceitas], value=catReceitas[0], style={'margin-top': '10px'}),
                                                dbc.Button('Remover', className="btn btn-danger", id='excluirCategoriaReceita', style={'margin-left': '30px'})
                                            ], width=6)
                                        ]),
                                    ], title='Adicionar ou Remover categoria')
                                ],flush=True, start_collapsed=True, id='accordionReceita'),

                                html.Div(id='teste_receita', style={ 'padding-top': '10px'}),
                                dbc.ModalFooter([
                                    dbc.Button("Adicionar Receita", id="salvarReceita", color="success"),
                                    dbc.Popover(dbc.PopoverBody("Receita adicionada com sucesso!"), target="salvarReceita", trigger="click", placement="left"),
                                ])
                            ], style={'margin-top': '10px'})
                        ])
                    ], style={"background-color": "rgba(17,140,79,0.10"}, id="modalReceita", size="lg", is_open=False, centered=True, backdrop='static'),

                # Modal para adicionar investimento
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Adicionar Investimento')),
                        dbc.ModalBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Descrição"),
                                    dbc.Input(id='descricaoInvestimento', type='text', placeholder='Descrição do investimento')
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Valor"),
                                    dbc.Input(id='valorInvestimento', type='number', placeholder='Valor do investimento')
                                ], width=6)
                            ]),
                        dbc.Row([
                                dbc.Col([
                                    dbc.Label("Data: "),
                                    dcc.DatePickerSingle(id='dataInvestimento',
                                        date=datetime.today(),
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'}
                                    ),
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Tipo: "),
                                    dbc.Checklist(
                                        options=[{"label": "Mensal", "value": 1},
                                                 {"label": "Reinvestimento", "value": 2},],
                                        value=[1],
                                        id='switchesInputInvestimento',
                                        switch=True
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectInvestimento', options=[{'label': i, 'value': i} for i in catInvestimentos], value=catInvestimentos[0])
                                ], width=4)
                            ], style={'margin-top': '10px'}),

                        dbc.Row([
                            dbc.Accordion([
                                dbc.AccordionItem(children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.Legend("Adicionar categoria", style={'color': 'black'}),
                                            dbc.Input(id='inputInvestimento', type='text', placeholder='Nova categoria', value=""),
                                            html.Br(),
                                            dbc.Button("Adicionar", className="btn btn-success", id='addCategoriaInvestimento', style={'margin-top': '10px'}),
                                            html.Br(),
                                            html.Div(id='outputCategoriaInvestimento', style={})
                                        ], width=6),
                                        
                                        dbc.Col([
                                            html.Legend("Excluir categoria", style={'color': 'black'}),
                                            dbc.Checklist(id='checklistInvestimento', options=[{'label': i, 'value': i} for i in catInvestimentos], value=catInvestimentos[0], style={'margin-top': '10px'}),
                                            dbc.Button('Remover', className="btn btn-danger", id='excluirCategoriaInvestimento', style={'margin-left': '30px'})
                                        ], width=6)
                                    ]),
                                ], title='Adicionar ou Remover categoria')
                            ],flush=True, start_collapsed=True, id='accordionInvestimento'),

                            html.Div(id='teste_Investimento', style={ 'padding-top': '10px'}),
                            dbc.ModalFooter([
                                dbc.Button("Adicionar Investimento", id="salvarInvestimento", color="success"),
                                dbc.Popover(dbc.PopoverBody("Investimento adicionada com sucesso!"), target="salvarInvestimento", trigger="click", placement="left"),
                            ])
                        ], style={'margin-top': '10px'})
                        ])
                ], style={"background-color": "rgba(17,140,79,0.10"}, id="modalInvestimento", size="lg", is_open=False, centered=True, backdrop='static'),


                # Modal para adicionar despesa
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Adicionar Despesa')),
                        dbc.ModalBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Descrição"),
                                    dbc.Input(id='descricaoDespesa', type='text', placeholder='Descrição da despesa')
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Valor"),
                                    dbc.Input(id='valorDespesa', type='number', placeholder='Valor da despesa')
                                ], width=6)
                            ]),
                        dbc.Row([
                                dbc.Col([
                                    dbc.Label("Data: "),
                                    dcc.DatePickerSingle(id='dataDespesa',
                                        date=datetime.today(),
                                        display_format='DD/MM/YYYY',
                                        style={'width': '100%'}
                                    ),
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Tipo: "),
                                    dbc.Checklist(
                                        options=[{"label": "Avista", "value": 1},
                                                 {"label": "Recorrente", "value": 2},
                                                 {"label": "Dividida", "value": 3}],
                                        value=[],
                                        id='switchesInputDespesa',
                                        switch=True
                                    ),
                                    dbc.Col([
                                        dbc.Input(id="qtdParcelas", placeholder="Quantas parcelas?", type="number", min=1, step=1),
                                    ])
                                    
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectDespesa', options=[{'label': i, 'value': i} for i in catDespesas], value=catDespesas[0])
                                ], width=4)
                            ], style={'margin-top': '10px'}),

                        dbc.Row([
                            dbc.Accordion([
                                dbc.AccordionItem(children=[
                                    dbc.Row([
                                        dbc.Col([
                                            html.Legend("Adicionar categoria", style={'color': 'black'}),
                                            dbc.Input(id='inputDespesa', type='text', placeholder='Nova categoria', value=""),
                                            html.Br(),
                                            dbc.Button("Adicionar", className="btn btn-success", id='addCategoriaDespesa', style={'margin-top': '10px'}),
                                            html.Br(),
                                            html.Div(id='outputCategoriaDespesa', style={})
                                        ], width=6),
                                        
                                        dbc.Col([
                                            html.Legend("Excluir categoria", style={'color': 'black'}),
                                            dbc.Checklist(id='checklistDespesa', options=[{'label': i, 'value': i} for i in catDespesas], value=catDespesas[0], style={'margin-top': '10px'}),
                                            dbc.Button('Remover', className="btn btn-danger", id='excluirCategoriaDespesa', style={'margin-left': '30px'})
                                        ], width=6)
                                    ]),
                                ], title='Adicionar ou Remover categoria')
                            ],flush=True, start_collapsed=True, id='accordionDespesa'),

                            html.Div(id='teste_Despesao', style={ 'padding-top': '10px'}),
                            dbc.ModalFooter([
                                dbc.Button("Adicionar Despesa", id="salvarDespesa", color="success"),
                                dbc.Popover(dbc.PopoverBody("Despesa adicionada com sucesso!"), target="salvarDespesa", trigger="click", placement="left"),
                            ])
                        ], style={'margin-top': '10px'}),
                        ])
                    ], style={"background-color": "rgba(17,140,79,0.10)"}, id="modalDespesa", size="lg", is_open=False, centered=True, backdrop='static'),

    # Seção navegação ---------------
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink("Dashboard", href="/dashboards", active="exact"),
                        dbc.NavLink("Extratos", href="/extratos", active="exact"),
                    ], vertical=True, pills=True, id='navButtons', style={"margin-bottom": "50px"}
                )

    
])


# =========  Callbacks  =========== #
# Pop-up receita
@app.callback(
    Output('modalReceita', 'is_open'),
    Input('novaReceita', 'n_clicks'),
    State('modalReceita', 'is_open') 
)
def toggle_modal_receita(n1, is_open):
    if n1:
        return not is_open

# Pop-up investimento
@app.callback(
    Output('modalInvestimento', 'is_open'),
    Input('novaInvestimento', 'n_clicks'),
    State('modalInvestimento', 'is_open') 
)
def toggle_modal_investimento(n1, is_open):
    if n1:
        return not is_open


# Pop-up despesa
@app.callback(
    Output('modalDespesa', 'is_open'),
    Input('novaDespesa', 'n_clicks'),
    State('modalDespesa', 'is_open') 
)
def toggle_modal_despesa(n1, is_open):
    if n1:
        return not is_open
    

# Registra receita
@app.callback(
    Output('storeReceitas', 'data'),
    Input('salvarReceita', 'n_clicks'),
    [
        State('descricaoReceita', 'value'),
        State('valorReceita', 'value'),
        State('dataReceita', 'date'),
        State('switchesInputReceita', 'value'),
        State('selectReceita', 'value'),
        State('storeReceitas', 'data')
    ]
)
def salvarReceiota(n, descricao, valor, date, switches, categoria, dictReceitas):
    dfReceitas = pd.DataFrame(dictReceitas)

    colunas = ['Valor', 'Recebido', 'Recorrente', 'Data', 'Categoria', 'Descrição']
    if list(dfReceitas.columns) != colunas:
        dfReceitas = dfReceitas.reindex(columns=colunas)

    if n and valor not in (None, ""):
        try:
            valor_float = locale.atof(valor)
        except Exception:
            valor_float = float(valor)
        valor_float = round(valor_float, 2)

        data_obj = pd.to_datetime(date).date()
        categoria_val = categoria[0] if isinstance(categoria, list) else categoria
        recebido_val = 1 if 1 in switches else 0
        recorrente_val = 1 if 2 in switches else 0

        dfReceitas.loc[dfReceitas.shape[0]] = [valor_float, recebido_val, recorrente_val, data_obj, categoria_val, descricao]

        dfReceitas.to_csv("dfReceitas.csv", index=False)

    return dfReceitas.to_dict()


# Registra despesa
@app.callback(
    Output('storeDespesas', 'data'),
    Input('salvarDespesa', 'n_clicks'),
    [
        State('descricaoDespesa', 'value'),
        State('valorDespesa', 'value'),
        State('dataDespesa', 'date'),
        State('switchesInputDespesa', 'value'),
        State('selectDespesa', 'value'),
        State('qtdParcelas', 'value'),
        State('storeDespesas', 'data')
    ]
)
def salvarDespesa(n, descricao, valor, date, switches, categoria, qtdParcelas, dictDespesa):
    dfDespesas = pd.DataFrame(dictDespesa)

    if n and not (valor == "" or valor == None):
        valor = round(float(valor), 2)
        date = pd.to_datetime(date).date()
        categoria = categoria[0] if type(categoria) == list else categoria
        recebido = 1 if 1 in switches else 0
        fixo = 1 if 2 in switches else 0
        dividida = 1 if 3 in switches else 0
        qtdParcelas = int(qtdParcelas) if dividida and qtdParcelas else 1
        recorrente = 1 if 2 in switches else 0
        
        if dividida and qtdParcelas > 1:
            valor_parcela = round(valor / qtdParcelas, 2)
            
            for parcela in range(1, qtdParcelas + 1):
                descricao_parcela = f"{descricao} ({parcela}/{qtdParcelas})"
                data_parcela = date + relativedelta(months=parcela-1)
                
                dfDespesas.loc[dfDespesas.shape[0]] = [
                    valor_parcela, 
                    recebido, 
                    fixo, 
                    data_parcela, 
                    categoria, 
                    descricao_parcela, 
                    recorrente, 
                    qtdParcelas, 
                    dividida
                ]
        else:
            dfDespesas.loc[dfDespesas.shape[0]] = [
                valor, 
                recebido, 
                fixo, 
                date, 
                categoria, 
                descricao, 
                recorrente, 
                1,
                dividida
            ]
        
        dfDespesas.to_csv("dfDespesas.csv")
    
    return dfDespesas.to_dict()


#registra investimento

@app.callback(
    Output('storeInvestimentos', 'data'),
    Input('salvarInvestimento', 'n_clicks'),
    [
        State('descricaoInvestimento', 'value'),
        State('valorInvestimento', 'value'),
        State('dataInvestimento', 'date'),
        State('switchesInputInvestimento', 'value'),
        State('selectInvestimento', 'value'),
        State('storeInvestimentos', 'data')
    ]
)
def salvarInvestimento(n, descricao, valor, date, switches, categoria, dictInvestimento):

    dfInvestimentos = pd.DataFrame(dictInvestimento)

    if n and not (valor == "" or valor == None):
        valor = round(float(valor), 2)
        date = pd.to_datetime(date).date()
        categoria = categoria[0] if type(categoria) == list else categoria
        recebido = 1 if 1 in switches else 0
        fixo = 1 if 2 in switches else 0

        dfInvestimentos.loc[dfInvestimentos.shape[0]] = [valor, recebido, fixo, date, categoria, descricao]
        dfInvestimentos.to_csv("dfInvestimentos.csv")
    
    dataReturn = dfInvestimentos.to_dict()
    return dataReturn

@app.callback(
   [   Output('selectDespesa', 'options'),
        Output('checklistDespesa', 'options'),
        Output('checklistDespesa', 'value'),
        Output('storeCatDespesas', 'data')
    ],
    [
        Input('addCategoriaDespesa', 'n_clicks'),
        Input('excluirCategoriaDespesa', 'n_clicks')
    ],
    [
        State('inputDespesa', 'value'),
        State('checklistDespesa', 'value'),
        State('storeCatDespesas', 'data')
    ]
)
def adicionarcategoria(n, n2, txt, checkDelete,data):
    catDespesas = list(data["Categoria"].values())

    if n and not (txt == "" or txt == None):
        catDespesas = catDespesas + [txt] if txt not in catDespesas else catDespesas
    
    if n2:
        if len(checkDelete) > 0:
            catDespesas = [i for i in catDespesas if i not in checkDelete]

    optDespesa = [{"label": i, "value": i} for i in catDespesas]
    dfCatDespesas = pd.DataFrame(catDespesas, columns=["Categoria"])
    dfCatDespesas.to_csv("dfCatDespesas.csv")
    dataReturn = dfCatDespesas.to_dict()

    return[optDespesa, optDespesa, [], dataReturn]