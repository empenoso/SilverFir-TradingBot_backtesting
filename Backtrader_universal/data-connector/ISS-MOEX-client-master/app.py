import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, title='Котировки MOEX',
                external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
                suppress_callback_exceptions=True)
server = app.server