import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Étudiant Ultra-Stable", layout="wide")

try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=GEMINI_KEY)
    else:
        st.error("⚠️ Clé API non trouvée dans les Secrets Streamlit (GEMINI_API_KEY).")
        st.stop()
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

# --- 2. INITIALISATION DU MODÈLE ---
@st.cache_resource
def load_stable_model():
    model_names = [
        'models/gemini-1.5-flash', 
        'gemini-1.5-flash', 
        'models/gemini-pro',
        'gemini-pro'
    ]
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # Test de connexion ultra-rapide
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = load_stable_model()

if model is None:
    st.error("❌ Impossible de contacter Gemini. Vérifie ta clé API ou ta connexion.")
    st.stop()

# --- 3. INTERFACE ---
st.title("🎓 Assistant de Cours (Version Stable)")

with st.sidebar:
    st.header("📁 Documents")
    uploaded_file = st.file_uploader("Uploader ton cours (PDF)", type="pdf")
    
    if uploaded_file:
        with st.spinner("Lecture du PDF..."):
            try:
                reader = PdfReader(uploaded_file)
                text_content = ""
                for page in reader.pages:
                    text_content += page.extract_text()
                st.session_state['cours_texte'] = text_content
                st.success("Cours chargé avec succès !")
            except Exception as e:
                st.error(f"Erreur lors de la lecture du PDF : {e}")

# --- 4. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages précédents
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Pose ta question sur le cours..."):
    # On ajoute la question de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse de l'IA
    with st.chat_message("assistant"):
        if 'cours_texte' not in st.session_state:
            st.warning("Veuillez d'abord uploader un PDF dans la barre latérale.")
        else:
            try:
                with st.spinner("L'IA réfléchit..."):
                    # On limite le contexte pour rester dans les clous de l'API
                    contexte = st.session_state['cours_texte'][:40000]
                    
                    instruction = f"""Tu es un tuteur académique. Utilise le texte du cours pour répondre.
                    
                    TEXTE DU COURS :
                    {contexte}
                    
                    QUESTION :
                    {prompt}"""
                    
                    response = model.generate_content(instruction)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Désolé, une erreur est survenue lors de la génération : {e}")
