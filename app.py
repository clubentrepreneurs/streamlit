import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# --- STYLE CSS (Interface épurée) ---
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    .block-container {padding-top: 2rem;}
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🎓 Assistant Officiel des Étudiants</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Session 2026 - Guide des Candidatures</p>", unsafe_allow_html=True)
st.write("---")

# --- SÉCURITÉ API ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Configuration incomplète : GOOGLE_API_KEY manquante dans les Secrets.")
    st.stop()

# Initialisation du modèle Gemini
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Utilisation du nom de modèle le plus compatible en 2026
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erreur d'initialisation Google AI : {e}")
    st.stop()

# --- 2. CHARGEMENT DU PDF ---
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

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("📂 Document Source")
    if texte_universite:
        st.success(f"Fichier : {PDF_PERMANENT}")
        st.info(f"📄 {pages_totales} pages analysées.")
    else:
        st.error(f"❌ Fichier '{PDF_PERMANENT}' introuvable sur le dépôt GitHub.")
    
    if st.button("🗑️ Effacer la discussion"):
        st.session_state.messages = []
        st.rerun()

# --- 4. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Comment puis-je vous aider pour votre candidature ?"):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Génération de la réponse
    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("Je ne peux pas répondre car le document de référence est absent.")
        else:
            try:
                with st.spinner("Analyse du guide en cours..."):
                    # Préparation du contexte (limité pour la performance, Gemini gère très bien 50k caractères)
                    contexte_extrait = texte_universite[:60000]
                    
                    # Prompt structuré pour forcer l'usage du PDF
                    prompt_final = f"""Tu es l'assistant pédagogique officiel. 
                    Utilise exclusivement les informations suivantes issues du guide de candidature pour répondre. 
                    Si l'information n'est pas dans le texte, réponds que tu ne sais pas et oriente l'étudiant vers le secrétariat.

                    GUIDE DE CANDIDATURE (CONTEXTE) :
                    {contexte_extrait}

                    QUESTION DE L'ÉTUDIANT :
                    {prompt}
                    
                    RÉPONSE (en français, polie et concise) :"""

                    # Appel à l'API Gemini
                    response = model.generate_content(prompt_final)
                    
                    if response.text:
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    else:
                        st.warning("Le modèle n'a pas pu générer de réponse. Réessayez avec une autre question.")
                        
            except Exception as e:
                # Gestion des erreurs d'API ou de quota
                st.error(f"Désolé, une erreur est survenue : {e}")        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text, len(reader.pages)
        except Exception:
            return None, 0
    return None, 0

texte_universite, pages_totales = charger_donnees(PDF_PERMANENT)

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("📂 Source")
    if texte_universite:
        st.success(f"Document : {PDF_PERMANENT}")
        st.info(f"📄 {pages_totales} pages analysées.")
    else:
        st.error("❌ Fichier PDF non trouvé sur GitHub.")

# --- 4. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("Impossible de répondre : document source absent.")
        else:
            try:
                with st.spinner("Recherche dans le document..."):
                    # On envoie les 50 000 premiers caractères pour rester prudent
                    contexte = texte_universite[:50000]
                    instruction = f"Tu es l'assistant de l'université. Réponds en utilisant ce contexte :\n\n{contexte}\n\nQuestion : {prompt}"
                    
                    response = model.generate_content(instruction)
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur : {e}")
