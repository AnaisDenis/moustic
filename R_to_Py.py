import streamlit as st
import pandas as pd
import plotly.express as px
import random
import time

st.set_page_config(layout="wide")  # Pleine largeur



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


import time
import streamlit as st

import time
import streamlit as st

import time
import streamlit as st


def interface_parametres(df):
    """Affiche les contrôles dans la barre latérale."""
    st.sidebar.header("Paramètres")
    time_min = df['time'].min()
    time_max = df['time'].max()

    # Initialisation des variables d'état
    if 'current_time' not in st.session_state:
        st.session_state.current_time = time_min
    if 'continuous_mode' not in st.session_state:
        st.session_state.continuous_mode = False

    # Slider et saisie manuelle synchronisés
    slider_val = st.sidebar.slider("Sélectionnez un temps via le slider",
                                 min_value=time_min,
                                 max_value=time_max,
                                 value=st.session_state.current_time,
                                 step=0.02)

    input_val = st.sidebar.number_input("Ou entrez un temps (manuellement)",
                                      min_value=time_min,
                                      max_value=time_max,
                                      value=slider_val,
                                      step=0.02)

    # Synchronisation des valeurs
    if input_val != slider_val:
        st.session_state.current_time = input_val
    else:
        st.session_state.current_time = slider_val

    st.sidebar.write(f"Temps sélectionné : {st.session_state.current_time:.2f}")

    # Bouton pour démarrer/arrêter le défilement
    if st.sidebar.button("▶️ Start Continuous" if not st.session_state.continuous_mode else "⏹️ Stop Continuous"):
        st.session_state.continuous_mode = not st.session_state.continuous_mode
        st.rerun()

    # Logique de défilement continu
    if st.session_state.continuous_mode:
        next_time = st.session_state.current_time + 0.02
        if next_time <= time_max:
            st.session_state.current_time = round(next_time, 2)
            time.sleep(0.5)  # Pause pour simuler le temps réel
            st.rerun()  # Actualise l'interface
        else:
            st.session_state.continuous_mode = False
            st.sidebar.warning("Fin des données atteinte.")

    return st.session_state.current_time


def generer_couleur_aleatoire():
    """Génère une couleur hexadécimale aléatoire."""
    return "#{:02x}{:02x}{:02x}".format(random.randint(0, 255),
                                        random.randint(0, 255),
                                        random.randint(0, 255))


def afficher_graphique(df, temps_max):
    window = 0.02

    for col in ['XSplined', 'YSplined', 'ZSplined', 'object', 'time']:
        if col not in df.columns:
            st.error(f"Colonne manquante : {col}")
            return

    df_temps = df[(df['time'] >= temps_max) & (df['time'] < temps_max + window)]

    if df_temps.empty:
        st.warning(f"Aucune donnée entre {temps_max:.2f} et {temps_max + window:.2f}")
        return

    objets_uniques = df_temps['object'].unique()
    couleurs = {obj: generer_couleur_aleatoire() for obj in objets_uniques}
    df_temps['color'] = df_temps['object'].map(couleurs)

    # 🔲 Cases à cocher individuelles dans la barre latérale
    st.sidebar.subheader("Afficher les graphiques")
    show_xy = st.sidebar.checkbox("X en fonction de Y", value=True)
    show_xz = st.sidebar.checkbox("X en fonction de Z", value=True)
    show_yz = st.sidebar.checkbox("Y en fonction de Z", value=True)
    show_3d = st.sidebar.checkbox("Vue 3D", value=True)

    col1, col2 = st.columns(2)

    if show_xy:
        with col1:
            fig_xy = px.scatter(
                df_temps, x='YSplined', y='XSplined',
                hover_name='object', color='color',
                title="X en fonction de Y",
                labels={'YSplined': 'Y', 'XSplined': 'X'}
            )
            st.plotly_chart(fig_xy)

    if show_xz:
        with col2:
            fig_xz = px.scatter(
                df_temps, x='ZSplined', y='XSplined',
                hover_name='object', color='color',
                title="X en fonction de Z",
                labels={'ZSplined': 'Z', 'XSplined': 'X'}
            )
            st.plotly_chart(fig_xz)

    if show_yz:
        with col1:
            fig_yz = px.scatter(
                df_temps, x='ZSplined', y='YSplined',
                hover_name='object', color='color',
                title="Y en fonction de Z",
                labels={'ZSplined': 'Z', 'YSplined': 'Y'}
            )
            st.plotly_chart(fig_yz)

    if show_3d:
        with col2:
            fig_3d = px.scatter_3d(
                df_temps,
                x='XSplined',
                y='YSplined',
                z='ZSplined',
                color='color',
                hover_name='object',
                title="Vue 3D",
                labels={'XSplined': 'X', 'YSplined': 'Y', 'ZSplined': 'Z'}
            )
            fig_3d.update_traces(marker=dict(size=3))
            fig_3d.update_layout(showlegend=False)
            st.plotly_chart(fig_3d)




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
