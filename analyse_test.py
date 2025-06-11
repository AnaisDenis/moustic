import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Dossier contenant les fichiers CSV
DOSSIER = 'C:/Users/2025ad007/Documents/Detection_Couple/Résultat_test_1/couple_M'

# Liste pour stocker les DataFrames
df_list = []

# Parcours de tous les fichiers CSV dans le dossier
for fichier in os.listdir(DOSSIER):
    if fichier.endswith('.csv'):
        chemin_fichier = os.path.join(DOSSIER, fichier)
        try:
            df = pd.read_csv(chemin_fichier)
            df_list.append(df)
        except Exception as e:
            print(f"Erreur lors de la lecture de {fichier} : {e}")

# Concaténation de tous les DataFrames en un seul
data = pd.concat(df_list, ignore_index=True)

# --- Analyse 1 : Comptage des types d'interaction ---
if 'type' in data.columns:
    type_counts = data['type'].value_counts()
    print("\nNombre de chaque type d'interaction :")
    print(type_counts)

    # Affichage en histogramme
    plt.figure(figsize=(10, 6))
    sns.countplot(y='type', data=data, order=type_counts.index)
    plt.title("Répartition des types d'interactions")
    plt.xlabel("Nombre")
    plt.ylabel("Type")
    plt.tight_layout()
    plt.show()
else:
    print("Colonne 'type' absente des données.")

# --- Analyse 2 : Histogramme des durées ---
if 'duration' in data.columns:
    print("\nStatistiques descriptives sur les durées d'interaction :")
    print(data['duration'].describe())

    plt.figure(figsize=(10, 6))
    sns.histplot(data['duration'].dropna(), bins=30, kde=True)
    plt.title("Distribution des durées d'interaction")
    plt.xlabel("Durée")
    plt.ylabel("Fréquence")
    plt.tight_layout()
    plt.show()
else:
    print("Colonne 'duration' absente des données.")

# --- Analyse 3 : Histogramme des durations_couple pour le type 'couple_fusion_to_rupture' ---
if 'duration_couple' in data.columns and 'type' in data.columns:
    couple_data = data[data['type'] == 'couple_fusion_to_rupture']
    if not couple_data.empty:
        print("\nStatistiques descriptives sur les durations_couple pour le type 'couple_fusion_to_rupture' :")
        print(couple_data['duration_couple'].describe())

        plt.figure(figsize=(10, 6))
        sns.histplot(couple_data['duration_couple'].dropna(), bins=30, kde=True)
        plt.title("Distribution des durations_couple pour le type 'couple_fusion_to_rupture'")
        plt.xlabel("Durée du couple")
        plt.ylabel("Fréquence")
        plt.tight_layout()
        plt.show()
    else:
        print("Aucune donnée pour le type 'couple_fusion_to_rupture'.")
else:
    print("Colonnes 'duration_couple' ou 'type' absentes des données.")
