import os
import platform
import subprocess
import random
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import sys
import json

from dash import html, dcc, dash_table
from dash import Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc

from .utils import *
from .utils import parse_contents
from .layout import *
from .generate_video import VideoRecorderApp, render_frame, ajuster_temps
from dash import Input, Output, State, callback


random.seed(42)

def register_callbacks(app):
    @app.callback(
        [
            Output('upload-data-storage', 'data', allow_duplicate=True),
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
            Output('object-checklist', 'options'),
            Output('object-checklist', 'value', allow_duplicate=True),
            Output('file-info', 'children')
        ],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
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
            html.P(f"File: {filename}"),
            html.P(f"Number of objects: {len(sorted_objects)}"),
            html.P(f"Time range: {df['time'].min():.2f} à {df['time'].max():.2f}")
        ])

        return (df.to_json(),
                obj_colors,
                axis_ranges,
                status_message,
                df['time'].min(),
                df['time'].max(),
                df['time'].min(),
                False, False, df['time'].min(),
                False, False, False, False, False,
                [{"label": str(obj), "value": obj} for obj in sorted_objects],
                sorted_objects,
                file_info)

    @app.callback(
        Output("video-status", "children"),
        Input("save-video-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def launch_video_script(n_clicks):
        try:
            script_path = os.path.abspath("src/generate_video.py")

            # Commande de lancement, directement python ou python3 selon OS
            if platform.system() == "Windows":
                cmd = [sys.executable, script_path]
            else:
                cmd = ["python3", script_path]

            # subprocess.run bloque jusqu'à la fin du script
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return "✅ Video generation complete."
            else:
                return f"❌ Error in the script: {result.stderr}"

        except Exception as e:
            return "Exception when opening:{str(e)}"

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
        prevent_initial_call=True,
        allow_duplicate=True
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

    @callback(
        Output("mosquitrack-collapse", "is_open"),
        Input("mosquitrack-title", "n_clicks"),
        State("mosquitrack-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_mosquitrack(n, is_open):
        return not is_open

    @callback(
        Output("mosquinvestigate-collapse", "is_open"),
        Input("mosquinvestigate-title", "n_clicks"),
        State("mosquinvestigate-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_mosquinvestigate(n, is_open):
        return not is_open

    @callback(
        Output("mosquitlove-collapse", "is_open"),
        Input("mosquitlove-title", "n_clicks"),
        State("mosquitlove-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_mosquitlove(n, is_open):
        return not is_open

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
            return False, "⏸️ Break"
        else:
            return True, "▶️ Start"

    @app.callback(
        Output("object-sidebar", "is_open"),
        [Input("toggle-objects-sidebar", "n_clicks")],
        [State("object-sidebar", "is_open")],
        prevent_initial_call=True
    )
    def toggle_sidebar(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open


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
        prevent_initial_call=True,
        allow_duplicate=True
    )
    def update_graphs(selected_time, selected_graphs, selected_objects, show_trajectory, show_vectors,
                      color_by_speed, min_vectors, distance_threshold, color_by_neighbors,
                      df_json, obj_colors_data, axis_ranges_data):


        if not df_json:
            return html.Div("Please upload a CSV file and select objects.")


        df, obj_colors, axis_ranges = load_inputs(df_json, obj_colors_data, axis_ranges_data)


        if df is None or not selected_objects:
            return html.Div("Please upload a CSV file and select objects.")
        # Étape 2 : Préparer les DataFrames utiles
        df_t, df_selected_objects, df_all_times = prepare_dataframes(df, selected_objects, selected_time)

        if df_selected_objects.empty:
            return html.Div("None of the selected objects were found in the data.")

        # Étape 3 : Ajouter colonnes de vitesse et de voisins
        df_t, max_neighbors = compute_speed_and_neighbors(df_t, color_by_neighbors)

        # Étape 4 : Calcul des bornes de vitesse
        speed_min, speed_max = (0, 1.3) if "by_speed" in color_by_speed else (None, None)

        # Étape 5 : Traitement des vecteurs (si demandés)
        if show_vectors and "vectors" in show_vectors:
            min_vectors = int(min_vectors) if min_vectors is not None else 2
            distance_threshold = float(distance_threshold) if distance_threshold is not None else 0.1

            objects_with_star_3d, pointing_pairs = get_objects_with_star_3d(
                df, selected_objects, selected_time,
                distance_threshold=distance_threshold,
                min_vectors=min_vectors
            )
            pointing_sources = {source for source, target in pointing_pairs if target in objects_with_star_3d}
        else:
            objects_with_star_3d = []
            pointing_sources = set()

        plots = []

        if "xy" in selected_graphs:
            fig_xy = go.Figure()
            for obj in selected_objects:
                df_obj = df_t[df_t['object'] == obj]
                if df_obj.empty:
                    continue

                marker, showlegend, name = create_marker(df_obj, obj, obj_colors, color_by_neighbors, color_by_speed,
                                                         max_neighbors, speed_min, speed_max)
                add_scatter_trace(fig_xy, df_obj["YSplined"], df_obj["XSplined"], marker, name, showlegend)

                if "trajectory" in show_trajectory:
                    color = obj_colors.get(str(obj), "#000000")
                    add_trajectory_trace(fig_xy, df_all_times, obj, "YSplined", "XSplined", color)

                if show_vectors and "vectors" in show_vectors:
                    add_direction_vector(fig_xy, df, obj, selected_time, "YSplined", "XSplined")

            update_layout(fig_xy, "X as a function of Y", "Y", "X",
                          [axis_ranges['y_min'], axis_ranges['y_max']],
                          [axis_ranges['x_min'], axis_ranges['x_max']])
            plots.append(dcc.Graph(figure=fig_xy))

        if "xz" in selected_graphs:
            fig_xz = go.Figure()
            for obj in selected_objects:
                df_obj = df_t[df_t['object'] == obj]
                if df_obj.empty:
                    continue

                marker, showlegend, name = create_marker(df_obj, obj, obj_colors, color_by_neighbors, color_by_speed,
                                                         max_neighbors, speed_min, speed_max)
                add_scatter_trace(fig_xz, df_obj["ZSplined"], df_obj["XSplined"], marker, name, showlegend)

                if "trajectory" in show_trajectory:
                    color = obj_colors.get(str(obj), "#000000")
                    add_trajectory_trace(fig_xz, df_all_times, obj, "ZSplined", "XSplined", color)

                if show_vectors and "vectors" in show_vectors:
                    add_direction_vector(fig_xz, df, obj, selected_time, "ZSplined", "XSplined")

            update_layout(fig_xz, "X as a function of Z", "Z", "X",
                          [axis_ranges['z_min'], axis_ranges['z_max']],
                          [axis_ranges['x_min'], axis_ranges['x_max']])
            plots.append(dcc.Graph(figure=fig_xz))

        if "yz" in selected_graphs:
            fig_yz = go.Figure()
            for obj in selected_objects:
                df_obj = df_t[df_t['object'] == obj]
                if df_obj.empty:
                    continue

                marker, showlegend, name = create_marker(df_obj, obj, obj_colors, color_by_neighbors, color_by_speed,
                                                         max_neighbors, speed_min, speed_max)
                add_scatter_trace(fig_yz, df_obj["ZSplined"], df_obj["YSplined"], marker, name, showlegend)

                if "trajectory" in show_trajectory:
                    color = obj_colors.get(str(obj), "#000000")
                    add_trajectory_trace(fig_yz, df_all_times, obj, "ZSplined", "YSplined", color)

                if show_vectors and "vectors" in show_vectors:
                    add_direction_vector(fig_yz, df, obj, selected_time, "ZSplined", "YSplined")

            update_layout(fig_yz, "Y as a function of Z", "Z", "Y",
                          [axis_ranges['z_min'], axis_ranges['z_max']],
                          [axis_ranges['y_min'], axis_ranges['y_max']])
            plots.append(dcc.Graph(figure=fig_yz))


        
        

        if "3d" in selected_graphs:
            fig3d = go.Figure()
            present_objects = set(df_t['object'].unique())

            for obj in selected_objects:
                if obj not in present_objects:
                    continue

                df_obj = df_t[df_t['object'] == obj]
                is_star = obj in objects_with_star_3d

                marker, showlegend, name = create_marker_3d(df_obj, obj, obj_colors, color_by_neighbors,
                                                            color_by_speed, max_neighbors,
                                                            speed_min, speed_max, is_star)

                fig3d.add_trace(go.Scatter3d(
                    x=df_obj["XSplined"],
                    y=df_obj["YSplined"],
                    z=df_obj["ZSplined"],
                    mode="markers",
                    marker=marker,
                    name=name,
                    showlegend=showlegend
                ))

                if show_trajectory and "trajectory" in show_trajectory:
                    color = obj_colors.get(str(obj), "#000000")
                    add_trajectory_3d(fig3d, df_all_times, obj, color)

                if show_vectors and "vectors" in show_vectors:
                    add_vector_3d(fig3d, df, obj, selected_time, pointing_sources)

            fig3d.update_layout(
                title="3D position of objects",
                scene=dict(
                    xaxis=dict(title="X(m)", range=[axis_ranges["x_min"], axis_ranges["x_max"]], autorange=False),
                    yaxis=dict(title="Y(m)", range=[axis_ranges["y_min"], axis_ranges["y_max"]], autorange=False),
                    zaxis=dict(title="Z(m)", range=[axis_ranges["z_min"], axis_ranges["z_max"]], autorange=False),
                    aspectmode='manual',
                    aspectratio=dict(x=1, y=1, z=1)
                ),
                height=600,
                margin=dict(l=0, r=0, b=0, t=40)
            )

            plots.append(dcc.Graph(figure=fig3d))

        if "xyzt" in selected_graphs:
            fig_time_series = go.Figure()
            gap_threshold = 0.05

            for obj in selected_objects:
                df_obj = df_selected_objects[df_selected_objects['object'] == obj]
                if df_obj.empty:
                    continue

                color = obj_colors.get(str(obj), "#000000")
                df_obj = df_obj.sort_values(by='time')
                segments = split_trajectory_segments(df_obj, gap_threshold)

                for i, segment in enumerate(segments):
                    if len(segment) < 2:
                        continue
                    show_legend = (i == 0)
                    add_time_series_trace(fig_time_series, segment, obj, color, coords=['X', 'Y', 'Z'], show_legend=show_legend)


            fig_time_series.update_layout(
                title="X, Y, Z versus time",
                xaxis_title="Time (s)",
                yaxis_title="Position (m)",
                legend_title="Object - Coordinates",
                height=500,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
            )

            plots.append(dcc.Graph(figure=fig_time_series))

        if any(coord in selected_graphs for coord in ["xt", "yt", "zt"]):
            gap_threshold = 0.05
            figs = {'X': None, 'Y': None, 'Z': None}
            coord_map = {'X': 'xt', 'Y': 'yt', 'Z': 'zt'}

            # Créer les figures nécessaires
            for coord, key in coord_map.items():
                if key in selected_graphs:
                    figs[coord] = go.Figure()

            for obj in selected_objects:
                df_obj = df_selected_objects[df_selected_objects['object'] == obj]
                if df_obj.empty:
                    continue

                color = obj_colors.get(str(obj), "#000000")
                df_obj = df_obj.sort_values(by='time')
                segments = split_trajectory_segments(df_obj, gap_threshold)

                for i, segment in enumerate(segments):
                    if len(segment) < 2:
                        continue
                    show_legend = (i == 0)

                    for coord, fig in figs.items():
                        if fig is not None:
                            add_time_series_trace(fig, segment, obj, color, coords=coord, show_legend=show_legend)

            for coord, fig in figs.items():
                if fig is not None:
                    update_coord_figure_layout(fig, f"{coord} versus time", coord)
                    plots.append(dcc.Graph(figure=fig))

        other_graphs = []
        time_series_basic = []  # xt, yt, zt
        dt_graph = None
        xyzt_graph = None

        for graph in plots:
            title = graph.figure.layout.title.text.lower() if hasattr(graph.figure.layout, "title") else ""

            if "x, y, y versus time" in title:
                xyzt_graph = graph
            elif any(coord in title for coord in
                     ["x versus time", "y versus time", "z versus time"]):
                time_series_basic.append(graph)
            else:
                other_graphs.append(graph)

        # Générer dt si demandé et <= 5 objets
        if "dt" in selected_graphs and len(selected_objects) <= 5:
            fig_distance = go.Figure()
            color_cycle = px.colors.qualitative.Plotly
            from itertools import combinations
            for idx, (obj1, obj2) in enumerate(combinations(selected_objects, 2)):
                df1 = df_selected_objects[df_selected_objects['object'] == obj1].sort_values(by='time')
                df2 = df_selected_objects[df_selected_objects['object'] == obj2].sort_values(by='time')
                if df1.empty or df2.empty:
                    continue
                color = color_cycle[idx % len(color_cycle)]
                add_distance_trace(fig_distance, df1, df2, obj1, obj2, color)

            fig_distance.update_layout(
                title="Distance between pairs of objects as a function of time",
                xaxis_title="Time (s)",
                yaxis_title="Distance (Euclidean)",
                legend_title="Pairs of objects",
                height=500,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
            )
            dt_graph = dcc.Graph(figure=fig_distance)

        # Construction finale des rangées

        rows = []

        # 1. autres graphes 2 par 2
        for i in range(0, len(other_graphs), 2):
            rows.append(
                dbc.Row([
                    dbc.Col(other_graphs[i], width=6),
                    dbc.Col(other_graphs[i + 1] if i + 1 < len(other_graphs) else None, width=6)
                ], className="mb-4")
            )

        # 2. xt, yt, zt un par ligne
        for graph in time_series_basic:
            rows.append(dbc.Row(dbc.Col(graph, width=12), className="mb-4"))

        # 3. dt juste après xt, yt, zt
        if dt_graph is not None:
            rows.append(dbc.Row(dbc.Col(dt_graph, width=12), className="mb-4"))

        # 4. xyzt à la fin
        if xyzt_graph is not None:
            rows.append(dbc.Row(dbc.Col(xyzt_graph, width=12), className="mb-4"))

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

        df = pd.read_json(df_json)


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
                    html.H4("💬 Rapprochements detected", className="text-info fw-bold mt-4"),
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
                    html.H4("🔗 Mergers detected", className="text-success fw-bold mt-4"),
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
                    html.H4("💔 Breakages detected", className="text-danger fw-bold mt-4"),
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
                    html.H4("💑 merger ➜ breakup", className="text-warning fw-bold mt-4"),
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
                    html.H4("♻️ breakup ➜ merger", className="text-secondary fw-bold mt-4"),
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
            return html.Div("No results to display."), ""

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

