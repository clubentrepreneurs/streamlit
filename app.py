import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide")
st.title("🎓 Assistant Officiel des Étudiants")

if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. CHARGEMENT AUTOMATIQUE DU COURS ---
# On définit le nom du fichier qui doit être sur ton GitHub
PDF_PERMANENT = "candidater.pdf"

@st.cache_resource
def charger_cours_permanent(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text
        except Exception as e:
            return f"Erreur de lecture : {e}"
    return None

# On charge le texte une seule fois pour tout le monde
texte_universite = charger_cours_permanent(PDF_PERMANENT)

# --- 3. INTERFACE ---
if texte_universite:
    st.success(f"📚 Base de connaissances chargée : {PDF_PERMANENT}")
else:
    st.warning("⚠️ Aucun fichier de cours permanent trouvé. Utilisez la barre latérale pour tester.")

with st.sidebar:
    st.header("⚙️ Administration")
    # On laisse l'option d'uploader un autre PDF pour les tests
    uploaded_file = st.file_uploader("Mettre à jour le document (optionnel)", type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text_upload = ""
        for page in reader.pages:
            text_upload += page.extract_text() + "\n"
        st.session_state['document_text'] = text_upload
        st.info("Document temporaire chargé pour cette session.")

# --- 4. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pose ta question sur le cours..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Priorité au texte uploadé, sinon texte permanent
        context_final = st.session_state.get('document_text', texte_universite)
        
        if not context_final:
            st.error("Désolé, je n'ai aucune donnée pour répondre.")
        else:
            try:
                with st.spinner("Analyse en cours..."):
                    contexte_limite = context_final[:50000]
                    full_prompt = f"Utilise ce cours pour répondre : {contexte_limite}\n\nQuestion : {prompt}"
                    
                    chat_response = client.chat.complete(
                        model=MODEL,
                        messages=[{"role": "user", "content": full_prompt}]
                    )
                    
                    response_text = chat_response.choices[0].message.content
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
