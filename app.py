from utils import *
from interface import *



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

    else:
        st.info("Veuillez importer un fichier CSV pour commencer.")

# ---------- Lancement de l'app ----------

if __name__ == "__main__":
    main()
