

from utils import *
from callbacks import *


random.seed(42)

import dash_bootstrap_components as dbc

layout = dbc.Container([
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
    ]),

# Stores
dcc.Store(id='upload-data-storage'),
dcc.Store(id='object-colors-storage'),
dcc.Store(id='axis-ranges-storage'),
], fluid=True)

