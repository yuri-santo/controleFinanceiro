# app.py
import dash
import dash_bootstrap_components as dbc
import plotly.io as pio

pio.templates.default = "plotly"

external_stylesheets = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    "https://fonts.googleapis.com/icon?family=Material+Icons",
    dbc.themes.COSMO,
    dbc.themes.LUX,
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
app.config.prevent_initial_callbacks = "initial_duplicate"

app.scripts.config.serve_locally = True
server = app.server
