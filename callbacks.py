import pandas as pd
import plotly.graph_objs as go
from dash import html, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
import random
import numpy as np
from dash import dash_table
from dash import dcc

from utils import *
from layout import *
from utils import parse_contents



random.seed(42)

def register_callbacks(app):

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

        if "xyzt" in selected_graphs:
            fig_time_series = go.Figure()
            gap_threshold = 0.05  # seuil pour considérer qu'il y a un "trou" dans la trajectoire

            for obj in selected_objects:
                df_obj = df_selected_objects[df_selected_objects['object'] == obj]
                if not df_obj.empty:
                    color = obj_colors.get(str(obj), "#000000")
                    df_obj = df_obj.sort_values(by='time')

                    # Découpage en segments sans gros trous temporels
                    times = df_obj['time'].values
                    time_diffs = np.diff(times)
                    gap_indices = np.where(time_diffs > gap_threshold)[0]

                    segments = []
                    start_idx = 0
                    for gap_idx in gap_indices:
                        end_idx = gap_idx + 1
                        segments.append(df_obj.iloc[start_idx:end_idx])
                        start_idx = end_idx
                    segments.append(df_obj.iloc[start_idx:])  # dernier segment

                    for segment in segments:
                        if len(segment) < 2:
                            continue

                        fig_time_series.add_trace(go.Scatter(
                            x=segment['time'], y=segment['XSplined'],
                            mode='lines',
                            name=f"{obj} - X",
                            line=dict(color=color, dash='solid'),
                            legendgroup=str(obj),
                            showlegend=True  # Affiche la légende une seule fois par groupe
                        ))

                        fig_time_series.add_trace(go.Scatter(
                            x=segment['time'], y=segment['YSplined'],
                            mode='lines',
                            name=f"{obj} - Y",
                            line=dict(color=color, dash='dot'),
                            legendgroup=str(obj),
                            showlegend=False
                        ))

                        fig_time_series.add_trace(go.Scatter(
                            x=segment['time'], y=segment['ZSplined'],
                            mode='lines',
                            name=f"{obj} - Z",
                            line=dict(color=color, dash='dash'),
                            legendgroup=str(obj),
                            showlegend=False
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

