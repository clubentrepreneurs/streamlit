import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# --- STYLE CSS (Tentative de masquage total) ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    /* Masquage du logo Streamlit en bas à droite sur mobile */
    img[alt="Streamlit logo"] {display: none;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. CHARGEMENT DU PDF ---
PDF_PERMANENT = "Candidater.pdf"

@st.cache_resource
def charger_donnees(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            nb_pages = len(reader.pages)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text, nb_pages
        except:
            return None, 0
    return None, 0

texte_universite, pages_totales = charger_donnees(PDF_PERMANENT)

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("📂 Source Officielle")
    
    if texte_universite:
        # On affiche une jolie boîte avec les infos du doc
        st.success(f"✅ **Document :** {PDF_PERMANENT}")
        st.caption(f"📄 Taille : {pages_totales} pages analysées")
        st.write("---")
    else:
        st.error("❌ Document source introuvable.")

    st.header("⚙️ Réglages IA")
    temp = st.slider("Créativité", 0.0, 1.0, 0.2)
    max_t = st.number_input("Longueur max", 100, 2000, 600)
    
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question sur le guide de candidature..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("Je ne peux pas répondre sans le document source.")
        else:
            try:
                with st.spinner("Recherche dans le document..."):
                    # On envoie un extrait suffisant (environ 15-20 pages)
                    contexte = texte_universite[:45000]
                    
                    system_prompt = f"""Tu es l'assistant officiel de l'université. 
                    Réponds UNIQUEMENT en te basant sur le document suivant : {PDF_PERMANENT}.
                    Si la réponse n'est pas dedans, dis que tu ne sais pas.
                    
                    DOCUMENT :
                    {contexte}"""
                    
                    response = client.chat.complete(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temp,
                        max_tokens=max_t
                    )
                    
                    full_response = response.choices[0].message.content
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erreur : {e}")
