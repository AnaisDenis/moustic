import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import random

# ---------- Chargement des données ----------
CSV_PATH = "data/PostProc_Filtered_2020_09_03_18_15_53_Splined_reconstitue.csv"

df = pd.read_csv(CSV_PATH, sep=';')
df['time'] = pd.to_numeric(df['time'], errors='coerce')
df.dropna(subset=['time'], inplace=True)

# Convertir 'object' en catégorie pour éviter une échelle de couleurs continue
df['object'] = df['object'].astype('category')

# Calcul des valeurs minimales et maximales des axes
x_min, x_max = df['XSplined'].min(), df['XSplined'].max()
y_min, y_max = df['YSplined'].min(), df['YSplined'].max()
z_min, z_max = df['ZSplined'].min(), df['ZSplined'].max()

# Liste des couleurs spécifiques à choisir
color_list = [
    "antiquewhite", "aqua", "aquamarine", "bisque", "black", "blanchedalmond", "blue",
    "blueviolet", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue",
    "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgrey", "darkgreen",
    "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen",
    "darkslateblue", "darkslategray", "darkslategrey", "darkturquoise", "darkviolet", "deeppink", "deepskyblue",
    "dimgray", "dimgrey", "dodgerblue", "firebrick", "forestgreen", "fuchsia", "gainsboro",
    "gold", "goldenrod", "gray", "grey", "green", "greenyellow", "hotpink", "indianred", "indigo",
    "khaki", "lavender", "lawngreen", "lemonchiffon", "lightblue", "lightcoral", "lightcyan",
    "lightgoldenrodyellow", "lightgray", "lightgrey", "lightgreen", "lightpink", "lightsalmon", "lightseagreen",
    "lightskyblue", "lightslategray", "lightslategrey", "lightsteelblue", "lime", "limegreen",
    "magenta", "maroon", "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple",
    "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue",
    "mistyrose", "moccasin", "navajowhite", "navy", "olive", "olivedrab", "orange", "orangered",
    "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff", "peru", "pink",
    "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "rebeccapurple", "saddlebrown", "salmon",
    "sandybrown", "seagreen", "sienna", "silver", "skyblue", "slateblue", "slategray", "slategrey",
    "springgreen", "steelblue", "tan", "teal", "thistle", "tomato", "turquoise", "violet", "wheat",
    "yellow", "yellowgreen"
]


# Fonction qui choisit une couleur aléatoire parmi color_list
def generate_random_color():
    return random.choice(color_list)


# Attribuer une couleur aléatoire à chaque objet
obj_colors = {obj: generate_random_color() for obj in df['object'].unique()}
df['color'] = df['object'].map(obj_colors)

# ---------- Application Dash ----------
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Préparer la liste des objets uniques triés
sorted_objects = sorted(df['object'].unique(), key=lambda x: int(x))

# ---------- Layout ----------
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Détection de couples", className="my-3"),

            # Sélection du temps
            html.Label("Sélection du temps :"),
            dcc.Slider(
                id="time-slider",
                min=df['time'].min(),
                max=df['time'].max(),
                step=0.02,
                value=df['time'].min(),
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Br(),

            dbc.Input(id="manual-time", type="number", step=0.02,
                      value=df['time'].min(), debounce=True),
            html.Br(),

            # Sélection des types de graphiques
            html.Label("Graphiques à afficher :"),
            dbc.Checklist(
                id="graph-selection",
                options=[
                    {"label": "X en fonction de Y", "value": "xy"},
                    {"label": "X en fonction de Z", "value": "xz"},
                    {"label": "Y en fonction de Z", "value": "yz"},
                    {"label": "3D", "value": "3d"},
                ],
                value=["xy", "xz", "yz", "3d"],
                inline=False
            ),
            html.Br(),

            # Bouton Start/Stop
            dbc.Button("▶️ Start", id="start-stop-button", color="primary", className="me-2"),
            dcc.Interval(id="interval", interval=500, n_intervals=0, disabled=True),
            html.Br(), html.Br(),

            # Sélection des objets
            html.Label("Objets à afficher :"),
            dbc.ButtonGroup([
                dbc.Button("Tout cocher", id="select-all", color="success", size="sm"),
                dbc.Button("Tout décocher", id="deselect-all", color="danger", size="sm"),
            ], className="mb-2"),

            # Checklist des objets avec barre de défilement
            html.Div(
                dbc.Checklist(
                    id="object-checklist",
                    options=[{"label": str(obj), "value": obj} for obj in sorted_objects],
                    value=sorted_objects,  # Tous cochés par défaut
                    inline=False,
                    style={"maxHeight": "400px", "overflowY": "auto", "fontSize": "0.85em"}
                ),
                style={"marginBottom": "20px"}
            ),

        ], width=3, style={"backgroundColor": "#f8f9fa", "padding": "20px"}),

        dbc.Col([
            html.Div(id="graphs-output")
        ], width=9)
    ])
], fluid=True)


# ---------- Callbacks ----------

@app.callback(
    [Output("time-slider", "value"),
     Output("manual-time", "value")],
    [Input("manual-time", "value"),
     Input("time-slider", "value"),
     Input("interval", "n_intervals")],
    [State("time-slider", "value"),
     State("time-slider", "max"),
     State("start-stop-button", "children")],
    prevent_initial_call=True
)
def sync_time_slider_and_input(manual_value, slider_value, n_intervals, current_time, max_time, button_text):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == "manual-time":
        return manual_value, manual_value
    elif triggered_id == "time-slider":
        return slider_value, slider_value
    elif triggered_id == "interval" and button_text == "⏸️ Pause":
        next_time = round(current_time + 0.02, 2)
        if next_time > max_time:
            return max_time, max_time
        return next_time, next_time

    return current_time, current_time


@app.callback(
    Output("object-checklist", "value"),
    [Input("select-all", "n_clicks"),
     Input("deselect-all", "n_clicks")],
    [State("object-checklist", "options")],
    prevent_initial_call=True
)
def toggle_all_objects(select_clicks, deselect_clicks, options):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == "select-all":
        return [option['value'] for option in options]
    elif triggered_id == "deselect-all":
        return []

    return dash.no_update


@app.callback(
    Output("interval", "disabled"),
    Output("start-stop-button", "children"),
    Input("start-stop-button", "n_clicks"),
    State("interval", "disabled"),
    prevent_initial_call=True
)
def toggle_interval(n_clicks, disabled):
    if n_clicks is None:
        return dash.no_update, dash.no_update

    if disabled:
        return False, "⏸️ Pause"
    else:
        return True, "▶️ Start"


@app.callback(
    Output("graphs-output", "children"),
    [Input("time-slider", "value"),
     Input("graph-selection", "value"),
     Input("object-checklist", "value")],
    prevent_initial_call=True
)
def update_graphs(selected_time, selected_graphs, selected_objects):
    window = 0.02

    # Filtrer le DataFrame par le temps et les objets sélectionnés
    df_t = df[(df['time'] >= selected_time) & (df['time'] < selected_time + window)]

    if selected_objects:
        df_t = df_t[df_t['object'].isin(selected_objects)]
    else:
        return html.Div("Aucun objet sélectionné pour l'affichage.")

    if df_t.empty:
        return html.Div("Aucune donnée pour ce temps.")

    plots = []

    if "xy" in selected_graphs:
        fig = px.scatter(df_t, x="YSplined", y="XSplined", color="object",
                         title="X en fonction de Y", color_discrete_map=obj_colors)
        fig.update_layout(
            xaxis=dict(range=[y_min, y_max]),
            yaxis=dict(range=[x_min, x_max])
        )
        plots.append(dcc.Graph(figure=fig))

    if "xz" in selected_graphs:
        fig = px.scatter(df_t, x="ZSplined", y="XSplined", color="object",
                         title="X en fonction de Z", color_discrete_map=obj_colors)
        fig.update_layout(
            xaxis=dict(range=[z_min, z_max]),
            yaxis=dict(range=[x_min, x_max])
        )
        plots.append(dcc.Graph(figure=fig))

    if "yz" in selected_graphs:
        fig = px.scatter(df_t, x="ZSplined", y="YSplined", color="object",
                         title="Y en fonction de Z", color_discrete_map=obj_colors)
        fig.update_layout(
            xaxis=dict(range=[z_min, z_max]),
            yaxis=dict(range=[y_min, y_max])
        )
        plots.append(dcc.Graph(figure=fig))

    if "3d" in selected_graphs:
        fig3d = go.Figure(data=[go.Scatter3d(
            x=df_t['XSplined'], y=df_t['YSplined'], z=df_t['ZSplined'],
            mode='markers',
            marker=dict(size=3, color=df_t['object'].map(obj_colors)),
            text=df_t['object'],
            hoverinfo='text'
        )])
        fig3d.update_layout(
            title="Graphique 3D",
            margin=dict(l=0, r=0, b=0, t=30),
            scene=dict(
                xaxis=dict(range=[x_min, x_max]),
                yaxis=dict(range=[y_min, y_max]),
                zaxis=dict(range=[z_min, z_max])
            )
        )
        plots.append(dcc.Graph(figure=fig3d))

    # Organiser les graphiques par rangées de deux
    rows = []
    for i in range(0, len(plots), 2):
        row = dbc.Row(
            [
                dbc.Col(plots[i], width=6),
                dbc.Col(plots[i + 1] if i + 1 < len(plots) else None, width=6)
            ],
            className="mb-4"
        )
        rows.append(row)

    return rows


# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)