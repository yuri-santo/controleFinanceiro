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
                dbc.Row([
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
    
    # Seção navegação ---------------
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink("Dashboard", href="/dashboards", active="exact"),
                        dbc.NavLink("Receitas", href="/receitas", active="exact"),
                        dbc.NavLink("Despesas", href="/despesas", active="exact"),
                        dbc.NavLink("Investimentos", href="/investimentos", active="exact"),
                        dbc.NavLink("Extratos", href="/extratos", active="exact"),
                    ], vertical=True, pills=True, id='navButtons', style={"margin-buttom": "50px"}
                )

    
])


# =========  Callbacks  =========== #
# Pop-up receita
