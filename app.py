import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import qdrant_client
import os

# --- 1. CONFIGURATION ET CONNEXIONS ---
st.set_page_config(page_title="UniBot RAG 2026", layout="wide")

# Récupération des clés depuis les Secrets Streamlit
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    Q_URL = st.secrets["QDRANT_URL"]
    Q_KEY = st.secrets["QDRANT_API_KEY"]
except KeyError:
    st.error("⚠️ Clés API manquantes dans les Secrets Streamlit !")
    st.stop()

# Initialisation des modèles IA
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_KEY)

# Connexion au client Qdrant
client = qdrant_client.QdrantClient(url=Q_URL, api_key=Q_KEY)
COLLECTION_NAME = "universite_savoir"

# --- 2. BARRE LATÉRALE : ADMINISTRATION (AJOUT DE FICHIERS) ---
with st.sidebar:
    st.title("⚙️ Administration")
    st.write("Alimentez la base de connaissances ici.")
    
    uploaded_files = st.file_uploader("Uploader des cours (PDF)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("🚀 Indexer les documents"):
        with st.spinner("Analyse et stockage des cours en cours..."):
            all_docs = []
            for uploaded_file in uploaded_files:
                # Sauvegarde temporaire locale
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Chargement du PDF
                loader = PyPDFLoader(uploaded_file.name)
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                docs = loader.load_and_split(text_splitter)
                all_docs.extend(docs)
                
                # Nettoyage du fichier temporaire
                os.remove(uploaded_file.name)
            
            # Envoi vers Qdrant
            Qdrant.from_documents(
                all_docs, 
                embeddings, 
                url=Q_URL, 
                api_key=Q_KEY, 
                collection_name=COLLECTION_NAME,
                force_recreate=False
            )
            st.success(f"C'est prêt ! {len(uploaded_files)} fichiers ajoutés.")

# --- 3. INTERFACE PRINCIPALE : CHAT ÉTUDIANT ---
st.title("🎓 Assistant Étudiant Intelligent")
st.markdown("Posez vos questions sur les cours indexés ci-dessous.")

# Configuration du moteur de recherche (Retriever)
vectorstore = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Modèle de réponse
template = """Tu es un assistant universitaire. Réponds à la question en utilisant UNIQUEMENT le contexte suivant. 
Si la réponse n'est pas dans le contexte, dis poliment que tu ne sais pas.

CONTEXTE :
{context}

QUESTION : 
{question}

RÉPONSE :"""
prompt_template = ChatPromptTemplate.from_template(template)

# Chaîne de traitement (RAG Chain)
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt_template
    | llm
    | StrOutputParser()
)

# Gestion de l'historique du chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Ex: Explique-moi le chapitre sur la thermodynamique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les cours..."):
            response = rag_chain.invoke(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
