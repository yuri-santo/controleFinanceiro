import dash
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from app import app
from services.firebase_service import salvar_dado, obter_dados
import pandas as pd

# =========  Função para gerar tabela de receitas ========= #
def criar_tabela_receitas():
    dados = obter_dados("receitas")
    
    if not dados:
        return html.Div("Nenhuma receita cadastrada.")
    
    for item in dados:
        if "categoria" not in item or item["categoria"] is None:
            item["categoria"] = ""
        else:
            item["categoria"] = str(item["categoria"])
    
    df = pd.DataFrame(dados)
    
    tabela = dash_table.DataTable(
        columns=[{"name": c.capitalize(), "id": c} for c in df.columns],
        data=df.to_dict('records'),
        hidden_columns=['id'],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'lightgray', 'fontWeight': 'bold'},
        page_size=10,
        column_selectable=False, 
    )
    
    return html.Div([
        html.H5("Tabela de Receitas"),  
        tabela
    ])


# =========  Layout  =========== #
layout = dbc.Col([
    html.H4("Receitas Registradas"),
    html.Div(id="tabelaReceitas", className='dbc'),
    html.Div(id="msgReceita"), 
    html.Hr(),
])

# =========  Callback  =========== #
@app.callback(
    Output("tabelaReceitas", "children"),
    Output("msgReceita", "children"),
    Input("salvarReceita", "n_clicks"),
    Input("page-content", "children"),
    State("descricaoReceita", "value"),
    State("valorReceita", "value"),
    State("dataReceita", "date"),
    State("selectReceita", "value"),
    prevent_initial_call=True
)
def salvar_ou_carregar_tabela(n_clicks, _, descricao, valor, data, categoria):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "salvarReceita":
        if not all([descricao, valor, data, categoria]):
            return criar_tabela_receitas(), dbc.Alert("Preencha todos os campos!", color="danger")
        nova = {
            "descricao": descricao,
            "valor": float(valor),
            "data": data,
            "categoria": categoria
        }
        salvar_dado("receitas", nova)
        return criar_tabela_receitas(), dbc.Alert("Receita salva com sucesso!", color="success")

    elif trigger == "page-content":
        return criar_tabela_receitas(), dash.no_update
