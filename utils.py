import streamlit as st
import pandas as pd

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