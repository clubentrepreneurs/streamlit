import streamlit as st
import os
from pypdf import PdfReader

# --- 1. COMPATIBILITÉ MISTRAL AI ---
# Ce bloc gère les différences entre les versions du SDK Mistral
try:
    from mistralai import Mistral
    MISTRAL_V1 = True
except ImportError:
    try:
        from mistralai.client import MistralClient
        MISTRAL_V1 = False
    except ImportError:
        st.error("La bibliothèque 'mistralai' n'est pas installée. Vérifiez votre requirements.txt.")
        st.stop()

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# --- STYLE CSS (Masquage total du header Streamlit) ---
hide_style = """
    <style>
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    .stDeployButton {display:none;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# --- TITRE POSITIONNÉ ---
st.markdown("<h1 style='text-align: center; margin-top: 0px;'>🎓 Assistant Officiel des Étudiants</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Session 2026 - Guide des Candidatures</p>", unsafe_allow_html=True)
st.write("---")

# --- SÉCURITÉ API & INITIALISATION CLIENT ---
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante dans les Secrets.")
    st.stop()

api_key = st.secrets["MISTRAL_API_KEY"]
MODEL = "mistral-small-latest"

# Initialisation du client selon la version détectée
if MISTRAL_V1:
    client = Mistral(api_key=api_key)
else:
    client = MistralClient(api_key=api_key)

# --- 3. CHARGEMENT DU PDF ---
# Assurez-vous que Candidater.pdf est dans le même dossier que app.py
PDF_PERMANENT = "Candidater.pdf"

@st.cache_resource
def charger_donnees(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text, len(reader.pages)
        except Exception as e:
            return None, 0
    return None, 0

texte_universite, pages_totales = charger_donnees(PDF_PERMANENT)

# --- 4. BARRE LATÉRALE ---
with st.sidebar:
    st.title("📂 Source Officielle")
    if texte_universite:
        st.success(f"**Fichier :** {PDF_PERMANENT}")
        st.info(f"📄 **{pages_totales} pages** analysées.")
    else:
        st.error(f"❌ Fichier '{PDF_PERMANENT}' introuvable.")
        st.info("Vérifiez qu'il est bien à la racine de votre dossier sur GitHub.")

    st.header("⚙️ Réglages IA")
