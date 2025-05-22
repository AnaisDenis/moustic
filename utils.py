import pandas as pd
import random
import numpy as np
import base64
import io




random.seed(42)



######################TRAITEMENTS DATA ####################################################

def assign_colors_to_objects(objects):
    """Assigne une couleur unique à chaque objet à partir de la palette"""
    # Assurez-vous que tous les objets sont convertis en chaînes
    objects_str = [str(obj) for obj in objects]
    return {obj: color_palette[i % len(color_palette)] for i, obj in enumerate(sorted(objects_str))}

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

# Liste de couleurs spécifiques (vous pouvez en ajouter plus si nécessaire)
color_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5"
]

####################FONCTIONS DETECTION DE COUPLES #########################################

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



################# FONCTION GRAPHIQUES #####################################################


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


