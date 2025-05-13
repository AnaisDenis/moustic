import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import random
import numpy as np
from dash import dash_table

random.seed(42)

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

def detect_couples(df, distance_threshold=0.055):
    df_sorted = df.sort_values(by="time")
    all_times = df_sorted["time"].unique()
    active_collisions = {}
    collision_records = []

    for t in all_times:
        df_t = df_sorted[df_sorted["time"] == t]
        objs = df_t["object"].tolist()
        positions = df_t[["XSplined", "YSplined", "ZSplined"]].values

        for i in range(len(objs)):
            for j in range(i + 1, len(objs)):
                o1, o2 = sorted([objs[i], objs[j]])
                pos1, pos2 = positions[i], positions[j]
                dist = np.linalg.norm(pos1 - pos2)

                key = (o1, o2)

                if dist < distance_threshold:
                    if key not in active_collisions:
                        # Début d'une nouvelle collision
                        active_collisions[key] = {"start": t, "end": t}
                    else:
                        # Mise à jour de la fin
                        active_collisions[key]["end"] = t
                else:
                    if key in active_collisions:
                        # Collision terminée
                        record = {
                            "couple_id": f"{o1}-{o2}",
                            "object1": o1,
                            "object2": o2,
                            "start": active_collisions[key]["start"],
                            "end": active_collisions[key]["end"],
                            "duration": round(active_collisions[key]["end"] - active_collisions[key]["start"], 2)
                        }
                        collision_records.append(record)
                        del active_collisions[key]

    # Si collisions encore actives à la fin
    for (o1, o2), tvals in active_collisions.items():
        record = {
            "couple_id": f"{o1}-{o2}",
            "object1": o1,
            "object2": o2,
            "start": tvals["start"],
            "end": tvals["end"],
            "duration": round(tvals["end"] - tvals["start"], 2)
        }
        collision_records.append(record)

    return pd.DataFrame(collision_records)



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
                    {"label": "X, Y, Z en fonction du temps", "value": "xyzt"},
                ],
                value=["xy", "xz", "yz", "3d"],
                inline=False
            ),
            html.Br(),

            # Detection des couples
            html.Label("Fonctionnalités avancées :"),
            dbc.Checklist(
            id="detect-couples-check",
            options=[{"label": "Détecter les couples", "value": "detect"}],
            value=[],
            inline=True,
            ),
            html.Br(),

            html.Div([
                dbc.Button("Analyser les couples", id="analyze-couples", color="info", className="mb-3"),
                dbc.Button("Télécharger CSV", id="download-button", color="secondary", className="mb-3"),
                dcc.Download(id="download-csv"),
                dcc.Loading(
                    id="loading-output",
                    type="circle",
                    fullscreen=True,
                    children=html.Div([
                        html.Div(id="status-message",
                                 style={"marginBottom": "10px", "fontWeight": "bold", "color": "blue"}),
                        html.Div(id="couples-table-output")
                    ])
                )
            ]),



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
            html.Div(id="graphs-output"),
            html.Div(id="couples-table-output", className="mt-4")  # ici on ajoute le tableau dans la colonne principale
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

    plots = []

    # Graphe X, Y, Z en fonction du temps
    if "xyzt" in selected_graphs:
        fig_time_series = go.Figure()

        for obj in selected_objects:
            df_obj = df[df['object'] == obj]
            color = obj_colors[obj]

            fig_time_series.add_trace(go.Scatter(
                x=df_obj['time'], y=df_obj['XSplined'],
                mode='lines',
                name=f"{obj} - X",
                line=dict(color=color, dash='solid')
            ))

            fig_time_series.add_trace(go.Scatter(
                x=df_obj['time'], y=df_obj['YSplined'],
                mode='lines',
                name=f"{obj} - Y",
                line=dict(color=color, dash='dot')
            ))

            fig_time_series.add_trace(go.Scatter(
                x=df_obj['time'], y=df_obj['ZSplined'],
                mode='lines',
                name=f"{obj} - Z",
                line=dict(color=color, dash='dash')
            ))

        fig_time_series.update_layout(
            title="X, Y, Z en fonction du temps",
            xaxis_title="Temps",
            yaxis_title="Position",
            legend_title="Objet - Coordonnée",
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(gridcolor='lightgray'),
            yaxis=dict(gridcolor='lightgray'),
        )

        plots.append(dcc.Graph(figure=fig_time_series))

    # Si après ça, df_t est vide, on ne fait pas les autres graphes
    if df_t.empty:
        if plots:
            return plots  # Afficher au moins le graphe temporel
        else:
            return html.Div("Aucune donnée pour ce temps.")


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

dbc.Col([
    html.Div(id="graphs-output"),
    html.Div(id="couples-table-output", className="mt-4")  # Ajout ici
], width=9)

@app.callback(
    Output("couples-table-output", "children"),
    Output("status-message", "children"),
    Input("analyze-couples", "n_clicks"),
    State("detect-couples-check", "value"),
    prevent_initial_call=True
)


def display_couples(n_clicks, checkbox_value):
    if "detect" not in checkbox_value:
        return html.Div("La détection de couples n'est pas activée."), ""

    # Message temporaire pendant le traitement
    status = "⏳ Analyse en cours sur tout le fichier..."

    # Lancer le traitement
    couples_df = detect_couples(df)

    # Résultat de l'analyse
    if couples_df.empty:
        return html.Div("Aucune collision détectée."), ""

    # Tableau interactif
    table = dash_table.DataTable(
        id='couples-table',
        columns=[{"name": col, "id": col} for col in couples_df.columns],
        data=couples_df.to_dict("records"),
        sort_action='native',
        filter_action='none',
        page_action='native',
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'minWidth': '100px',
            'width': '150px',
            'maxWidth': '200px',
            'whiteSpace': 'normal'
        }
    )

    return table, ""



@app.callback(
    Output("download-csv", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def export_csv(n_clicks):
    couples_df = detect_couples(df)
    return dcc.send_data_frame(couples_df.to_csv, "couples_detectes.csv", index=False)

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)