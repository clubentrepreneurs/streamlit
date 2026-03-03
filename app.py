import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Mistral 2026", layout="wide")
st.title("🎓 Assistant de Cours (Mistral AI)")

# Vérification de la clé API
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ Erreur : MISTRAL_API_KEY est introuvable dans les Secrets Streamlit.")
    st.stop()

# Initialisation du client Mistral (Version 2026)
client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. BARRE LATÉRALE (LECTURE PDF) ---
with st.sidebar:
    st.header("📁 Documents")
    uploaded_file = st.file_uploader("Uploader un PDF", type="pdf")
    
    if uploaded_file:
        with st.spinner("Lecture du contenu..."):
            try:
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        text += content + "\n"
                st.session_state['document_text'] = text
                st.success("✅ Cours chargé avec succès !")
            except Exception as e:
                st.error(f"Erreur lors de la lecture : {e}")

# --- 3. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Pose ta question sur le cours..."):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse de l'IA
    with st.chat_message("assistant"):
        if 'document_text' not in st.session_state:
            st.warning("⚠️ Veuillez d'abord uploader un PDF dans la barre latérale.")
        else:
            try:
                with st.spinner("Mistral analyse le document..."):
                    # On prépare le contexte (limité à ~15 000 mots pour la rapidité)
                    contexte = st.session_state['document_text'][:50000]
                    
                    full_prompt = f"""Tu es un assistant pédagogique. Utilise le texte du cours ci-dessous pour répondre à la question.
                    
                    TEXTE DU COURS :
                    {contexte}
                    
                    QUESTION DE L'ÉTUDIANT :
                    {prompt}"""
                    
                    # Appel à l'API Mistral (Nouvelle syntaxe)
                    chat_response = client.chat.complete(
                        model=MODEL,
                        messages=[{"role": "user", "content": full_prompt}]
                    )
                    
                    response_text = chat_response.choices[0].message.content
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"❌ Erreur Mistral : {str(e)}")
