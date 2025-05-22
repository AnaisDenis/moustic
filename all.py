import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
import random
import numpy as np
from dash import dash_table
import base64
import io
from dash import dcc

random.seed(42)


# ---------- Fonctions d'aide ----------
def assign_colors_to_objects(objects):
    """Assigne une couleur unique à chaque objet à partir de la palette"""
    # Assurez-vous que tous les objets sont convertis en chaînes
    objects_str = [str(obj) for obj in objects]
    return {obj: color_palette[i % len(color_palette)] for i, obj in enumerate(sorted(objects_str))}



def detect_interactions(df, distance_threshold=0.055, time_gap_threshold=0.05, min_duration=1.0):
    """Détecte les couples d'objets proches, filtre ceux dont la durée < min_duration."""
    df_sorted = df.sort_values(by="time")
    all_times = df_sorted["time"].unique()
    active_collisions = {}
    collision_records = []
    interaction_counters = {}

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
                        if key not in interaction_counters:
                            interaction_counters[key] = 0
                        interaction_counters[key] += 1
                        suffix = chr(96 + interaction_counters[key])
                        interaction_id = f"{o1}-{o2}-{suffix}"
                        active_collisions[key] = {
                            "interaction_id": interaction_id,
                            "start": t,
                            "end": t,
                            "last_time": t
                        }
                    else:
                        last_time = active_collisions[key]["last_time"]
                        if t - last_time > time_gap_threshold:
                            duration = active_collisions[key]["end"] - active_collisions[key]["start"]
                            if duration >= min_duration:
                                record = {
                                    "interaction_id": active_collisions[key]["interaction_id"],
                                    "object1": o1,
                                    "object2": o2,
                                    "start": active_collisions[key]["start"],
                                    "end": active_collisions[key]["end"],
                                    "duration": round(duration, 2)
                                }
                                collision_records.append(record)
                            interaction_counters[key] += 1
                            suffix = chr(96 + interaction_counters[key])
                            interaction_id = f"{o1}-{o2}-{suffix}"
                            active_collisions[key] = {
                                "interaction_id": interaction_id,
                                "start": t,
                                "end": t,
                                "last_time": t
                            }
                        else:
                            active_collisions[key]["end"] = t
                            active_collisions[key]["last_time"] = t
                else:
                    if key in active_collisions:
                        duration = active_collisions[key]["end"] - active_collisions[key]["start"]
                        if duration >= min_duration:
                            record = {
                                "interaction_id": active_collisions[key]["interaction_id"],
                                "object1": o1,
                                "object2": o2,
                                "start": active_collisions[key]["start"],
                                "end": active_collisions[key]["end"],
                                "duration": round(duration, 2)
                            }
                            collision_records.append(record)
                        del active_collisions[key]

    for (o1, o2), vals in active_collisions.items():
        duration = vals["end"] - vals["start"]
        if duration >= min_duration:
            record = {
                "interaction_id": vals["interaction_id"],
                "object1": o1,
                "object2": o2,
                "start": vals["start"],
                "end": vals["end"],
                "duration": round(duration, 2)
            }
            collision_records.append(record)

    return pd.DataFrame(collision_records)





def detect_union(df, distance_seuil=0.02):
    """
    Détecte les objets qui pourraient avoir fusionné avec un autre
    en se basant sur la proximité lors de leur dernier instant de vie.

    Paramètres :
        df (pd.DataFrame) : contient 'object', 'time', 'XSplined', 'YSplined', 'ZSplined'
        distance_seuil (float) : distance maximale pour considérer une fusion

    Retour :
        pd.DataFrame : lignes indiquant les fusions possibles
    """
    df_sorted = df.sort_values(by=["object", "time"])
    fusion_records = []

    # Dernière observation pour chaque objet
    last_obs = df_sorted.groupby("object").tail(1)

    for idx, row in last_obs.iterrows():
        obj_a = row["object"]
        t_final = row["time"]
        pos_a = np.array([row["XSplined"], row["YSplined"], row["ZSplined"]])

        # Tous les objets présents au moment t_final (sauf A)
        df_at_t = df_sorted[(df_sorted["time"] == t_final) & (df_sorted["object"] != obj_a)]

        for _, row_b in df_at_t.iterrows():
            obj_b = row_b["object"]
            pos_b = np.array([row_b["XSplined"], row_b["YSplined"], row_b["ZSplined"]])
            dist = np.linalg.norm(pos_a - pos_b)

            if dist < distance_seuil:
                fusion_records.append({
                    "fusion_id": f"{obj_a}-{obj_b}",
                    "object1": obj_a,
                    "object2": obj_b,
                    "fusion_time": t_final,
                    "distance": round(dist, 5),
                    "fusion_name" : obj_b
                })

    return pd.DataFrame(fusion_records)



def detect_rupture(df, distance_seuil=0.02):
    """
    Détecte les objets qui pourraient être issus d'une rupture (apparition soudaine proche d'un autre objet)
    en se basant sur la proximité lors de leur premier instant de vie.

    Paramètres :
        df (pd.DataFrame) : contient 'object', 'time', 'XSplined', 'YSplined', 'ZSplined'
        distance_seuil (float) : distance maximale pour considérer une rupture

    Retour :
        pd.DataFrame : lignes indiquant les ruptures possibles
    """
    df_sorted = df.sort_values(by=["object", "time"])
    rupture_records = []

    # Première observation pour chaque objet
    first_obs = df_sorted.groupby("object").head(1)

    for idx, row in first_obs.iterrows():
        obj_a = row["object"]
        t_initial = row["time"]
        pos_a = np.array([row["XSplined"], row["YSplined"], row["ZSplined"]])

        # Tous les objets présents au même moment (sauf A)
        df_at_t = df_sorted[(df_sorted["time"] == t_initial) & (df_sorted["object"] != obj_a)]

        for _, row_b in df_at_t.iterrows():
            obj_b = row_b["object"]
            pos_b = np.array([row_b["XSplined"], row_b["YSplined"], row_b["ZSplined"]])
            dist = np.linalg.norm(pos_a - pos_b)

            if dist < distance_seuil:
                rupture_records.append({
                    "rupture_id": f"{obj_b}-{obj_a}",
                    "object1": obj_a,
                    "object2": obj_b,
                    "rupture_time": t_initial,
                    "distance": round(dist, 5),
                    "rupture_name": obj_b
                })

    return pd.DataFrame(rupture_records)

def detect_couples(inter_df, union_df, rupture_df):
    couples_records = []

    for _, fusion in union_df.iterrows():
        fusion_name = fusion["fusion_name"]
        fusion_time = fusion["fusion_time"]
        obj1_preF = fusion["object1"]
        obj2_preF = fusion["object2"]

        matching_ruptures = rupture_df[rupture_df["rupture_name"] == fusion_name]

        for _, rupture in matching_ruptures.iterrows():
            rupture_time = rupture["rupture_time"]
            if rupture_time > fusion_time:
                obj3_postR = rupture["object1"]
                obj4_postR = rupture["object2"]
                duration_couple = round(rupture_time - fusion_time, 3)

                # Identifier le couple peu importe l'ordre
                couple_id_1 = f"{obj1_preF}-{obj2_preF}"
                couple_id_2 = f"{obj2_preF}-{obj1_preF}"

                # Chercher toutes les interactions avec ce couple, peu importe le suffixe
                inter_rows = inter_df[inter_df["interaction_id"].str.startswith(couple_id_1) |
                                      inter_df["interaction_id"].str.startswith(couple_id_2)]

                interaction_count = len(inter_rows)
                total_duration = inter_rows["duration"].sum() if not inter_rows.empty else 0

                couples_records.append({
                    "name_couple": fusion_name,
                    "obj1preF": obj1_preF,
                    "obj2preF": obj2_preF,
                    "obj3postR": obj3_postR,
                    "obj4postR": obj4_postR,
                    "timeF": fusion_time,
                    "timeR": rupture_time,
                    "duration_couple": duration_couple,
                    "interaction_count": interaction_count,
                    "total_duration": round(total_duration, 3)
                })

    return pd.DataFrame(couples_records)



def detect_rupture_fusion(inter_df, union_df, rupture_df):
    couples_records = []

    for _, fusion in union_df.iterrows():
        fusion_name = fusion["fusion_name"]
        fusion_time = fusion["fusion_time"]
        obj1_preF = fusion["object1"]
        obj2_preF = fusion["object2"]

        matching_ruptures = rupture_df[rupture_df["rupture_name"] == fusion_name]

        for _, rupture in matching_ruptures.iterrows():
            rupture_time = rupture["rupture_time"]
            if rupture_time < fusion_time:
                obj3_postR = rupture["object1"]
                obj4_postR = rupture["object2"]
                duration_couple = round(fusion_time - rupture_time, 3)  # durée positive

                # Identifier le couple, peu importe l'ordre
                couple_id_1 = f"{obj1_preF}-{obj2_preF}"
                couple_id_2 = f"{obj2_preF}-{obj1_preF}"

                # Récupérer toutes les interactions associées à ce couple
                inter_rows = inter_df[inter_df["interaction_id"].str.startswith(couple_id_1) |
                                      inter_df["interaction_id"].str.startswith(couple_id_2)]

                interaction_count = len(inter_rows)
                total_duration = inter_rows["duration"].sum() if not inter_rows.empty else 0

                couples_records.append({
                    "name_couple": fusion_name,
                    "obj1preF": obj1_preF,
                    "obj2preF": obj2_preF,
                    "obj3postR": obj3_postR,
                    "obj4postR": obj4_postR,
                    "timeF": fusion_time,
                    "timeR": rupture_time,
                    "duration_couple": duration_couple,
                    "interaction_count": interaction_count,
                    "total_duration": round(total_duration, 3)
                })

    return pd.DataFrame(couples_records)



def parse_contents(contents, filename):
    """Analyse le contenu du fichier téléchargé"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume que le fichier est un CSV avec séparateur point-virgule
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=';')
        else:
            return None, "Le fichier doit être au format CSV."

        # Vérifier si les colonnes nécessaires sont présentes
        required_cols = ['time', 'object', 'XSplined', 'YSplined', 'ZSplined']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            return None, f"Colonnes manquantes dans le fichier: {', '.join(missing_cols)}"

        # Traiter les données comme dans votre code original
        df['time'] = pd.to_numeric(df['time'], errors='coerce')
        df.dropna(subset=['time'], inplace=True)
        # Modifier cette partie
        df['object'] = df['object'].astype('category')  # Les objets sont déjà traités comme des chaînes

        # Attribuer des couleurs aux objets de manière cohérente
        unique_objects = sorted(df['object'].unique())  # Pas besoin de conversion ici
        obj_colors = assign_colors_to_objects(unique_objects)

        # Assurez-vous que les clés dans obj_colors sont du même type que les valeurs dans df['object']
        df['color'] = df['object'].map(lambda x: obj_colors.get(str(x), "#000000"))

        return df, obj_colors, "Fichier chargé avec succès"

    except Exception as e:
        return None, None, f"Erreur lors du chargement du fichier: {str(e)}"


def get_objects_with_star_3d(df, selected_objects, selected_time, distance_threshold=0.1, min_vectors=2):
    """
    Identifie les objets qui sont pointés par au moins min_vectors autres objets à un instant donné.

    Retourne aussi les vecteurs de direction vers les étoiles détectées.
    """
    df_time = df[(df['time'] == selected_time) & (df['object'].isin(selected_objects))]

    if df_time.empty:
        return [], []

    star_candidates = {}
    pointing_pairs = []

    for _, source_obj in df_time.iterrows():
        source_id = int(source_obj['object'])
        source_pos = np.array([source_obj['XSplined'], source_obj['YSplined'], source_obj['ZSplined']])
        source_vel = np.array([source_obj['VXSplined'], source_obj['VYSplined'], source_obj['VZSplined']])

        norm = np.linalg.norm(source_vel)
        if norm == 0:
            continue

        source_dir = source_vel / norm

        for _, target_obj in df_time.iterrows():
            target_id = int(target_obj['object'])
            if target_id == source_id:
                continue

            target_pos = np.array([target_obj['XSplined'], target_obj['YSplined'], target_obj['ZSplined']])
            vector_to_target = target_pos - source_pos
            distance = np.linalg.norm(vector_to_target)

            if distance == 0:
                continue

            dir_to_target = vector_to_target / distance
            dot_product = np.dot(source_dir, dir_to_target)

            if dot_product > 0.9 and distance <= distance_threshold:
                pointing_pairs.append((source_id, target_id))
                star_candidates[target_id] = star_candidates.get(target_id, 0) + 1

    starred_objects = [obj_id for obj_id, count in star_candidates.items() if count >= min_vectors]
    return starred_objects, pointing_pairs


def count_closest_neighbors_with_ties(df, tol=1e-6):
    """
    Pour chaque objet dans le DataFrame donné, trouve les objets les plus proches
    (en cas d'égalité, tous sont pris en compte) et incrémente leur compteur.

    df doit contenir les colonnes 'object', 'XSplined', 'YSplined', 'ZSplined'

    Retour :
    - dict {objet: nombre de fois où il est le plus proche d’un autre}
    """
    positions = {
        row['object']: np.array([row['XSplined'], row['YSplined'], row['ZSplined']])
        for _, row in df.iterrows()
    }

    neighbor_counts = {obj: 0 for obj in positions}

    for obj1 in positions:
        dists = {}
        for obj2 in positions:
            if obj1 == obj2:
                continue
            dist = np.linalg.norm(positions[obj1] - positions[obj2])
            dists[obj2] = dist

        if not dists:
            continue

        min_dist = min(dists.values())

        closest_objs = [obj for obj, dist in dists.items() if abs(dist - min_dist) <= tol]

        for neighbor in closest_objs:
            neighbor_counts[neighbor] += 1

    return neighbor_counts

# Liste de couleurs spécifiques (vous pouvez en ajouter plus si nécessaire)
color_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5"
]

# ---------- Initialisation de l'application ----------
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Ajoutez cette configuration pour gérer les callbacks en double
app.config.suppress_callback_exceptions = True
app.config.prevent_initial_callbacks = 'initial_duplicate'

# ---------- Layout ----------

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Détection de couples", className="my-3 text-primary fw-bold"),

            # Bloc : Fichier
            html.H5("1️⃣ Charger un fichier CSV", className="mt-4 text-secondary"),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['📁 Glisser-déposer ou ', html.A('sélectionner un fichier')]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='upload-status', style={'color': 'green'}),

            # Bloc : Info sur le fichier avec prévention de débordement du texte
            html.Div(
                id='file-info',
                title="",  # Info-bulle avec le nom complet
                style={
                    'margin': '10px 0',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': '100%',
                    'color': 'gray',
                    'fontSize': '0.85rem'
                }
            ),

            # Bloc : Contrôle du temps
            html.H5("2️⃣ Contrôle du temps", className="mt-4 text-secondary"),
            html.Label("Temps sélectionné :"),
            dcc.Slider(
                id="time-slider",
                min=0, max=10, step=0.02, value=0,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
                disabled=True
            ),
            dbc.Input(id="manual-time", type="number", step=0.02, value=0, debounce=True, disabled=True,
                      className="mt-2"),
            dbc.Button("▶️ Start", id="start-stop-button", color="primary", className="mt-3 w-100", disabled=True),
            dcc.Interval(id="interval", interval=500, n_intervals=0, disabled=True),

            html.Label("⏱️ Vitesse de lecture (ms entre frames) :"),
            dcc.Slider(
                id="interval-slider",
                min=50,
                max=1000,
                step=50,
                value=500,  # Valeur par défaut
                marks={i: f"{i} ms" for i in range(100, 1001, 200)},
                tooltip={"placement": "bottom", "always_visible": False},
                className="mt-2 mb-3"
            ),



            # Bloc : Affichage des graphes
            html.H5("3️⃣ Options d'affichage", className="mt-4 text-secondary"),
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
                value=["xy", "xz"],
                inline=False,
                className="mb-3"
            ),
            html.Label("Options graphiques :"),
            dbc.Checklist(
                id="show-trajectory",
                options=[{"label": "Afficher trajectoire continue", "value": "trajectory"}],
                value=[],
                inline=True,
            ),
            # Checklist vecteurs
            dbc.Checklist(
                id="show-vectors",
                options=[{"label": "Afficher vecteurs de direction", "value": "vectors"}],
                value=[],
                inline=True,
            ),

            # Div masqué conditionnellement
            html.Div(
                id="vector-parameters-container",
                children=[
                    dbc.Label("Nombre minimal de vecteurs"),
                    dbc.Input(id="min-vectors-input", type="number", min=1, step=1, value=2),

                    dbc.Label("Distance maximale"),
                    dbc.Input(id="distance-threshold-input", type="number", step=0.01, value=0.1),
                ],
                style={"marginLeft": "20px", "marginTop": "10px", "maxWidth": "300px"},
            ),
            dbc.Checklist(
                id="color-by-speed",
                options=[{"label": "Colorer par vitesse", "value": "by_speed"}],
                value=[],
                inline=True,
                className=""
            ),
            dbc.Checklist(
                id="color-by-neighbors",
                options=[{"label": "Colorer par plus proches voisins", "value": "neighbors"}],
                value=[],
                inline=True,
                className="mb-3"
            ),

            # Bloc : Détection de couples
            html.H5("4️⃣ Détection de couples", className="mt-4 text-secondary"),

            dbc.Checklist(
                id="detect-couples-check",
                options=[
                    {"label": "Détecter les interactions", "value": "detect_interaction"},
                    {"label": "Détecter les fusions", "value": "detect_union"},
                    {"label": "Détecter les ruptures", "value": "detect_rupture"},
                    {"label": "Détecter les couples", "value": "detect_couples"},
                    {"label": "Détecter les ruptures-fusions", "value": "detect_rupture_fusion"},
                ],
                value=[],
                inline=True,
            ),

            # Sliders séparés pour chaque type
            html.Label("Seuil de distance pour les interractions :"),
            dcc.Slider(
                id="distance-threshold-interraction",
                min=0, max=0.1, step=0.001, value=0.055,
                marks={i: str(i) for i in [0, 0.02, 0.04, 0.06, 0.08, 0.1]},
                tooltip={"placement": "bottom", "always_visible": True}
            ),

            html.Label("Durée minimale d'une interaction (s) :"),
            dcc.Slider(
                id="min-duration-threshold",
                min=0, max=5, step=0.1, value=1.0,
                marks={i: f"{i}s" for i in range(6)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),


            html.Label("Distance seuil pour fusions/ruptures :"),
            dcc.Slider(
                id="distance-threshold-unionrupture-slider",
                min=0, max=0.1, step=0.001, value=0.02,
                marks={i: str(i) for i in [0, 0.02, 0.04, 0.06, 0.08, 0.1]},
                tooltip={"placement": "bottom", "always_visible": True}
            ),

            # Boutons
            dbc.Button("Analyser les couples", id="analyze-couples", color="primary", className="mt-3 w-100"),

            dcc.Loading(
                id="loading-analyze",
                type="circle",  # ou 'default', 'dot'
                fullscreen=True,
                children=html.Div(id="loading-status")
            ),


            dbc.Button("Télécharger CSV", id="download-button", color="secondary", className="mt-2 w-100",
                       disabled=True),
            dbc.Button("Afficher les tableaux", id="show-tables-button", color="info", className="mt-2 w-100"),


            # Sortie CSV et état
            dcc.Download(id="download-csv"),
            dcc.Loading(
                id="loading-output",
                type="circle",
                fullscreen=True,
                children=html.Div([
                    html.Div(id="status-message", style={"fontWeight": "bold", "color": "blue"}),
                ])
            ),
            dcc.Store(id="analysis-complete", data=False),
            dcc.Store(id='store-interactions'),
            dcc.Store(id='store-fusions'),
            dcc.Store(id='store-ruptures'),
            dcc.Store(id='store-couples'),
            dcc.Store(id='store-rupture-fusion'),

            # Bloc : Objets à afficher
            html.H5("5️⃣ Objets à afficher", className="mt-4 text-secondary"),
            dbc.ButtonGroup([
                dbc.Button("Tout cocher", id="select-all", color="success", size="sm", disabled=True),
                dbc.Button("Tout décocher", id="deselect-all", color="danger", size="sm", disabled=True),
            ], className="mb-2"),
            html.Div(
                dbc.Checklist(
                    id="object-checklist",
                    options=[],
                    value=[],
                    inline=False,
                    style={"maxHeight": "400px", "overflowY": "auto"}
                ),
                id="object-checklist-container"
            )

        ], width=3, style={"backgroundColor": "#f8f9fa", "padding": "20px", "borderRight": "1px solid #dee2e6"}),

        dbc.Col([
            html.Div(id="graphs-output"),
            html.Div(id="couples-table-output", className="mt-4")
        ], width=9)
    ])
], fluid=True)

# Stores
app.layout.children.append(dcc.Store(id='upload-data-storage'))
app.layout.children.append(dcc.Store(id='object-colors-storage'))
app.layout.children.append(dcc.Store(id='axis-ranges-storage'))


# ---------- Callbacks ----------

@app.callback(
    [Output('upload-data-storage', 'data', allow_duplicate=True),
     Output('object-colors-storage', 'data'),
     Output('axis-ranges-storage', 'data'),
     Output('upload-status', 'children'),
     Output('time-slider', 'min'),
     Output('time-slider', 'max'),
     Output('time-slider', 'value'),
     Output('time-slider', 'disabled'),
     Output('manual-time', 'disabled'),
     Output('manual-time', 'value'),
     Output('start-stop-button', 'disabled'),
     Output('analyze-couples', 'disabled'),
     Output('download-button', 'disabled'),
     Output('select-all', 'disabled'),
     Output('deselect-all', 'disabled'),
     Output('object-checklist-container', 'children'),
     Output('file-info', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')],
    prevent_initial_call=True
)
def update_output(contents, filename):
    if contents is None:
        # Valeurs par défaut si aucun fichier n'est chargé
        return None, None, None, "", 0, 10, 0, True, True, 0, True, True, True, True, True, "", ""

    df, obj_colors, status_message = parse_contents(contents, filename)

    if df is None:
        # En cas d'erreur lors du chargement du fichier
        return None, None, None, status_message, 0, 10, 0, True, True, 0, True, True, True, True, True, "", ""

    # Calcul des limites des axes
    axis_ranges = {
        'x_min': df['XSplined'].min(), 'x_max': df['XSplined'].max(),
        'y_min': df['YSplined'].min(), 'y_max': df['YSplined'].max(),
        'z_min': df['ZSplined'].min(), 'z_max': df['ZSplined'].max()
    }

    # Préparer la liste des objets uniques triés
    sorted_objects = sorted(df['object'].unique(), key=lambda x: int(x))

    # Création de la checklist des objets
    object_checklist = dbc.Checklist(
        id="object-checklist",
        options=[{"label": str(obj), "value": obj} for obj in sorted_objects],
        value=sorted_objects,  # Tous cochés par défaut
        inline=False,
        style={"maxHeight": "400px", "overflowY": "auto", "fontSize": "0.85em"}
    )

    # Informations sur le fichier
    file_info = html.Div([
        html.P(f"Fichier: {filename}"),
        html.P(f"Nombre d'objets: {len(sorted_objects)}"),
        html.P(f"Plage de temps: {df['time'].min():.2f} à {df['time'].max():.2f}")
    ])

    return (df.to_json(date_format='iso', orient='split'),
            obj_colors,
            axis_ranges,
            status_message,
            df['time'].min(),
            df['time'].max(),
            df['time'].min(),
            False,
            False,
            df['time'].min(),
            False,
            False,
            False,
            False,
            False,
            object_checklist,
            file_info)


@app.callback(
    [Output("time-slider", "value", allow_duplicate=True),
     Output("manual-time", "value", allow_duplicate=True)],
    [Input("manual-time", "value"),
     Input("time-slider", "value"),
     Input("interval", "n_intervals")],
    [State("time-slider", "value"),
     State("time-slider", "max"),
     State("start-stop-button", "children"),
     State("time-slider", "disabled")],
    prevent_initial_call='initial_duplicate'  # Modifié ici
)
def sync_time_slider_and_input(manual_value, slider_value, n_intervals, current_time, max_time, button_text,
                               slider_disabled):
    if slider_disabled:
        return current_time, current_time

    ctx = callback_context
    if not ctx.triggered:
        return current_time, current_time

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
    [Output("interval", "disabled"),
     Output("start-stop-button", "children")],
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
    Output("interval", "interval"),
    Input("interval-slider", "value")
)
def update_interval_speed(user_interval):
    return user_interval





@callback(
    Output("vector-parameters-container", "style"),
    Input("show-vectors", "value"),
    prevent_initial_call=False
)
def toggle_vector_parameters(show_vectors):
    if "vectors" in show_vectors:
        return {"display": "block", "marginLeft": "20px", "marginTop": "10px", "maxWidth": "300px"}
    else:
        return {"display": "none"}



@app.callback(
    Output("graphs-output", "children"),
    [Input("time-slider", "value"),
     Input("graph-selection", "value"),
     Input("object-checklist", "value"),
     Input("show-trajectory", "value"),
     Input("show-vectors", "value"),
     Input("color-by-speed", "value"),
     Input("min-vectors-input", "value"),
     Input("distance-threshold-input", "value"),
     Input("color-by-neighbors", "value")     ],
    [State("upload-data-storage", "data"),
     State("object-colors-storage", "data"),
     State("axis-ranges-storage", "data")],
    prevent_initial_call=True
)
def update_graphs(selected_time, selected_graphs, selected_objects, show_trajectory, show_vectors, color_by_speed,
                  min_vectors, distance_threshold, color_by_neighbors,
                  df_json, obj_colors_data, axis_ranges_data):

    if df_json is None or not selected_objects:
        return html.Div("Veuillez charger un fichier CSV et sélectionner des objets.")

    # Convertir JSON en DataFrame
    try:
        df = pd.read_json(df_json, orient='split')
    except ValueError as e:
        return html.Div(f"Erreur lors de la conversion du fichier JSON en DataFrame : {e}")

    # Récupérer les couleurs et les plages d'axes
    if not isinstance(obj_colors_data, dict):
        obj_colors = {}  # Gestion des erreurs
    else:
        obj_colors = obj_colors_data

    if not isinstance(axis_ranges_data, dict):
        axis_ranges = {}  # Gestion des erreurs
    else:
        axis_ranges = axis_ranges_data

    window = 0.02
    plots = []

    # Filtrer le DataFrame par les objets sélectionnés (pour XYZT)
    df_selected_objects = df[df['object'].isin(selected_objects)] if selected_objects else df

    if df_selected_objects.empty:
        return html.Div("Aucun des objets sélectionnés n'a été trouvé dans les données.")



    # Filtrer le DataFrame complet pour les objets sélectionnés (pour les trajectoires)
    df_all_times = df[df['object'].isin(selected_objects)] if selected_objects else df

    # Maintenant, filtrer par temps pour les autres graphiques
    df_t = df[(df['time'] >= selected_time) & (df['time'] < selected_time + window)]

    # Calculer la vitesse pour la coloration si nécessaire
    df_t["speed"] = np.sqrt(df_t["VXSplined"] ** 2 + df_t["VYSplined"] ** 2 + df_t["VZSplined"] ** 2)

    df_t["neighbors_count"] = 0  # valeur par défaut

    if "neighbors" in color_by_neighbors:
        neighbor_counts = count_closest_neighbors_with_ties(df_t)
        df_t["neighbors_count"] = df_t["object"].map(neighbor_counts)
        max_neighbors = max(neighbor_counts.values()) if neighbor_counts else 1
    else:
        max_neighbors = 1


    if selected_objects:
        df_t = df_t[df_t['object'].isin(selected_objects)]

    if "by_speed" in color_by_speed:
        speed_min = 0
        speed_max = 1.3

    # Récupérer min_vectors et distance_threshold avec des valeurs par défaut
    if min_vectors is None:
        min_vectors = 2
    else:
        min_vectors = int(min_vectors)

    if distance_threshold is None:
        distance_threshold = 0.1
    else:
        distance_threshold = float(distance_threshold)

    if show_vectors and "vectors" in show_vectors:
        objects_with_star_3d, pointing_pairs = get_objects_with_star_3d(
            df,
            selected_objects,
            selected_time,
            distance_threshold=distance_threshold,
            min_vectors=min_vectors
        )
        # Construire un set des sources qui pointent vers des étoiles
        pointing_sources = {source for source, target in pointing_pairs if target in objects_with_star_3d}

    else:
        objects_with_star_3d = []


    if "xy" in selected_graphs:
        # Créer la figure avec go.Figure()
        fig_xy = go.Figure()

        # Ajouter chaque objet
        for obj in selected_objects:
            df_obj = df_t[df_t['object'] == obj]
            if not df_obj.empty:
                str_obj = str(obj)

                if "neighbors" in color_by_neighbors:
                    marker = dict(
                        size=8,
                        color=df_obj["neighbors_count"],
                        colorscale="Plasma",
                        cmin=0,
                        cmax=max_neighbors,
                        showscale=True,  # Toujours visible
                        colorbar=dict(title="Voisins")  # Toujours visible
                    )
                    showlegend = False
                    name = None

                elif "by_speed" in color_by_speed:
                    # Colorer par vitesse + colorbar à gauche
                    marker = dict(
                        size=8,
                        color=df_obj["speed"],
                        colorscale="Viridis",
                        cmin=speed_min,
                        cmax=speed_max,
                        showscale=True,
                        colorbar=dict(title="Vitesse")
                    )
                    showlegend = False
                    name = None
                else:
                    # Couleur fixe par objet + légende visible
                    color = obj_colors.get(str_obj, "#000000")
                    marker = dict(size=8, color=color)
                    showlegend = True
                    name = str_obj

                fig_xy.add_trace(go.Scatter(
                    x=df_obj["YSplined"],
                    y=df_obj["XSplined"],
                    mode="markers",
                    marker=marker,
                    name=name,
                    showlegend=showlegend
                ))

                # Ajouter la trajectoire si l'option est activée
                if "trajectory" in show_trajectory:
                    df_obj_all = df_all_times[df_all_times['object'] == obj]
                    fig_xy.add_trace(go.Scatter(
                        x=df_obj_all["YSplined"],
                        y=df_obj_all["XSplined"],
                        mode='lines',
                        line=dict(color=color, width=1),
                        name=f"{obj} (trajectoire)",
                        opacity=0.5
                    ))

                # Ajouter une ligne directionnelle en XY si les vecteurs sont activés
                if show_vectors and "vectors" in show_vectors:
                    df_obj_all = df[df['object'] == obj].copy()
                    df_obj_all["time_diff"] = abs(df_obj_all["time"] - selected_time)
                    df_obj_current = df_obj_all.sort_values("time_diff").head(1)

                    if not df_obj_current.empty:
                        current_pos = df_obj_current[["YSplined", "XSplined"]].iloc[0].values  # Y en X ici

                        df_obj_next = df_obj_all[df_obj_all["time"] > df_obj_current["time"].values[0]].sort_values(
                            "time").head(1)
                        if not df_obj_next.empty:
                            next_pos = df_obj_next[["YSplined", "XSplined"]].iloc[0].values

                            vector = next_pos - current_pos
                            norm = np.linalg.norm(vector)

                            if norm > 0.001:
                                unit_vector = vector / norm
                                scale = 0.1  # allongement du vecteur directionnel
                                extended_vector = unit_vector * scale
                                end_pos = current_pos + extended_vector

                                fig_xy.add_trace(go.Scatter(
                                    x=[current_pos[0], end_pos[0]],  # Y
                                    y=[current_pos[1], end_pos[1]],  # X
                                    mode='lines',
                                    line=dict(color='black', width=2),
                                    showlegend=False,
                                    name=f"Direction {obj}"
                                ))

        # Mettre à jour la mise en page
        fig_xy.update_layout(
            title="X en fonction de Y",
            xaxis_title="Y",
            yaxis_title="X",
            xaxis=dict(range=[axis_ranges['y_min'], axis_ranges['y_max']]),
            yaxis=dict(range=[axis_ranges['x_min'], axis_ranges['x_max']]),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_gridcolor='lightgray',
            yaxis_gridcolor='lightgray'
        )

        plots.append(dcc.Graph(figure=fig_xy))

    if "xz" in selected_graphs:
        fig_xz = go.Figure()

        for obj in selected_objects:
            df_obj = df_t[df_t['object'] == obj]
            if not df_obj.empty:
                color = obj_colors.get(str(obj), "#000000")
                if "neighbors" in color_by_neighbors:
                    marker = dict(
                        size=8,
                        color=df_obj["neighbors_count"],
                        colorscale="Plasma",
                        cmin=0,
                        cmax=max_neighbors,
                        showscale=True,  # Toujours visible
                        colorbar=dict(title="Voisins")  # Toujours visible
                    )
                    showlegend = False
                    name = None

                elif "by_speed" in color_by_speed:
                    marker = dict(
                        size=8,
                        color=df_obj["speed"],
                        colorscale="Viridis",
                        cmin=speed_min,
                        cmax=speed_max,
                        showscale=True,
                        colorbar=dict(title="Vitesse")
                    )
                    showlegend = False
                    name = None
                else:
                    color = obj_colors.get(str(obj), "#000000")
                    marker = dict(size=8, color=color)
                    showlegend = True
                    name = str(obj)

                fig_xz.add_trace(go.Scatter(
                    x=df_obj["ZSplined"],
                    y=df_obj["XSplined"],
                    mode="markers",
                    marker=marker,
                    name=name,
                    showlegend=showlegend
                ))



                if show_trajectory and "trajectory" in show_trajectory:
                    df_obj_all = df_all_times[df_all_times['object'] == obj]
                    fig_xz.add_trace(go.Scatter(
                        x=df_obj_all["ZSplined"],
                        y=df_obj_all["XSplined"],
                        mode='lines',
                        line=dict(color=color, width=1),
                        name=f"{obj} (trajectoire)",
                        opacity=0.5,
                        showlegend=False
                    ))

                # Ajouter une ligne directionnelle en XZ si les vecteurs sont activés
                if show_vectors and "vectors" in show_vectors:
                    df_obj_all = df[df['object'] == obj].copy()
                    df_obj_all["time_diff"] = abs(df_obj_all["time"] - selected_time)
                    df_obj_current = df_obj_all.sort_values("time_diff").head(1)

                    if not df_obj_current.empty:
                        current_pos = df_obj_current[["ZSplined", "XSplined"]].iloc[0].values  # Z en X ici

                        df_obj_next = df_obj_all[df_obj_all["time"] > df_obj_current["time"].values[0]].sort_values(
                            "time").head(1)
                        if not df_obj_next.empty:
                            next_pos = df_obj_next[["ZSplined", "XSplined"]].iloc[0].values

                            vector = next_pos - current_pos
                            norm = np.linalg.norm(vector)

                            if norm > 0.001:
                                unit_vector = vector / norm
                                scale = 0.1
                                extended_vector = unit_vector * scale
                                end_pos = current_pos + extended_vector

                                fig_xz.add_trace(go.Scatter(
                                    x=[current_pos[0], end_pos[0]],  # Z
                                    y=[current_pos[1], end_pos[1]],  # X
                                    mode='lines',
                                    line=dict(color='black', width=2),
                                    showlegend=False,
                                    name=f"Direction {obj}"
                                ))

        fig_xz.update_layout(
            title="X en fonction de Z",
            xaxis_title="Z",
            yaxis_title="X",
            xaxis=dict(range=[axis_ranges['z_min'], axis_ranges['z_max']]),
            yaxis=dict(range=[axis_ranges['x_min'], axis_ranges['x_max']]),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_gridcolor='lightgray',
            yaxis_gridcolor='lightgray'
        )

        plots.append(dcc.Graph(figure=fig_xz))

    if "yz" in selected_graphs:
        fig_yz = go.Figure()

        for obj in selected_objects:
            df_obj = df_t[df_t['object'] == obj]
            if not df_obj.empty:
                color = obj_colors.get(str(obj), "#000000")
                if "neighbors" in color_by_neighbors:
                    marker = dict(
                        size=8,
                        color=df_obj["neighbors_count"],
                        colorscale="Plasma",
                        cmin=0,
                        cmax=max_neighbors,
                        showscale=True,  # Toujours visible
                        colorbar=dict(title="Voisins")  # Toujours visible
                    )
                    showlegend = False
                    name = None

                elif "by_speed" in color_by_speed:
                    marker = dict(
                        size=8,
                        color=df_obj["speed"],
                        colorscale="Viridis",
                        cmin=speed_min,
                        cmax=speed_max,
                        showscale=True,
                        colorbar=dict(title="Vitesse")
                    )
                    showlegend = False
                    name = None
                else:
                    color = obj_colors.get(str(obj), "#000000")
                    marker = dict(size=8, color=color)
                    showlegend = True
                    name = str(obj)

                fig_yz.add_trace(go.Scatter(
                    x=df_obj["ZSplined"],
                    y=df_obj["YSplined"],
                    mode="markers",
                    marker=marker,
                    name=name,
                    showlegend=showlegend
                ))

                if show_trajectory and "trajectory" in show_trajectory:
                    df_obj_all = df_all_times[df_all_times['object'] == obj]
                    fig_yz.add_trace(go.Scatter(
                        x=df_obj_all["ZSplined"],
                        y=df_obj_all["YSplined"],
                        mode='lines',
                        line=dict(color=color, width=1),
                        name=f"{obj} (trajectoire)",
                        opacity=0.5,
                        showlegend=False
                    ))

                # Ajouter une ligne directionnelle en YZ si les vecteurs sont activés
                if show_vectors and "vectors" in show_vectors:
                    df_obj_all = df[df['object'] == obj].copy()
                    df_obj_all["time_diff"] = abs(df_obj_all["time"] - selected_time)
                    df_obj_current = df_obj_all.sort_values("time_diff").head(1)

                    if not df_obj_current.empty:
                        current_pos = df_obj_current[["ZSplined", "YSplined"]].iloc[0].values  # Z en Y ici

                        df_obj_next = df_obj_all[df_obj_all["time"] > df_obj_current["time"].values[0]].sort_values(
                            "time").head(1)
                        if not df_obj_next.empty:
                            next_pos = df_obj_next[["ZSplined", "YSplined"]].iloc[0].values

                            vector = next_pos - current_pos
                            norm = np.linalg.norm(vector)

                            if norm > 0.001:
                                unit_vector = vector / norm
                                scale = 0.1
                                extended_vector = unit_vector * scale
                                end_pos = current_pos + extended_vector

                                fig_yz.add_trace(go.Scatter(
                                    x=[current_pos[0], end_pos[0]],  # Z
                                    y=[current_pos[1], end_pos[1]],  # Y
                                    mode='lines',
                                    line=dict(color='black', width=2),
                                    showlegend=False,
                                    name=f"Direction {obj}"
                                ))

        fig_yz.update_layout(
            title="Y en fonction de Z",
            xaxis_title="Z",
            yaxis_title="Y",
            xaxis=dict(range=[axis_ranges['z_min'], axis_ranges['z_max']]),
            yaxis=dict(range=[axis_ranges['y_min'], axis_ranges['y_max']]),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_gridcolor='lightgray',
            yaxis_gridcolor='lightgray'
        )

        plots.append(dcc.Graph(figure=fig_yz))

    # Partie à modifier dans la section où vous traitez les vecteurs dans le graphique 3D
    # Trouver la section suivante dans la fonction update_graphs:

    if "3d" in selected_graphs:
        fig3d = go.Figure()

        # D'abord, obtenir la liste des objets présents à l'instant t
        present_objects = df_t['object'].unique()

        for obj in selected_objects:
            # Vérifier si l'objet est présent à l'instant t
            if obj not in present_objects:
                continue  # Passer à l'objet suivant si non présent

            df_obj = df_t[df_t['object'] == obj]
            color = obj_colors.get(str(obj), "#000000")

            is_star = obj in objects_with_star_3d
            marker_size = 5 if is_star else 5

            if "neighbors" in color_by_neighbors:
                marker = dict(
                    size=5,
                    color=df_obj["neighbors_count"],
                    colorscale="Plasma",
                    cmin=0,
                    cmax=max_neighbors,
                    showscale=True,  # Toujours visible
                    colorbar=dict(title="Voisins")  # Toujours visible
                )
                showlegend = False
                name = None

            elif "by_speed" in color_by_speed:
                marker = dict(
                    size=marker_size,
                    color=df_obj["speed"],
                    colorscale="Viridis",
                    cmin=speed_min,
                    cmax=speed_max,
                    showscale=True if obj == selected_objects[0] else False,
                    colorbar=dict(title="Vitesse") if obj == selected_objects[0] else None,
                    symbol='diamond' if is_star else 'circle'
                )
                showlegend = False
                name = None
            else:
                color = obj_colors.get(str(obj), "#000000")
                marker = dict(
                    size=marker_size,
                    color=color,
                    symbol='diamond' if is_star else 'circle'
                )
                showlegend = True
                name = str(obj)

            fig3d.add_trace(go.Scatter3d(
                x=df_obj["XSplined"],
                y=df_obj["YSplined"],
                z=df_obj["ZSplined"],
                mode="markers",
                marker=marker,
                name=name,
                showlegend=showlegend
            ))

            # Ajouter la trajectoire seulement si l'objet est présent à l'instant t
            if show_trajectory and "trajectory" in show_trajectory:
                df_obj_all = df_all_times[df_all_times['object'] == obj]
                fig3d.add_trace(go.Scatter3d(
                    x=df_obj_all["XSplined"],
                    y=df_obj_all["YSplined"],
                    z=df_obj_all["ZSplined"],
                    mode='lines',
                    line=dict(color=color, width=2),
                    name=f"{obj} (trajectoire)",
                    opacity=0.5,
                    showlegend=False
                ))

            if show_vectors and "vectors" in show_vectors:
                df_obj_all = df[df['object'] == obj].copy()

                # Chercher le point le plus proche de selected_time
                df_obj_all["time_diff"] = abs(df_obj_all["time"] - selected_time)
                df_obj_current = df_obj_all.sort_values("time_diff").head(1)

                if not df_obj_current.empty:
                    current_pos = df_obj_current[["XSplined", "YSplined", "ZSplined"]].iloc[0].values

                    # Point suivant dans le temps (pour déterminer la direction)
                    df_obj_next = df_obj_all[df_obj_all["time"] > df_obj_current["time"].values[0]].sort_values(
                        "time").head(1)

                    if not df_obj_next.empty:
                        next_pos = df_obj_next[["XSplined", "YSplined", "ZSplined"]].iloc[0].values
                        direction_vector = next_pos - current_pos
                        norm = np.linalg.norm(direction_vector)

                        if norm > 0.001:
                            # Normaliser le vecteur de direction
                            unit_vector = direction_vector / norm

                            # Allonger le vecteur (longueur arbitraire, ex: 0.1)
                            scale = 0.1
                            extended_vector = unit_vector * scale
                            end_pos = current_pos + extended_vector

                            vector_color = 'red' if obj in pointing_sources else 'black'
                            fig3d.add_trace(go.Scatter3d(
                                x=[current_pos[0], end_pos[0]],
                                y=[current_pos[1], end_pos[1]],
                                z=[current_pos[2], end_pos[2]],
                                mode='lines',
                                line=dict(color=vector_color, width=6),
                                name=f"Direction {obj}",
                                showlegend=False
                            ))

        fig3d.update_layout(
            title="Position 3D des objets",
            scene=dict(
                xaxis=dict(
                    title="X",
                    range=[axis_ranges["x_min"], axis_ranges["x_max"]],
                    autorange=False,
                ),
                yaxis=dict(
                    title="Y",
                    range=[axis_ranges["y_min"], axis_ranges["y_max"]],
                    autorange=False,
                ),
                zaxis=dict(
                    title="Z",
                    range=[axis_ranges["z_min"], axis_ranges["z_max"]],
                    autorange=False,
                ),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=1)
            ),
            height=600,
            margin=dict(l=0, r=0, b=0, t=40)
        )

        plots.append(dcc.Graph(figure=fig3d))

    # Graphe X, Y, Z en fonction du temps - utilise df_selected_objects (TOUS les temps)
    if "xyzt" in selected_graphs:
        fig_time_series = go.Figure()

        for obj in selected_objects:
            df_obj = df_selected_objects[df_selected_objects['object'] == obj]
            if not df_obj.empty:  # Vérifier que l'objet existe dans les données
                # Assurez-vous que la clé pour obj_colors est une chaîne
                color = obj_colors.get(str(obj), "#000000")  # Valeur par défaut si la clé n'existe pas

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


@app.callback(
    Output("store-interactions", "data"),
    Output("store-fusions", "data"),
    Output("store-ruptures", "data"),
    Output("store-couples", "data"),
    Output("store-rupture-fusion", "data"),
    Output("analysis-complete", "data"),
    Output("loading-status", "children"),
    Input("analyze-couples", "n_clicks"),
    State("upload-data-storage", "data"),
    State("distance-threshold-interraction", "value"),
    State("distance-threshold-unionrupture-slider", "value"),
    State("detect-couples-check", "value"),
    State("min-duration-threshold", "value"),  # <-- attention ici, `min-duration-slider` est renommé
    prevent_initial_call=True
)
def run_all_detections(n_clicks, df_json, threshold_inter, threshold_union, checkbox_values, min_duration):
    if df_json is None:
        return None, None, None, None, None

    df = pd.read_json(df_json, orient="split")

    inter_df, union_df, rupture_df, couples_df, rupture_fusion_df = None, None, None, None, None

    if "detect_interaction" in checkbox_values:
        inter_df = detect_interactions(df, distance_threshold=threshold_inter, min_duration=min_duration)

    if "detect_union" in checkbox_values:
        union_df = detect_union(df, distance_seuil=threshold_union)

    if "detect_rupture" in checkbox_values:
        rupture_df = detect_rupture(df, distance_seuil=threshold_union)

    if all(k in checkbox_values for k in ["detect_interaction", "detect_union", "detect_rupture"]):
        if inter_df is not None and not inter_df.empty and union_df is not None and rupture_df is not None:
            if "detect_couples" in checkbox_values:
                couples_df = detect_couples(inter_df, union_df, rupture_df)
            if "detect_rupture_fusion" in checkbox_values:
                rupture_fusion_df = detect_rupture_fusion(inter_df, union_df, rupture_df)

    return (
        inter_df.to_json(date_format="iso", orient="split") if inter_df is not None else None,
        union_df.to_json(date_format="iso", orient="split") if union_df is not None else None,
        rupture_df.to_json(date_format="iso", orient="split") if rupture_df is not None else None,
        couples_df.to_json(date_format="iso", orient="split") if couples_df is not None else None,
        rupture_fusion_df.to_json(date_format="iso", orient="split") if rupture_fusion_df is not None else None,
        True,
        ""
    )


@app.callback(
    Output("couples-table-output", "children"),
    Output("status-message", "children"),
    Input("show-tables-button", "n_clicks"),
    State("store-interactions", "data"),
    State("store-fusions", "data"),
    State("store-ruptures", "data"),
    State("store-couples", "data"),
    State("store-rupture-fusion", "data"),
    prevent_initial_call=True
)
def display_couples(n_clicks, inter_json, fusion_json, rupture_json, couples_json, rupture_fusion_json):
    results = []
    status_messages = []

    if inter_json:
        inter_df = pd.read_json(inter_json, orient="split")
        results.append(
            html.Div([
                html.H4("💬 Interactions détectées", className="text-info fw-bold mt-4"),
                dbc.Card(
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='inter-table',
                            columns=[{"name": col, "id": col} for col in inter_df.columns],
                            data=inter_df.to_dict("records"),
                            page_size=10,
                            sort_action='native',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'}
                        )
                    ]),
                    className="shadow-sm bg-light rounded mb-4"
                )
            ])
        )

    if fusion_json:
        fusion_df = pd.read_json(fusion_json, orient="split")
        results.append(
            html.Div([
                html.H4("🔗 Fusions détectées", className="text-success fw-bold mt-4"),
                dbc.Card(
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='fusion-table',
                            columns=[{"name": col, "id": col} for col in fusion_df.columns],
                            data=fusion_df.to_dict("records"),
                            page_size=10,
                            sort_action='native',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'}
                        )
                    ]),
                    className="shadow-sm bg-light rounded mb-4"
                )
            ])
        )

    if rupture_json:
        rupture_df = pd.read_json(rupture_json, orient="split")
        results.append(
            html.Div([
                html.H4("💔 Ruptures détectées", className="text-danger fw-bold mt-4"),
                dbc.Card(
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='rupture-table',
                            columns=[{"name": col, "id": col} for col in rupture_df.columns],
                            data=rupture_df.to_dict("records"),
                            page_size=10,
                            sort_action='native',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'}
                        )
                    ]),
                    className="shadow-sm bg-light rounded mb-4"
                )
            ])
        )

    if couples_json:
        couples_df = pd.read_json(couples_json, orient="split")
        results.append(
            html.Div([
                html.H4("💑 Couples fusion ➜ rupture", className="text-warning fw-bold mt-4"),
                dbc.Card(
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='couples-table',
                            columns=[{"name": col, "id": col} for col in couples_df.columns],
                            data=couples_df.to_dict("records"),
                            page_size=10,
                            sort_action='native',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'}
                        )
                    ]),
                    className="shadow-sm bg-light rounded mb-4"
                )
            ])
        )

    if rupture_fusion_json:
        rf_df = pd.read_json(rupture_fusion_json, orient="split")
        results.append(
            html.Div([
                html.H4("♻️ Couples rupture ➜ fusion", className="text-secondary fw-bold mt-4"),
                dbc.Card(
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='rf-table',
                            columns=[{"name": col, "id": col} for col in rf_df.columns],
                            data=rf_df.to_dict("records"),
                            page_size=10,
                            sort_action='native',
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'}
                        )
                    ]),
                    className="shadow-sm bg-light rounded mb-4"
                )
            ])
        )

    if not results:
        return html.Div("Aucun résultat à afficher."), ""

    return html.Div(results), html.Div(status_messages)

@app.callback(
    Output("download-csv", "data"),
    Input("download-button", "n_clicks"),
    State("store-interactions", "data"),
    State("store-fusions", "data"),
    State("store-ruptures", "data"),
    State("store-couples", "data"),
    State("store-rupture-fusion", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, inter_json, fusion_json, rupture_json, couples_json, rupture_fusion_json):
    output_dfs = []

    if inter_json:
        df = pd.read_json(inter_json, orient="split")
        df["type"] = "interaction"
        output_dfs.append(df)

    if fusion_json:
        df = pd.read_json(fusion_json, orient="split")
        df["type"] = "fusion"
        output_dfs.append(df)

    if rupture_json:
        df = pd.read_json(rupture_json, orient="split")
        df["type"] = "rupture"
        output_dfs.append(df)

    if couples_json:
        df = pd.read_json(couples_json, orient="split")
        df["type"] = "couple_fusion_to_rupture"
        output_dfs.append(df)

    if rupture_fusion_json:
        df = pd.read_json(rupture_fusion_json, orient="split")
        df["type"] = "couple_rupture_to_fusion"
        output_dfs.append(df)

    if output_dfs:
        final_df = pd.concat(output_dfs, ignore_index=True)
        return dcc.send_data_frame(final_df.to_csv, "resultats_detection.csv", index=False)

    return None




# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)