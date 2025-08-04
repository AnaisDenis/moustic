from dash import Dash
import dash_bootstrap_components as dbc
import random



random.seed(42)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.config.suppress_callback_exceptions = True
app.config.prevent_initial_callbacks = 'initial_duplicate'

# Importer layout **après** création de app
from src.layout import layout
app.layout = layout

# Importer callbacks ET enregistrer les callbacks **après** création de app
from src.callbacks import register_callbacks
register_callbacks(app)   # appel d’une fonction à définir dans callbacks.py

if __name__ == '__main__':
    app.run(debug=True)
