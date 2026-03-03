import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from pypdf import PdfReader

# 1. CONFIGURATION
st.set_page_config(page_title="Assistant Mistral AI", layout="wide")
st.title("🎓 Assistant de Cours (Propulsé par Mistral)")

if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ Ajoute MISTRAL_API_KEY dans tes Secrets Streamlit.")
    st.stop()

client = MistralClient(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest" # Modèle rapide et efficace

# 2. LECTURE DU PDF
with st.sidebar:
    st.header("📁 Documents")
    uploaded_file = st.file_uploader("Uploader un PDF", type="pdf")
    
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        st.session_state['document_text'] = text
        st.success("✅ Cours chargé !")

# 3. CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pose ta question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if 'document_text' not in st.session_state:
            st.warning("Uploade un PDF d'abord.")
        else:
            try:
                # On prépare le contexte
                context = st.session_state['document_text'][:20000]
                full_content = f"Utilise ce cours pour répondre : {context}\n\nQuestion : {prompt}"
                
                messages = [ChatMessage(role="user", content=full_content)]
                
                # Appel à Mistral
                chat_response = client.chat(model=MODEL, messages=messages)
                
                response_text = chat_response.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur Mistral : {str(e)}")
