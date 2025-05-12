import streamlit as st


def interface_parametres(df):
    """Affiche les contrôles dans la barre latérale."""
    st.sidebar.header("Paramètres")
    time_min = 0.0
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

