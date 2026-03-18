import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# (Gardez votre bloc CSS hide_style ici...)

# --- SÉCURITÉ API ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ GOOGLE_API_KEY manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. CHARGEMENT DU PDF (Inchangé) ---
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
        except Exception:
            return None, 0
    return None, 0

texte_universite, pages_totales = charger_donnees(PDF_PERMANENT)

# --- 3. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question à l'assistant Gemini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("Document source manquant.")
        else:
            try:
                with st.spinner("Gemini analyse le document..."):
                    # On limite le texte pour ne pas dépasser les limites (bien que Gemini ait une large fenêtre)
                    contexte = texte_universite[:100000] 
                    
                    full_prompt = f"""Tu es l'assistant officiel de l'université. 
                    Utilise les informations suivantes pour répondre :
                    
                    CONTEXTE : {contexte}
                    
                    QUESTION : {prompt}"""
                    
                    response = model.generate_content(full_prompt)
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur Gemini : {e}")    if texte_universite:
        st.success(f"**Fichier :** {PDF_PERMANENT}")
        st.info(f"📄 **{pages_totales} pages** analysées.")
        st.write("---")
    else:
        st.error("❌ Fichier source absent sur GitHub.")

    st.header("⚙️ Réglages IA")
    temp = st.slider("Précision / Créativité", 0.0, 1.0, 0.2)
    max_t = st.number_input("Longueur max réponse", 100, 2000, 600)
    
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

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
            st.error("Document source manquant.")
        else:
            try:
                with st.spinner("Analyse en cours..."):
                    # Préparation du prompt pour Gemini
                    contexte = texte_universite[:100000]
                    full_prompt = f"Contexte: {contexte}\n\nQuestion: {prompt}"
                    
                    response = model.generate_content(full_prompt)
                    
                    response_text = response.text
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur Gemini : {e}")
