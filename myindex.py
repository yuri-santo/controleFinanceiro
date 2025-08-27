# myindex.py
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import threading
import webbrowser

from app import app
# importe seus módulos de páginas/componentes
from components import sidebar, dashboards, extratos, simulacoes, carteira, ir

# ===== Layout principal =====
app.layout = dbc.Container(children=[
    dcc.Location(id='url'),
    dbc.Row([
        dbc.Col([ sidebar.layout ], md=3),                   # <-- Sidebar SEMPRE presente
        dbc.Col([ html.Div(id="page-content") ], md=9),
    ])
], fluid=True)

# ===== Validation layout =====
# registra todos os componentes possíveis (evita "nonexistent object")
app.validation_layout = html.Div([
    app.layout,
    sidebar.layout,
    dashboards.layout,
    extratos.layout,
    simulacoes.layout,
    ir.layout,
    carteira.layout(),   # função layout() no arquivo carteira.py
])

# ===== Roteamento =====
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def page(pathname):
    if pathname in ('/', '/dashboards'):
        return dashboards.layout
    elif pathname == '/extratos':
        return extratos.layout
    elif pathname == '/simulacoes':
        return simulacoes.layout
    elif pathname == '/ir':
        return ir.layout
    elif pathname == '/carteira':
        return carteira.layout()
    else:
        return html.Div([
            html.H1('404: Página não encontrada'),
            html.P('A página que você está procurando não existe.'),
        ])

# ===== Boot =====
if __name__ == '__main__':
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8051")).start()
    app.run(port=8051, debug=True)
