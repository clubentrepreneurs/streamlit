import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# 1. INITIALISATION
st.set_page_config(page_title="Assistant Université", layout="centered")
st.title("🎓 Assistant Officiel 2026")

# 2. SÉCURITÉ API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("ERREUR : La clé GOOGLE_API_KEY est manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. LECTURE DU PDF
@st.cache_resource
def get_pdf_content(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            return full_text
        except Exception as e:
            return f"Erreur de lecture : {e}"
    return None

pdf_text = get_pdf_content("Candidater.pdf")

# 4. INTERFACE CHAT
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Affichage de l'historique
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Nouvelle question
if prompt := st.chat_input("Posez votre question ici..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not pdf_text:
            st.error("Le fichier 'Candidater.pdf' est introuvable sur GitHub.")
        else:
            try:
                # On utilise les 40 000 premiers caractères du PDF pour le contexte
                contexte = pdf_text[:40000]
                full_query = f"En t'appuyant sur ce document :\n{contexte}\n\nQuestion : {prompt}"
                
                response = model.generate_content(full_query)
                answer = response.text
                
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
