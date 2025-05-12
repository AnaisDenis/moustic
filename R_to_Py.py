import streamlit as st
import pandas as pd
import plotly.express as px
import random



# ---------- Fonctions utilitaires ----------

def charger_donnees(uploaded_file):
    """Charge le fichier CSV avec un séparateur ';'."""
    try:
        df = pd.read_csv(uploaded_file, sep=';')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None

def verifier_colonne_time(df):
    """Vérifie et convertit la colonne 'time' en numérique."""
    if 'time' not in df.columns:
        st.error("La colonne 'time' est introuvable dans le fichier CSV.")
        return None
    df['time'] = pd.to_numeric(df['time'], errors='coerce')
    return df

def interface_parametres(df):
    """Affiche les contrôles dans la barre latérale."""
    st.sidebar.header("Paramètres")
    time_min = df['time'].min()

    time_max = df['time'].max()

    # Slider et saisie manuelle synchronisés
    slider_val = st.sidebar.slider("Sélectionnez un temps via le slider",
                                   min_value=time_min,
                                   max_value=time_max,
                                   value=time_min,
                                   step=0.02)

    input_val = st.sidebar.number_input("Ou entrez un temps (manuellement)",
                                        min_value=time_min,
                                        max_value=time_max,
                                        value=slider_val,
                                        step=0.02)

    # Synchronisation des valeurs
    if input_val != slider_val:
        slider_val = input_val

    st.sidebar.write(f"Temps sélectionné : {slider_val:.2f}")
    return slider_val


def generer_couleur_aleatoire():
    """Génère une couleur hexadécimale aléatoire."""
    return "#{:02x}{:02x}{:02x}".format(random.randint(0, 255),
                                        random.randint(0, 255),
                                        random.randint(0, 255))


def afficher_graphique(df, temps_max):
    """Affiche les points X/Y entre [temps_max, temps_max + 0.02] avec identifiants et couleurs uniques."""
    window = 0.02

    # Vérification des colonnes nécessaires
    for col in ['XSplined', 'YSplined', 'object']:
        if col not in df.columns:
            st.error(f"Colonne manquante : {col}")
            return

    # Calcul des bornes globales pour X et Y
    x_min, x_max = df['XSplined'].min(), df['XSplined'].max()
    y_min, y_max = df['YSplined'].min(), df['YSplined'].max()

    # Filtrage des données dans la fenêtre temporelle
    df_temps = df[(df['time'] >= temps_max) & (df['time'] < temps_max + window)]

    if df_temps.empty:
        st.warning(f"Aucune donnée entre {temps_max:.2f} et {temps_max + window:.2f}")
        return

    # Générer un dictionnaire de couleurs pour chaque objet
    objets_uniques = df_temps['object'].unique()
    couleurs = {obj: generer_couleur_aleatoire() for obj in objets_uniques}

    # Créer une colonne 'color' dans le DataFrame avec la couleur correspondante à chaque 'object'
    df_temps['color'] = df_temps['object'].map(couleurs)

    # Création du graphique avec couleur associée à chaque objet
    fig = px.scatter(
        df_temps,
        x='XSplined',
        y='YSplined',
        hover_name='object',
        color='color',  # Utiliser la couleur associée à chaque object
        title=f"Objets entre t = {temps_max:.2f} et t + 0.02",
        labels={'XSplined': 'X', 'YSplined': 'Y'}
    )

    # Fixer les axes
    fig.update_xaxes(range=[x_min, x_max])
    fig.update_yaxes(range=[y_min, y_max])
    fig.update_layout(height=500)

    st.plotly_chart(fig)


# ---------- Code principal ----------

def main():
    st.title("Détection de couples")

    # Chargement du fichier
    with st.sidebar:
        uploaded_file = st.file_uploader("Importez un fichier CSV", type=["csv"])

    if uploaded_file is not None:
        df = charger_donnees(uploaded_file)
        if df is not None:
            df = verifier_colonne_time(df)
            if df is not None:
                temps_max = interface_parametres(df)
                afficher_graphique(df, temps_max)

    else:
        st.info("Veuillez importer un fichier CSV pour commencer.")

# ---------- Lancement de l'app ----------

if __name__ == "__main__":
    main()
