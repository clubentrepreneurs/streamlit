import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# --- STYLE CSS ---
hide_style = """
    <style>
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display:none;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🎓 Assistant Officiel</h1>", unsafe_allow_html=True)
st.write("---")

# --- SÉCURITÉ API ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ GOOGLE_API_KEY manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

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
