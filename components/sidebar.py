import os
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from app import app

from datetime import datetime, date
import plotly.express as px
import numpy as np
import pandas as pd






# ========= Layout ========= #
layout = dbc.Col([
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
                                        options=[],
                                        value=[],
                                        id='switches-inputReceita',
                                        switch=True
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectReceita', options=[], value=[])
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
                                                dbc.Checklist(id='checklistReceita', options=[], value=[], style={'margin-top': '10px'}),
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
                                        options=[],
                                        value=[],
                                        id='switches-inputInvestimento',
                                        switch=True
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectInvestimento', options=[], value=[])
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
                                            dbc.Checklist(id='checklistInvestimento', options=[], value=[], style={'margin-top': '10px'}),
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
                                        options=[],
                                        value=[],
                                        id='switches-inputDespesa',
                                        switch=True
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label("Categoria: "),
                                    dbc.Select(id='selectDespesa', options=[], value=[])
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
                                            dbc.Checklist(id='checklistDespesa', options=[], value=[], style={'margin-top': '10px'}),
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
                        dbc.NavLink("Receitas", href="/receitas", active="exact"),
                        dbc.NavLink("Despesas", href="/despesas", active="exact"),
                        dbc.NavLink("Investimentos", href="/investimentos", active="exact"),
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