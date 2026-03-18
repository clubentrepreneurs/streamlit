import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

st.set_page_config(page_title="Assistant 2026")
st.title("🎓 Assistant Université")

# Config API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Ajoutez GOOGLE_API_KEY dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- SOLUTION AU 404 : Tester les modèles disponibles ---
@st.cache_resource
def get_model():
    # On essaie d'abord le plus moderne, sinon on se rabat sur le pro
    for m in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
        try:
            model = genai.GenerativeModel(m)
            # Petit test rapide
            model.generate_content("test")
            return model
        except:
            continue
    return None

model = get_model()

# --- CHARGEMENT PDF ---
@st.cache_resource
def load_data():
    if os.path.exists("Candidater.pdf"):
        pdf = PdfReader("Candidater.pdf")
        return "\n".join([page.extract_text() for page in pdf.pages])
    return None

text = load_data()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Votre question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if not model:
            st.error("Aucun modèle Gemini n'est accessible avec cette clé.")
        elif not text:
            st.error("Fichier Candidater.pdf non trouvé.")
        else:
            res = model.generate_content(f"Contexte: {text[:30000]}\n\nQuestion: {prompt}")
            st.markdown(res.text)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
