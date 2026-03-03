import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Assistant Étudiant Simplifié", layout="wide")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
except:
    st.error("Configurez votre GEMINI_API_KEY dans les Secrets.")
    st.stop()

# Initialisation du modèle
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🎓 Mon Assistant de Cours (Direct)")

# --- LECTURE DU PDF ---
with st.sidebar:
    st.header("1. Document")
    uploaded_file = st.file_uploader("Uploader ton PDF", type="pdf")
    
    if uploaded_file:
        with st.spinner("Lecture du fichier..."):
            reader = PdfReader(uploaded_file)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text()
            st.session_state['cours_texte'] = text_content
            st.success("Cours chargé !")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Pose ta question sur le cours..."):
    if 'cours_texte' not in st.session_state:
        st.warning("Veuillez d'abord uploader un PDF dans la barre latérale.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # On envoie le texte du cours DIRECTEMENT dans le contexte
            # Gemini 1.5 Flash accepte jusqu'à 1 million de mots, donc ça passe largement !
            prompt_complet = f"""Tu es un assistant prof. Utilise le texte du cours suivant pour répondre.
            
            TEXTE DU COURS :
            {st.session_state['cours_texte'][:30000]} 
            
            QUESTION DE L'ÉTUDIANT :
            {prompt}"""
            
            response = model.generate_content(prompt_complet)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
