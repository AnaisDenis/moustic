from dash import Dash
import dash_bootstrap_components as dbc
import random

def main():
    random.seed(42)

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server

    app.config.suppress_callback_exceptions = True
    app.config.prevent_initial_callbacks = 'initial_duplicate'

    # Importer layout **après** la création de `app`
    from src.layout import layout
    app.layout = layout

    # Enregistrer les callbacks
    from src.callbacks import register_callbacks
    register_callbacks(app)

    app.run(debug=True)

# Permet d'exécuter directement le script OU via `moustic` depuis pyproject.toml
if __name__ == '__main__':
    main()
