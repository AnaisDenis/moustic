import random
import dash_bootstrap_components as dbc
from dash import dcc, html

from .utils import *
from .callbacks import *

random.seed(42)

layout = dbc.Container([
    dbc.Row([
        # Colonne de gauche : tous les contrôles
        dbc.Col([
            html.Img(src="/doc/img/moustic.png", style={'height': '80px'}, className="my-3"),

            html.H3("Upload a CSV file", className="mt-4 text-secondary"),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['📁 Drag and drop ou ', html.A('select a file')]),
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
            html.Div(id='file-info', style={
                'margin': '10px 0',
                'whiteSpace': 'nowrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': '100%',
                'color': 'gray',
                'fontSize': '0.85rem'
            }),

            # ------ Mosqui'Track collapsible ------
            html.H3("Mosqui'Track", id="mosquitrack-title", style={
                "backgroundColor": "#FFCCEC",
                "padding": "1rem",
                "borderRadius": "10px",
                "color": "#FF0073",
                "textAlign": "center",
                "fontWeight": "bold",
                "boxShadow": "2px 2px 8px rgba(0,0,0,0.2)",
                "cursor": "pointer"
            }),

            dbc.Collapse(id="mosquitrack-collapse", is_open=True, children=[
                html.H5("Save video", className="mt-4 text-secondary"),
                dbc.Button("🎥 Save video", id="save-video-btn", color="danger", className="mb-2 w-100"),
                html.Div(id="video-status", style={"fontWeight": "bold", "color": "green"}),

                html.H5("Time selection", className="mt-4 text-secondary"),
                html.Label("Selected time :"),
                dcc.Slider(id="time-slider", min=0, max=10, step=0.02, value=0, disabled=True,
                           tooltip={"placement": "bottom", "always_visible": True}),
                dbc.Input(id="manual-time", type="number", step=0.02, value=0, debounce=True, disabled=True,
                          className="mt-2"),
                dbc.Button("▶️ Start", id="start-stop-button", color="primary", className="mt-3 w-100", disabled=True),
                dcc.Interval(id="interval", interval=500, n_intervals=0, disabled=True),

                html.Label("⏱️ Read speed (ms between frames) :"),
                dcc.Slider(
                    id="interval-slider", min=50, max=1000, step=50, value=500,
                    marks={i: f"{i} ms" for i in range(100, 1001, 200)},
                    tooltip={"placement": "bottom"}
                ),

                html.H5("Affichage des graphiques", className="mt-4 text-secondary"),
                html.Label("Displaying graphics :"),
                dbc.Checklist(
                    id="graph-selection",
                    options=[
                        {"label": "X as a function of Y", "value": "xy"},
                        {"label": "X as a function of Z", "value": "xz"},
                        {"label": "Y as a function of Z", "value": "yz"},
                        {"label": "3D", "value": "3d"},
                        {"label": "X, Y, Z versus time", "value": "xyzt"},
                        {"label": "X as a function of time", "value": "xt"},
                        {"label": "Y as a function of time", "value": "yt"},
                        {"label": "Z as a function of time", "value": "zt"},
                        {"label": "Distance versus time", "value": "dt"},
                    ],
                    value=["xy", "xz"],
                    className="mb-3"
                ),
            ]),

            # ------ Mosqu'Investigate collapsible ------
            html.H3("Mosqu'Investigate", id="mosquinvestigate-title", style={
                "backgroundColor": "#FFCCEC",
                "padding": "1rem",
                "borderRadius": "10px",
                "color": "#FF0073",
                "textAlign": "center",
                "fontWeight": "bold",
                "boxShadow": "2px 2px 8px rgba(0,0,0,0.2)",
                "cursor": "pointer"
            }),

            dbc.Collapse(id="mosquinvestigate-collapse", is_open=True, children=[
                html.H5("Graphics options", className="mt-4 text-secondary"),
                dbc.Checklist(
                    id="show-trajectory",
                    options=[{"label": "Show continuous trajectory", "value": "trajectory"}],
                    value=[], inline=True
                ),
                dbc.Checklist(
                    id="show-vectors",
                    options=[{"label": "Show direction vectors", "value": "vectors"}],
                    value=[], inline=True
                ),

                html.Div(id="vector-parameters-container", children=[
                    dbc.Label("Minimum number of vectors"),
                    dbc.Input(id="min-vectors-input", type="number", min=1, step=1, value=2),
                    dbc.Label("Maximum distance"),
                    dbc.Input(id="distance-threshold-input", type="number", step=0.01, value=0.1),
                ], style={"marginLeft": "20px", "marginTop": "10px", "maxWidth": "300px"}),

                dbc.Checklist(
                    id="color-by-speed",
                    options=[{"label": "Color by speed", "value": "by_speed"}],
                    value=[], inline=True
                ),
                dbc.Checklist(
                    id="color-by-neighbors",
                    options=[{"label": "Color by nearest neighbors", "value": "neighbors"}],
                    value=[], inline=True, className="mb-3"
                ),
            ]),

            # ------ Mosquit'Love collapsible ------
            html.H3("Mosquit'Love", id="mosquitlove-title", style={
                "backgroundColor": "#FFCCEC",
                "padding": "1rem",
                "borderRadius": "10px",
                "color": "#FF0073",
                "textAlign": "center",
                "fontWeight": "bold",
                "boxShadow": "2px 2px 8px rgba(0,0,0,0.2)",
                "cursor": "pointer"
            }),

            dbc.Collapse(id="mosquitlove-collapse", is_open=True, children=[
                dbc.Checklist(
                    id="detect-couples-check",
                    options=[


                        {"label": "Detect rapprochements", "value": "detect_interaction"},
                        {"label": "Detect mergers", "value": "detect_union"},
                        {"label": "Detect breaks", "value": "detect_rupture"},
                        {"label": "Detect mergers and breakups", "value": "detect_couples"},
                        {"label": "Detect break-merges", "value": "detect_rupture_fusion"},
                    ],
                    value=[], inline=True
                ),




                html.Label("Distance threshold for rapprochements :"),
                dcc.Slider(id="distance-threshold-interraction", min=0, max=0.1, step=0.001, value=0.055,
                           marks={i: str(i) for i in [0, 0.02, 0.04, 0.06, 0.08, 0.1]},
                           tooltip={"placement": "bottom", "always_visible": True}),




                html.Label("Minimum duration of a rapprochement (s) :"),
                dcc.Slider(id="min-duration-threshold", min=0, max=5, step=0.1, value=1.0,
                           marks={i: f"{i}s" for i in range(6)},
                           tooltip={"placement": "bottom", "always_visible": True}),

                html.Label("Threshold distance for mergers/breakups :"),
                dcc.Slider(id="distance-threshold-unionrupture-slider", min=0, max=0.1, step=0.001, value=0.02,
                           marks={i: str(i) for i in [0, 0.02, 0.04, 0.06, 0.08, 0.1]},
                           tooltip={"placement": "bottom", "always_visible": True}),

                dbc.Button("Analyze couples", id="analyze-couples", color="primary", className="mt-3 w-100"),
                dcc.Loading(id="loading-analyze", type="circle", fullscreen=True,
                            children=html.Div(id="loading-status")),
                dbc.Button("Download CSV", id="download-button", color="secondary", className="mt-2 w-100",
                           disabled=False),
                dcc.Download(id="download-csv"),

                dbc.Button("Show tables", id="show-tables-button", color="info", className="mt-2 w-100"),
                html.Div(id="status-message", style={"marginTop": "10px", "color": "red"}),
            ]),
        ], width=3, style={"backgroundColor": "#f8f9fa", "padding": "20px", "borderRight": "1px solid #dee2e6"}),
        

                

        # Colonne centrale
        dbc.Col([
            html.Div(dbc.Button("🧾 Objects to display", id="toggle-objects-sidebar", color="info", size="sm"),
                     style={"textAlign": "right", "marginBottom": "10px"}),
            html.Div(id="graphs-output"),
            html.Div(id="couples-table-output", className="mt-4")
        ], width=9)
    ]),

    # Sidebar
    dbc.Offcanvas(
        title="Objects to display",
        id="object-sidebar",
        is_open=False,
        placement="end",
        scrollable=True,
        style={"width": "300px"},
        children=[
            dbc.ButtonGroup([
                dbc.Button("Tout cocher", id="select-all", color="success", size="sm"),
                dbc.Button("Tout décocher", id="deselect-all", color="danger", size="sm"),
            ], className="mb-2"),
            dbc.Checklist(
                id="object-checklist",
                options=[], value=[], inline=False,
                style={"maxHeight": "400px", "overflowY": "auto"}
            )
        ]
    ),

    # Stores
    dcc.Store(id='upload-data-storage'),
    dcc.Store(id='object-colors-storage'),
    dcc.Store(id='axis-ranges-storage'),
    dcc.Store(id="analysis-complete", data=False),
    dcc.Store(id='store-interactions'),
    dcc.Store(id='store-fusions'),
    dcc.Store(id='store-ruptures'),
    dcc.Store(id='store-couples'),
    dcc.Store(id='store-rupture-fusion'),
], fluid=True)
