from dash import html, dcc
import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from app import *
from components import sidebar,dashboards,extratos,receitas,investimentos,despesas



# =========  Layout  =========== #
content = html.Div(id="page-content")


app.layout = dbc.Container(children=[
    dbc.Row([
        dbc.Col([
            dcc.Location(id='url'),
            sidebar.layout
        ],md=4),
        dbc.Col([
            content
        ], md=10),
    ])

], fluid=True,)

@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def page(pathname):
    if pathname == '/' or pathname == '/dashboards':
        return dashboards.layout
    elif pathname == '/extratos':
        return extratos.layout
    elif pathname == '/receitas':
        return receitas.layout
    elif pathname == '/investimentos':
        return investimentos.layout
    elif pathname == '/despesas':
        return despesas.layout
    else:
        return html.Div([
            html.H1('404: Página não encontrada'),
            html.P('A página que você esta procurando ou não exixte ou não esta disponivel.')
        ])

if __name__ == '__main__':
    app.run(port=8051, debug=True)