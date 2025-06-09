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

card_icon = {
    "color": "white",
    "textAlign": "center",
    "fontSize": "50px",
    "margin": "auto",
}

# =========  Layout  =========== #
layout = dbc.Col(
    [
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
                                    html.Div(
                                        className="fa fa-university", style=card_icon
                                    ),
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
                                        html.Legend(
                                            "Despesas", className="text-center"
                                        ),
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
        )
    ]
)


# =========  Callbacks  =========== #
